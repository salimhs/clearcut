# Templates

Templates are pre-bundled configurations that set multiple pipeline parameters at once. Use them with `--template` in `clearcut process`, or specify individual flags for fine-grained control.

## Available Templates

### `clean` — Standard YouTube-ready

Clean, professional look for talking-head and tutorial videos.

| Setting | Value |
|---------|-------|
| Format | 16:9 (landscape) |
| Caption style | `default` (Arial, no animation) |
| Transition | Fade (0.3s) |
| Audio target | -14 LUFS |
| Saturation | 1.0 (neutral) |
| Contrast | 1.0 (neutral) |
| Brightness | 0.0 (neutral) |
| Punch zoom | Off |
| Hook zoom | Off |
| Colour preset | None |

### `tiktok` — Vertical Social Media

Optimized for TikTok, Instagram Reels, and YouTube Shorts. Punchy, dynamic, vertical format.

| Setting | Value |
|---------|-------|
| Format | **9:16 (vertical)** |
| Caption style | `modern` (Montserrat, word-highlight) |
| Transition | Wipe-right (0.4s) |
| Audio target | **-13 LUFS** (louder) |
| Saturation | **1.1** (slightly boosted) |
| Contrast | **1.05** (slightly boosted) |
| Brightness | **+0.02** |
| Punch zoom | **1.05 (5%)** |
| Hook zoom | **On** |
| Colour preset | None |

### `cinematic` — Film-Like

Desaturated, higher contrast, slow dissolves. Great for vlogs and storytelling.

| Setting | Value |
|---------|-------|
| Format | 16:9 (landscape) |
| Caption style | `minimal` (Helvetica Neue, no animation) |
| Transition | **Dissolve (0.5s)** |
| Audio target | **-16 LUFS** (quieter, more dynamic range) |
| Saturation | **0.85** (desaturated) |
| Contrast | **1.15** (boosted) |
| Brightness | **-0.02** (slightly dark) |
| Punch zoom | **1.03 (3%)** |
| Hook zoom | Off |
| Colour preset | None |

### `bold` — Eye-Catching

High-impact, high-contrast style for reaction videos, reviews, and commentary.

| Setting | Value |
|---------|-------|
| Format | 16:9 (landscape) |
| Caption style | **`bold`** (Impact, centered, word-highlight) |
| Transition | **Slide-left (0.4s)** |
| Audio target | -14 LUFS |
| Saturation | **1.2** (very boosted) |
| Contrast | **1.1** (boosted) |
| Brightness | **+0.02** |
| Punch zoom | **1.08 (8%)** |
| Hook zoom | **On** |
| Colour preset | None |

## Colour Presets

Colour presets are independent of templates and can be used with `--color-preset`. When used with a template, the template's base values apply, but explicit CLI flags still override.

| Preset | Brightness | Contrast | Saturation | Temperature |
|--------|-----------|---------|------------|-------------|
| `warm` | 0.0 | 1.0 | 1.1 | +15 (warm) |
| `cool` | 0.0 | 1.0 | 1.0 | -15 (cool) |
| `vintage` | 0.0 | 0.9 | 0.7 | +10 (warm) |
| `vibrant` | 0.0 | 1.0 | 1.3 | +5 (warm) |
| `drama` | -0.05 | 1.3 | 1.0 | 0 |

### Using Colour Presets

```bash
clearcut process --main input.mp4 --color-preset warm --output output.mp4
```

They can be combined with templates — the template sets base values, the colour preset refines them:

```bash
# TikTok template + vintage colour
clearcut process --main input.mp4 --template tiktok --color-preset vintage --output output.mp4
```

## Caption Style Presets

Four caption styles are available via `--style`. Each sets specific ASS subtitle parameters.

### `default` — Clean, Safe

| Parameter | Value |
|-----------|-------|
| Font | Arial |
| Size | 48 |
| Color | White |
| Outline | 2px black |
| Shadow | 1px |
| Position | Bottom |
| Animation | None |
| Bold | Yes |

### `modern` — YouTube Standard

| Parameter | Value |
|-----------|-------|
| Font | Montserrat |
| Size | 52 |
| Color | White |
| Outline | 3px black |
| Shadow | None |
| Position | Bottom |
| Animation | **Word-highlight** |
| Bold | Yes |

### `minimal` — Subtle

| Parameter | Value |
|-----------|-------|
| Font | Helvetica Neue |
| Size | 40 |
| Color | Light gray |
| Outline | 1px dark gray |
| Shadow | None |
| Position | Bottom |
| Animation | None |
| Bold | No |

### `bold` — Eye-Catching

| Parameter | Value |
|-----------|-------|
| Font | **Impact** |
| Size | **64** |
| Color | **Yellow** |
| Outline | 4px black |
| Shadow | 2px |
| Position | **Center** |
| Animation | **Word-highlight** |
| Bold | Yes |

### Combining with Templates

Each template selects a default caption style:

| Template | Caption Style |
|----------|--------------|
| `clean` | `default` |
| `tiktok` | `modern` |
| `cinematic` | `minimal` |
| `bold` | `bold` |

You can override the caption style on any template with `--style`:

```bash
clearcut process --main input.mp4 --template tiktok --style bold --output output.mp4
```
