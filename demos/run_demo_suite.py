#!/usr/bin/env python3
"""Demo runner: run ClearCut pipeline features and capture before/after frames."""
import subprocess, sys, os
from pathlib import Path

RAW = Path(__file__).parent / "raw"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return f"ERROR({r.returncode}): {r.stderr[:300]}"
    return r.stdout.strip()

def extract_frame(video, out_path, time_s=2, size="960x540"):
    """Extract a single frame from a video."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    return sh(f'ffmpeg -y -ss {time_s} -i "{video}" -vframes 1 -s {size} "{out_path}" 2>&1 | tail -1')

def extract_first_frame(video, out_path, size="960x540"):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    return sh(f'ffmpeg -y -i "{video}" -vframes 1 -s {size} "{out_path}" 2>&1 | tail -1')

# Set PYTHONPATH to include clearcut
os.environ['PYTHONPATH'] = str(Path(__file__).parent.parent)
CC = "python -m clearcut.cli"

print("=" * 65)
print("  CLEARCUT DEMO SUITE")
print("=" * 65)

# ─── DEMO 1: Silence removal ──────────────────────────────────
print("\n" + "─" * 50)
print("  DEMO 1: Silence Removal")
print("  Input: audio_test.mp4 (15s, 3 speech + 6s silence)")
print("─" * 50)

v = RAW / "audio_test.mp4"
extract_frame(v, OUT / "demo1_before.png")
r = sh(f'{CC} trim --input "{v}" --output "{OUT / "demo1_trimmed.mp4"}" 2>&1')
extract_first_frame(OUT / "demo1_trimmed.mp4", OUT / "demo1_after.png")

dur_before = sh(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{v}"')
dur_after = sh(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{OUT / "demo1_trimmed.mp4"}"')
print(f"  Duration before: {float(dur_before):.1f}s  →  after: {float(dur_after):.1f}s")
print(f"  Silence removed: {float(dur_before) - float(dur_after):.1f}s")

# ─── DEMO 2: Talking head → full pipeline (no GPU) ────────────
print("\n" + "─" * 50)
print("  DEMO 2: Full Pipeline (Talking Head)")
print("  Input: talking_head.mp4 (30s)")
print("─" * 50)

v = RAW / "talking_head.mp4"
extract_frame(v, OUT / "demo2_before.png", time_s=15)

# Full pipeline without captions (no WhisperX without GPU)
r = sh(f'{CC} process --input "{v}" --template tiktok --punch-zoom 1.08 --hook-zoom \
  --color --brightness 0.1 --contrast 0.15 \
  --output "{OUT / "demo2_pipeline.mp4"}" 2>&1')
extract_frame(OUT / "demo2_pipeline.mp4", OUT / "demo2_after.png", size="480x852")
dur = sh(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{OUT / "demo2_pipeline.mp4"}"')
print(f"  Output: {OUT / 'demo2_pipeline.mp4'}")
print(f"  Duration: {float(dur):.1f}s (9:16 vertical, zoomed, color graded)")

# ─── DEMO 3: Format conversion + zoom ─────────────────────────
print("\n" + "─" * 50)
print("  DEMO 3: Format Conversion + Zoom Effects")
print("  Input: talking_head.mp4 (16:9, 1920x1080)")
print("─" * 50)

v = RAW / "talking_head.mp4"

# 9:16 vertical with zoom (hook + punch)
r = sh(f'{CC} process --input "{v}" --format vertical --punch-zoom 1.1 --hook-zoom \
  --output "{OUT / "demo3_vertical.mp4"}" 2>&1')
extract_frame(OUT / "demo3_vertical.mp4", OUT / "demo3_vertical.png", time_s=3, size="270x480")
extract_frame(OUT / "demo3_vertical.mp4", OUT / "demo3_hook.png", time_s=0.5, size="270x480")

# Square (1:1) format
r = sh(f'{CC} process --input "{v}" --format square --punch-zoom 1.05 \
  --output "{OUT / "demo3_square.mp4"}" 2>&1')
extract_frame(OUT / "demo3_square.mp4", OUT / "demo3_square.png", size="480x480")

print(f"  ✓ Vertical 9:16 (TikTok) + punch zoom (1.1x) + hook zoom (first 2s)")
print(f"  ✓ Square 1:1 (Instagram) with 1.05x zoom")

# ─── DEMO 4: Color grading ────────────────────────────────────
print("\n" + "─" * 50)
print("  DEMO 4: Color Grading")
print("  Input: color_test2.mp4 (mild blue-gray background)")
print("─" * 50)

v = RAW / "color_test2.mp4"
extract_frame(v, OUT / "demo4_before.png")

for grade_name, opts in [
    ("warm", '--saturation 0.15 --brightness 0.08 --contrast 0.12 --temperature warm'),
    ("cool", '--saturation 0.1 --brightness 0.05 --contrast 0.1 --temperature cool'),
    ("bold", '--saturation 0.3 --brightness 0.1 --contrast 0.2'),
]:
    r = sh(f'{CC} process --input "{v}" {opts} --output "{OUT / f"demo4_{grade_name}.mp4"}" 2>&1')
    extract_frame(OUT / f"demo4_{grade_name}.mp4", OUT / f"demo4_{grade_name}.png")
    print(f"  ✓ {grade_name}")

# Extract raw frame and graded frame side by side for visual comparison
print(f"  Frames saved: demo4_warm.png, demo4_cool.png, demo4_bold.png")

# ─── DEMO 5: Compositing (PiP) ───────────────────────────────
print("\n" + "─" * 50)
print("  DEMO 5: Picture-in-Picture Compositing")
print("  Input: streamer_main.mp4 + broll.mp4 (face cam)")
print("─" * 50)

v = RAW / "streamer_main.mp4"
broll = RAW / "broll.mp4"
pip_img = RAW / "pip_image.png"

extract_frame(v, OUT / "demo5_before.png", time_s=8)
r = sh(f'{CC} process --input "{v}" --context "{broll}" --pip-position bottom-right \
  --output "{OUT / "demo5_pip.mp4"}" 2>&1')
extract_frame(OUT / "demo5_pip.mp4", OUT / "demo5_pip.png", time_s=8)
print(f"  ✓ PiP overlay: gameplay + face cam at bottom-right")

# Compositing with image overlay
r = sh(f'{CC} process --input "{v}" --context "{broll}" --pip-position bottom-left \
  --output "{OUT / "demo5_pip2.mp4"}" 2>&1')
extract_frame(OUT / "demo5_pip2.mp4", OUT / "demo5_pip2.png", time_s=8)
print(f"  ✓ PiP at bottom-left")

# ─── DEMO 6: Transitions ──────────────────────────────────────
print("\n" + "─" * 50)
print("  DEMO 6: Scene Transitions (ffmpeg xfade)")
print("  Input: scene1.mp4 → scene2.mp4 → scene3.mp4")
print("─" * 50)

# Create concat list with transition types
for ttype in ["fade", "dissolve", "slideleft", "radial", "fadeblack"]:
    out = OUT / f"demo6_{ttype}.mp4"
    r = sh(f'{CC} process --input "{RAW / "scene1.mp4"}" --context "{RAW / "scene2.mp4"}" \
      --transition {ttype} --output "{out}" 2>&1')
    # Check if it was created
    if out.exists():
        extract_frame(out, OUT / f"demo6_{ttype}.png", time_s=0.5, size="480x270")
        print(f"  ✓ {ttype} transition")

# ─── DEMO 7: Streamer VOD → full pipeline ────────────────────
print("\n" + "─" * 50)
print("  DEMO 7: Full Streamer Pipeline")
print("  Input: streamer.mp4 (45s gameplay + text reactions)")
print("─" * 50)

v = RAW / "streamer_main.mp4"
extract_frame(v, OUT / "demo7_before.png", time_s=6)

# Full TikTok-styled pipeline for the streamer
r = sh(f'{CC} process --input "{v}" --context "{RAW / "broll.mp4"}" \
  --template tiktok --punch-zoom 1.08 --hook-zoom --color \
  --brightness 0.05 --contrast 0.15 --saturation 0.2 \
  --pip-position bottom-right \
  --output "{OUT / "demo7_streamer.mp4"}" 2>&1')
extract_frame(OUT / "demo7_streamer.mp4", OUT / "demo7_streamer.png", time_s=8, size="480x852")
extract_frame(OUT / "demo7_streamer.mp4", OUT / "demo7_streamer_hook.png", time_s=0.8, size="480x852")

dur = sh(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{OUT / "demo7_streamer.mp4"}"')
print(f"  Output: 9:16, PiP, zoomed, color graded → {float(dur):.1f}s")
print(f"  Before frame: 1920x1080 gameplay")
print(f"  After frames: 1080x1920 + PiP face cam + color + zoom")

# ─── Summary table ────────────────────────────────────────────
print("\n" + "=" * 65)
print("  DEMO SUMMARY")
print("=" * 65)
results = []
for f in sorted(OUT.glob("*")):
    if f.suffix == ".png":
        sz = f.stat().st_size
        name = f.stem
        # Group by demo
        print(f"  {f.name:40s} {sz:>7,} bytes")
print("\n" + "=" * 65)
print("  Output directory: demos/output/")
print("  Run 'ls -lh demos/output/*.png' to see all frames")
print("=" * 65)
