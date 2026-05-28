# Quick Start

## Real-World Example: Silence Removal + Captions + Format Conversion

This is the most common workflow — take a talking-head recording, remove the dead air, add captions, and export for social media:

```bash
clearcut process \
  --main ~/videos/tutorial_recording.mp4 \
  --captions \
  --burn \
  --style modern \
  --format 9:16 \
  --output ~/output/final_tiktok.mp4
```

### What Each Flag Does

| Flag | Purpose |
|------|---------|
| `--main` | Your main video file (the talking-head footage) |
| `--captions` | Enable transcription and caption generation |
| `--burn` | Burn captions directly into the video (hardcoded, not separate subtitle file) |
| `--style modern` | Use the "modern" caption style — Montserrat font with word-by-word highlight animation |
| `--format 9:16` | Convert to vertical 9:16 aspect ratio (TikTok / YouTube Shorts / Instagram Reels) |
| `--output` | Where to save the final video |

## TikTok Preset

For the fastest path to a TikTok-ready video, use the built-in `tiktok` template:

```bash
clearcut process \
  --main ~/videos/raw_talk.mp4 \
  --template tiktok \
  --captions \
  --burn \
  --output ~/output/tiktok_ready.mp4
```

The `tiktok` template automatically configures:

- Format conversion to **9:16** (vertical video)
- **Word-highlight** captions with Montserrat font
- **Slightly boosted** saturation (+1.1) and contrast (+1.05)
- **Punch zoom** (5%) for dynamic feel
- **Hook zoom** on the first 2 seconds
- **LUFS target** of -13 (louder, competitive for social media)
- **Wipe-right** transitions between segments

## Full Production Pipeline

This example shows nearly every feature at once:

```bash
clearcut process \
  --main talking_head.mp4 \
  --context screen_recording.mp4 \
  --images diagram.png chart.jpg \
  --assets screenshot@15 logo@120 \
  --style bold \
  --captions \
  --burn \
  --preset slow \
  --hardware nvenc \
  --output final.mp4
```

| Flag | What It Does |
|------|-------------|
| `--main` | Main talking-head video |
| `--context` | B-roll video shown as picture-in-picture |
| `--images` | Static images overlaid sequentially (5s each) |
| `--assets` | Images inserted at specific timestamps (`screenshot@15` = insert at 15s) |
| `--style bold` | Bold, eye-catching Impact font captions |
| `--captions --burn` | Generate and burn captions into the video |
| `--preset slow` | Slower encoding = better quality/smaller file |
| `--hardware nvenc` | Force NVIDIA NVENC hardware encoding |

## Basic Silence Removal

Just want to cut the dead air from a recording?

```bash
clearcut trim --input raw_recording.mp4 --output clean.mp4
```

That's it. ClearCut uses Silero-VAD by default to detect speech segments and removes everything else. Result: a tightly-edited video with smooth jump cuts.

## Batch Processing

Have a directory full of recordings? Process them all at once:

```bash
clearcut batch --dir ~/recordings/ --output ~/processed/ --pattern "*.mp4"
```

This processes every `.mp4` file in `~/recordings/` through the full pipeline in parallel (2 workers by default). To preview which files will be processed first:

```bash
clearcut batch --dir ~/recordings/ --output ~/processed/ --dry-run
```

## Next Steps

- See the [CLI Reference](cli-reference.md) for all available commands and options
- Explore [Pipeline Stages](pipeline-stages.md) to understand the processing order
- Check [Templates](templates.md) for ready-made configurations
- Learn about [Configuration](configuration.md) for reusable project settings
