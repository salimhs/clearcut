# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Intro/outro injection (`--intro`, `--outro`)
- Speed ramping (`--speed-segments start-end:multiplier`)
- Smart crop with face detection (`--smart-crop face`)
- Scene detection (`--detect-scenes`, `--max-clip-duration`)
- Color presets (`--color-preset warm/cool/vintage/vibrant/drama`)
- MkDocs documentation site
- Dockerfile for containerized deployment
- CONTRIBUTING.md with development guide
- GitHub issue templates (bug report, feature request)
- Template YAML preset files
- `--dry-run` flag for pipeline validation
- `clearcut metadata` command for video info
- `clearcut preview` command for ffplay preview
- Integration test suite for real pipeline stages
- LLM provider abstraction (Claude CLI)
- Plugin system with pre/post stage hooks
- Social upload stubs (TikTok, YouTube)
- Gradio web UI (`clearcut[web]`)

## [0.1.0] — 2025-05-27

### Added

- **Core pipeline:** silence removal, compositing, captions, encoding
- **Silence removal:** Silero-VAD with ffmpeg concat splicing
- **PiP compositing:** B-roll overlays with configurable position/size
- **Image insertion:** Timestamped static overlays with fade transitions
- **Caption generation:** WhisperX transcription → ASS subtitles
- **ASS caption styles:** default, modern, minimal, bold
- **Hardware encoding:** auto-detects NVENC, AMF, QSV
- **Watermark:** image overlay with position, scale, opacity
- **Audio ducking:** auto-volume reduction for background music
- **LUT colour grading:** `.cube` LUT file support
- **Color correction:** brightness, contrast, saturation controls
- **Batch processing:** process multiple videos in parallel
- **Video merging:** combine clips with transition effects
- **7 transition types:** fade, wipe, slide, dissolve, radial
- **YAML config:** file-based pipeline configuration
- **Remote GPU:** Tailscale-based GPU pipeline execution
- **GPU detection:** `clearcut info` for acceleration status
- **Progress bars:** Rich console progress indicators
- **Signal handling:** graceful interrupt on SIGINT/SIGTERM
- **Signal handling:** graceful interrupt on SIGINT/SIGTERM
- **Config validation:** Pydantic models with field validators
- **Error hierarchy:** typed exceptions (ConfigError, FileError)
- **Logging:** structured logging with verbose mode
- **Mypy typing:** strict type checking throughout
- **CI:** pre-commit hooks (ruff, trailing-whitespace, check-yaml)
- **Test suite:** 165+ unit tests with pytest
- **Demo scripts:** automated demo suite generation
