# -*- coding: utf-8 -*-
"""The one place the version number lives.

Every builder imports from here, so a version bump is a single edit and cannot
leave a document, a filename or a printed component behind. Before this existed
the string was written out by hand in nine places, and the objectives module was
still footing itself "v0.2".

Bumping: change VERSION, run source/build_pdfs.sh, done. The rules HTML and PDF
rename themselves.
"""

VERSION = "0.23"
VTAG = f"v{VERSION}"

# Output names that carry the version. Everything else is version-stable, so a
# bump does not churn filenames that people may have linked to.
RULES_HTML = f"Blink-rules-{VTAG}.html"
RULES_PDF = f"Blink-rules-{VTAG}.pdf"
RULES_HTML_BW = f"Blink-rules-{VTAG}-bw.html"
RULES_PDF_BW = f"Blink-rules-{VTAG}-bw.pdf"
