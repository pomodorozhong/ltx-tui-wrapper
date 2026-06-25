# Best Generation Flow

A two-phase workflow: explore prompts with cheap short clips, then extend only the winners.

## Phase 1 — Prompt exploration (short clips)

1. **Generate batch 1** — Run `ltx-tui` once with a broad, general prompt, then batch it:

```bash
uv run ltx-tui-batch -n 5
```

Review outputs for unwanted behavior (odd objects, camera drift, motion artifacts).

2. **Refine the prompt** — Tighten wording to remove unwanted elements and emphasize what you want.

3. **Generate batch 2** — Run `ltx-tui` again with the refined prompt, then batch:

```bash
uv run ltx-tui-batch -n 5
```

Keep only the best clips.

## Phase 2 — Extend winners

4. **Extend from a folder** — Move the keepers into one folder and extend them:

```bash
uv run ltx-tui-extend-from -i path/to/best/ -l 20 --continue-on-error
```

If you pick quite a few clips to extend, expect it to take a while. But don't worry too much about interrupting it — re-run the same command and it picks up where it left off. Finished videos are skipped; in-progress ones resume from their last completed segment, so you lose at most one segment's worth of work (~5 minutes).

**Tip:** Quality drops noticeably past ~20 seconds total. Prefer shorter extensions; only go longer if a clip is holding up well.
