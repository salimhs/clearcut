# Pipeline Stages

ClearCut's pipeline processes raw footage through up to 10 stages in a carefully designed order. Each stage's position is intentional — reordering them would break downstream processing.

## Stage Order

```
 1. Silence removal
 2. Scene detection (optional)
 3. Audio normalization + ducking
 4. Compositing (PiP, image overlays)
 5. Colour grading (LUT + basic correction)
 6. Format conversion (9:16, 1:1, etc.)
 7. Caption generation + burn-in
 8. Effects (punch zoom, hook zoom)
 9. Speed ramping
10. Transitions between segments
11. Final encode (hardware-accelerated)
```

## Why This Order?

### Stage 1: Silence Removal

Silence removal **must come first** because it changes the video duration. Speech segments are spliced together with smooth jump cuts, which means every timestamp after this stage may differ from the original. Running silence removal later would require re-syncing any timestamped assets — so we do it immediately.

### Stage 1b: Scene Detection

Scene boundaries are detected **after** silence removal so that scene transitions align with actual content boundaries rather than silence gaps. Each detected scene becomes a segment that can have its own transition.

### Stage 2: Audio Normalization + Ducking

Audio is normalized **before** compositing because:

- Audio processing doesn't depend on video composition
- Normalized audio provides a consistent level for voice/music mixing
- Ducking (auto-lowering background music during speech) is easier with a normalized voice track

### Stage 3: Compositing

PiP overlays, image insertions, and watermarks are applied **after** silence removal and audio processing because:

- Compositing creates a new video stream from layers
- We want the shortest possible video (post-silence removal) for compositing
- Timestamped image assets (`--assets diagram@30`) reference the post-silence timeline

### Stage 4: Colour Grading

Colour correction is applied **before** format conversion and captions because:

- LUT application and colour correction are resolution-independent
- Doing it early means captions and effects work on the final colour-graded image
- Better to grade once and have everything downstream inherit the correct look

### Stage 5: Format Conversion

Format conversion (e.g., 9:16 vertical, 1:1 square) is placed **before captions** — this is critical.

!!! important "Why Format Before Captions"
    ASS subtitle positioning uses pixel coordinates. If we burned captions into a 16:9 video and _then_ cropped to 9:16, the caption text would be off-screen or mispositioned. By converting format first, ASS coordinates map correctly to the final frame dimensions.

### Stage 6: Captions

Caption generation + burn-in happens **after format conversion** so that:

- ASS positioning coordinates match the final video dimensions
- Word-level highlight animations render at the correct resolution
- No need to re-burn captions if format changes

### Stage 7: Effects

Effects (punch zoom, hook zoom) come **after captions** so that:

- Zooming/dynamic effects don't break caption text positioning
- If we zoomed first, the caption content area would shift unpredictably
- The zoom effect _includes_ the captions, giving a more integrated look

### Stage 7b: Speed Ramping

Variable-speed segments (speed up/slow down) come after effects so that:

- Speed changes apply to the final composited + captioned video
- The zoom effect timeline isn't distorted by speed changes
- Speed ramps affect the complete frame including captions

### Stage 8: Transitions

Transitions between segments (fade, wipe, dissolve) come near the end because:

- All individual segments have been fully processed (silence removed, graded, captioned, effects applied)
- Transitions only need to blend the final processed clips
- Doing transitions earlier would require re-processing on each segment

### Stage 9: Final Encode

The encode stage is always last. It takes the fully processed video and compresses it with the selected hardware encoder (NVENC, AMF, QSV) or software x264, using the chosen quality/speed preset.

## Summary

| Stage | Why It's Here |
|-------|---------------|
| 1. Silence removal | Changes duration — everything after references this timeline |
| 1b. Scene detection | Split at content boundaries, not silence gaps |
| 2. Audio normalization | Independent of video; consistent level for mixing |
| 3. Compositing | Works on shortest possible timeline |
| 4. Colour grading | Resolution-independent; downstream inherits the look |
| 5. Format conversion | **Must be before captions** for correct ASS coordinates |
| 6. Captions | ASS positions match final dimensions |
| 7. Effects | Zoom after captions = captions stay positioned correctly |
| 7b. Speed ramps | Speed after effects = zoom timeline is preserved |
| 8. Transitions | Blend fully-processed segments |
| 9. Final encode | Compress the complete, polished output |
