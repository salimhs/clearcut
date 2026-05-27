#!/home/salim/clearcut/.venv/bin/python3.11
"""ClearCut Demo Suite - runs each feature independently, captures frames."""
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

def run(cmd, timeout=60, label=""):
    """Run command with timeout, print output."""
    print(f"\n  Running: {' '.join(str(a) for a in cmd[:6])}...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            print(f"  ERROR({r.returncode}): {r.stderr.strip()[:300]}")
            return False
        out = r.stdout.strip()[-200:]
        print(f"  OK: {out}")
        return True
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT ({timeout}s)")
        return False

def frame(video, out, time=None, size="960x540"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    ss = ["-ss", str(time)] if time is not None else []
    cmd = ["ffmpeg", "-y"] + ss + ["-i", str(video), "-vframes", "1", "-s", size, str(out)]
    subprocess.run(cmd, capture_output=True, timeout=15)

def duration(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, timeout=10)
    try:
        return float(r.stdout.strip())
    except:
        return 0.0

results = []

# ─── DEMO 1: Silence Removal ─────────────────────────
print("\n" + "="*55 + "\n  DEMO 1: Silence Removal\n" + "="*55)
src = RAW / "audio_test.mp4"
frame(src, OUT / "demo1_before.png")
dur_before = duration(src)
r = subprocess.run([str(AE), str(src), "--edit", "audio", "--when-silent", "cut",
                    "--output", str(OUT / "demo1_trimmed.mp4")],
                   capture_output=True, text=True, timeout=30)
print(f"  auto-editor: {'OK' if r.returncode == 0 else 'FAIL'}")
if (OUT / "demo1_trimmed.mp4").exists():
    frame(OUT / "demo1_trimmed.mp4", OUT / "demo1_after.png")
    da = duration(OUT / "demo1_trimmed.mp4")
    print(f"  {dur_before:.1f}s → {da:.1f}s (removed {dur_before-da:.1f}s)")
    results.append(("silence", dur_before, da))

# ─── DEMO 2: Full Pipeline ───────────────────────────
print("\n" + "="*55 + "\n  DEMO 2: Full Pipeline (Talking Head → TikTok)\n" + "="*55)
src = RAW / "talking_head.mp4"
frame(src, OUT / "demo2_before.png", time=15)
ok = run(CC + ["process", "--main", str(src), "--output", str(OUT / "demo2_pipeline.mp4"),
               "--format", "vertical", "--punch-zoom", "1.05", "--hook-zoom",
               "--no-silence", "--no-normalize"], timeout=120)
if ok:
    frame(OUT / "demo2_pipeline.mp4", OUT / "demo2_after.png", size="480x852")
    print(f"  Duration: {duration(OUT / 'demo2_pipeline.mp4'):.1f}s")

# ─── DEMO 3: Format + Zoom ─────────────────────────
print("\n" + "="*55 + "\n  DEMO 3: Format + Zoom\n" + "="*55)
src = RAW / "talking_head.mp4"
ok1 = run(CC + ["process", "--main", str(src), "--output", str(OUT / "demo3_vertical.mp4"),
                "--format", "vertical", "--punch-zoom", "1.1", "--hook-zoom",
                "--no-silence", "--no-normalize"], timeout=120)
if ok1:
    frame(OUT / "demo3_vertical.mp4", OUT / "demo3_vertical.png", size="270x480")
    frame(OUT / "demo3_vertical.mp4", OUT / "demo3_hook.png", time=0.4, size="270x480")
    print("  ✓ 9:16 + punch 1.1x + hook")

ok2 = run(CC + ["process", "--main", str(src), "--output", str(OUT / "demo3_square.mp4"),
                "--format", "square", "--punch-zoom", "1.05",
                "--no-silence", "--no-normalize"], timeout=120)
if ok2:
    frame(OUT / "demo3_square.mp4", OUT / "demo3_square.png", size="480x480")
    print("  ✓ 1:1 + punch 1.05x")

# ─── DEMO 4: Color Grading ─────────────────────────
print("\n" + "="*55 + "\n  DEMO 4: Color Grading\n" + "="*55)
src = RAW / "color_test2.mp4"
frame(src, OUT / "demo4_before.png")
for grade, opts, desc in [
    ("warm", ["--saturation", "0.15", "--brightness", "0.08", "--contrast", "1.2"], "warm"),
    ("cool", ["--saturation", "0.1", "--brightness", "0.05", "--contrast", "1.1"], "cool"),
    ("bold", ["--saturation", "0.3", "--brightness", "0.1", "--contrast", "1.3"], "bold"),
]:
    ok = run(CC + ["process", "--main", str(src), "--output", str(OUT / f"demo4_{grade}.mp4")] +
             opts + ["--no-silence", "--no-normalize"], timeout=60, label=desc)
    if ok:
        frame(OUT / f"demo4_{grade}.mp4", OUT / f"demo4_{grade}.png")
        print(f"  ✓ {grade}")

# ─── DEMO 5: PiP ──────────────────────────────────
print("\n" + "="*55 + "\n  DEMO 5: PiP Compositing\n" + "="*55)
src = RAW / "streamer_main.mp4"
frame(src, OUT / "demo5_before.png", time=8)
ok = run(CC + ["process", "--main", str(src), "--context", str(RAW / "broll.mp4"),
               "--output", str(OUT / "demo5_pip.mp4"),
               "--no-silence", "--no-normalize"], timeout=120)
if ok:
    frame(OUT / "demo5_pip.mp4", OUT / "demo5_pip.png", time=8)
    print("  ✓ PiP overlay")

# ─── DEMO 6: Transitions ──────────────────────────
print("\n" + "="*55 + "\n  DEMO 6: Transitions\n" + "="*55)
for ttype in ["fade", "dissolve", "slideleft", "radial"]:
    ok = run(CC + ["process", "--main", str(RAW / "scene1.mp4"), "--context", str(RAW / "scene2.mp4"),
                   "--transition", ttype, "--output", str(OUT / f"demo6_{ttype}.mp4"),
                   "--no-silence", "--no-normalize"], timeout=60, label=ttype)
    if ok:
        frame(OUT / f"demo6_{ttype}.mp4", OUT / f"demo6_{ttype}.png", time=0.5)
        print(f"  ✓ {ttype}")

# ─── DEMO 7: Full Streamer Pipeline ────────────────
print("\n" + "="*55 + "\n  DEMO 7: Streamer → TikTok\n" + "="*55)
src = RAW / "streamer_main.mp4"
frame(src, OUT / "demo7_before.png", time=6)
ok = run(CC + ["process", "--main", str(src), "--context", str(RAW / "broll.mp4"),
               "--output", str(OUT / "demo7_streamer.mp4"),
               "--format", "vertical", "--punch-zoom", "1.08", "--hook-zoom",
               "--no-silence", "--no-normalize"], timeout=120)
if ok:
    frame(OUT / "demo7_streamer.mp4", OUT / "demo7_streamer.png", time=8, size="480x852")
    frame(OUT / "demo7_streamer.mp4", OUT / "demo7_streamer_hook.png", time=0.6, size="480x852")
    print(f"  Duration: {duration(OUT / 'demo7_streamer.mp4'):.1f}s")
    print("  ✓ Streamer → TikTok: vertical + PiP + zoom + hook")

# ─── SUMMARY ───────────────────────────────────
print("\n" + "="*55)
print("  DEMO RESULTS")
print("="*55)
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name:40s} {f.stat().st_size:>7,} bytes")
print(f"\n  {len(list(OUT.glob('*.png')))} frames captured")
print("  View any .png: MEDIA:clearcut/demos/output/<filename>")
print("="*55)
