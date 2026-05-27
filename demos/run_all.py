#!/home/salim/clearcut/.venv/bin/python3.11
"""ClearCut Demo Suite - runs all features and captures before/after frames."""
import subprocess, sys, os
from pathlib import Path

BASE = Path.home() / "clearcut"
PY = BASE / ".venv" / "bin" / "python"
AE = BASE / ".venv" / "bin" / "auto-editor"
RAW = BASE / "demos" / "raw"
OUT = BASE / "demos" / "output"
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(str(BASE))

CC = [str(PY), "-m", "clearcut.cli"]

def sh(cmd, timeout=120):
    if isinstance(cmd, str):
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    else:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        err = r.stderr.strip()[:200]
        return f"ERROR({r.returncode}): {err}"
    return r.stdout.strip()

def frame(video, out, time=None, size="960x540"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    ss = f"-ss {time}" if time is not None else ""
    subprocess.run(f"ffmpeg -y {ss} -i '{video}' -vframes 1 -s {size} '{out}'".split(),
                   capture_output=True, timeout=30)

results = []

# ═══════════════════════════════════════════════
# DEMO 1: Silence Removal
# ═══════════════════════════════════════════════
print("=" * 55)
print("  DEMO 1: Silence Removal")
print("  Input: audio_test.mp4 (15s, 3 speech bursts + 3 gaps)")
print("=" * 55)

src = RAW / "audio_test.mp4"
frame(src, OUT / "demo1_before.png")
r = sh(f"{AE} '{src}' --edit audio --when-silent cut --margin 0.1s --output '{OUT / 'demo1_trimmed.mp4'}'", 60)
frame(OUT / "demo1_trimmed.mp4", OUT / "demo1_after.png")

db = float(sh(f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{src}'"))
da = float(sh(f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{OUT / 'demo1_trimmed.mp4'}'"))
print(f"  Duration: {db:.1f}s → {da:.1f}s  (removed {db-da:.1f}s silence)")
results.append(("silence", db, da))

# ═══════════════════════════════════════════════
# DEMO 2: Full Pipeline (Talking Head)
# ═══════════════════════════════════════════════
print("\n" + "=" * 55)
print("  DEMO 2: Full Pipeline (Talking Head → TikTok)")
print("  Input: talking_head.mp4 (30s, 16:9)")
print("=" * 55)

src = RAW / "talking_head.mp4"
frame(src, OUT / "demo2_before.png", time=15)

cmd = CC + ["process", "--main", str(src), "--output", str(OUT / "demo2_pipeline.mp4"),
            "--template", "tiktok", "--punch-zoom", "1.05", "--hook-zoom", "--no-silence"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
out = r.stdout.strip()[:200]
print(f"  {out}")

frame(OUT / "demo2_pipeline.mp4", OUT / "demo2_after.png", size="480x852")
da = float(sh(f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{OUT / 'demo2_pipeline.mp4'}'"))
print(f"  Output: 9:16 vertical + zoom + color + hook")
results.append(("pipeline_talking", da))

# ═══════════════════════════════════════════════
# DEMO 3: Format + Zoom
# ═══════════════════════════════════════════════
print("\n" + "=" * 55)
print("  DEMO 3: Format Conversion + Zoom")
print("  Input: talking_head.mp4 (16:9)")
print("=" * 55)

# 9:16 vertical with hook zoom
cmd = CC + ["process", "--main", str(src), "--output", str(OUT / "demo3_vertical.mp4"),
            "--format", "vertical", "--punch-zoom", "1.1", "--hook-zoom", "--no-silence"]
subprocess.run(cmd, capture_output=True, text=True, timeout=120)
frame(OUT / "demo3_vertical.mp4", OUT / "demo3_vertical.png", size="270x480")
frame(OUT / "demo3_vertical.mp4", OUT / "demo3_hook.png", time=0.4, size="270x480")
print("  ✓ 9:16 → punch zoom 1.1x + hook on first 2s")

# 1:1 square
cmd = CC + ["process", "--main", str(src), "--output", str(OUT / "demo3_square.mp4"),
            "--format", "square", "--punch-zoom", "1.05", "--no-silence"]
subprocess.run(cmd, capture_output=True, text=True, timeout=120)
frame(OUT / "demo3_square.mp4", OUT / "demo3_square.png", size="480x480")
print("  ✓ 1:1 → punch zoom 1.05x")

# ═══════════════════════════════════════════════
# DEMO 4: Color Grading
# ═══════════════════════════════════════════════
print("\n" + "=" * 55)
print("  DEMO 4: Color Grading")
print("  Input: color_test2.mp4 (mild blue-gray)")
print("=" * 55)

src = RAW / "color_test2.mp4"
frame(src, OUT / "demo4_before.png")

for grade, opts in [
    ("warm", ["--saturation", "0.15", "--brightness", "0.08", "--contrast", "1.2"]),
    ("cool", ["--saturation", "0.1", "--brightness", "0.05", "--contrast", "1.1"]),
    ("bold", ["--saturation", "0.3", "--brightness", "0.1", "--contrast", "1.3"]),
]:
    cmd = CC + ["process", "--main", str(src), "--output", str(OUT / f"demo4_{grade}.mp4")] + opts + ["--no-silence"]
    subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    frame(OUT / f"demo4_{grade}.mp4", OUT / f"demo4_{grade}.png")
    print(f"  ✓ {grade}")

# ═══════════════════════════════════════════════
# DEMO 5: Picture-in-Picture
# ═══════════════════════════════════════════════
print("\n" + "=" * 55)
print("  DEMO 5: Picture-in-Picture (Compositing)")
print("  Input: streamer_main.mp4 + broll.mp4")
print("=" * 55)

src = RAW / "streamer_main.mp4"
frame(src, OUT / "demo5_before.png", time=8)

cmd = CC + ["process", "--main", str(src), "--context", str(RAW / "broll.mp4"),
            "--output", str(OUT / "demo5_pip.mp4"), "--no-silence"]
subprocess.run(cmd, capture_output=True, text=True, timeout=120)
frame(OUT / "demo5_pip.mp4", OUT / "demo5_pip.png", time=8)
print("  ✓ Gameplay + face cam PiP overlay")

# ═══════════════════════════════════════════════
# DEMO 6: Transitions
# ═══════════════════════════════════════════════
print("\n" + "=" * 55)
print("  DEMO 6: Scene Transitions")
print("  Input: scene1.mp4 → scene2.mp4")
print("=" * 55)

for ttype in ["fade", "dissolve", "slideleft", "radial"]:
    cmd = CC + ["process", "--main", str(RAW / "scene1.mp4"), "--context", str(RAW / "scene2.mp4"),
                "--transition", ttype, "--output", str(OUT / f"demo6_{ttype}.mp4"), "--no-silence"]
    subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    f = OUT / f"demo6_{ttype}.mp4"
    if f.exists():
        frame(f, OUT / f"demo6_{ttype}.png", time=0.5)
        print(f"  ✓ {ttype}")

# ═══════════════════════════════════════════════
# DEMO 7: Streamer → Full TikTok Pipeline
# ═══════════════════════════════════════════════
print("\n" + "=" * 55)
print("  DEMO 7: Streamer VOD → TikTok-Ready")
print("  Input: streamer_main.mp4 (45s gameplay + reactions)")
print("=" * 55)

src = RAW / "streamer_main.mp4"
frame(src, OUT / "demo7_before.png", time=6)

cmd = CC + ["process", "--main", str(src), "--context", str(RAW / "broll.mp4"),
            "--output", str(OUT / "demo7_streamer.mp4"),
            "--template", "tiktok", "--punch-zoom", "1.08", "--hook-zoom", "--no-silence"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print(f"  {r.stdout.strip()[:200]}")

frame(OUT / "demo7_streamer.mp4", OUT / "demo7_streamer.png", time=8, size="480x852")
frame(OUT / "demo7_streamer.mp4", OUT / "demo7_streamer_hook.png", time=0.6, size="480x852")
da = float(sh(f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{OUT / 'demo7_streamer.mp4'}'"))
print(f"  Output: 9:16 TikTok + PiP face cam + zoom 1.08x + hook + color")
print(f"  Duration: {da:.1f}s")

# ═══════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════
print("\n" + "=" * 55)
print("  DEMO RESULTS")
print("=" * 55)
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name:40s} {f.stat().st_size:>7,} bytes")

print(f"\n  View any .png file with the MEDIA: prefix.")
print("=" * 55)
