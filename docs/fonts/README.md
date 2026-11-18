# Fonts

The site's two families, served with it instead of from Google Fonts. Google Fonts splits each family into subsets by script, and none of them includes the arrows (→ ↗) or ≤ and ≥, so the browser drew those in a system font.

| File | Family | Weights | From |
|---|---|---|---|
| `InterTight.woff2` | Inter Tight | 300 to 500 (variable) | [google/fonts](https://github.com/google/fonts/tree/main/ofl/intertight) `InterTight[wght].ttf`, commit `0b58fb370093` |
| `GeistMono.woff2` | Geist Mono | 400 to 500 (variable) | [google/fonts](https://github.com/google/fonts/tree/main/ofl/geistmono) `GeistMono[wght].ttf`, commit `121c8e30e209` |

Both are cut to the weights the pages use and to these characters: Basic Latin, Latin-1, Latin Extended-A and -B, spacing modifiers, general punctuation, currency, letterlike symbols, arrows, mathematical operators and geometric shapes (U+0020–007E, U+00A0–024F, U+02B0–02FF, U+2000–206F, U+20A0–20CF, U+2100–214F, U+2190–21FF, U+2200–22FF, U+25A0–25FF). Every character in the published pages and their data is in that set. To cut them again, with fontTools:

```sh
fonttools varLib.instancer 'InterTight[wght].ttf' wght=300:500 -o it.ttf
fonttools subset it.ttf --unicodes="U+0020-007E,U+00A0-024F,U+02B0-02FF,U+2000-206F,U+20A0-20CF,U+2100-214F,U+2190-21FF,U+2200-22FF,U+25A0-25FF" --layout-features='*' --flavor=woff2 --output-file=InterTight.woff2
```

and the same for Geist Mono with `wght=400:500`. Both fonts are under the SIL Open Font License 1.1 (`InterTight-OFL.txt`, `GeistMono-OFL.txt`).
