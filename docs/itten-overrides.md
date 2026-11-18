# ITTEN overrides

Every departure from this project's system or from an ITTEN rule, with its reason. Rendered from `itten.overrides.json` by `node itten/scripts/overrides.js render`; edit that file, not this one.

| Date | Where | Rule | Check | System value | Used instead | Reason | Floors still met | ITTEN |
|---|---|---|---|---|---|---|---|---|
| 2026-11-16 | `.head` | CRF-01 · Spacing comes only from the scale | `spacing-scale` | a step of the spacing scale | padding-bottom: 38svh (22svh below 900 px) | How far the reader scrolls past the header before the first week arrives. It is a share of the screen so the valley stays in view at any screen height; it does not space text. | Yes | 0.3.4 |
| 2026-11-16 | `.head` | CRF-30 · Spacing follows the text size | `spacing-unit` | spacing in rem | padding-bottom: 38svh (22svh below 900 px) | The same padding follows the screen height, not the text size, for the same reason. | Yes | 0.3.4 |
| 2026-11-16 | `.col` | CRF-01 · Spacing comes only from the scale | `spacing-scale` | a step of the spacing scale | margin-top: -100svh | Pulls the weeks column up by one screen so it scrolls over the sticky stage. It places the column over the scene; it does not space text. | Yes | 0.3.4 |
| 2026-11-16 | `.col` | CRF-30 · Spacing follows the text size | `spacing-unit` | spacing in rem | margin-top: -100svh | The same margin has to match the stage, which is one screen tall whatever the text size. | Yes | 0.3.4 |
