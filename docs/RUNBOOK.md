# Setup, operation and recovery

Updated 15 November 2026. For the packaged desktop application, use the [download instructions](DOWNLOADS.md). This page describes running and inspecting a source checkout. No account, API key, hosted endpoint or external dataset is used by the game.

## Install and inspect

Use the [README setup commands](../README.md#run-from-source). The dependencies match actual imports: NumPy, Pygame and PyTorch. Python 3.11 and 3.12 parsed the source and ran the focused checks during review; full desktop operation was not verified locally.

For CPU/CUDA selection, use the [official PyTorch installer](https://pytorch.org/get-started/locally/). The source needs `torch`, not torchvision or torchaudio. Pygame documents its [basic installation and loop](https://www.pygame.org/docs/), and NumPy provides [installation guidance](https://numpy.org/install/). Install into the virtual environment used to launch the game.

The unpinned `requirements.txt` declares imports, not a reproducible lock. Retain actual Python/platform/package versions with any experiment result after installation is verified. The CI smoke uses the official CPU PyTorch index and PyPI packages on Ubuntu; it is not a Windows/macOS certification.

## Launch and stop

The entry point is `ai.py`. Run it from the repository directory. Normal launch opens a 1200-by-700 Pygame window and trains while playing. `--version` prints the application version without loading the game dependencies. `--smoke-test --smoke-report PATH` runs a bounded, seeded diagnostic with SDL dummy drivers and saves its execution report. There is no saved-policy mode or keyboard-controlled player. The small CPU network uses one Torch computation thread to keep the event loop responsive.

Close the window to stop normally; the loop calls `pygame.quit()` on exit. If it freezes, stop the terminal process. Weights, optimiser state and replay are not saved, so there is no persistent learning state to recover. Avoid importing `ai.py` into other applications because it starts the interactive loop.

## Optional audio

The game looks for `shoot.wav`, `hit.wav`, `zombie_death.wav` and `level_up.wav` in the **current working directory**. None is supplied. Missing files and lack of an audio device permit silent play. A corrupt or unsupported file may still raise a loading error; remove the optional file and retry. Only use assets you have permission to include.

## What to observe

The agent chooses four movements or shooting. The HUD reports health, kills, remaining zombies, highest kills, trials and level. Death or final-wave completion resets the trial; learned parameters/replay remain in memory. Optimisation begins after replay contains 64 records and prints periodically by its update counter.

A moving agent, a low loss or a high single-run score does not establish convergence or generalisation. The [RL contract](ARCHITECTURE.md) states the actual reward and remaining limitations.

## Focused and runtime checks

`python -m unittest discover -s tests -v` needs only Python's standard library.

`python scripts/runtime_smoke.py` needs all runtime dependencies. It runs the actual program with SDL dummy video/audio drivers and injects a QUIT event for a bounded one-frame run. It then exercises real inference and one optimiser update using explicitly synthetic in-memory fixtures. These fixtures are not observed trajectories or a policy-performance dataset. No weights are saved.

## Common failures

| Symptom | Check |
| --- | --- |
| Missing package | Use the interpreter from the environment where dependencies were installed. |
| Display error in a remote session | Use a desktop session for interactive play; the smoke harness is a separate contract check. |
| Audio load failure | Remove optional assets and inspect them separately. |
| GPU setup mismatch | Select the appropriate official PyTorch build; CPU is the fallback when CUDA is unavailable. |
| Slow high-zombie levels | Measure frame/update time; no real-time capacity has been established. |
| Learning disappears after exit | Expected: the application has no checkpoint persistence. |

Preserve the exact commit and environment information before changing constants. The [baseline snapshot](../legacy/baseline-2026-11-14/) is source evidence for comparison, not a trained-model checkpoint.
