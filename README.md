# Questionnaire TTS Web Player

Generate a static web page that plays questionnaire items with high-quality neural TTS with **keyboard controls** and smarter **audio caching**.

## Features

* ↑ Studio-grade synthesis via **edge-tts** (free Microsoft neural voices).
* ↔️   Buttons **and** keyboard shortcuts  
  * **← / →** – previous / next item  
  * **space / R** – replay current audio.
* 🏃‍♂️  One-shot build: creates `tts_site/` with MP3s + `index.html`, then serves on
  `http://localhost:8000`.
* ⚡  Caching: skips synthesis if the MP3 already exists unless `--force` is given.
* 📊 Item numbering display (1-based indexing)
* 🎵 Audio completion tracking (prevents skipping during playback)
* 📋 Multi-questionnaire support with selection page
* 🎯 Individual questionnaire directories with dedicated audio files

## Setup

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

git clone https://github.com/yuckyman/questionnaire-tts.git
cd questionnaire-tts
uv sync
uv run pai_tts.py --build-all
```

## Usage

```bash
# Build all questionnaires and serve selection page
uv run pai_tts.py --build-all

# Build single questionnaire
uv run pai_tts.py items.txt

# Just serve existing site
uv run pai_tts.py --serve-only

# Rebuild audio with different voice
uv run pai_tts.py --build-all --force --voice en-US-GuyNeural
```

## Windows Executable

A pre-built Windows executable is included: `pai_tts_v3.exe`

- **What is it?**
  - A standalone version of the TTS builder for Windows users. No Python or dependencies required.
- **How to use:**
  1. Place your questionnaire `.txt` files in the `questionnaires/` folder (same as with the Python version).
  2. Double-click `pai_tts_v3.exe` or run it from the command line:
     ```
     pai_tts_v3.exe --build-all
     ```
     or for a single questionnaire:
     ```
     pai_tts_v3.exe items.txt
     ```
  3. The output will be in the `tts_site/` folder, just like with the Python script.
- **Limitations:**
  - Only tested on Windows 10/11.
  - Some advanced features (like custom voices or serving via HTTP) may be limited compared to the Python version.
  - If you encounter issues, try running from the command prompt to see error messages.

## Available Voices

You can use any Microsoft Edge neural voice. Some popular ones:
- `en-US-JennyNeural` (default)
- `en-US-GuyNeural`
- `en-US-AriaNeural`
- `en-GB-RyanNeural`
- `en-GB-SoniaNeural`

## Questionnaire Structure

Place your questionnaire files in the `questionnaires/` directory:

```
questionnaires/
├── PAI.txt
├── SASSI.txt
└── PSI-4.txt
```

Each `.txt` file should contain one question per line. The script will automatically:
- Create individual directories for each questionnaire
- Generate audio files for each question
- Build a selection page with questionnaire cards
- Show estimated duration and question count 
