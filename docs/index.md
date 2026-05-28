# 🎬 ClearCut

**Raw footage to publish-ready video. One command.**

[![PyPI](https://img.shields.io/pypi/v/clearcut)](https://pypi.org/project/clearcut/)
[![License](https://img.shields.io/github/license/salimhs/clearcut)](https://github.com/salimhs/clearcut/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/salimhs/clearcut)](https://github.com/salimhs/clearcut)

*Silence removal · Picture-in-picture overlays · Image insertion · Styled captions · Hardware-accelerated encoding*

```bash
pip install clearcut
clearcut process --main take1.mp4 --context broll.mp4 --images diagram.png --captions --output final.mp4
```

ClearCut is an automated video editing pipeline for content creators. Feed it your raw footage, B-roll clips, and screenshots — it outputs a polished video ready for publishing.

## Use Cases

- 🎙️ **Talking-head videos** — remove dead air, silence, and restarts
- 📚 **Tutorials** — PiP screen recordings, styled captions
- 🏢 **Presentations** — insert slides at timestamps, B-roll overlays
- 🎥 **Content repurposing** — slice long recordings into publish-ready clips

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **Silence removal** | Detects and removes dead air using Silero-VAD (voice activity detection) or auto-editor fallback. Smooth jump cuts between speech segments. |
| 🖼️ **PiP overlays** | Composite B-roll or screen recordings as picture-in-picture in any corner. Configurable size and position. |
| 🏷️ **Image insertion** | Insert screenshots, diagrams, or slides at specific timestamps with fade transitions. |
| 📝 **Styled captions** | Transcribe with WhisperX (word-level timestamps), generate ASS subtitles, burn directly into video. Four style presets. |
| ⚡ **Hardware encoding** | Auto-detects NVIDIA NVENC, AMD AMF, Intel QSV, or falls back to software x264. |
| 🔌 **Modular** | Run the full pipeline or individual stages (`clearcut trim`, `clearcut transcribe`). |
| 🎨 **Colour presets** | Quick colour grading with warm, cool, vintage, vibrant, or drama presets. |
| 📐 **Format conversion** | Convert to 9:16 (TikTok/Reels), 1:1 (Instagram), or 16:9 widescreen with smart face-tracking crop. |
| 🔄 **Batch processing** | Process entire directories of videos in parallel. |
| 🖥️ **Remote GPU** | Offload processing to a remote GPU machine via Tailscale SSH. |

## Pipeline Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Raw footage  │   │ Silence      │   │ Compositing  │   │ Final encode │
│               │──▶│ removal      │──▶│ (lossless)   │──▶│ (HW accel)   │──▶ output.mp4
│ .mp4 / .mov   │   │ Silero-VAD   │   │ MoviePy PiP  │   │ NVENC/AMF    │
│ .mkv          │   │ auto-editor  │   │ + overlays   │   │ x264 fallback│
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                            │
                                     ┌──────┴──────┐
                                     │  Captions   │
                                     │  WhisperX   │
                                     │  → ASS subs │
                                     │  → ffmpeg   │
                                     └─────────────┘
```

The full pipeline includes up to 10 stages. See [Pipeline Stages](pipeline-stages.md) for the complete breakdown.

## Why ClearCut?

- 🎯 **Turnkey** — one command from raw footage to publish-ready video
- 🔒 **Works offline** — no cloud API calls, everything runs locally
- ⚡ **Hardware accelerated** — auto-detects NVENC, AMF, QSV
- 🧩 **Modular** — run the full pipeline or individual stages
- 📦 **Pip installable** — `pip install clearcut` and go
- 🐍 **Python** — easy to extend, script, and integrate

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Silence detection | [Silero-VAD](https://github.com/snakers4/silero-vad) ⭐ 9.1k | Enterprise-grade VAD, 98%+ accuracy |
| Silence removal | ffmpeg concat demuxer | Lossless segment splicing |
| Video compositing | [MoviePy](https://github.com/Zulko/moviepy) ⭐ 14.6k | `CompositeVideoClip` for PiP + overlays |
| Transcription | [WhisperX](https://github.com/m-bain/whisperX) ⭐ 22k | Word-level timestamps with forced alignment |
| Subtitles | ASS (Advanced SubStation Alpha) | Karaoke, styling, positioning |
| Encoding | ffmpeg (NVENC/AMF/QSV) | Hardware-accelerated final output |
| CLI framework | [Typer](https://github.com/fastapi/typer) | Type-annotated CLI with auto-generated help |
| Configuration | [Pydantic](https://github.com/pydantic/pydantic) | Declarative config models with validation |

## License

MIT
