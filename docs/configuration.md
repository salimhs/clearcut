# Configuration

ClearCut supports YAML configuration files for reusable project settings. Pass them with `--config`:

```bash
clearcut process --config project.yaml
```

## How It Works

CLI arguments and config file values are **merged**. The rule is simple:

> **CLI arguments always override config file values.**

If a value is not set via CLI and not set in the config file, the default is used.

This means you can have a base config file for your project and override specific values per run:

```bash
# Base config has --format 9:16, but override output path on the CLI
clearcut process --config project.yaml --output special_episode.mp4
```

## Complete Example

```yaml
# project.yaml
main: recordings/tutorial_day1.mp4
intro: assets/intro_v3.mp4
outro: assets/outro.mp4
context:
  - broll/screen_recording.mp4
  - broll/demo_clip.mp4
images:
  - assets/logo.png
  - assets/screenshot1.png
  - assets/screenshot2.png
assets:
  - path: assets/diagram.png
    seconds: 15
  - path: assets/chart.png
    seconds: 45
style: modern
output: output/final_video.mp4

# Pipeline control
remove_silence: true
silence_method: vad
generate_captions: true
burn_captions: true

# Audio
normalize: true
audio_target: -14.0

# Colour
brightness: 0.0
contrast: 1.0
saturation: 1.0
color_preset: warm

# Format
format: 9:16
smart_crop: face
smart_crop_smooth: 5

# Effects
punch_zoom: 1.05
hook_zoom: true
speed_segments:
  - "10-15:2.0"
  - "30-35:0.5"

# Transitions
transition: fade
transition_duration: 0.3

# Watermark
watermark: assets/logo.png
watermark_position: bottom-right
watermark_scale: 0.15
watermark_opacity: 0.7

# Background music
background_music: music/track.mp3
music_volume: 0.3

# Encoding
preset: slow
hardware: nvenc

# Scene detection
detect_scenes: true
max_clip_duration: 60.0

# Template (overrides individual flags)
template: tiktok
```

## Configuration Keys

### Input / Output

| Key | Default | Description |
|-----|---------|-------------|
| `main` | *(required)* | Main video file path |
| `intro` | — | Intro video clip to prepend |
| `outro` | — | Outro video clip to append |
| `intro_only` | `False` | Only inject intro |
| `outro_only` | `False` | Only append outro |
| `context` | `[]` | List of B-roll video paths |
| `images` | `[]` | List of static image paths |
| `assets` | `[]` | List of `{path, seconds}` objects |
| `style` | `default` | Caption style name |
| `output` | `output.mp4` | Output file path |

### Pipeline Control

| Key | Default | Description |
|-----|---------|-------------|
| `remove_silence` | `True` | Enable silence removal |
| `silence_method` | `vad` | `vad` or `auto-editor` |
| `generate_captions` | `False` | Enable caption generation |
| `burn_captions` | `False` | Burn captions into video |
| `detect_scenes` | `False` | Detect scene boundaries |
| `max_clip_duration` | `0.0` | Max segment duration (0 = off) |

### Audio

| Key | Default | Description |
|-----|---------|-------------|
| `normalize` | `True` | Normalize audio loudness |
| `audio_target` | `-14.0` | Target LUFS level |
| `duck_music` | — | Background music file |
| `background_music` | — | Auto-ducked music file |
| `music_volume` | `0.3` | Music volume (0.0–1.0) |

### Colour

| Key | Default | Description |
|-----|---------|-------------|
| `lut` | — | Path to `.cube` LUT file |
| `brightness` | `0.0` | -1.0 to 1.0 |
| `contrast` | `1.0` | 0.0 to 2.0 |
| `saturation` | `1.0` | 0.0 to 2.0 |
| `color_preset` | — | `warm`, `cool`, `vintage`, `vibrant`, `drama` |

### Format

| Key | Default | Description |
|-----|---------|-------------|
| `format` | `16:9` | `16:9`, `9:16`, or `1:1` |
| `smart_crop` | `center` | `center` or `face` |
| `smart_crop_smooth` | `5` | Face tracking smoothing window |

### Effects

| Key | Default | Description |
|-----|---------|-------------|
| `punch_zoom` | `0.0` | Zoom factor (0 = off) |
| `hook_zoom` | `False` | Quick zoom on first 2s |
| `speed_segments` | `[]` | List of `"start-end:multiplier"` strings |

### Transitions

| Key | Default | Description |
|-----|---------|-------------|
| `transition` | `fade` | `fade`, `wipeleft`, `wiperight`, `slideleft`, `slideright`, `dissolve`, `radial` |
| `transition_duration` | `0.3` | Duration in seconds |

### Watermark

| Key | Default | Description |
|-----|---------|-------------|
| `watermark` | — | Path to watermark image |
| `watermark_position` | `bottom-right` | Corner position |
| `watermark_scale` | `0.15` | Fraction of frame width |
| `watermark_opacity` | `0.7` | 0.0–1.0 |

### Encoding

| Key | Default | Description |
|-----|---------|-------------|
| `preset` | `fast` | `ultrafast`, `fast`, `medium`, `slow` |
| `hardware` | `auto` | `auto`, `nvenc`, `amf`, `qsv`, `software` |

### Template

| Key | Default | Description |
|-----|---------|-------------|
| `template` | — | `clean`, `tiktok`, `cinematic`, `bold` |
