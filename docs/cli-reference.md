# CLI Reference

ClearCut provides 9 commands for various video processing tasks.

## Global Options

These options are available on every command:

| Option | Description |
|--------|-------------|
| `--version, -v` | Show version and exit |
| `--verbose` | Enable verbose/debug logging |

---

## `clearcut process`

Run the full video editing pipeline. This is the main command that ties all stages together.

```bash
clearcut process --main input.mp4 --output final.mp4 [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-m, --main` | *(required)* | Main talking-head video file |
| `--intro` | — | Intro video clip to prepend |
| `--outro` | — | Outro video clip to append |
| `--intro-only` | `False` | Only inject intro (skip outro) |
| `--outro-only` | `False` | Only append outro (skip intro) |
| `-c, --context` | — | B-roll video(s) for PiP overlay (repeatable) |
| `-i, --images` | — | Static images to overlay sequentially (repeatable) |
| `-a, --assets` | — | Timestamped images: `path@seconds` (repeatable) |
| `-s, --style` | `default` | Caption style: `default`, `modern`, `minimal`, `bold` |
| `-o, --output` | `output.mp4` | Output video file path |
| `--no-silence` | *(flag)* | Skip silence removal stage |
| `--silence-method` | `vad` | Silence detection: `vad` or `auto-editor` |
| `--captions` | *(flag)* | Generate captions from audio |
| `--burn` | *(flag)* | Burn captions directly into video |
| `--preset` | `fast` | Encoder speed: `ultrafast`, `fast`, `medium`, `slow` |
| `--hardware` | `auto` | Encoder: `auto`, `nvenc`, `amf`, `qsv`, `software` |
| `--normalize/--no-normalize` | `True` | Normalize audio loudness |
| `--audio-target` | `-14.0` | Target loudness in LUFS |
| `--duck-music` | — | Background music file for ducking |
| `--background-music` | — | Auto-ducked background music file |
| `--music-volume` | `0.3` | Background music volume (0.0–1.0) |
| `--lut` | — | Path to `.cube` LUT file for colour grading |
| `--brightness` | `0.0` | Brightness adjustment (-1.0 to 1.0) |
| `--contrast` | `1.0` | Contrast adjustment (0.0 to 2.0) |
| `--saturation` | `1.0` | Saturation adjustment (0.0 to 2.0) |
| `--format` | `16:9` | Output aspect ratio: `16:9`, `9:16`, `1:1` |
| `--smart-crop` | `center` | Crop mode: `center` or `face` (face-tracking) |
| `--smart-crop-smooth` | `5` | Smoothing window for face tracking |
| `--transition` | `fade` | Transition type: `fade`, `wipeleft`, `wiperight`, `slideleft`, `slideright`, `dissolve`, `radial` |
| `--transition-duration` | `0.3` | Transition duration in seconds |
| `--punch-zoom` | `0.0` | Punch zoom factor (0=off, 1.05=5%, 1.15=15%) |
| `--hook-zoom/--no-hook-zoom` | `False` | Quick zoom on first 2 seconds |
| `--speed-segments` | — | Speed ramp segments in `start-end:multiplier` format (repeatable) |
| `--watermark` | — | Path to watermark/logo image |
| `--watermark-position` | `bottom-right` | Watermark position: `bottom-right`, `bottom-left`, `top-right`, `top-left` |
| `--watermark-scale` | `0.15` | Watermark scale (fraction of frame width) |
| `--watermark-opacity` | `0.7` | Watermark opacity (0.0–1.0) |
| `--detect-scenes` | `False` | Detect and split at scene boundaries |
| `--max-clip-duration` | `0.0` | Max segment duration in seconds (0 = no forced splits) |
| `--color-preset` | — | Colour preset: `warm`, `cool`, `vintage`, `vibrant`, `drama` |
| `--template` | — | Template preset: `clean`, `tiktok`, `cinematic`, `bold` |
| `--config` | — | YAML config file (CLI args override config values) |

### Example

```bash
clearcut process \
  --main talk.mp4 \
  --context broll.mp4 \
  --images slide1.png slide2.png \
  --assets diagram@30 \
  --style modern \
  --captions \
  --burn \
  --format 9:16 \
  --color-preset warm \
  --hook-zoom \
  --output final.mp4
```

---

## `clearcut trim`

Remove silence from a single video file.

```bash
clearcut trim --input raw.mp4 --output trimmed.mp4 --method vad --threshold 0.5
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | *(required)* | Video file to trim |
| `-o, --output` | *(auto)* | Output file (default: `input_trimmed.mp4`) |
| `--method` | `vad` | Detection method: `vad` or `auto-editor` |
| `--threshold` | `0.5` | VAD sensitivity (0.0–1.0, lower = more audio kept) |

---

## `clearcut transcribe`

Generate ASS subtitle captions from a video or audio file.

```bash
clearcut transcribe --input video.mp4 --style modern --output captions.ass
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | *(required)* | Video/audio file to transcribe |
| `-s, --style` | `default` | Caption style preset |
| `-o, --output` | *(auto)* | Output ASS file (default: `input.ass`) |

---

## `clearcut merge`

Merge multiple video clips into a single video with transitions.

```bash
clearcut merge --input clip1.mp4 clip2.mp4 clip3.mp4 --output merged.mp4
# Or use a directory:
clearcut merge --from-dir ./clips/ --pattern "*.mp4" --output merged.mp4
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | — | Input video clips to merge (repeatable) |
| `--from-dir` | — | Directory containing clips to merge |
| `--pattern` | `*.mp4` | Glob pattern when using `--from-dir` |
| `-o, --output` | `merged.mp4` | Output file path |
| `--transition` | `fade` | Transition type between clips |
| `--transition-duration` | `0.5` | Transition duration in seconds |
| `--hardware` | `auto` | Hardware encoder (`auto`, `nvenc`, `amf`, `qsv`, `software`) |

---

## `clearcut batch`

Batch process all videos in a directory through the full pipeline.

```bash
clearcut batch --dir ~/recordings/ --output ~/processed/ --pattern "*.mp4"
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dir` | *(required)* | Input directory containing video files |
| `-o, --output` | *(required)* | Output directory |
| `--pattern` | `*.mp4` | Glob pattern to filter files |
| `--dry-run` | `False` | Preview files without processing |
| `--max-workers` | `2` | Number of parallel workers |

---

## `clearcut repurpose`

Analyze a video with AI and repurpose it into short-form clips.

Uses Anthropic Claude to identify the most engaging segments, extracts them, and optionally runs each through the full editing pipeline.

```bash
clearcut repurpose --input long_video.mp4 --output ./clips/ --num-clips 5
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | *(required)* | Input video file |
| `-o, --output` | `output_clips` | Output directory for clips |
| `-n, --num-clips` | `5` | Number of clips to generate |
| `--min-duration` | `20.0` | Minimum clip duration in seconds |
| `--max-duration` | `90.0` | Maximum clip duration in seconds |
| `--no-process` | `False` | Skip pipeline processing (extract only) |
| `--template` | `tiktok` | Template to apply to each clip |
| `--model` | `sonnet` | Claude model (`sonnet`, `opus`, `haiku`) |
| `--captions` | `True` | Generate captions for clips |
| `--burn` | `True` | Burn captions into clips |
| `--style` | `default` | Caption style preset |

---

## `clearcut remote`

Run the pipeline on a remote GPU machine via Tailscale SSH.

Transfers your video to the remote machine, processes it with full CUDA/NVENC acceleration, and returns the result. No files are left on the remote machine.

```bash
clearcut remote --input video.mp4 --output result.mp4 --host 100.97.187.60 --captions
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | *(required)* | Input video file to process on remote GPU |
| `-o, --output` | *(required)* | Output file path |
| `--host` | `100.97.187.60` | Remote GPU machine Tailscale IP or hostname |
| `-u, --user` | — | SSH username for remote machine |
| `--captions` | `False` | Generate captions (requires GPU on remote) |
| `--template` | — | Template preset (`clean`, `tiktok`, `cinematic`, `bold`) |
| `--format` | `16:9` | Output format: `16:9`, `9:16`, `1:1` |
| `--no-silence` | `False` | Skip silence removal |

---

## `clearcut templates`

List all available pipeline templates and their configurations.

```bash
clearcut templates
```

Output example:

```
  clean — format=16:9, transition=fade, lufs=-14.0, sat=1.0, con=1.0, bri=+0.00
  tiktok — format=9:16, transition=wiperight, lufs=-13.0, sat=1.1, con=1.05, bri=+0.02
  cinematic — format=16:9, transition=dissolve, lufs=-16.0, sat=0.85, con=1.15, bri=-0.02
  bold — format=16:9, transition=slideleft, lufs=-14.0, sat=1.2, con=1.1, bri=+0.02
```

No options — just runs and shows the list.

---

## `clearcut info`

Show system information, GPU acceleration status, and dependency checks.

```bash
clearcut info
```

Checks for:

- GPU capabilities (CUDA, NVENC, AMF, QSV)
- ffmpeg availability
- ffprobe availability

No options — just runs and displays diagnostics.
