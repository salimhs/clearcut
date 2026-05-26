# ClearCut

**Raw footage to publish-ready video. One command.**

ClearCut is an automated video editing pipeline for content creators. Feed it your raw talking-head footage, B-roll clips, and screenshots — it outputs a polished video with silence removed, picture-in-picture overlays, image inserts, and styled captions.

## Quick Start

```bash
pip install clearcut

# Full pipeline
clearcut process \
  --main take1.mp4 \
  --context broll.mp4 \
  --images diagram.png \
  --assets screenshot.jpg@30 \
  --captions \
  --style modern \
  --output final.mp4

# Standalone silence removal
clearcut trim --input raw.mp4

# Standalone captions
clearcut transcribe --input raw.mp4
```

## Pipeline

```
Raw footage → Silence removal → Compositing → Captions → Final encode
```

| Stage | Tool | Description |
|-------|------|-------------|
| Silence removal | Silero-VAD + ffmpeg | Detects speech segments, removes dead air |
| Compositing | MoviePy | PiP B-roll overlay, image insertion at timestamps |
| Captions | WhisperX → ASS → ffmpeg | Word-level timestamps, styled subtitles |
| Final encode | ffmpeg (auto-detects NVENC/AMF/QSV) | Hardware-accelerated output |

## CLI Reference

### `clearcut process`

| Flag | Default | Description |
|------|---------|-------------|
| `--main`, `-m` | required | Main talking-head video |
| `--context`, `-c` | — | B-roll video(s) for PiP overlay |
| `--images`, `-i` | — | Static images to overlay |
| `--assets`, `-a` | — | Timestamped images: `path@seconds` |
| `--style`, `-s` | `default` | Caption style: `default`, `modern`, `minimal`, `bold` |
| `--output`, `-o` | `output.mp4` | Output file path |
| `--no-silence` | — | Skip silence removal |
| `--silence-method` | `vad` | `vad` or `auto-editor` |
| `--captions` | — | Generate captions |
| `--burn` | — | Burn captions into video |
| `--preset` | `fast` | Encoder preset |
| `--hardware` | `auto` | Encoder: `auto`, `nvenc`, `amf`, `qsv`, `software` |

### `clearcut trim`

```bash
clearcut trim --input raw.mp4 --output trimmed.mp4 --method vad --threshold 0.5
```

### `clearcut transcribe`

```bash
clearcut transcribe --input raw.mp4 --style modern --output captions.ass
```

## Style Presets

| Style | Font | Size | Animation | Vibe |
|-------|------|------|-----------|------|
| `default` | Arial | 48 | none | Clean, safe |
| `modern` | Montserrat | 52 | word-highlight | YouTube-standard |
| `minimal` | Helvetica Neue | 40 | none | Subtle |
| `bold` | Impact | 64 | word-highlight | Eye-catching |

## Installation Options

```bash
pip install clearcut               # core (silence, compositing, encoding)
pip install clearcut[captions]      # + WhisperX transcription
pip install clearcut[silence]       # + Silero-VAD (on-device VAD)
pip install clearcut[scenes]        # + PySceneDetect
pip install clearcut[all]           # everything
```

## Architecture

```
clearcut/
├── __init__.py         # version
├── cli.py              # Typer CLI (process, trim, transcribe)
├── models.py           # Pydantic config models
├── pipeline.py         # Orchestrator: silence → composite → captions → encode
├── silence.py          # Silero-VAD detection + ffmpeg concat
├── compositor.py       # MoviePy PiP overlays + image insertion
├── captions.py         # WhisperX transcription + ASS subtitle generation
├── styles.py           # Caption style presets (ASS parameters)
└── encoder.py          # Hardware-accelerated ffmpeg encoding
```

## Why ClearCut?

- **Turnkey** — one command from raw footage to publish-ready video
- **Works offline** — no cloud API calls, everything runs locally
- **Hardware accelerated** — auto-detects NVENC, AMF, QSV
- **Flexible** — run the full pipeline or just the stage you need
- **Modular** — each stage is a standalone function you can import

## License

MIT
