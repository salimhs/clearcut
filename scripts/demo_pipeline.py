#!/usr/bin/env python3
"""Test the full clearcut pipeline end-to-end with generated test content."""

import subprocess
import sys
from pathlib import Path

WORKDIR = Path("/tmp/clearcut_demo")
WORKDIR.mkdir(exist_ok=True)


def run(cmd, desc):
    print(f"\n=== {desc} ===")
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ FAILED (exit {result.returncode})")
        print(result.stderr[:500])
        return False
    print(result.stdout[:300])
    return True


def main():
    print("🚧 ClearCut Demo — Generating test content...")

    # 1. Generate a test video (color bars + tone, 30 seconds)
    if not run(
        f"ffmpeg -y -f lavfi -i color=c=blue:s=1920x1080:d=30 "
        f"-f lavfi -i sine=frequency=440:duration=30 "
        f"-c:v libx264 -preset ultrafast -crf 28 "
        f"-c:a aac -b:a 128k {WORKDIR / 'main.mp4'}",
        "Generate main test video (30s blue with 440Hz tone)"
    ):
        return

    # 2. Generate a context video (different color + tone)
    if not run(
        f"ffmpeg -y -f lavfi -i color=c=red:s=1920x1080:d=30 "
        f"-f lavfi -i sine=frequency=660:duration=30 "
        f"-c:v libx264 -preset ultrafast -crf 28 "
        f"-c:a aac -b:a 128k {WORKDIR / 'broll.mp4'}",
        "Generate B-roll test video (30s red with 660Hz tone)"
    ):
        return

    # 3. Generate a test image
    if not run(
        f"python3 -c \""
        f"from PIL import Image, ImageDraw; "
        f"img = Image.new('RGB', (800, 600), 'white'); "
        f"d = ImageDraw.Draw(img); "
        f"d.text((200, 250), 'Hello ClearCut!', fill='black'); "
        f"img.save('{WORKDIR / 'test_img.png'}')\"",
        "Generate test image"
    ):
        return

    # 4. Run clearcut process with silence removal disabled (no audio gaps in test)
    print("\n🚀 Running clearcut process...")
    cmd = (
        f"clearcut process "
        f"--main {WORKDIR / 'main.mp4'} "
        f"--context {WORKDIR / 'broll.mp4'} "
        f"--images {WORKDIR / 'test_img.png'} "
        f"--no-silence "
        f"--output {WORKDIR / 'final.mp4'} "
        f"--preset ultrafast "
        f"--hardware software"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ clearcut failed: {result.stderr[:500]}")
        return

    output = WORKDIR / "final.mp4"
    if output.exists():
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"\n✅ Final video: {output} ({size_mb:.1f} MB)")
    else:
        print(f"\n❌ Output not found at {output}")
        return

    # 5. Verify the output plays
    probe = subprocess.run(
        f"ffprobe -v quiet -print_format json -show_format -show_streams {output}",
        shell=True, capture_output=True, text=True
    )
    if probe.returncode == 0:
        import json
        data = json.loads(probe.stdout)
        streams = data.get("streams", [])
        for s in streams:
            codec = s.get("codec_name", "?")
            codec_type = s.get("codec_type", "?")
            duration = s.get("duration", "?")
            print(f"  Stream: {codec_type} = {codec} ({duration}s)")

    print("\n🎉 Demo complete! Output: /tmp/clearcut_demo/final.mp4")


if __name__ == "__main__":
    main()
