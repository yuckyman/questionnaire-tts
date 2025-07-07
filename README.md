# PAI TTS Web Player

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

# Install dependencies
uv sync
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
├── daily_health_check.txt
├── anxiety_assessment.txt
└── depression_screening.txt
```

Each `.txt` file should contain one question per line. The script will automatically:
- Create individual directories for each questionnaire
- Generate audio files for each question
- Build a selection page with questionnaire cards
- Show estimated duration and question count 