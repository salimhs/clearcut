#!/usr/bin/env python3
"""Generate synthetic test content and run ClearCut demos.
Outputs frames as PNG files to demos/output/ — no GPU needed."""

import subprocess, os, json, shutil, sys
from pathlib import Path

DEMOS = Path(__file__).parent
OUTPUT = DEMOS / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)
RAW = DEMOS / "raw"
RAW.mkdir(exist_ok=True)

def sh(cmd, **kw):
    print(f"  $ {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(f"  ERROR ({r.returncode}): {r.stderr[:500]}")
    return r.stdout.strip()

# ─── 1. Talking head simulation ─────────────────────────────────
print("\n=== 1. Talking head simulation ===")
if not (RAW / "talking_head.mp4").exists():
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#334455:s=1920x1080:d=30:r=30" \
        -f lavfi -i "anullsrc=r=44100:cl=mono" \
        -filter_complex "\
            [0:v]drawtext=text='Hello everyone\! Today we are testing ClearCut\: silence removal\, captions\, zoom\, color grading\, and more. This is a talking head simulation for the demo suite.\ Let us see how well the pipeline handles this synthetic test content.':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,0,10)',\
            drawtext=text='Okay so here is the interesting part\: the pipeline detects AI highlights automatically by analyzing transcript sentiment and emphasis. It identifies the five most shareable moments from any long-form video\: moments with high energy\, strong opinions\, or valuable insights that drive engagement.':fontsize=36:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,10,20)',\
            drawtext=text='And that is why this approach works so well for content creators who want to repurpose their long-form videos into short-form clips without spending hours manually cutting and editing each segment individually. It is a complete game changer for workflow efficiency\!':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,20,30)'\
        [v] -map '[v]' -map '1:a' -c:a aac -shortest {RAW / 'talking_head.mp4'}""")
    print("  ✓ Generated 30s talking head simulation")

# ─── 2. Streamer/gameplay simulation ────────────────────────────
print("\n=== 2. Streamer simulation (with PiP b-roll) ===")
if not (RAW / "streamer_main.mp4").exists():
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#1a1a2e:s=1920x1080:d=45:r=30" \
        -f lavfi -i "anullsrc=r=44100:cl=mono" \
        -filter_complex "\
            [0:v]drawtext=text='GAMEPLAY FOOTAGE - ELDEN RING':fontsize=42:fontcolor=#00FF88:x=100:y=100:enable='between(t,0,45)',\
            drawtext=text='OH MY GOD DID YOU SEE THAT THE BOSS JUST TELEPORTED BEHIND ME THAT IS INSANE':fontsize=32:fontcolor=#FF4444:x=(w-text_w)/2:y=400:enable='between(t,5,9)',\
            drawtext=text'=wait wait wait hold up this is actually the easiest boss in the game just roll into his attacks':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=500:enable='between(t,12,17)',\
            drawtext=text='THE TRICK THAT GOT ME TO TOP RANK was actually really simple I just stopped panicking':fontsize=32:fontcolor=#FFFF00:x=(w-text_w)/2:y=350:enable='between(t,20,25)',\
            drawtext=text='anyway thats the gameplay for today like and subscribe see you tomorrow':fontsize=28:fontcolor=#888888:x=(w-text_w)/2:y=600:enable='between(t,38,45)'\
        [v] -map '[v]' -map '1:a' -shortest {RAW / 'streamer_main.mp4'}""")
    print("  ✓ Generated 45s streamer simulation")

if not (RAW / "broll.mp4").exists():
    # PiP overlay content
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#2ECC71:s=640x360:d=15:r=30" \
        -filter_complex "drawtext=text='FACE CAM':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
        -shortest {RAW / 'broll.mp4'}""")
    # Also a PiP image overlay
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#E74C3C:s=200x200:d=15:r=30" {RAW / 'pip_image.png'}""")
    print("  ✓ Generated B-roll + PiP overlay")

# ─── 3. Audio test (silences + music) ───────────────────────────
print("\n=== 3. Audio test (intentional silences) ===")
if not (RAW / "audio_test.mp4").exists():
    # Generate audio with gaps: speech 0-3s, silence 3-6s, speech 6-9s, silence 9-12s, speech 12-15s
    sh(f"""ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=15:r=30" \
        -f lavfi -i "sine=frequency=220:duration=3" \
        -f lavfi -i "anullsrc=r=44100:cl=mono:duration=3" \
        -f lavfi -i "sine=frequency=440:duration=3" \
        -f lavfi -i "anullsrc=r=44100:cl=mono:duration=3" \
        -f lavfi -i "sine=frequency=660:duration=3" \
        -filter_complex "\
            [0:v]drawtext=text='Speech 1 (220Hz) - Silence - Speech 2 (440Hz) - Silence - Speech 3 (660Hz)':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2[v];\
            [1:a][2:a][3:a][4:a][5:a]concat=n=5:v=0:a=1[a]" \
        -map '[v]' -map '[a]' -c:v libx264 -shortest {RAW / 'audio_test.mp4'}""")
    print("  ✓ Generated audio test with intentional gaps")

# ─── 4. Captions test ──────────────────────────────────────────
print("\n=== 4. Captions test (speech-like audio) ===")
if not (RAW / "captions_test.mp4").exists():
    # Generate audio with varying speech-like tones for WhisperX
    sh(f"""ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=12:r=30" \
        -filter_complex "\
            [0:v]drawtext=text='CAPTIONS TEST\: This content will be transcribed by WhisperX and burned as ASS subtitles':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2[v]" \
        -map '[v]' -f lavfi -i "sine=frequency=300:duration=12" -shortest {RAW / 'captions_test.mp4'}""")
    print("  ✓ Generated captions test video")

# ─── 5. Color grading test ─────────────────────────────────────
print("\n=== 5. Color grading test ===")
if not (RAW / "color_test.mp4").exists():
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#AABBCC:s=1920x1080:d=8:r=30" \
        -filter_complex "\
            [0:v]drawtext=text='COLOR GRADE TEST - Should be warm/contrasty':fontsize=36:fontcolor=black:x=(w-text_w)/2:y=(h-text_h)/2,\
            drawtext=text='Default colors: mild blue-gray background':fontsize=24:fontcolor=#666666:x=(w-text_w)/2:y=h-100" \
        -shortest {RAW / 'color_test.mp4'}""")
    print("  ✓ Generated color grading test")

# ─── 6. Transitions test ───────────────────────────────────────
print("\n=== 6. Transitions test ===")
if not (RAW / "scene1.mp4").exists():
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#E74C3C:s=1920x1080:d=3:r=30" \
        -filter_complex "drawtext=text='SCENE 1':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" -shortest {RAW / 'scene1.mp4'}""")
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#3498DB:s=1920x1080:d=3:r=30" \
        -filter_complex "drawtext=text='SCENE 2':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" -shortest {RAW / 'scene2.mp4'}""")
    sh(f"""ffmpeg -y -f lavfi -i "color=c=#2ECC71:s=1920x1080:d=3:r=30" \
        -filter_complex "drawtext=text='SCENE 3':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" -shortest {RAW / 'scene3.mp4'}""")
    print("  ✓ Generated scene clips for transitions")

print("\n=== RAW files ready ===")
sh("ls -la {RAW}/*.mp4 {RAW}/*.png 2>/dev/null || true", timeout=5)
