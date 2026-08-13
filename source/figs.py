import math

R = 26.0
SQ = math.sqrt(3) * R / 2.0     # 22.517
DX = math.sqrt(3) * R           # horizontal step
DY = 1.5 * R                    # vertical step

TER = {
    "plains":   {"top": "#D2A93A", "side": "#9B7A16", "h": 5,  "glyph": ""},
    "forest":   {"top": "#37704A", "side": "#1E4229", "h": 13, "glyph": ""},
    "ocean":    {"top": "#256A8C", "side": "#123D53", "h": 5,  "glyph": ""},
    "mountain": {"top": "#8A837A", "side": "#5A544C", "h": 21, "glyph": ""},
}

PLAYER = {
    "you":   {"fill": "#C0392B", "edge": "#7B2018"},
    "rival": {"fill": "#EDEAE1", "edge": "#5A544C"},
    "third": {"fill": "#3B3F8F", "edge": "#232659"},
}


def axial(col, row):
    """Pointy-top offset grid -> pixel centre."""
    x = col * DX + (DX / 2 if row % 2 else 0)
    y = row * DY
    return x, y


def hex_pts(cx, cy):
    return [(cx, cy - R), (cx + SQ, cy - R / 2), (cx + SQ, cy + R / 2),
            (cx, cy + R), (cx - SQ, cy + R / 2), (cx - SQ, cy - R / 2)]


def pstr(pts):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def prism(cx, cy, terrain, empty=False, dashed=False):
    """Extruded hex: side walls then top face. cy is the TOP face centre."""
    if empty:
        pts = hex_pts(cx, cy)
        style = 'fill="none" stroke="#B4AFA3" stroke-width="1.6"'
        if dashed:
            style += ' stroke-dasharray="5 4"'
        return f'<polygon points="{pstr(pts)}" {style}/>'
    t = TER[terrain]
    h = t["h"]
    top = hex_pts(cx, cy)
    # side wall: lower three edges of the top face, extruded down by h
    wall = [top[1], top[2], top[3], top[4],
            (top[4][0], top[4][1] + h), (top[3][0], top[3][1] + h),
            (top[2][0], top[2][1] + h), (top[1][0], top[1][1] + h)]
    out = f'<polygon points="{pstr(wall)}" fill="{t["side"]}"/>'
    out += f'<polygon points="{pstr(top)}" fill="{t["top"]}" stroke="{t["side"]}" stroke-width="1.2"/>'
    return out


def unit(cx, cy, who="you", n=1):
    """n stacked discs sitting on a top face centred at cx,cy."""
    p = PLAYER[who]
    out = ""
    for i in range(n):
        oy = cy - i * 7.0 + 3
        out += (f'<ellipse cx="{cx:.2f}" cy="{oy+3:.2f}" rx="11" ry="5.5" fill="{p["edge"]}"/>'
                f'<ellipse cx="{cx:.2f}" cy="{oy:.2f}" rx="11" ry="5.5" fill="{p["fill"]}" '
                f'stroke="{p["edge"]}" stroke-width="1.2"/>')
    return out


def gold(cx, cy):
    return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="7.5" fill="#E8C25A" stroke="#9B7A16" stroke-width="1.4"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="3.6" fill="none" stroke="#9B7A16" stroke-width="1"/>')


def label(x, y, text, size=11, anchor="middle", cls="fig-label"):
    return f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" class="{cls}" font-size="{size}">{text}</text>'


def card(x, y, rank, suit, w=44, h=62, faded=False):
    """A small playing card. suit in plains/forest/ocean/mountain."""
    c = TER[suit]["top"]
    op = ' opacity="0.35"' if faded else ""
    out = f'<g{op}>'
    out += (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#FBFAF6" '
            f'stroke="#2A2E2B" stroke-width="1.4"/>')
    out += f'<rect x="{x}" y="{y}" width="{w}" height="9" rx="4" fill="{c}"/>'
    out += f'<rect x="{x}" y="{y+5}" width="{w}" height="4" fill="{c}"/>'
    out += (f'<text x="{x+w/2:.1f}" y="{y+h/2+11:.1f}" text-anchor="middle" '
            f'class="fig-rank" font-size="26">{rank}</text>')
    out += f'<circle cx="{x+w/2:.1f}" cy="{y+h-13:.1f}" r="5" fill="{c}"/>'
    out += '</g>'
    return out


import re as _re


def _path_points(d):
    """Points touched by a path. Handles the commands these figures use —
    M (absolute move/line), l (relative line), C (absolute cubic) — tracking the
    current point so relative offsets are never mistaken for coordinates."""
    toks = _re.findall(r'[MmLlCcHhVvZz]|-?[\d.]+', d)
    pts = []
    cx = cy = 0.0
    cmd = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if _re.match(r'[A-Za-z]', t):
            cmd = t
            i += 1
            if cmd in "Zz":
                cmd = None
            continue
        if cmd is None:
            i += 1
            continue
        n = {"M": 2, "L": 2, "m": 2, "l": 2, "C": 6, "c": 6,
             "H": 1, "h": 1, "V": 1, "v": 1}.get(cmd, 2)
        try:
            vals = [float(v) for v in toks[i:i + n]]
        except ValueError:
            break
        if len(vals) < n:
            break
        i += n
        if cmd in "MLC":
            if cmd == "C":
                for j in range(0, 6, 2):
                    pts.append((vals[j], vals[j + 1]))
                cx, cy = vals[4], vals[5]
            else:
                cx, cy = vals[0], vals[1]
                pts.append((cx, cy))
        elif cmd in "mlc":
            if cmd == "c":
                for j in range(0, 6, 2):
                    pts.append((cx + vals[j], cy + vals[j + 1]))
                cx, cy = cx + vals[4], cy + vals[5]
            else:
                cx, cy = cx + vals[0], cy + vals[1]
                pts.append((cx, cy))
        elif cmd == "H":
            cx = vals[0]; pts.append((cx, cy))
        elif cmd == "h":
            cx += vals[0]; pts.append((cx, cy))
        elif cmd == "V":
            cy = vals[0]; pts.append((cx, cy))
        elif cmd == "v":
            cy += vals[0]; pts.append((cx, cy))
        # after an explicit M, repeated pairs are implicit L
        if cmd == "M":
            cmd = "L"
        elif cmd == "m":
            cmd = "l"
    return pts


def _segments(body):
    """Split body into (fragment, dx, dy), honouring nested
    <g transform="translate(dx,dy)"> groups. Without this, anything drawn
    inside a translated group is invisible to the bounds calculation and the
    figure gets clipped."""
    out = []
    stack = [(0.0, 0.0)]
    pos = 0
    for m in _re.finditer(r'<g\b[^>]*>|</g>', body):
        if m.start() > pos:
            out.append((body[pos:m.start()],) + stack[-1])
        if m.group(0) == "</g>":
            if len(stack) > 1:
                stack.pop()
        else:
            dx, dy = stack[-1]
            t = _re.search(r'translate\(\s*(-?[\d.]+)\s*[, ]\s*(-?[\d.]+)\s*\)',
                           m.group(0))
            if t:
                dx += float(t.group(1))
                dy += float(t.group(2))
            stack.append((dx, dy))
        pos = m.end()
    if pos < len(body):
        out.append((body[pos:],) + stack[-1])
    return out


def _collect(frag, dx, dy, xs, ys):
    for m in _re.finditer(r'\b(cx|x|x1|x2)="(-?[\d.]+)"', frag):
        xs.append(float(m.group(2)) + dx)
    for m in _re.finditer(r'\b(cy|y|y1|y2)="(-?[\d.]+)"', frag):
        ys.append(float(m.group(2)) + dy)
    for m in _re.finditer(r'<rect x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"', frag):
        x, y, w, h = map(float, m.groups())
        xs += [x + dx, x + w + dx]
        ys += [y + dy, y + h + dy]
    for m in _re.finditer(r'points="([^"]+)"', frag):
        nums = [float(n) for n in _re.findall(r'-?[\d.]+', m.group(1))]
        xs += [n + dx for n in nums[0::2]]
        ys += [n + dy for n in nums[1::2]]
    for m in _re.finditer(r'\bd="([^"]+)"', frag):
        for px, py in _path_points(m.group(1)):
            xs.append(px + dx)
            ys.append(py + dy)
    for m in _re.finditer(r'<text x="(-?[\d.]+)" y="(-?[\d.]+)"[^>]*text-anchor="(\w+)"[^>]*font-size="([\d.]+)"[^>]*>([^<]*)</text>', frag):
        x, y = float(m.group(1)) + dx, float(m.group(2)) + dy
        anc, fs, txt = m.group(3), float(m.group(4)), m.group(5)
        w = len(txt) * fs * 0.62
        if anc == "middle":
            xs += [x - w / 2, x + w / 2]
        elif anc == "end":
            xs += [x - w, x]
        else:
            xs += [x, x + w]
        ys += [y - fs, y + fs * 0.35]


def fig_bounds(body):
    """True (minx, miny, maxx, maxy) of everything drawn in body."""
    xs, ys = [], []
    for frag, dx, dy in _segments(body):
        _collect(frag, dx, dy, xs, ys)
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _fit_viewbox(body, pad=14):
    bb = fig_bounds(body)
    if bb is None:
        return "0 0 240 210"
    minx, miny, maxx, maxy = bb
    minx -= pad; miny -= pad; maxx += pad; maxy += pad
    return f"{minx:.0f} {miny:.0f} {maxx - minx:.0f} {maxy - miny:.0f}"


def svg(w, h, body, vb=None):
    if vb == "auto" or vb is None:
        vb = _fit_viewbox(body)
    return (f'<svg class="fig" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img">{body}</svg>')
