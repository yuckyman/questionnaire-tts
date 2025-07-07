# tts_web_player.py
"""
Generate a static web page that plays questionnaire items with high-quality neural TTS with **keyboard controls** and smarter **audio caching**.

Features
========
* ↑ Studio-grade synthesis via **edge-tts** (free Microsoft neural voices).
* ↔️   Buttons **and** keyboard shortcuts  
  * **← / →** – previous / next item  
  * **space / R** – replay current audio.
* 🏃‍♂️  One-shot build: creates `tts_site/` with MP3s + `index.html`, then serves on
  `http://localhost:8000`.
* ⚡  Caching: skips synthesis if the MP3 already exists unless `--force` is given.

Install
-------
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

Usage
-----
```bash
python tts_web_player.py items.txt                  # build + serve
python tts_web_player.py --serve-only               # just re-serve existing site
python tts_web_player.py items.txt --force --voice en-US-GuyNeural  # rebuild audio
```

"""
from __future__ import annotations

import argparse
import asyncio
import http.server
import json
import os
import socketserver
import sys
import textwrap
import webbrowser
from pathlib import Path

import edge_tts
from jinja2 import Template
from tqdm import tqdm

# ---------------------------------------------------------------------------
# HTML template with keyboard listeners
# ---------------------------------------------------------------------------
HTML_TEMPLATE = Template(
    textwrap.dedent(
        """
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
          <meta charset=\"utf-8\" />
          <title>Questionnaire Player</title>
          <style>
             :root { color-scheme: light dark; }
             body { font-family: system-ui, sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0; }
             #controls { display:flex; gap:2rem; margin-top:2rem; }
             button { font-size:2rem; padding:0.5rem 1rem; border:none; background:#222; color:#fff; border-radius:0.5rem; cursor:pointer; }
             button:disabled { opacity:0.4; cursor:auto; }
             #current { font-size:1.5rem; margin:1rem auto; max-width:80%; text-align:center; line-height:1.4; }
             #item-number { font-size:1rem; color:#888; margin-bottom:1rem; }
          </style>
        </head>
        <body>
          <h1>PAI Items</h1>
          <div id=\"item-number\"></div>
          <div id=\"current\"></div>
          <div id=\"controls\">
            <button id=\"prev\">⬅️</button>
            <button id=\"replay\">🔁</button>
            <button id=\"next\">➡️</button>
          </div>
          <script>
            const items = {{ items_json | safe }};
            let idx = 0;
            let isPlaying = false;
            const audio = new Audio();
            const currentDiv = document.getElementById('current');
            const itemNumberDiv = document.getElementById('item-number');
            const prevBtn = document.getElementById('prev');
            const nextBtn = document.getElementById('next');
            const replayBtn = document.getElementById('replay');

            function updateButtons(){
                prevBtn.disabled = idx === 0 || isPlaying;
                nextBtn.disabled = idx === items.length-1 || isPlaying;
            }
            function playItem(){
                itemNumberDiv.textContent = `Item ${idx + 1} of ${items.length}`;
                currentDiv.textContent = items[idx].text;
                audio.src = items[idx].audio;
                updateButtons();
                audio.play();
            }
            prevBtn.addEventListener('click', ()=>{ if(idx>0 && !isPlaying){ idx--; playItem(); }});
            nextBtn.addEventListener('click', ()=>{ if(idx<items.length-1 && !isPlaying){ idx++; playItem(); }});
            replayBtn.addEventListener('click', ()=>{ if(!isPlaying){ audio.currentTime = 0; audio.play(); }});

            // audio event listeners
            audio.addEventListener('play', () => {
                isPlaying = true;
                updateButtons();
            });
            audio.addEventListener('ended', () => {
                isPlaying = false;
                updateButtons();
            });
            audio.addEventListener('pause', () => {
                isPlaying = false;
                updateButtons();
            });
            audio.addEventListener('error', () => {
                isPlaying = false;
                updateButtons();
                console.error('Audio failed to load');
            });

            // keyboard shortcuts
            document.addEventListener('keydown', e => {
              switch(e.key){
                case 'ArrowLeft':
                  e.preventDefault(); if(!isPlaying) prevBtn.click(); break;
                case 'ArrowRight':
                  e.preventDefault(); if(!isPlaying) nextBtn.click(); break;
                case ' ': // space bar
                case 'r':
                case 'R':
                  e.preventDefault(); if(!isPlaying) replayBtn.click(); break;
              }
            });

            window.onload = playItem;
          </script>
        </body>
        </html>
        """
    )
)

# ---------------------------------------------------------------------------
# TTS helpers
# ---------------------------------------------------------------------------
async def synthesize(text: str, outfile: Path, voice: str) -> None:
    """Render *text* to *outfile* with Edge Neural voice."""
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(str(outfile))

async def build_audio(items: list[str], voice: str, outdir: Path, force: bool) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for idx, line in enumerate(tqdm(items, desc="Synthesizing")):
        mp3_path = outdir / f"{idx:04d}.mp3"
        if force or not mp3_path.exists():
            await synthesize(line, mp3_path, voice)

# ---------------------------------------------------------------------------
# HTML + server helpers
# ---------------------------------------------------------------------------
def make_index(items: list[str], outdir: Path) -> None:
    mapping = [
        {"text": line, "audio": f"audio/{idx:04d}.mp3"}
        for idx, line in enumerate(items)
    ]
    html = HTML_TEMPLATE.render(items_json=json.dumps(mapping, ensure_ascii=False))
    (outdir / "index.html").write_text(html, encoding="utf-8")

class SilentRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # shhh

def serve(directory: Path, port: int = 8000) -> None:
    os.chdir(directory)
    with socketserver.TCPServer(("", port), SilentRequestHandler) as httpd:
        url = f"http://localhost:{port}/selection.html"
        print(f"Serving on {url} (Ctrl+C to stop)…")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

async def build_all_questionnaires(project_dir: Path, voice: str, force: bool) -> None:
    """Build all questionnaires in the questionnaires/ directory."""
    questionnaires_dir = Path.cwd() / "questionnaires"
    if not questionnaires_dir.exists():
        sys.exit("❌ questionnaires/ directory not found")
    
    project_dir.mkdir(exist_ok=True)
    questionnaire_cards = []
    
    # Find all .txt files in questionnaires/
    questionnaire_files = list(questionnaires_dir.glob("*.txt"))
    if not questionnaire_files:
        sys.exit("❌ No questionnaire files found in questionnaires/ directory")
    
    for questionnaire_file in tqdm(questionnaire_files, desc="Building questionnaires"):
        questionnaire_name = questionnaire_file.stem
        questionnaire_dir = project_dir / questionnaire_name
        audio_dir = questionnaire_dir / "audio"
        
        # Read items
        items = [line.strip() for line in questionnaire_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        
        # Build audio
        await build_audio(items, voice, audio_dir, force)
        
        # Create index.html for this questionnaire
        make_index(items, questionnaire_dir)
        
        # Create card for selection page
        card_html = f'''
        <div class="questionnaire-card" data-link="{questionnaire_name}/index.html">
          <div class="questionnaire-title">{questionnaire_name.replace('_', ' ').title()}</div>
          <div class="questionnaire-description">
            {len(items)} questions • {sum(len(item.split()) for item in items)} words
          </div>
          <div class="questionnaire-stats">
            Estimated duration: {len(items) * 15 // 60}:{len(items) * 15 % 60:02d}
          </div>
        </div>
        '''
        questionnaire_cards.append(card_html)
    
    # Create selection page
    selection_template = Path("selection_template.html").read_text(encoding="utf-8")
    selection_html = selection_template.replace("{{ questionnaire_cards | safe }}", "\n".join(questionnaire_cards))
    (project_dir / "selection.html").write_text(selection_html, encoding="utf-8")
    
    print(f"✅ Built {len(questionnaire_files)} questionnaires")
    print(f"📁 Site ready at {project_dir}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
async def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build & serve a questionnaire TTS web page")
    parser.add_argument("items_file", nargs="?", help="Text file with one item per line")
    parser.add_argument("--voice", default="en-US-JennyNeural", help="Edge neural voice name")
    parser.add_argument("--serve-only", action="store_true", help="Skip audio generation & just serve")
    parser.add_argument("--force", action="store_true", help="Regenerate audio even if it already exists")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--build-all", action="store_true", help="Build all questionnaires in questionnaires/ directory")
    args = parser.parse_args(argv)

    project_dir = Path.cwd() / "tts_site"
    
    if args.build_all:
        await build_all_questionnaires(project_dir, args.voice, args.force)
    elif not args.serve_only:
        if args.items_file:
            try:
                items = [line.strip() for line in Path(args.items_file).read_text(encoding="utf-8").splitlines() if line.strip()]
            except FileNotFoundError:
                sys.exit(f"❌ items_file '{args.items_file}' not found")
        else:
            items = [
                "Please state your full name.",
                "On a scale from one to ten, how would you rate your current mood?",
                "Have you experienced any headaches in the past week?",
            ]
        audio_dir = project_dir / "audio"
        project_dir.mkdir(exist_ok=True)
        await build_audio(items, args.voice, audio_dir, args.force)
        make_index(items, project_dir)

    if not (project_dir / "index.html").exists():
        sys.exit("❌ No site built yet; run without --serve-only first.")

    serve(project_dir, args.port)

if __name__ == "__main__":
    asyncio.run(main())