# Zombie Hunter: a DQN learning game

An educational Python game in which an online Deep Q-Network selects movement or shooting actions while zombies approach the player. Pygame renders the world; PyTorch updates a Q-network from a bounded replay buffer.

The source demonstrates reinforcement-learning mechanics. No trained checkpoint, controlled learning curve or evidence of an optimal policy is included.

![Existing repository game screenshot](RL%20agent.png)

## Explore the project

| Resource | What it explains |
| --- | --- |
| [Current source](ai.py) | Game rules, five-value observation, five actions and DQN update |
| [Architecture and RL contract](docs/ARCHITECTURE.md) | Exact state, actions, reward rules, episode lifecycle and design limits |
| [Setup and operating guide](docs/RUNBOOK.md) | Correct launcher, dependencies, optional audio and recovery |
| [Verification record](docs/VERIFICATION.md) | Focused regressions, real-dependency smoke design and remaining limits |
| [Source provenance](docs/PROVENANCE.md) | Inspected commit, preserved baseline and dated maintenance |
| [Pre-update source snapshot](legacy/baseline-2026-11-14/) | Exact inspected source before this update |

## Download the desktop application

Open [desktop release 1.0.0](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/releases/tag/desktop-v1.0.0) and select your computer's package. Python, Pygame, NumPy and CPU PyTorch are included; no Python installation or AI API key is needed.

| Computer | Package | Open after extracting |
| --- | --- | --- |
| Windows 10/11 x64 | `ZombieHunter-windows-x64.zip` | `ZombieHunter/ZombieHunter.exe` |
| Ubuntu 22.04+ x64 | `ZombieHunter-linux-x64.tar.gz` | `ZombieHunter/ZombieHunter` |
| macOS 15+ Apple silicon | `ZombieHunter-macos-arm64.zip` | `ZombieHunter/ZombieHunter.app` |

Keep the complete extracted application folder. See [download and launch instructions](docs/DOWNLOADS.md) for checksums, supported targets and troubleshooting. Windows packages are unsigned; the macOS application has an ad-hoc signature without Developer ID or notarization. Intel Macs do not have a native package in this release.

The agent plays automatically. Close the window to stop. Learning stays in memory and resets when the application exits; no pretrained policy is supplied. Optional sound recordings are not included.

## Run from source

[Download the source ZIP](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/archive/refs/heads/main.zip), extract it and open a terminal in that directory. The launcher is **`ai.py`**. A desktop display is required.

Use Python 3.11 or 3.12 for the documented setup. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe ai.py
```

On macOS or Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python ai.py
```

The agent plays automatically; movement keys do not control it. Close the game window to stop. Weights and replay exist only in memory and are lost on exit. Optional sounds are not supplied. See the [runbook](docs/RUNBOOK.md) for platform-specific PyTorch builds and setup limits.

The dependency file lists the actual imports; it is not a tested lockfile. Native desktop builds use the pinned [build environment](packaging/BUILDING.md) and record installed versions in each release manifest.

## Verify

Without the game dependencies:

```sh
python -m unittest discover -s tests -v
```

Ten standard-library checks execute isolated production methods and transition statements without importing the game module. They cover exploration, reset boundaries, death, final-wave completion and continuing wave transitions.

With dependencies installed, a bounded headless check is available:

```sh
python scripts/runtime_smoke.py
```

The GitHub workflow also runs this real-dependency smoke with CPU PyTorch and SDL dummy drivers. It checks startup/exit, a Q-network forward pass and an optimiser update using labelled synthetic test fixtures. Check the hosted run's actual status; this is not a convergence or policy-quality experiment. See [verification](docs/VERIFICATION.md).

The native release workflow additionally builds each supported platform, archives it, extracts it into a separate directory, and executes the extracted application for 72 real gameplay frames. Its report must confirm finite Q values and changed, finite network parameters after actual Adam updates. [Release manifests](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/releases/tag/desktop-v1.0.0) retain this evidence and archive hashes. Automated dummy-display checks do not replace a human check of the visible GUI on every laptop.

```sh
python ai.py --smoke-test --smoke-report build/source-smoke.json
```

## Maintenance and scope

The 14 November 2026 fixes clamp exploration to its minimum, clear stale damage-flash/banner state on reset, mark final-wave completion terminal, and record the actual successor world when a lower-level wave advances. A preserved baseline and the [11 November maintenance note](docs/ARCHITECTURE_MAINTENANCE.md) keep the history inspectable.

The `2025` suffix records the repository creation year, 27 January 2025. Later changes retain their own dates. No `LICENSE` file is present, so no blanket MIT licence is asserted for this source.
