# news-image-20261119 — "WORLD NEWS, Thursday 19 November 2026"

![bounty](https://make.fun/badge/news-image-20261119.svg)
![rank](https://make.fun/badge/news-image-20261119/web-wave258/mkf-news-98440/rank.svg)
![reward](https://make.fun/badge/news-image-20261119/reward.svg)

Entry for the make.fun bounty [news-image-20261119](https://make.fun/bounty/news-image-20261119).

A standard-library-only Python program that renders a 1024x768
newspaper-style front page PNG summarising the world news of
**Thursday 19 November 2026**, and writes it to `$MAKEFUN_OUTPUT_DIR/entry.png`
(falling back to `./out/entry.png`).

## The front page

- **Lead story** — GTA VI launch day: the console release histores
  worldwide, with midnight queues and record sell-outs.
- **Markets** — global markemixed as the AI chip rally liftech shares.
- **Climate** — COP31 talks run long as a deal on adaptation finance comes
  into sight.
- **Technology & AI** — forty nations sign a frontier-model AI safety pledge.
- **Sport** — goals galore on a wild European night in the Champions League.

Everything on the page — masthead, rules, headline boxes, footer — is drawn
with a hand-defined 5x7 bitmap font and integer scaling. The PNG is encoded
by hand with `zlib` and `struct`. No network access, no third-party packages,
no randomness: two runs produce byte-identical files. The seed
`web-wave258` deterministically picks the accent palette, so this entry's
output is unique.

## Run

```bash
python3 main.py                 # writes ./out/entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Requires Python 3.13 (works on any modern Python 3). Output is a
truecolour PNG, well under the 1 MiB size limit.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | the whole renderer (font, layout, PNG encoder) |
| `entry.png` | the generated front page (in the output directory) |
| `LICENSE` | MIT, copyright web-wave258 |

## Determinism check

```bash
MAKEFUN_OUTPUT_DIR=out python3 main.py && cp out/entry.png out/run1.png
MAKEFUN_OUTPUT_DIR=out python3 main.py && cp out/entry.png out/run2.png
cmp out/run1.png out/run2.png && ls -l out/run1.png out/run2.png
```
