# -*- coding: utf-8 -*-
"""Wrap a standalone SVG in a minimal HTML page sized to the SVG itself.

The player boards are SVG and used to be converted with cairosvg, which needs
the native Cairo library underneath it — a dependency that is fiddly on macOS
and was not installed, so the boards were the one thing build_pdfs.sh could not
produce. Every other document already goes through a browser, and a browser
renders SVG as vector into a PDF perfectly well, so this removes the extra
toolchain rather than asking anyone to install it.

The whole job is page geometry. An SVG opened on its own gets whatever page the
renderer defaults to (A4 portrait), and a 297x210mm landscape board would be
scaled down and centred on it with white margins. Declaring `@page` at the
SVG's own size, with no margin, makes the page BE the board.

    python3 wrap_svg.py board_a4.svg _tmp.html

SEVERAL SVGs MAKE SEVERAL PAGES. Pass more than one and each becomes its own
page in one document, which is what a two-sided player aid has to be: two PDFs
do not print back to back without the person at the printer getting it right,
and a sheet whose back is a separate file is a sheet whose back goes missing.
Every SVG must share the first one's page size, because `@page` is declared
once for the document; mixing sizes is refused rather than silently scaled.

    python3 wrap_svg.py front.svg back.svg _tmp.html
"""
import pathlib
import re
import sys


def _one(svg_path):
    """Returns (width, height, inlined svg) for one file."""
    svg = pathlib.Path(svg_path).read_text(encoding="utf8")
    open_tag = re.search(r"<svg[^>]*>", svg)
    if not open_tag:
        raise SystemExit(f"{svg_path}: no <svg> element found")
    attrs = open_tag.group(0)

    w = re.search(r'\bwidth="([^"]+)"', attrs)
    h = re.search(r'\bheight="([^"]+)"', attrs)
    if not (w and h):
        raise SystemExit(f"{svg_path}: the <svg> has no width/height to size a page with")

    # Strip the XML prolog: it is only valid at the very start of a document,
    # and this SVG is about to be inlined into the middle of one.
    return w.group(1), h.group(1), re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", svg)


def wrap(*svg_paths):
    if not svg_paths:
        raise SystemExit("wrap_svg: nothing to wrap")
    pages = [_one(q) for q in svg_paths]
    width, height, _ = pages[0]
    for q, (pw, ph, _) in zip(svg_paths[1:], pages[1:]):
        if (pw, ph) != (width, height):
            raise SystemExit(
                f"{q}: {pw}x{ph} does not match {svg_paths[0]}'s {width}x{height} "
                "- one document has one page size")
    # Each SVG in its own block, page-broken between them. The LAST one must
    # not force a break or the document ends with a blank page, which prints
    # and is thrown away.
    body = "\n".join(
        f'<div class="pg">{svg}</div>' for _, _, svg in pages)
    svg_path = svg_paths[0]

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>{pathlib.Path(svg_path).stem}</title>
<style>
  /* The page IS the board: same size, no margin, nothing to centre it in. */
  @page {{ size: {width} {height}; margin: 0; }}
  html, body {{ margin: 0; padding: 0; }}
  svg {{ display: block; width: {width}; height: {height}; }}
  .pg {{ break-after: page; page-break-after: always; }}
  .pg:last-child {{ break-after: auto; page-break-after: auto; }}
  /* Board colours are the point of the board, so keep them when printing. */
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
</style>
</head><body>
{body}
</body></html>
"""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: wrap_svg.py <in.svg> [more.svg ...] <out.html>")
    *ins, out = sys.argv[1:]
    pathlib.Path(out).write_text(wrap(*ins), encoding="utf8")
