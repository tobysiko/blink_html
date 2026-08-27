# -*- coding: utf-8 -*-
"""The one place the version number lives.

Every builder imports from here, so a version bump is a single edit and cannot
leave a document, a filename or a printed component behind. Before this existed
the string was written out by hand in nine places, and the objectives module was
still footing itself "v0.2".

Bumping: edit the VERSION file at the top of the project, run
source/build_pdfs.sh and node app/build.js, done. The rules HTML and PDF rename
themselves.

The number itself lives in a plain text file rather than here, because the
JavaScript build needs it too and a Python constant is not readable from
node. Two copies of a version number is one copy too many: v0.24 was found
half-applied across nine files before this existed.
"""
import pathlib

VERSION = (pathlib.Path(__file__).resolve().parent.parent / "VERSION"
           ).read_text(encoding="utf8").strip()
VTAG = f"v{VERSION}"

# Output names that carry the version. Everything else is version-stable, so a
# bump does not churn filenames that people may have linked to.
RULES_HTML = f"Blink-rules-{VTAG}.html"
RULES_PDF = f"Blink-rules-{VTAG}.pdf"
RULES_HTML_BW = f"Blink-rules-{VTAG}-bw.html"
RULES_PDF_BW = f"Blink-rules-{VTAG}-bw.pdf"
