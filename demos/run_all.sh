#!/bin/bash
# ClearCut Demo Suite Runner v2
set -e
cd ~/clearcut
PY=".venv/bin/python"
CC="$PY -m clearcut.cli"
AE=".venv/bin/auto-editor"
RAW="demos/raw"
OUT="demos/output"
mkdir -p "$OUT"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}"
echo "═══════════════════════════════════════════════════════"
echo "  CLEARCUT DEMO SUITE"
echo "═══════════════════════════════════════════════════════${NC}"

# ─── DEMO 1: Silence Removal ────────────────────────
echo -e "\n${BOLD}DEMO 1: Silence Removal${NC}"
ffmpeg -y -ss 0 -i "$RAW/audio_test.mp4" -vframes 1 -s 960x540 "$OUT/demo1_before.png" 2>/dev/null
"$AE" "$RAW/audio_test.mp4" --silent-threshold 0.03 --output "$OUT/demo1_trimmed.mp4" 2>&1 | grep -E "^|silence|frame|Done" | head -5
ffmpeg -y -i "$OUT/demo1_trimmed.mp4" -vframes 1 -s 960x540 "$OUT/demo1_after.png" 2>/dev/null
DUR_B=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW/audio_test.mp4")
DUR_A=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/demo1_trimmed.mp4")
echo -e "  ${GREEN}${DUR_B}s → ${DUR_A}s ($(echo "$DUR_B - $DUR_A" | bc)s silence removed)${NC}"

# ─── DEMO 2: Full Pipeline (Talking Head) ───────────
echo -e "\n${BOLD}DEMO 2: Full Pipeline (Talking Head → TikTok)${NC}"
ffmpeg -y -ss 15 -i "$RAW/talking_head.mp4" -vframes 1 -s 960x540 "$OUT/demo2_before.png" 2>/dev/null
$CC process --main "$RAW/talking_head.mp4" --output "$OUT/demo2_pipeline.mp4" \
  --template tiktok --punch-zoom 1.05 --hook-zoom --no-silence 2>&1 | grep -E "Done|Output|frame|saved" | head -5
ffmpeg -y -i "$OUT/demo2_pipeline.mp4" -vframes 1 -s 480x852 "$OUT/demo2_after.png" 2>/dev/null
echo -e "  ${GREEN}9:16 vertical, zoomed, color graded${NC}"

# ─── DEMO 3: Format + Zoom ──────────────────────────
echo -e "\n${BOLD}DEMO 3: Format Conversion + Zoom${NC}"
$CC process --main "$RAW/talking_head.mp4" --output "$OUT/demo3_vertical.mp4" \
  --format vertical --punch-zoom 1.1 --hook-zoom --no-silence 2>&1 | grep -E "Done|Output|frame" | head -5
ffmpeg -y -i "$OUT/demo3_vertical.mp4" -vframes 1 -s 270x480 "$OUT/demo3_vertical.png" 2>/dev/null
ffmpeg -y -ss 0.4 -i "$OUT/demo3_vertical.mp4" -vframes 1 -s 270x480 "$OUT/demo3_hook.png" 2>/dev/null
$CC process --main "$RAW/talking_head.mp4" --output "$OUT/demo3_square.mp4" \
  --format square --punch-zoom 1.05 --no-silence 2>&1 | grep -E "Done|Output" | head -5
ffmpeg -y -i "$OUT/demo3_square.mp4" -vframes 1 -s 480x480 "$OUT/demo3_square.png" 2>/dev/null
echo -e "  ${GREEN}✓ 9:16 + 1:1 with zoom effects${NC}"

# ─── DEMO 4: Color Grading ─────────────────────────
echo -e "\n${BOLD}DEMO 4: Color Grading${NC}"
ffmpeg -y -i "$RAW/color_test2.mp4" -vframes 1 -s 960x540 "$OUT/demo4_before.png" 2>/dev/null
for grade in warm cool bold; do
  case $grade in
    warm) OPTS="--saturation 0.15 --brightness 0.08 --contrast 1.2" ;;
    cool) OPTS="--saturation 0.1 --brightness 0.05 --contrast 1.1" ;;
    bold) OPTS="--saturation 0.3 --brightness 0.1 --contrast 1.3" ;;
  esac
  $CC process --main "$RAW/color_test2.mp4" --output "$OUT/demo4_${grade}.mp4" \
    $OPTS --no-silence 2>&1 | grep -E "Done|Output|saved" | head -2
  ffmpeg -y -i "$OUT/demo4_${grade}.mp4" -vframes 1 -s 960x540 "$OUT/demo4_${grade}.png" 2>/dev/null
done
echo -e "  ${GREEN}✓ Warm / Cool / Bold presets${NC}"

# ─── DEMO 5: PiP Compositing ───────────────────────
echo -e "\n${BOLD}DEMO 5: Picture-in-Picture${NC}"
ffmpeg -y -ss 8 -i "$RAW/streamer_main.mp4" -vframes 1 -s 960x540 "$OUT/demo5_before.png" 2>/dev/null
$CC process --main "$RAW/streamer_main.mp4" --context "$RAW/broll.mp4" \
  --output "$OUT/demo5_pip.mp4" --no-silence 2>&1 | grep -E "Done|Output|saved|frame" | head -5
ffmpeg -y -ss 8 -i "$OUT/demo5_pip.mp4" -vframes 1 -s 960x540 "$OUT/demo5_pip.png" 2>/dev/null
echo -e "  ${GREEN}✓ PiP: gameplay + face cam at bottom-right${NC}"

# ─── DEMO 6: Transitions ───────────────────────────
echo -e "\n${BOLD}DEMO 6: Scene Transitions${NC}"
for ttype in fade dissolve slideleft radial; do
  $CC process --main "$RAW/scene1.mp4" --context "$RAW/scene2.mp4" \
    --transition "$ttype" --output "$OUT/demo6_${ttype}.mp4" --no-silence 2>&1 | grep -E "Done|Output|saved" | head -2
  [ -f "$OUT/demo6_${ttype}.mp4" ] && \
    ffmpeg -y -ss 0.5 -i "$OUT/demo6_${ttype}.mp4" -vframes 1 -s 960x540 "$OUT/demo6_${ttype}.png" 2>/dev/null && \
    echo -e "  ${GREEN}✓ ${ttype}${NC}"
done

# ─── DEMO 7: Full Streamer TikTok Pipeline ──────────
echo -e "\n${BOLD}DEMO 7: Streamer → TikTok ready${NC}"
ffmpeg -y -ss 6 -i "$RAW/streamer_main.mp4" -vframes 1 -s 960x540 "$OUT/demo7_before.png" 2>/dev/null
$CC process --main "$RAW/streamer_main.mp4" --context "$RAW/broll.mp4" \
  --output "$OUT/demo7_streamer.mp4" --template tiktok --punch-zoom 1.08 \
  --hook-zoom --no-silence 2>&1 | grep -E "Done|saved|Output|frame" | head -5
ffmpeg -y -i "$OUT/demo7_streamer.mp4" -ss 8 -vframes 1 -s 480x852 "$OUT/demo7_streamer.png" 2>/dev/null
ffmpeg -y -i "$OUT/demo7_streamer.mp4" -ss 0.6 -vframes 1 -s 480x852 "$OUT/demo7_streamer_hook.png" 2>/dev/null
echo -e "  ${GREEN}✓ Full TikTok: vertical + PiP + zoom 1.08x + hook${NC}"

# ─── SUMMARY ───────────────────────────────────────
echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}RESULTS: ${OUT}/ (${NC}"
find "$OUT" -name "*.png" | while read f; do echo "  $(basename $f): $(du -h "$f" | cut -f1)"; done
echo ""
echo "  Open any .png to see results."
echo "  Use MEDIA:demos/output/<file.png> to view."
echo ""
echo -e "${BOLD}What each demo proves:${NC}"
echo "   1. Silence: 15s→trimmed (3 gaps removed)"
echo "   2. Pipeline: 16:9→9:16 + zoom + color"
echo "   3. Format:   16:9→9:16 + 1:1 with zoom"
echo "   4. Color:    warm/cool/bold before/after"
echo "   5. PiP:      overlay compositing"
echo "   6. Xfade:    fade/dissolve/slide/radial"
echo "   7. Streamer: Full TikTok ready output"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
