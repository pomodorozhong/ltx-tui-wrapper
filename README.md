# LTX TUI Wrapper

A [Textual](https://github.com/Textualize/textual) TUI for building and running [ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx) `generate` commands on Apple Silicon.

## Setup

```bash
uv sync
```

## Usage

Open the interactive generate command builder:

```bash
uv run ltx-tui
```

Fill in the form, review the command preview at the bottom, then press **Ctrl+R** or click **Run** to generate.

Pre-fill common fields from the CLI:

```bash
uv run ltx-tui -p "a sunset over the ocean" -o sunset.mp4
uv run ltx-tui -p "animate this photo" -i photo.jpg -o anim.mp4
```

### Batch generation

Re-run the last successful generate settings multiple times. Each output gets a timestamp suffix (e.g. `sunset_20250619_143022.mp4`). Requires at least one prior run from `ltx-tui`.

```bash
# Generate 5 videos with the same settings
uv run ltx-tui-batch -n 5

# Keep going if one run fails
uv run ltx-tui-batch -n 10 --continue-on-error
```

### Extend a video

Chain I2V segments from the last generated video until the combined length exceeds a target duration. Uses each segment's last frame as the next input (no upscaling by default). Requires `ffmpeg` and `ffprobe` on PATH.

```bash
# Extend to over 60 seconds (default output: <last-output>_extended.mp4)
uv run ltx-tui-extend -l 60

# Target 90 seconds with a custom output path
uv run ltx-tui-extend -l 90s -o rain_extended.mp4

# AI-upscale each last frame before the next segment (requires realesrgan-ncnn-vulkan)
uv run ltx-tui-extend -l 60 --upscale

# Retry failed segments up to 3 times; keep intermediate segment files
uv run ltx-tui-extend -l 1.5m -r 3 --keep-segments

# Extend 5 videos; each final output gets a timestamp suffix
uv run ltx-tui-extend -l 60 -n 5

# Keep going if one extend run fails
uv run ltx-tui-extend -l 60 -n 10 --continue-on-error
```

Duration accepts seconds (`60`), suffixed seconds (`90s`), or minutes (`1.5m`).

### Upscale to 1080p

Scale a video to strict 1920×1080, preserving aspect ratio and padding to 16:9. Requires `ffmpeg` and `ffprobe` on PATH.

```bash
# Fast Lanczos upscale (default output: <last-output>_1080p.mp4)
uv run ltx-tui-upscale

# Custom input/output
uv run ltx-tui-upscale -i rain.mp4 -o rain_1080p.mp4

# AI upscale via realesrgan-ncnn-vulkan (requires binary on PATH)
uv run ltx-tui-upscale --model realesrgan-x4plus

# AI upscale for anime-style content
uv run ltx-tui-upscale --model realesr-animevideov3
```

Without `--model`, uses FFmpeg Lanczos — fast and stable, but cannot reconstruct detail. With `--model`, extracts frames, runs [realesrgan-ncnn-vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan), then encodes to 1080p. Download the macOS zip from [GitHub releases](https://github.com/xinntao/Real-ESRGAN/releases) and place the binary + `models/` folder on PATH.

## Generate options

The TUI covers the full `ltx-2-mlx generate` surface:

| Section | Options |
|---------|---------|
| Core | prompt, output, pipeline mode, frame rate |
| Video | resolution, frame count |
| I2V | reference image with optional frame/strength/CRF, extra image specs |
| Sampler | steps, stage 1/2 steps, CFG/STG scale, prompt enhancement |
| Two-stage | dev transformer, distilled LoRA, TeaCache |
| LoRA | repeatable `PATH STRENGTH` lines |
| Model | model ID, Gemma encoder, seed, low-RAM streaming, tiling |

Pipeline mode (required — pick one):

- **Two-stage** — dev + CFG at half-res, upscale, distilled refine (recommended)
- **Two-stage HQ** — res_2s sampler for stage 1
- **Distilled** — fastest path
- **One-stage** — dev + CFG at full resolution

For `--image`, enter a path alone (`photo.jpg`) or with frame/strength (`photo.jpg 0 1.0`).
