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
