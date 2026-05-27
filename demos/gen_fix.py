#!/usr/bin/env python3
"""Generate remaining test clips using subprocess with proper argument handling."""
import subprocess, sys
from pathlib import Path

def ffmpeg(*args):
    cmd = ["ffmpeg", "-y"] + list(args)
    print(f"  Running: ffmpeg {' '.join(str(a) for a in args[:8])}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[:300]}")
        return False
    return True

RAW = Path(__file__).parent / "raw"

# 1. Talking head - use drawtext with safe escaping via Python
print("\n=== Talking head ===")
filter_complex = (
    "[0:v]"
    "drawtext=text='Hello everyone! Today we are testing ClearCut.':"
    "fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,0,12)',"
    "drawtext=text='The pipeline detects AI highlights from any long video.':"
    "fontsize=36:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,12,22)',"
    "drawtext=text='This is a complete game changer for repurposing content!':"
    "fontsize=40:fontcolor=#FF6B6B:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,22,30)'"
    "[v]"
)

r = ffmpeg(
    "-f", "lavfi", "-i", "color=c=#334455:s=1920x1080:d=30:r=30",
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
    "-filter_complex", filter_complex,
    "-map", "[v]", "-map", "1:a", "-c:a", "aac", "-shortest",
    str(RAW / "talking_head.mp4")
)
if r:
    print("  ✓ Talking head generated")

# 2. Streamer simulation  
print("\n=== Streamer ===")
filter_complex2 = (
    "[0:v]"
    "drawtext=text='GAMEPLAY - ELDEN RING':fontsize=42:fontcolor=#00FF88:x=100:y=100:enable='between(t,0,45)',"
    "drawtext=text='OH MY GOD DID YOU SEE THAT?!':fontsize=36:fontcolor=#FF4444:x=(w-text_w)/2:y=400:enable='between(t,5,10)',"
    "drawtext=text='Okay this is actually the easiest boss':fontsize=30:fontcolor=white:x=(w-text_w)/2:y=500:enable='between(t,12,18)',"
    "drawtext=text='THE TRICK THAT GOT ME TO TOP RANK':fontsize=36:fontcolor=#FFFF00:x=(w-text_w)/2:y=350:enable='between(t,20,26)',"
    "drawtext=text='like and subscribe see you tomorrow':fontsize=28:fontcolor=#888888:x=(w-text_w)/2:y=600:enable='between(t,38,45)'"
    "[v]"
)

r = ffmpeg(
    "-f", "lavfi", "-i", "color=c=#1a1a2e:s=1920x1080:d=45:r=30",
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
    "-filter_complex", filter_complex2,
    "-map", "[v]", "-map", "1:a", "-shortest",
    str(RAW / "streamer_main.mp4")
)
if r:
    print("  ✓ Streamer generated")

# 3. Captions test
print("\n=== Captions test ===")
filter_complex3 = (
    "[0:v]drawtext=text='CAPTIONS TEST - will be transcribed by WhisperX':"
    "fontsize=28:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2[v]"
)

r = ffmpeg(
    "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=12:r=30",
    "-filter_complex", filter_complex3,
    "-map", "[v]",
    "-f", "lavfi", "-i", "tone=frequency=300:duration=12",
    "-shortest",
    str(RAW / "captions_test.mp4")
)
if r:
    print("  ✓ Captions test generated")

# 4. PiP image (need a proper duration)
print("\n=== PiP overlay ===")
r = ffmpeg(
    "-f", "lavfi", "-i", "color=c=#E74C3C:s=200x200:d=15:r=30",
    str(RAW / "pip_image.png")
)
if r:
    print("  ✓ PiP image generated")

# 5. Color test with proper video
print("\n=== Color grading test (2nd attempt) ===")
filter_complex5 = (
    "[0:v]"
    "drawtext=text='COLOR GRADE TEST - Default is mild blue-gray':"
    "fontsize=36:fontcolor=black:x=(w-text_w)/2:y=(h-text_h)/2"
)

r = ffmpeg(
    "-f", "lavfi", "-i", "color=c=#AABBCC:s=1920x1080:d=8:r=30",
    "-filter_complex", filter_complex5,
    "-shortest",
    str(RAW / "color_test2.mp4")
)
if r:
    print("  ✓ Color test generated")

print("\n=== Final file listing ===")
for f in sorted(RAW.glob("*")):
    sz = f.stat().st_size
    print(f"  {f.name:30s} {sz:>8,} bytes")
