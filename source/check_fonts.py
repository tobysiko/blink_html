# -*- coding: utf-8 -*-
"""Did the PDFs come out in the right typefaces?

This is the one production failure the other checks cannot see. Every builder
here pulls Fraunces and IBM Plex from Google Fonts with a <link> in the head,
so the typography of a printed rulebook depends on a NETWORK FETCH succeeding
at the moment the PDF is rendered. When it does not, nothing breaks: the
browser silently falls back to a system serif, writes a perfectly valid PDF,
and every other check in this folder passes. The rulebook simply comes out in
Lucida Grande and nobody notices until it is in front of a publisher.

That happened. A v0.24 build embedded IBM Plex Mono (installed locally on that
machine), Lucida Grande and Menlo — no Fraunces, no IBM Plex Sans — and the
build reported success.

    python3 check_fonts.py

THE FIX, if this fails: install the two families locally, which makes every
builder here work offline and removes the dependency for good.

    brew install --cask font-fraunces font-ibm-plex-sans font-ibm-plex-mono

or download them from fonts.google.com and drop them in Font Book.
"""
import pathlib
import re
import sys

from version import VTAG

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

# The families the design actually asks for, by the name that ends up inside a
# PDF (no spaces, and usually behind a six-letter subset tag).
WANT = {
    "Fraunces": "the display face — every heading and the masthead",
    "IBMPlexSans": "the body face — nearly all the running text",
}

# Documents where a missing face ruins the artefact. Card and token sheets are
# reported but not failed, because several are set entirely in the mono face by
# design. The player boards ARE checked: they came out in Times, which nobody
# chose.
CHECKED = (f"Blink-rules-{VTAG}", "Blink-first-game", "Blink-variants",
           "Blink-map-objectives", "Blink-player-board")

# ...but a document is only asked for the faces IT USES. The boards are set
# entirely in IBM Plex - there is not one word of Fraunces on them - so
# demanding Fraunces of them made this check fail every single run, for a
# document that was correct. A check that always fails is a check nobody reads,
# and on 5 Sep 2026 a genuine failure was buried in its noise and shipped. So
# the wanted faces are read out of the document the PDF was made from.
SOURCES = {"Blink-player-board-A4": "board_a4.svg",
           "Blink-player-board-A4-bw": "board_a4-bw.svg",
           "Blink-player-board-blank": "board_blank.svg"}


def wanted(name):
    """The design faces this document actually sets text in."""
    src = HERE / SOURCES.get(name, name + ".html")
    if not src.exists():
        return dict(WANT)
    text = src.read_text(encoding="utf-8", errors="replace")
    # Only what the DOCUMENT asks for, never the @font-face rules embed_fonts.py
    # adds - those name every family whether the page uses it or not.
    text = re.sub(r"<style id=\"embedded-fonts\">.*?</style>", "", text, flags=re.S)
    use = {}
    for face, why in WANT.items():
        if re.search(re.escape(face[:3]) + r"[a-zA-Z ]*", text) and \
           re.search(r"font-family[^;}\n]*" + face[:3], text, re.I):
            use[face] = why
    return use or dict(WANT)

# Only this version. Older rulebooks are kept in the folder on purpose and
# there is nothing to be done about how they were printed.
def current(name):
    other = re.search(r"-v0\.\d+", name)
    return not other or other.group(0) == "-" + VTAG

fails, notes = [], []
pdfs = sorted(ROOT.glob("Blink-*.pdf"))
if not pdfs:
    print("no PDFs found — run build_pdfs.sh first")
    sys.exit(2)

for pdf in pdfs:
    raw = pdf.read_bytes()
    fonts = {m.decode("latin1").split("+")[-1]
             for m in re.findall(rb"/(?:BaseFont|FontName)\s*/([A-Za-z0-9+\-]+)", raw)}
    # /FontName as well as /BaseFont, and the comma: a VARIABLE font is embedded
    # as a CID font whose Type0 /BaseFont is a synthetic name, while the real
    # family only appears in the descriptor's /FontName - and Fraunces arrives
    # as "Fraunces-9ptBlack". Reading /BaseFont alone, this check reported "no
    # Fraunces" about a PDF with Fraunces correctly embedded seven times over,
    # which is the same class of silent failure it was written to catch.
    families = {re.split(r"[-,]", f)[0] for f in fonts}
    if not current(pdf.name):
        continue
    prose = any(pdf.name.startswith(p) for p in CHECKED)
    missing = [w for w in wanted(pdf.stem) if w not in families]
    if prose and missing:
        fails.append(f"{pdf.name}: no {', '.join(missing)} — "
                     f"it embedded {', '.join(sorted(families)) or 'nothing'}")
    elif missing:
        notes.append(f"{pdf.name}: without {', '.join(missing)} "
                     f"({', '.join(sorted(families)) or 'no embedded fonts'})")

for n in notes:
    print("  note: " + n)
if fails:
    print("\n".join("FAIL: " + f for f in fails))
    print("\n  \"it embedded nothing\" is not a font problem: a PDF with no fonts\n"
          "  in it has no TEXT in it. Look for blank pages first - build_pdfs.sh\n"
          "  measures the ink on every page and will say so.\n"
          "\n  Otherwise the fonts did not load. Install them once and every\n"
          "  builder here works offline:\n"
          "    brew install --cask font-fraunces font-ibm-plex-sans font-ibm-plex-mono\n"
          "  then re-run build_pdfs.sh.")
    sys.exit(1)

print(f"fonts: all {len(pdfs)} PDFs carry the faces the design asks for "
      f"({' and '.join(WANT)})")
