# Blink — print-and-play

Every document exists in a colour and a black-and-white version. Pick one of
each pair; the content is identical.

### Cards

| File | Contents | Pages |
|---|---|---|
| `Blink-deck-colour.pdf` / `-bw` | main deck, 80 cards + 1 sheet of backs | 10 |
| `Blink-objectives-colour.pdf` / `-bw` | 12 secret map objectives, fronts and backs | 4 |

### Booklets and components

| File | Contents |
|---|---|
| `Blink-rules-v0.22.pdf` / `-bw` | the rulebook |
| `Blink-first-game.pdf` / `-bw` | the First Game booklet |
| `Blink-card-effects.pdf` / `-bw` | victory-card effects reference |
| `Blink-map-objectives.pdf` / `-bw` | the objectives module — **not re-tuned for v0.21**, leave it out of a first game |
| `Blink-player-board-A4.pdf` / `-bw` | player board, one per player |
| `Blink-player-aid.pdf` / `-bw` | the turn on one face, the numbers on the other. One page is a four-player set: cut the four cards out and fold each one backwards along the dotted line, so it comes out double thickness at 88×63mm with no duplex printing to register |
| `Blink-playtest-sheet.pdf` | one page to fill in while you play |
| `Blink-variants.pdf` | variants and shelved rules — none are part of the base game |

## Reading a card in hand

Each card carries a **corner index** — the rank with its suit glyph directly
beneath it — in the top-left corner, repeated rotated in the bottom-right. Fan
the hand either way up and rank and suit stay together in the exposed sliver, so
you can sort by suit or by rank without spreading the cards.

Everything else on the face is reference, not something you read while playing:
the terrain's `holds` and `attack` values, the three effects, and the player
counts the card is used at.

## Printing

Cards are **63 × 88 mm** — standard poker size, so ordinary sleeves fit. Nine to
an A4 sheet.

- Print at **100% / "actual size"**. Do not use "fit to page" or "shrink to
  printable area"; either will make the cards the wrong size for sleeves.
- The dashed rules are the cut lines.
- Card stock of 200–250 gsm, or print on plain paper and sleeve each card in
  front of a card from an ordinary deck. The second option is cheaper, shuffles
  better, and means you can skip the backs entirely.

**Objective backs** are laid out for duplex printing on the **long edge** — each
back sheet is mirrored left-to-right so it lines up with the fronts. Print one
test sheet before committing to the whole deck; duplex alignment varies by
printer.

**Main-deck backs** are a single sheet of nine. Print it as many times as you
need, or skip it if you are sleeving.

## Which cards you need

The main deck is 20 ranks in four suits. Not every rank is used at every count:

| Players | Starting hands | Market |
|---|---|---|
| 2 | ranks 6–10 | ranks 11–15 |
| 3 | ranks 3–10 | ranks 11–18 |
| 4 | ranks 1–10 | ranks 11–20 |

Each card's footer names the counts it is used at, so you can pull a subset
without consulting a table. Printing all 80 lets you play at any count.

Player boards now carry **five tiers** and printed **ascension coin spots** — print at
100% or the 13 mm unit slots will not match your components.

You need **at least eight** objective cards for a four-player game, since each
player is dealt two and keeps one. The deck of twelve covers every count.

The objectives are an **advanced module and are not re-tuned for v0.21** — the
chains were balanced against the old placement rules and are now both harder and
unevenly hard. Print them if you like, but do not add them to a first game.

## The black-and-white versions

They are not greyscale conversions. Each terrain carries its own **hatch
pattern** as well as its own **glyph**, so components stay sortable face-up
after a photocopy and remain readable to colour-blind players. The four
patterns are:

| Terrain | Pattern |
|---|---|
| mountain | cross-hatch |
| forest | single diagonal |
| plains | scattered dots |
| ocean | horizontal waves |

The same four run through everything — cards, the hex diagrams on the objective
cards, and every figure in the rulebook and the First Game booklet.

The three **player colours** also had to survive losing hue, because the
rulebook figures show players contesting the same tiles. They become a solid
dark disc with a white rim (you), an open disc (a rival), and a mid-grey disc (a
third player). Stacks stay countable because each disc keeps its rim.

Page tints are dropped to white so a mono booklet does not lay down a full-bleed
grey on every page.

## Regenerating

Everything is generated, so nothing can drift from the rules:

```
cd source
sh build_pdfs.sh        # everything: booklets, decks, boards, colour and mono
```

Card effects are read from `build_effects.py`, which derives them from the same
rank bands the rulebook prints. Objective wording and pattern art come from
`build_module.py` and `pattern_figs.py`, the sources the objectives booklet uses.
Change a rule in one place and every document follows.

The black-and-white booklets are **not** a parallel set of builders — `build_bw.py`
post-processes the HTML the normal builders just produced, rewriting the palette
and hatching the figures. There is one source for the words and one for the
figures, so a rules change cannot land in the colour booklet and miss the mono
one.

`build_pdfs.sh` uses **wkhtmltopdf**, the reference renderer. PDFs built with
WeasyPrint paginate differently and render the masthead at the wrong size, since
WeasyPrint does not support the CSS `clamp()` the display headings use.
