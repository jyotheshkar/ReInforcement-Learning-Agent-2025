# Zombie Hunter DQN desktop 1.0.0

Native desktop packages for the existing Pygame reinforcement-learning game. Download an operating-system asset from this release, extract it and launch the application. Python and CPU inference/training dependencies are included.

| Asset | Target |
| --- | --- |
| `ZombieHunter-windows-x64.zip` | Windows 10/11, Intel/AMD x64 |
| `ZombieHunter-linux-x64.tar.gz` | Ubuntu 22.04 or newer, Intel/AMD x64 |
| `ZombieHunter-macos-arm64.zip` | macOS 15 or newer, Apple silicon ARM64 |

**Start here:** [download, launch and checksum instructions](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/blob/desktop-v1.0.0/docs/DOWNLOADS.md).

The agent controls movement and shooting automatically. Close the game window to exit. Network weights and replay are memory-only and reset when the application restarts. Optional audio assets are not included, so silent operation is expected. No pretrained checkpoint, convergence result or optimal-policy claim accompanies this release.

The release workflow builds on Windows Server 2022 x64, Ubuntu 22.04 x64 and macOS 15 ARM64. It extracts each native archive and requires a bounded executable smoke check that exercises rendering through SDL dummy drivers, agent actions, replay and at least one optimiser update before publication. This is an execution check, not a human desktop usability test or a policy-quality experiment. Consult the associated Actions run and manifests for the actual build results and source revision.

Use `SHA256SUMS.txt` to verify downloaded archives. Platform-specific `BUILD-MANIFEST-*.json` assets record build/dependency information; each package also contains `BUILD-MANIFEST.json` and third-party licence notices. Keep the package's bundled libraries and notices intact.

`pygame-2.6.1.tar.gz` supplies the corresponding Pygame source. It is a dependency source archive, not an application to launch.

See the [native build guide](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/blob/desktop-v1.0.0/packaging/BUILDING.md) for the pinned environment and rebuild instructions.

Windows packages have no publisher certificate. The macOS application has no Apple Developer ID signature or notarization; its local ad-hoc signature does not establish a verified publisher, and Gatekeeper may block it. Intel Macs and other unlisted architectures do not have native packages in this release. See the download guide for compatibility and troubleshooting details.
