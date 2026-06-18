# LTX TUI Wrapper

A [Trogon](https://github.com/Textualize/trogon) TUI for building and running [ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx) commands on Apple Silicon.

## Setup

```bash
uv sync
```

## Usage

Open the interactive TUI:

```bash
uv run ltx-tui tui
```

Pick a command from the sidebar, fill in the form, then press **Ctrl+R** to run it.

You can also use the CLI directly (same options as `ltx-2-mlx`):

```bash
uv run ltx-tui generate --prompt "a sunset over the ocean" --frame-rate 24 --two-stage -o sunset.mp4
uv run ltx-tui info --model dgrauet/ltx-2.3-mlx-q8
uv run ltx-tui enhance --prompt "a cat walking"
```

## Commands

| Command | Description |
|---------|-------------|
| `generate` | Text-to-video or image-to-video generation |
| `a2v` | Audio-to-video (beta) |
| `retake` | Regenerate a segment of an existing video |
| `extend` | Add frames before/after a video |
| `keyframe` | Interpolate between keyframe images |
| `ic-lora` | IC-LoRA control conditioning |
| `lipdub` | Lip-dub a reference video (experimental) |
| `hdr-ic-lora` | HDR video via IC-LoRA |
| `enhance` | Enhance a prompt with Gemma |
| `info` | Model info and memory estimate |
| `train` | Train a LoRA (requires `ltx-trainer-mlx`) |
| `preprocess` | Preprocess videos for training |
| `slice` | Slice videos into training clips |

For `--image`, enter a path alone (`photo.jpg`) or with frame/strength (`photo.jpg 0 1.0`).

Boolean options (`--distilled`, `--low-ram`, etc.) use a **true/false** dropdown in the TUI — select `true` to enable. On the CLI, both `--distilled` and `--distilled true` work.
