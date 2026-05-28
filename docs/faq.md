# FAQ

## General

### I don't have a GPU. Can I still use ClearCut?

**Yes.** ClearCut works without a GPU. It automatically detects available hardware and falls back to software encoding (x264) if no GPU is found. Silence removal, compositing, and captions all work on CPU — it's just slower for the final encode.

For caption generation (WhisperX), you'll want at least 8 GB of RAM. Transcription runs on CPU by default.

If you need GPU acceleration but don't have one locally, check out [Remote GPU](remote-gpu.md) — you can offload processing to a machine that has one.

### Can I just trim silence without running the full pipeline?

**Yes.** That's what `clearcut trim` is for:

```bash
clearcut trim --input raw.mp4 --output trimmed.mp4
```

It removes silence and nothing else. No captions, no compositing, no encoding changes — just a tighter edit with smooth jump cuts.

### How do I install on Windows?

1. **Install Python 3.10+** from [python.org](https://python.org)
2. **Install ffmpeg** — either via Chocolatey (`choco install ffmpeg`) or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
3. **Install ClearCut**: `pip install clearcut`

If you want the full feature set: `pip install "clearcut[all]"`

For PyTorch (silence detection acceleration), follow the [official PyTorch Windows install guide](https://pytorch.org/get-started/locally/).

### Why does ClearCut require ffmpeg?

ffmpeg is the industry-standard tool for video processing. It handles:

- **Decoding/encoding** all video formats (H.264, H.265, VP9, etc.)
- **Hardware acceleration** via NVENC, AMF, QSV
- **Lossless segment splicing** for silence removal
- **Filter graph** operations (colour grading, format conversion, transitions)
- **ASS subtitle burning**

ClearCut's approach: **use ffmpeg for what it's best at** (encode/decode/mux/filter), and use Python libraries (MoviePy, WhisperX) for the higher-level editing logic. This gives us the best of both worlds — Python's flexibility + ffmpeg's raw performance.

Without ffmpeg, ClearCut can't process any video files.

### Is there a web UI?

Not yet. ClearCut is a **command-line tool** designed for:

- Scripting and automation
- Integration into CI/CD pipelines
- Batch processing
- Headless/server environments

A web UI is on the roadmap for future releases. If you'd like to build one, the pipeline is fully importable as a Python library:

```python
from clearcut.models import PipelineConfig
from clearcut.pipeline import Pipeline

config = PipelineConfig(main="input.mp4", output="output.mp4")
pipeline = Pipeline(config)
pipeline.run()
```

## Technical

### How does silence removal work?

ClearCut uses [Silero-VAD](https://github.com/snakers4/silero-vad), a pre-trained neural network for voice activity detection. It:

1. Analyzes the audio track frame-by-frame
2. Identifies which segments contain speech (confidence > threshold)
3. Splices those segments together with small cross-fades at cut points

The result is a tightly-edited video where all dead air, pauses, and restarts are removed. No visual artifacts — just smooth jump cuts.

If you prefer, you can use `auto-editor` as an alternative backend.

### What is ASS format and why does ClearCut use it?

[Advanced SubStation Alpha (ASS)](http://www.tcax.org/docs/ass-specs.htm) is a subtitle format that supports:

- **Arbitrary positioning** — place text at any pixel coordinate
- **Karaoke-style word highlighting** — animate word-by-word
- **Advanced styling** — fonts, colors, outlines, shadows, gradients
- **Event timing** — precise start/end for each word

ClearCut generates ASS subtitles from WhisperX's word-level timestamps, then burns them into the video with ffmpeg's ASS filter. This gives us:

- **Word-by-word highlight animations** (like YouTube's auto-captions)
- **Pixel-perfect positioning** in any aspect ratio
- **No font dependency** on the playback device (they're burned in)

### Will ClearCut work with my camera's footage?

Probably yes. ClearCut accepts any video format that ffmpeg can decode — which is virtually everything: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.mts`, etc.

If you're getting errors, try re-encoding to a standard format first:

```bash
ffmpeg -i your_footage.mts -c:v libx264 -c:a aac output.mp4
```

### Can I use ClearCut in a Docker container?

Yes. See the [Installation](installation.md#using-docker) page for Docker usage. The container has all dependencies pre-installed.

### How do I add my own caption style?

Caption styles are defined in `clearcut/styles.py` as `CaptionStyle` Pydantic models. You can add a new preset:

```python
MY_STYLE = CaptionStyle(
    font="Comic Sans MS",
    color="&H00FF8800",  # orange
    size=56,
    position="bottom",
    bold=False,
    outline=2,
    shadow=1,
    margin_v=50,
    animation="fade",
)
```

Then add it to the `PRESETS` dictionary and it'll be available via `--style my_style`.

## Troubleshooting

### `ffmpeg not found` error

Install ffmpeg. See the [Installation](installation.md#installing-ffmpeg) page for your OS.

### `No module named 'torch'` when using silence removal

Install the silence extra:

```bash
pip install "clearcut[silence]"
```

### Captions don't match the video

If you're burning captions into a video that was format-converted, the ASS positioning uses the converted dimensions. This should work correctly because captions are generated **after** format conversion in the pipeline (see [Pipeline Stages](pipeline-stages.md)).

If captions are misaligned, ensure you're not running `transcribe` on a pre-conversion video and then burning into the converted one. Use the pipeline with `--captions --burn` instead.

### Processing is very slow

- Use hardware encoding: `--hardware nvenc` (or `amf`/`qsv`)
- Use a faster encoder preset: `--preset ultrafast`
- Install PyTorch (`pip install "clearcut[silence]"`) for faster silence detection
- Process shorter segments and merge them with `clearcut merge`

### Batch processing fails on some files

Use `--dry-run` first to check which files will be processed:

```bash
clearcut batch --dir ~/videos/ --output ~/output/ --dry-run
```

Problematic files may have unusual codecs or be corrupted. Re-encode them first with ffmpeg.
