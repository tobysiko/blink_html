import json, pathlib, re

OUT = pathlib.Path("/mnt/user-data/outputs/blink-svg")
OUT.mkdir(parents=True, exist_ok=True)

# The figure CSS classes referenced by the SVGs (fills/fonts), inlined so each
# SVG is self-contained and renders correctly outside the HTML rulebook.
STYLE = """<style>
.fig-label{font-family:'IBM Plex Sans',sans-serif;fill:#5A5F59}
.fig-strong{font-family:'IBM Plex Sans',sans-serif;fill:#1C1F1D;font-weight:600}
.fig-step{font-family:'IBM Plex Mono',monospace;fill:#8A837A;letter-spacing:.06em}
.fig-rank{font-family:Fraunces,Georgia,serif;fill:#1C1F1D;font-weight:600}
.fig-attack{font-family:'IBM Plex Sans',sans-serif;fill:#C0392B;font-weight:600}
</style>"""

def finalize(svg):
    # inject the style block right after the opening <svg ...> tag
    svg = re.sub(r'(<svg[^>]*>)', r'\1' + STYLE, svg, count=1)
    # add XML declaration for standalone files
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg

count = 0
for src in ("figs.json", "pattern_figs.json"):
    data = json.load(open(src))
    for name, svg in data.items():
        (OUT / f"{name}.svg").write_text(finalize(svg))
        count += 1

print(f"wrote {count} SVG files to {OUT}")
for f in sorted(OUT.glob("*.svg")):
    print(" ", f.name)
