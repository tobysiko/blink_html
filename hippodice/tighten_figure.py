# Squeezes the empty horizontal bands out of the rulebook's table diagram, so
# the same picture prints wider and shorter on one A4 page.
#
#   python3 tighten_figure.py [gap-min] [gap-keep]      e.g. 7 5
#
# Every element keeps its own size and its x position; only the dead air
# between rows is removed, and the viewBox is re-fitted to what is left.
import re, sys

# The source is the rulebook's first figure — "the table from your seat".
RULEBOOK = '../rulebook.html'
import os
if os.path.exists('table-figure-source.svg'):
    src = open('table-figure-source.svg', encoding='utf-8').read()
else:
    html = open(RULEBOOK, encoding='utf-8').read()
    src = re.search(r'<svg.*?</svg>', html, re.S).group(0)
head_end = src.index('>') + 1
head, inner = src[:head_end], src[head_end:src.rindex('</svg>')]

ELEM = re.compile(r'<text\b[^>]*>.*?</text>|<(?:rect|polygon|ellipse|circle)\b[^>]*/?>', re.S)
def attr(tag, name, d=0.0):
    m = re.search(rf'{name}="([-\d.]+)"', tag)
    return float(m.group(1)) if m else d

def extent(tag):
    """(ymin, ymax, xmin, xmax) for one element."""
    if tag.startswith('<rect'):
        y, h = attr(tag, 'y'), attr(tag, 'height')
        x, w = attr(tag, 'x'), attr(tag, 'width')
        return y, y + h, x, x + w
    if tag.startswith('<circle'):
        cy, cx, r = attr(tag, 'cy'), attr(tag, 'cx'), attr(tag, 'r')
        return cy - r, cy + r, cx - r, cx + r
    if tag.startswith('<ellipse'):
        cy, cx = attr(tag, 'cy'), attr(tag, 'cx')
        ry, rx = attr(tag, 'ry'), attr(tag, 'rx')
        return cy - ry, cy + ry, cx - rx, cx + rx
    if tag.startswith('<polygon'):
        pts = re.search(r'points="([^"]+)"', tag).group(1)
        nums = [float(n) for n in re.findall(r'[-\d.]+', pts)]
        xs, ys = nums[0::2], nums[1::2]
        return min(ys), max(ys), min(xs), max(xs)
    if tag.startswith('<text'):
        y, x = attr(tag, 'y'), attr(tag, 'x')
        fs = attr(tag, 'font-size', 10.0)
        body = re.sub(r'<[^>]+>', '', tag)
        anchor = re.search(r'text-anchor="(\w+)"', tag)
        anchor = anchor.group(1) if anchor else 'start'
        w = len(body) * fs * 0.56
        x0 = x - w / 2 if anchor == 'middle' else (x - w if anchor == 'end' else x)
        return y - fs * 0.85, y + fs * 0.28, x0, x0 + w
    return 0.0, 0.0, 0.0, 0.0

els = [(m.group(0), *extent(m.group(0))) for m in ELEM.finditer(inner)]
print(f'{len(els)} elements')

GAP_MIN  = float(sys.argv[1]) if len(sys.argv) > 1 else 9.0   # gaps bigger than this get cut
GAP_KEEP = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0   # ...down to this

spans = sorted((a, b) for _, a, b, _, _ in els)
merged = []
for a, b in spans:
    if merged and a <= merged[-1][1] + 0.01: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])

cuts = []                       # (gap_start, amount_removed)
for (a1, b1), (a2, b2) in zip(merged, merged[1:]):
    gap = a2 - b1
    if gap > GAP_MIN: cuts.append((b1, gap - GAP_KEEP))
print('vertical gaps closed:', [(round(p), round(d)) for p, d in cuts],
      '=> saves', round(sum(d for _, d in cuts)), 'units')

def shift_for(y):
    return sum(d for p, d in cuts if p < y)

out, xs, ys = [], [], []
for tag, y0, y1, x0, x1 in els:
    dy = shift_for(y0)
    out.append(f'<g transform="translate(0,{-dy:.2f})">{tag}</g>' if dy else tag)
    xs += [x0, x1]; ys += [y0 - dy, y1 - dy]

PAD = 6
vb = (min(xs) - PAD, min(ys) - PAD, max(xs) - min(xs) + 2 * PAD, max(ys) - min(ys) + 2 * PAD)
svg = (f'<svg class="fig" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}"'
       f' xmlns="http://www.w3.org/2000/svg" role="img">' + ''.join(out) + '</svg>')
open('table-figure.svg', 'w', encoding='utf-8').write(svg)
old = re.search(r'viewBox="([^"]+)"', head).group(1).split()
print(f'aspect  before {float(old[2])/float(old[3]):.2f}   after {vb[2]/vb[3]:.2f}')
print(f'viewBox before {" ".join(old)}   after {vb[0]:.0f} {vb[1]:.0f} {vb[2]:.0f} {vb[3]:.0f}')
