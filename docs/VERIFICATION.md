# Verification record

Review date: 14 November 2026. Baseline: `3cdc285d2b3f5ce61c61c109bd87e6c65c6b0392`.

## Reproduced defects and scoped changes

The existing terminal regression initially passed. Added checks reproduced exploration-floor and reset-state failures:

- Epsilon 0.1001 decayed to 0.0995995, below its configured 0.1 minimum. The successful-update path now clamps to the minimum.
- Reset retained the previous trial's damage flash and expired banner. These presentation fields now reset while learner state remains intact.

The transition contract was also corrected: final-wave completion is terminal without a death penalty, and continuing wave advancement records the actual successor world. The death path still records its terminal observation before reset. Other reward/game constants are retained.

## Local checks

```sh
python -m unittest discover -s tests -v
python -m compileall -q ai.py tests scripts legacy
```

Ten focused checks pass on Python 3.11.15. They execute selected production method/loop AST nodes without importing the interactive application. Coverage includes exploration above/near/at its floor, replay warmup, reset presentation and learner preservation, death, final-wave completion, continuing-wave successor state and an ordinary active wave.

Syntax, local document targets and preserved-baseline hashes are checked separately. These tests do not execute PyTorch or Pygame.

## Hosted real-dependency smoke

The workflow adds a bounded Ubuntu/Python 3.11 job installing CPU PyTorch from its official index plus NumPy/Pygame from PyPI. `scripts/runtime_smoke.py` runs the actual program with SDL dummy drivers and one injected QUIT event, then checks a finite five-output forward pass, a real optimiser update, epsilon clamping and target-network synchronisation.

Its in-memory training batch is explicitly synthetic test data. No checkpoint or score series is generated. The job's real hosted status must be inspected on the published commit; merely adding the job does not establish that it passed.

## Local environment and remaining limits

Default Python 3.11.15 has no NumPy, PyTorch or Pygame. The available bundled Python 3.12.14 has NumPy but no PyTorch or Pygame. No packages were installed locally, so no actual desktop/audio/GPU run or clean local dependency installation was performed.

No convergence experiment, saved-policy evaluation, controlled benchmark or supported-platform matrix is established. Passing source boundaries and a bounded tensor/window smoke cannot establish that this agent learns an effective policy. Before broader claims, retain actual desktop evidence and a separately specified no-learning evaluation over held-out seeds.

## Hosted validation — 15 November 2026

[GitHub Actions run 43676931574](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/actions/runs/43676931574) passed both jobs on the reviewed code: the ten source-contract regressions and a real CPU PyTorch/Pygame smoke. The smoke exercised one bounded game frame, a five-output network forward pass, and a finite optimiser update using explicitly synthetic in-memory transition fixtures. No policy convergence, gameplay score or learning-performance result is claimed. Local absence of these ML/game dependencies remains as recorded above.

## Native desktop release checks - 15 November 2026

The desktop workflow builds Windows x64, Ubuntu x64 and macOS Apple-silicon packages with Python 3.11 and pinned dependencies. It first checks the source, then runs each frozen application before archiving and again after extraction into an unrelated working directory. Publishing requires every target to pass.

The explicit `--smoke-test` mode runs 72 real gameplay frames with SDL dummy drivers, fills replay past 64 experiences, and checks actual Adam updates, a finite five-value Q output and changed, finite network parameters. This does not use the earlier source smoke's synthetic transition fixtures. Default launch remains the interactive autoplay game.

Each published platform manifest identifies its exact source commit, installed dependencies, archive size/hash, signing status and extracted-executable execution report. Inspect those [release assets](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/releases/tag/desktop-v1.0.0) and the associated [native workflow](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/actions/workflows/release.yml) for actual results. Human visible-window, audio-device and broad laptop compatibility tests are not established by this automated check.
