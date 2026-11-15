# Download Zombie Hunter DQN

Zombie Hunter DQN is a desktop reinforcement-learning demonstration. A Deep Q-Network controls a player in a Pygame zombie-survival world and learns during the session. You watch the agent act; this release does not add manual movement controls.

Get the native application from the repository's [Releases page](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/releases). Open the release's **Assets** section and choose your operating system. The application packages include Python, Pygame, NumPy and CPU PyTorch, so you do not need to install Python, CUDA or an AI API key.

## Choose a package

| Computer | Release asset | Launch after extracting | Native build runner |
| --- | --- | --- | --- |
| Windows 10/11, Intel or AMD 64-bit | `ZombieHunter-windows-x64.zip` | `ZombieHunter/ZombieHunter.exe` | Windows Server 2022 x64 |
| Ubuntu 22.04 or newer, Intel or AMD 64-bit | `ZombieHunter-linux-x64.tar.gz` | `ZombieHunter/ZombieHunter` | Ubuntu 22.04 x64 |
| macOS 15 or newer, Apple silicon | `ZombieHunter-macos-arm64.zip` | `ZombieHunter/ZombieHunter.app` | macOS 15 ARM64 |

These are the release's build targets, not a claim that every OS version or Linux distribution has been tested. The native workflow checks each extracted executable with a bounded automated run using SDL dummy display/audio drivers. It does not replace a human test of a visible window on every laptop.

Intel Macs, Windows ARM64, Linux ARM64, 32-bit computers and older operating systems do not have native packages in this release. An Intel-Mac build is not supplied because current official PyTorch macOS wheels target Apple silicon. The automatically generated **Source code** archives are for developers; they are not the packaged desktop application.

## Windows

1. Download `ZombieHunter-windows-x64.zip` and `SHA256SUMS.txt` from the same release.
2. Verify the archive using the checksum instructions below.
3. Right-click the ZIP, choose **Extract All**, and open the extracted `ZombieHunter` folder.
4. Open `ZombieHunter.exe`. Keep the `_internal` folder and the other bundled files beside it.

The application is portable and does not need an installer or administrator access. Do not run the executable from inside the ZIP or move only the executable to another folder.

## Linux

Download `ZombieHunter-linux-x64.tar.gz` and `SHA256SUMS.txt` from the same release. In the download directory, verify and extract the archive:

```sh
sha256sum --ignore-missing -c SHA256SUMS.txt
tar -xzf ZombieHunter-linux-x64.tar.gz
./ZombieHunter/ZombieHunter
```

Continue only if your downloaded archive reports `OK`. Use a normal graphical desktop session with a working display. A server shell without a display is not an interactive desktop. Extract onto a filesystem that preserves Unix permissions and symbolic links, and keep the application folder intact.

The package is built on Ubuntu 22.04. Older GNU C libraries, Alpine Linux's musl environment and other distributions are outside the verified build target. A graphics/display library supplied by the operating system may still be required; bundling Python does not bundle the operating system.

## macOS

1. Download `ZombieHunter-macos-arm64.zip` and `SHA256SUMS.txt` from the same release.
2. Verify the ZIP using the checksum instructions below.
3. Extract it using Finder's Archive Utility, then open the extracted `ZombieHunter` folder and locate `ZombieHunter.app`.
4. Open `ZombieHunter.app`. You may move the application to your Applications folder; keep the supplied notices and build manifest for reference.

Use an Apple-silicon Mac running macOS 15 or newer. This is an ARM64 application, not a universal Intel/Apple-silicon application.

The release does not have an Apple Developer ID signature or Apple notarization. PyInstaller's local ad-hoc signature does not establish a verified publisher. Gatekeeper may therefore prevent a downloaded copy from opening. A checksum verifies that the download matches the published file; it does not provide notarization or an independent security review. See [Apple's explanation of downloaded-app checks](https://support.apple.com/102445) if macOS blocks it. No command to disable those checks is required or provided here.

## Verify a download

Download `SHA256SUMS.txt` from the **same release** as your archive. Compare the full SHA-256 value for the exact filename you downloaded. If it differs, do not launch the archive; download a fresh copy from this repository's release.

On Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\ZombieHunter-windows-x64.zip
Get-Content -LiteralPath .\SHA256SUMS.txt
```

Compare the displayed hash with the `ZombieHunter-windows-x64.zip` line. Uppercase and lowercase hexadecimal letters represent the same hash.

On macOS:

```sh
shasum -a 256 ZombieHunter-macos-arm64.zip
cat SHA256SUMS.txt
```

Compare the displayed hash with the `ZombieHunter-macos-arm64.zip` line. On Linux, the `sha256sum --ignore-missing -c` command above checks whichever listed archive is present in the current directory.

## What to expect

The game opens a 1200 × 700 window. The agent moves and shoots automatically while the window displays the survival world and counters. Close the window to stop the application. There are no keyboard controls for directing the player in this release.

Learning happens locally in memory. The network weights, replay buffer and current session are discarded when the application exits; reopening starts a new run. No pretrained checkpoint or demonstrated optimal policy is included. An automated startup/learning check confirms that the program can execute a learning update; it is not evidence that the agent has learned a successful strategy.

Optional sound recordings are not included in the repository, so a silent run is expected. No online account, API key or gameplay network connection is needed.

## If it does not open

| Symptom | What to check |
| --- | --- |
| Windows cannot find a DLL, or the application closes immediately | Extract the whole ZIP again and keep `_internal` beside the executable. Confirm that you downloaded the x64 package. |
| Windows shows an unknown-publisher warning | This release does not have a publisher certificate. Verify its origin and checksum; do not disable Windows security protections. |
| Linux reports a missing display | Launch from a graphical desktop. Remote/headless sessions are for the automated smoke check, not the visible game. |
| Linux reports `GLIBC` or a shared-library error | Record the message and distribution version. Ubuntu 22.04 x64 is the build baseline; older or different distributions may be incompatible. |
| macOS reports an incompatible application | Confirm Apple silicon and macOS 15 or newer. The ARM64 archive does not support Intel Macs. |
| macOS cannot verify the developer | Read the signing limitation above. A notarized distribution is not supplied in this release. |
| It runs without sounds or the agent performs poorly | Silent operation and a newly initialized learner are expected; neither is evidence of a packaging failure. |

When reporting a problem in [Issues](https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025/issues), include the release tag, asset filename, OS version, CPU architecture, exact error and whether its checksum matched. The supplied `BUILD-MANIFEST.json` identifies the packaged source and dependency versions. Do not include personal files or credentials.

## Package contents and notices

Keep `THIRD-PARTY-LICENSES.txt` and the bundled `licenses` directory with the application when redistributing a package. PyTorch, NumPy, Pygame, SDL and other bundled components retain their own licence terms. The release includes `pygame-2.6.1.tar.gz` as the corresponding Pygame source. The desktop packaging does not assign a new licence to the repository's original source.

Each release also supplies platform-specific `BUILD-MANIFEST-*.json` files and `SHA256SUMS.txt`. Build information and checksums make the distributed artifacts inspectable; they do not imply bit-for-bit reproducible builds or a security certification.

Developers can use the [source runbook](RUNBOOK.md), [architecture](ARCHITECTURE.md) and [verification record](VERIFICATION.md) to inspect or run the Python project directly.

The [native build guide](../packaging/BUILDING.md) explains the pinned build environment, source inputs and package rebuild process.
