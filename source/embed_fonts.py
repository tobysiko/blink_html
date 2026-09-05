# -*- coding: utf-8 -*-
"""Put the typefaces INSIDE the document, so a PDF cannot come out wrong.

Every builder here pulls Fraunces and IBM Plex from Google Fonts with a <link>,
which makes the typography of a printed rulebook depend on a network fetch
succeeding at the moment the PDF is rendered. When it does not, nothing breaks
loudly: the browser falls back to a system serif, writes a valid PDF, and every
other check passes. check_fonts.py exists because that happened.

It happened again, and worse: on 4 Sep 2026 EVERY shipped PDF was checked and
none of them had Fraunces or IBM Plex Sans in it. The rulebook bound for the
Hippodice entry was set in DejaVu Sans and Liberation Serif.

So the fetch is removed rather than retried. This rewrites a built HTML file
into a print copy with the font files inlined as base64 @font-face rules and
the Google <link> tags stripped. The print copy is what gets rendered; the
web HTML keeps the CDN link, because a 500 KB page is the wrong trade online
and the browser there has a network.

    python3 embed_fonts.py Blink-rules-v0.24.html /tmp/print-rules.html

The woff2 files live in source/fonts/ and are the Google Fonts originals, taken
from the @fontsource npm packages. Fraunces is the full variable font: the
rulebook sets "SOFT" and "WONK" axes, so a static instance will not do.
"""
import base64
import pathlib
import re
import sys

FONTS = pathlib.Path(__file__).resolve().parent / "fonts"


def _b64(name):
    return base64.b64encode((FONTS / name).read_bytes()).decode()


def faces():
    out = []
    for style, f in (("normal", "fraunces-latin-full-normal.woff2"),
                     ("italic", "fraunces-latin-full-italic.woff2")):
        out.append("@font-face{font-family:'Fraunces';font-style:%s;"
                   "font-weight:100 900;src:url(data:font/woff2;base64,%s) "
                   "format('woff2');}" % (style, _b64(f)))
    for fam, key, weights in (("IBM Plex Sans", "ibm-plex-sans", (400, 500, 600)),
                              ("IBM Plex Mono", "ibm-plex-mono", (400, 500))):
        for w in weights:
            out.append("@font-face{font-family:'%s';font-style:normal;"
                       "font-weight:%d;src:url(data:font/woff2;base64,%s) "
                       "format('woff2');}"
                       % (fam, w, _b64("%s-latin-%d-normal.woff2" % (key, w))))
    return out


# THE PRINT COPY DOES NOT ANIMATE. Chrome's `--print-to-pdf` snapshots the page
# the instant it loads, before any animation has advanced a frame, so an
# entrance animation that starts at opacity:0 prints as a blank page - the
# right number of them, correctly paginated, with no text on any of them. That
# is what happened to every document built from build_html.py's stylesheet on
# 5 Sep 2026. The stylesheet is fixed at source; this is here because this file
# is the last thing to touch a document before it is printed, and a rule like
# that must not be able to reach paper again.
PRINT_SAFE = ("@media print{*,*::before,*::after{animation:none!important;"
              "transition:none!important}}")


def convert(src, dst):
    html = pathlib.Path(src).read_text(encoding="utf-8")
    n = len(re.findall(r"<link[^>]*fonts\.g[^>]*>", html))
    html = re.sub(r"<link[^>]*fonts\.g[^>]*>\s*", "", html)
    if "</head>" not in html:
        raise SystemExit("embed_fonts: no </head> in " + src)
    style = ('<style id="embedded-fonts">' + "".join(faces()) + PRINT_SAFE
             + "</style>")
    html = html.replace("</head>", style + "</head>", 1)
    pathlib.Path(dst).write_text(html, encoding="utf-8")
    return n


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: embed_fonts.py <built.html> <print.html>")
    dropped = convert(sys.argv[1], sys.argv[2])
    print("embed_fonts: %s -> %s (%d CDN links removed, 7 faces inlined)"
          % (pathlib.Path(sys.argv[1]).name, pathlib.Path(sys.argv[2]).name, dropped))
