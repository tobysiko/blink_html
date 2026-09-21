# -*- coding: utf-8 -*-
"""Write font_metrics.json from the woff2 faces in source/fonts/.

WHY THIS EXISTS. build_aid_visual.py had no text engine, so every wrapped
line and every heading was sized by a GUESSED per-character width table. It
was right to within a few per cent on average and wrong per character - "W"
is 0.891 em and the guess said 0.72, "i" is 0.25 and the guess said 0.28 -
so a capital-heavy or w-heavy string overran its box while the estimate said
it fitted. That produced text outside nine boxes on the first build of the
sheet, headings printed over their own subtitles on the second, and a word
touching the border somewhere on every build since.

The faces are already in the repository - they have to be, because the PDFs
embed them - so the exact advance widths are right there. This reads them
once and writes a table; nothing at build time needs fontTools.

Re-run it only when a font file changes:

    pip install fonttools brotli
    python3 gen_metrics.py

Weight 700 is deliberately NOT a separate entry: only 400, 500 and 600 exist
as files, so a renderer asked for 700 uses the 600 face. Mapping 700 to 600
is what actually happens on the page.
"""
import json
import pathlib

from fontTools.ttLib import TTFont

HERE = pathlib.Path(__file__).resolve().parent
SRC = {
    "sans400": "ibm-plex-sans-latin-400-normal.woff2",
    "sans600": "ibm-plex-sans-latin-600-normal.woff2",
    "mono400": "ibm-plex-mono-latin-400-normal.woff2",
}


def main():
    out = {}
    for key, fn in SRC.items():
        path = HERE / "fonts" / fn
        f = TTFont(path)
        upem = f["head"].unitsPerEm
        cmap = f.getBestCmap()
        metrics = f["hmtx"].metrics
        tbl = {}
        for cp, g in cmap.items():
            if 0x20 <= cp <= 0x2122 and g in metrics:
                tbl[chr(cp)] = round(metrics[g][0] / upem, 4)
        vals = sorted(tbl.values())
        out[key] = {"w": tbl, "default": vals[len(vals) // 2]}
        print(f"  {key}: {len(tbl)} glyphs from {fn}")
    dest = HERE / "font_metrics.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"),
                               sort_keys=True), encoding="utf8")
    print(f"  wrote {dest.name} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
