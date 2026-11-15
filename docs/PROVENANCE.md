# Source and evidence provenance

The existing year-provenance record identifies repository creation as 27 January 2025. The `2025` suffix records that project year. This documentation, scoped runtime fixes and regressions were added on 14 November 2026 with AI assistance.

Inspected base commit: `3cdc285d2b3f5ce61c61c109bd87e6c65c6b0392`.
Base tree: `5e1b849703823572232f95f07b04ddb1fa3be72d`.

| Existing material | Evidence boundary |
| --- | --- |
| `ai.py` | Local Pygame/PyTorch DQN game. The inspected version already includes earlier maintenance. |
| `RL agent.png` | Existing screenshot, retained unchanged. It is not a controlled learning evaluation. |
| `docs/ARCHITECTURE_MAINTENANCE.md` | Preserved 11 November 2026 review and terminal-order fix. |
| Terminal-transition regression | Extended to cover final completion and continuing waves; source-based test approach remains explicit. |

The inspected `ai.py` is preserved byte-for-byte under [legacy/baseline-2026-11-14/](../legacy/baseline-2026-11-14/). It is a maintenance baseline, **not a certified original January 2025 submission**.

- Baseline size: 15,765 bytes.
- Baseline SHA-256: `0be9e40555ac8c87f98b7b33c11de24ce942ebef4093910529f6dc8481b538c6`.
- Baseline Git blob: `027cbc97094b073ef609e4f61c5492d122990c3a`.
- Retained screenshot Git blob: `ad4cb74a371dcb9e7947ee27f4a66fade4e1ea59`.

No game dataset, audio pack, pretrained model, engagement data, score history or training artefact was added. Runtime-smoke fixtures are synthetic contract inputs, labelled in their harness; they are not experimental learning evidence. Official library documentation and the original DQN paper are technical references, not proof of the original development process. No source licence file was found, so no blanket MIT licence is asserted.
