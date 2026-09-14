# -*- coding: utf-8 -*-
"""Blink civ-ladder skin — the tech illustrations.

Every drawing is line art on a 48x48 field: one stroke weight, round caps and
joins, no interior shading. Colour comes from the card, not from the drawing,
so a single set of paths serves the colour deck and the b/w deck — which is
also why a drawing has to work as a silhouette before it works at all.

Conventions that keep eighty drawings looking like one deck:

  * the subject occupies roughly x 4..44, y 5..42, centred on x 24
  * a building or an object sits on a ground line near y 40
  * an ocean card sits on the wave line instead
  * solid fills are reserved for tiny accents (fill="currentColor")
  * nothing is drawn smaller than about 3 units, because 48 units is 20 mm on
    the printed card and a 3-unit gap is a millimetre and a quarter
"""

TECH = {}


def _add(suit, rank, name, *parts):
    TECH[f"{suit}-{rank}"] = "".join(parts)


GROUND = '<path d="M4 42h40"/>'
WAVES = '<path d="M3 42q4.5-3.2 9 0t9 0 9 0 9 0"/>'

# ============ PLAINS · settlement, farming, law, governance ================

_add("plains", 1, "Hearth",
     '<path d="M25 5C24 11 27 12 29 15C31.5 18.5 32 21.5 32 24A10 10 0 0 1 12 24'
     'C12 20 14 17 17 14.5C17.5 17 19 17.5 20 18C18 13 19 8 25 5Z"/>',
     '<path d="M24 21c2.4 3.4 3.6 5 3.6 7a3.8 3.8 0 0 1-7.6 0c0-2 1.6-3.6 4-7Z"/>',
     '<path d="M8 38.5q3-4.6 6 0t6 0 6 0 6 0 6 0"/>',
     '<path d="M4 42.5h40"/>')

_add("plains", 2, "Hamlet",
     '<path d="M6 39V28h12v11"/>',
     '<path d="M3 28.5L12 20l9 8.5"/>',
     '<path d="M26 39V25h13v14"/>',
     '<path d="M23 25.5L32.5 17l9.5 8.5"/>',
     '<path d="M30 39v-6h5v6"/>',
     GROUND)

_add("plains", 3, "Granary",
     '<path d="M11 33V20h26v13"/>',
     '<path d="M8 20.5L24 11l16 9.5"/>',
     '<path d="M14 33v8M20 33v8M28 33v8M34 33v8"/>',
     '<path d="M24 15v9"/>',
     '<path d="M21.5 17q2.5.6 2.5 3M26.5 17q-2.5.6-2.5 3'
     'M21.5 20.5q2.5.6 2.5 3M26.5 20.5q-2.5.6-2.5 3"/>',
     '<path d="M4 41h40"/>')

_add("plains", 4, "Village",
     '<path d="M7 38V29l6-5 6 5v9"/>',
     '<path d="M20 38V26l7-6 7 6v12"/>',
     '<path d="M24 38v-6h6v6"/>',
     '<path d="M35 38v-8l5-4 5 4v8"/>',
     '<path d="M3 38h42"/>')

_add("plains", 5, "Elders' Council",
     '<circle cx="11" cy="20" r="3.2"/>',
     '<path d="M11 23.6c-4 0-6.2 3-6.7 8.4h13.4c-.5-5.4-2.7-8.4-6.7-8.4Z"/>',
     '<circle cx="24" cy="15" r="3.2"/>',
     '<path d="M24 18.6c-4 0-6.2 3-6.7 8.4h13.4c-.5-5.4-2.7-8.4-6.7-8.4Z"/>',
     '<circle cx="37" cy="20" r="3.2"/>',
     '<path d="M37 23.6c-4 0-6.2 3-6.7 8.4h13.4c-.5-5.4-2.7-8.4-6.7-8.4Z"/>',
     '<path d="M17.3 27h13.4v5H17.3z"/>',
     '<path d="M3 37h42"/>')

_add("plains", 8, "Marketplace",
     '<path d="M7 18h34"/>',
     '<path d="M7 18q4.25 6 8.5 0t8.5 0 8.5 0 8.5 0"/>',
     '<path d="M9 24v16M39 24v16"/>',
     '<path d="M13 32h22M16 32v8M32 32v8"/>',
     '<circle cx="20" cy="28.6" r="2.6"/><circle cx="28" cy="28.6" r="2.6"/>')

_add("plains", 12, "Guildhall",
     '<path d="M9 40V23l13-9 13 9v17"/>',
     '<path d="M18 40v-9a4 4 0 0 1 8 0v9"/>',
     '<path d="M12.5 25h4.5v4.5h-4.5z"/><path d="M27 25h4.5v4.5H27z"/>',
     '<path d="M35 27h7M41.5 27v4"/><path d="M38 31h7v5h-7z"/>',
     '<path d="M5 40h40"/>')

_add("plains", 18, "Parliament",
     '<path d="M24 8v3"/>',
     '<path d="M14 25a10 10 0 0 1 20 0"/>',
     '<path d="M10 25h28"/>',
     '<path d="M13 27.5v9M19 27.5v9M29 27.5v9M35 27.5v9"/>',
     '<path d="M22 27.5v9M26 27.5v9" opacity=".45"/>',
     '<path d="M9 36.5h30M6 40.5h36"/>')

# ============ FOREST · tools, machines, knowledge, science =================

_add("forest", 1, "Firemaking",
     '<path d="M6 14l4-6 9-1 3 6-2 7-8 2z"/>',
     '<path d="M27 13l5-6 9 1 3 7-4 6-9 1z"/>',
     '<path d="M22 20l2 3M28 21l-3 2"/>',
     '<path d="M24 25v3.5M19.5 25l-2.5 3M29 25.5l2.5 3"/>',
     '<path d="M11 38q13-9 26 0"/><path d="M11 38q13 6 26 0"/>',
     '<path d="M16 37q3.5-3 7 0M25 37q3.5-3 7 0"/>')

_add("forest", 2, "Stone Tools",
     '<path d="M20 16h5v26h-5z"/>',
     '<path d="M25 11c7-1 12 2 15 7-5 4-10 6-15 5z"/>',
     '<path d="M27 15q4 3 4 6"/>',
     '<path d="M19 14.5l7 3.5M19 21l7-3.5"/>',
     '<path d="M5 40l6.5-3.4 2.2 4.6z"/>')

_add("forest", 3, "Cordage",
     '<path d="M5 18q3.8-5.5 7.6 0t7.6 0 7.6 0 7.6 0 7.6 0"/>',
     '<path d="M5 18q3.8 5.5 7.6 0t7.6 0 7.6 0 7.6 0 7.6 0"/>',
     '<ellipse cx="24" cy="33" rx="13.5" ry="6.2"/>',
     '<ellipse cx="24" cy="33" rx="7" ry="3"/>')

_add("forest", 4, "The Wheel",
     '<circle cx="24" cy="23" r="13"/>',
     '<circle cx="24" cy="23" r="3.4"/>',
     '<path d="M24 10v26M11 23h26"/>',
     '<path d="M5 39h38"/>')

_add("forest", 5, "Carpentry",
     '<path d="M6 15h26v7H6z"/>',
     '<path d="M6 22l1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5'
     ' 1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5'
     ' 1 2.5 1-2.5 1 2.5 1-2.5 1 2.5 1-2.5"/>',
     '<path d="M32 11.5h5a6.5 6.5 0 0 1 0 13h-5z"/>',
     '<path d="M35.5 15a3.2 3.2 0 0 1 0 6"/>',
     '<path d="M4 33h40v7H4z"/><path d="M4 36.5h40"/>')

_add("forest", 8, "Block and Tackle",
     '<path d="M8 8h32"/>',
     '<path d="M20 8v5M28 8v5"/>',
     '<circle cx="24" cy="17" r="4.2"/>',
     '<path d="M20 18.5v8M28 18.5v8"/>',
     '<circle cx="24" cy="30" r="4.2"/>',
     '<path d="M18 34.5h12v7H18z"/>')

_add("forest", 12, "The Lens",
     '<path d="M24 9q9 15 0 30 -9-15 0-30Z"/>',
     '<path d="M4 15h11M4 24h11M4 33h11"/>',
     '<path d="M31 19.5l11 4.5M32 24h10M31 28.5l11-4.5"/>',
     '<circle cx="43" cy="24" r="1.7" fill="currentColor" stroke="none"/>')

_add("forest", 18, "Electricity",
     '<path d="M16 21a8 8 0 1 1 16 0c0 4.4-2.8 6-2.8 9h-10.4c0-3-2.8-4.6-2.8-9Z"/>',
     '<path d="M19 33.5h10M20.5 37.5h7"/>',
     '<path d="M26 13.5l-4.5 7.5h5l-3.5 7"/>',
     '<path d="M7 21h4M37 21h4M11 10l3 3M37 13l3-3"/>')

# ============ OCEAN · seafaring, trade, frontier ===========================

_add("ocean", 1, "The Raft",
     '<ellipse cx="10" cy="30" rx="3.5" ry="4"/><ellipse cx="17" cy="30" rx="3.5" ry="4"/>',
     '<ellipse cx="24" cy="30" rx="3.5" ry="4"/><ellipse cx="31" cy="30" rx="3.5" ry="4"/>',
     '<ellipse cx="38" cy="30" rx="3.5" ry="4"/>',
     '<path d="M7 27.5h34M7 32.5h34"/>',
     '<path d="M14 27L33 7"/>',
     '<path d="M3 40q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 2, "Fishing Net",
     '<path d="M7 13h34"/>',
     '<circle cx="14" cy="13" r="2.1"/><circle cx="24" cy="13" r="2.1"/>',
     '<circle cx="34" cy="13" r="2.1"/>',
     '<path d="M10 20L28 38M19 20L37 38M28 20L38 30M10 29L19 38"/>',
     '<path d="M38 20L20 38M29 20L11 38M20 20L10 30M38 29L29 38"/>',
     '<circle cx="16" cy="41" r="1.5" fill="currentColor" stroke="none"/>',
     '<circle cx="24" cy="42" r="1.5" fill="currentColor" stroke="none"/>',
     '<circle cx="32" cy="41" r="1.5" fill="currentColor" stroke="none"/>')

_add("ocean", 3, "Dugout Canoe",
     '<path d="M6 25q18 13 36 0"/>',
     '<path d="M6 25q18-7 36 0"/>',
     '<path d="M11.5 25.8q12.5 5.6 25 0"/>',
     '<path d="M17 27.6v4.4M24 28.8v4.6M31 27.6v4.4"/>',
     '<path d="M3 40q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 4, "The Oar",
     '<ellipse cx="35" cy="12" rx="4.4" ry="7.4" transform="rotate(38 35 12)"/>',
     '<path d="M31.5 16.5L13 39"/>',
     '<path d="M10.5 40.5l4.5-3.6"/>',
     '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 5, "Barter",
     '<path d="M7 40q-2.5-11 3.5-14h8q6 3 3.5 14z"/>',
     '<path d="M9.5 26.5l2-4.5h6.5l2 4.5"/>',
     '<path d="M31 40q-4-9 1-13h8q5 4 1 13z"/>',
     '<path d="M31.6 27h8.8"/><path d="M34 27v-4h3v4"/><path d="M32.4 23h6.2"/>',
     '<path d="M12 18q12-11 24 0"/>',
     '<path d="M12 18l-.8-4.6M12 18l4.6 1.2"/>',
     '<path d="M36 18l.8-4.6M36 18l-4.6 1.2"/>')

_add("ocean", 8, "Coinage",
     '<circle cx="18" cy="24" r="12"/><circle cx="18" cy="24" r="7.5"/>',
     '<circle cx="18" cy="24" r="2.2" fill="currentColor" stroke="none"/>',
     '<ellipse cx="37" cy="31" rx="7" ry="2.6"/>',
     '<ellipse cx="37" cy="25" rx="7" ry="2.6"/>',
     '<path d="M30 25v6M44 25v6"/>')

_add("ocean", 12, "Lighthouse",
     '<path d="M18 39L21 16h6l3 23Z"/>',
     '<path d="M19.4 29h9.2M20.2 22.5h7.6"/>',
     '<path d="M19.5 16h9"/>',
     '<path d="M20 16v-5h8v5"/><path d="M19 11l5-4.5 5 4.5"/>',
     '<path d="M17.5 8L7 4M17 13.5L5 12M30.5 8L41 4M31 13.5l12-1.5"/>',
     '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 18, "Steamship",
     '<path d="M6 29h36l-4.5 9H10.5z"/>',
     '<path d="M15 29v-5h13v5"/>',
     '<path d="M20 24v-9h5.5v9"/>',
     '<path d="M22 12.5q0-3 3-3.5t3-3.5"/><path d="M28.5 11q2-2.5 5-2.5"/>',
     '<path d="M34 29V13"/><path d="M30.5 17h7"/>',
     '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>')

# ============ MOUNTAIN · metal, engineering, defence =======================

_add("mountain", 1, "The Sling",
     '<circle cx="12" cy="9" r="2.8"/>',
     '<path d="M13 11.8q-2 12 4 16.2"/>',
     '<path d="M31 7h7v5h-7z"/>',
     '<path d="M34 12q2 12-4 16"/>',
     '<path d="M13 28h22"/>',
     '<path d="M13 28q11 13 22 0"/>',
     '<circle cx="24" cy="31.5" r="4.2"/>',
     '<circle cx="10" cy="41" r="2.8"/><circle cx="16.5" cy="43" r="2"/>')

_add("mountain", 2, "Copper",
     '<path d="M6 40l-2.5-8 5-7 9-1.5 7 5-1 9-7.5 4z"/>',
     '<path d="M9 24l4 7.5 8-1M13 31.5l-2 8.5M21 30.5l3.5 5"/>',
     '<path d="M22 9l11 2.5-2.5 10.5-11-2.5z"/>',
     '<path d="M32.5 13l12 2.5"/>',
     '<path d="M19 23l1-3M24.5 24l1-3"/>')

_add("mountain", 3, "Bronze",
     '<path d="M16 23h16l3 7H13z"/>',
     '<path d="M5 31h16l3 7H2z"/>',
     '<path d="M27 31h16l3 7H24z"/>',
     '<path d="M18.5 26.5h11M7.5 34.5h11M29.5 34.5h11"/>')

_add("mountain", 4, "Palisade",
     '<path d="M6 39V21l3-5 3 5v18"/>',
     '<path d="M15 39V21l3-5 3 5v18"/>',
     '<path d="M27 39V21l3-5 3 5v18"/>',
     '<path d="M36 39V21l3-5 3 5v18"/>',
     '<path d="M4 25h40M4 33h40"/>')

_add("mountain", 5, "The Shield",
     '<circle cx="24" cy="24" r="16.5"/>',
     '<circle cx="24" cy="24" r="13"/>',
     '<circle cx="24" cy="24" r="4.8"/>',
     '<circle cx="24" cy="9.3" r="1.4" fill="currentColor" stroke="none"/>',
     '<circle cx="34.4" cy="13.6" r="1.4" fill="currentColor" stroke="none"/>',
     '<circle cx="38.7" cy="24" r="1.4" fill="currentColor" stroke="none"/>',
     '<circle cx="34.4" cy="34.4" r="1.4" fill="currentColor" stroke="none"/>',
     '<circle cx="24" cy="38.7" r="1.4" fill="currentColor" stroke="none"/>',
     '<circle cx="13.6" cy="34.4" r="1.4" fill="currentColor" stroke="none"/>',
     '<circle cx="9.3" cy="24" r="1.4" fill="currentColor" stroke="none"/>',
     '<circle cx="13.6" cy="13.6" r="1.4" fill="currentColor" stroke="none"/>')

_add("mountain", 8, "Stonemasonry",
     '<path d="M7 12h34v28H7z"/>',
     '<path d="M7 21.3h34M7 30.6h34"/>',
     '<path d="M19 12v9.3M31 12v9.3"/>',
     '<path d="M13 21.3v9.3M25 21.3v9.3M37 21.3v9.3"/>',
     '<path d="M19 30.6v9.4M31 30.6v9.4"/>')

_add("mountain", 12, "Crossbow",
     '<path d="M8 21h30v6H8z"/>',
     '<path d="M38 11q7 13 0 26"/>',
     '<path d="M38 11L22 24l16 13"/>',
     '<path d="M22 24h18"/><path d="M40 21.5L45 24l-5 2.5z" fill="currentColor"/>',
     '<path d="M14 27v5"/>')

_add("mountain", 18, "Blast Furnace",
     '<path d="M15 40V19l4-8h10l4 8v21Z"/>',
     '<path d="M15 26h18M15 33h18"/>',
     '<path d="M20 40v-4a4 4 0 0 1 8 0v4"/>',
     '<path d="M20 9q0-3.5 3-4t3-4"/><path d="M29 9q1.5-3 5-3"/>',
     '<path d="M7 40h34"/>')


def tech(suit, rank, size=1):
    """The illustration for one card, as an inline SVG."""
    body = TECH.get(f"{suit}-{rank}")
    if body is None:
        return ('<svg class="tech ghost" viewBox="0 0 48 48" aria-hidden="true">'
                '<path d="M12 36V16l12-8 12 8v20Z" stroke-dasharray="3 3"/></svg>')
    return (f'<svg class="tech" viewBox="0 0 48 48" aria-hidden="true">'
            f'{body}</svg>')

# ============================== AGE II · CRAFT =============================

_add("plains", 6, "Irrigation",
     '<path d="M4 13h40M4 19h40"/>',
     '<path d="M11 19v21M24 19v21M37 19v21"/>',
     '<path d="M7 16q3-2.5 6 0t6 0 6 0 6 0 6 0 6 0"/>',
     '<path d="M17 40v-6M17 34q-3 0-3 3M17 34q3 0 3 3"/>',
     '<path d="M31 40v-6M31 34q-3 0-3 3M31 34q3 0 3 3"/>',
     '<path d="M4 43h40"/>')

_add("plains", 7, "Township",
     '<path d="M5 40V23h11v17"/>',
     '<path d="M8 27h5v4H8zM8 34h5v4H8z"/>',
     '<path d="M19 40V13h10v27"/>',
     '<circle cx="24" cy="19" r="3.4"/>',
     '<path d="M24 13V9"/>',
     '<path d="M22 40v-6h4v6"/>',
     '<path d="M32 40V26h11v14"/>',
     '<path d="M35 30h5v4h-5z"/>',
     '<path d="M3 40h42"/>')

_add("plains", 9, "Code of Law",
     '<path d="M14 41V17a10 10 0 0 1 20 0v24z"/>',
     '<path d="M19 20h10M18 26h12M18 31h12M18 36h9"/>',
     '<path d="M8 41h32"/>')

_add("plains", 10, "Census",
     '<path d="M9 9h30v31H9z"/>',
     '<path d="M14 15v8M18 15v8M22 15v8M26 15v8"/><path d="M12.5 23l15-8.5"/>',
     '<path d="M14 27v8M18 27v8M22 27v8M26 27v8"/><path d="M12.5 35l15-8.5"/>',
     '<path d="M32 15v8M36 15v8M32 27v8"/>',
     '<path d="M29.5 9v31"/>')

_add("forest", 6, "The Kiln",
     '<path d="M10 40V27a14 13 0 0 1 28 0v13z"/>',
     '<path d="M19 40v-9h10v9"/>',
     '<path d="M15 22h18"/>',
     '<path d="M24 13q0-3.5 3-4t3-4"/><path d="M18 15q0-3 2.5-3.5"/>',
     '<path d="M6 40h36"/>')

_add("forest", 7, "Papermaking",
     '<path d="M9 8h30v22H9z"/>',
     '<path d="M16 8v22M24 8v22M32 8v22"/>',
     '<path d="M9 14h30M9 19h30M9 24h30"/>',
     '<path d="M7 35h34M10 39h28M13 43h22"/>')

_add("forest", 9, "Windmill",
     '<path d="M18 42l2-19h8l2 19z"/>',
     '<path d="M20.5 34h7"/>',
     '<path d="M24 23V19"/>',
     '<circle cx="24" cy="17" r="2.2"/>',
     '<path d="M22.4 15.4L13 6M25.6 18.6L35 28M25.6 15.4L35 6M22.4 18.6L13 28"/>',
     '<path d="M11 8l4-1M33 6l1 4M37 26l-4 1M15 28l-1-4"/>',
     '<path d="M12 42h24"/>')

_add("forest", 10, "Waterwheel",
     '<circle cx="21" cy="23" r="13"/>',
     '<circle cx="21" cy="23" r="3"/>',
     '<path d="M21 10v-3.5M31.2 23h3.5M21 36v3.5M7.3 23H10.8"/>',
     '<path d="M28.2 15.8l2.5-2.5M28.2 30.2l2.5 2.5M13.8 30.2l-2.5 2.5M13.8 15.8l-2.5-2.5"/>',
     '<path d="M36 8h10v4H36z"/><path d="M36 12q-4 3-6 7"/>',
     '<path d="M3 41q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 6, "The Sail",
     '<path d="M7 31h34l-5 8H12z"/>',
     '<path d="M24 31V9"/>',
     '<path d="M12 12h24"/>',
     '<path d="M13 12h22l-2.5 15h-17z"/>',
     '<path d="M13 12q11 4 22 0"/>',
     '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 7, "Harbour",
     '<path d="M4 24h22v10H4z"/>',
     '<path d="M4 27.5h22"/>',
     '<path d="M8 24v-4h4v4M17 24v-4h4v4"/>',
     '<path d="M26 30h16l-3 6H29z"/>',
     '<path d="M34 30V17"/><path d="M34 18h7l-2.5 2 2.5 2h-7"/>',
     '<path d="M21 21q7 3.5 12 8"/>',
     '<path d="M3 42q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 9, "Cartography",
     '<path d="M7 10h34v27H7z"/>',
     '<path d="M7 26q7-8 13-2.5T29 13t12-1.5"/>',
     '<path d="M11 32q5-3 10 0t10 0"/>',
     '<path d="M33 16l1.6 4.4 4.4 1.6-4.4 1.6L33 28l-1.6-4.4L27 22l4.4-1.6z"/>',
     '<path d="M4 41h40"/>')

_add("ocean", 10, "The Compass",
     '<circle cx="24" cy="24" r="15"/>',
     '<path d="M24 11l3.2 9.8 9.8 3.2-9.8 3.2L24 37l-3.2-9.8L11 24l9.8-3.2z"/>',
     '<circle cx="24" cy="24" r="2.2"/>',
     '<path d="M24 5v3.5M24 39.5V43M5 24h3.5M39.5 24H43"/>',
     '<path d="M13 13l2.4 2.4M35 13l-2.4 2.4M35 35l-2.4-2.4M13 35l2.4-2.4"/>')

_add("mountain", 6, "Iron",
     '<path d="M6 21h27l7 3.5-6 3.5H14z"/>',
     '<path d="M18 28l-2 8h16l-2-8"/>',
     '<path d="M12 36h24v5H12z"/>',
     '<path d="M17 21a4.6 4.6 0 0 1 9.2 0"/>',
     '<path d="M19 14v-3.5M25 14.5V11"/>',
     '<path d="M6 43h36"/>')

_add("mountain", 7, "Rampart",
     '<path d="M5 41l7-16h24l7 16z"/>',
     '<path d="M12 25h24"/>',
     '<path d="M11 25v-7h5v7M21 25v-7h6v7M32 25v-7h5v7"/>',
     '<path d="M15 41l3-16M33 41l-3-16"/>',
     '<path d="M3 44h42"/>')

_add("mountain", 9, "Siegecraft",
     '<path d="M9 37l9-15M31 37l-9-15"/>',
     '<path d="M13 30h12"/>',
     '<path d="M19 22L37 9"/>',
     '<circle cx="39.5" cy="7.5" r="3.6"/>',
     '<path d="M20 24l-8 9"/>',
     '<circle cx="11" cy="39.5" r="2.8"/><circle cx="29" cy="39.5" r="2.8"/>',
     '<path d="M5 43h34"/>')

_add("mountain", 10, "The Keep",
     '<path d="M13 41V17h22v24z"/>',
     '<path d="M13 17v-5h5v5M21.5 17v-5h5v5M30 17v-5h5v5"/>',
     '<path d="M21 41v-9a3 3 0 0 1 6 0v9"/>',
     '<path d="M17 22h4v5h-4zM27 22h4v5h-4z"/>',
     '<path d="M8 41h32"/>')

# =========================== AGE III · DISCOVERY ===========================

_add("plains", 11, "Aqueduct",
     '<path d="M4 12h40v6H4z"/>',
     '<path d="M6 15q3-2 6 0t6 0 6 0 6 0 6 0 6 0"/>',
     '<path d="M7 18v23M17 18v23M27 18v23M37 18v23"/>',
     '<path d="M7 28a5 5 0 0 1 10 0M17 28a5 5 0 0 1 10 0M27 28a5 5 0 0 1 10 0"/>',
     '<path d="M4 41h40"/>')

_add("plains", 13, "Charter",
     '<path d="M11 5h26v26H11z"/>',
     '<path d="M15 12h18M15 17h18M15 22h13"/>',
     '<path d="M24 31v4M28 31v4"/>',
     '<circle cx="26" cy="39" r="4.6"/>',
     '<path d="M23.6 37.2l4.8 3.6M23.6 40.8l4.8-3.6"/>')

_add("plains", 14, "Public Assembly",
     '<path d="M7 36a17 17 0 0 1 34 0"/>',
     '<path d="M12 36a12 12 0 0 1 24 0"/>',
     '<path d="M17 36a7 7 0 0 1 14 0"/>',
     '<path d="M24 36L13.5 25.5M24 36l10.5-10.5"/>',
     '<circle cx="24" cy="15" r="3"/>',
     '<path d="M24 18.4c-3.2 0-5 2.4-5.4 6.6h10.8c-.4-4.2-2.2-6.6-5.4-6.6Z"/>',
     '<path d="M4 40h40"/>')

_add("plains", 15, "Capital City",
     '<path d="M6 40V22h8v18"/>',
     '<path d="M17 40V15h7v25"/>',
     '<path d="M20.5 15V7"/><path d="M20.5 8h9l-2.5 2.5L29.5 13h-9"/>',
     '<path d="M27 40V25h9v15"/><path d="M27 25a4.5 4.5 0 0 1 9 0"/>',
     '<path d="M39 40V28h5v12"/>',
     '<path d="M30 40v-7h3v7"/>',
     '<path d="M3 40h42"/>')

_add("forest", 11, "Printing Press",
     '<path d="M8 7h32"/>',
     '<path d="M21 10h6M21 13h6M21 16h6"/>',
     '<path d="M24 7v3"/>',
     '<path d="M14 18h20v5H14z"/>',
     '<path d="M12 7v30M36 7v30"/>',
     '<path d="M10 29h28v4H10z"/>',
     '<path d="M27 12h12"/>',
     '<path d="M8 37h32"/>')

_add("forest", 13, "Clockwork",
     '<circle cx="19" cy="19" r="8.5"/><circle cx="19" cy="19" r="2.4"/>',
     '<path d="M19 10.5V7M19 27.5V31M10.5 19H7M27.5 19H31"/>',
     '<path d="M13 13l-2.5-2.5M25 13l2.5-2.5M25 25l2.5 2.5M13 25l-2.5 2.5"/>',
     '<circle cx="34" cy="32" r="6"/><circle cx="34" cy="32" r="1.8"/>',
     '<path d="M34 26v-3M34 38v3M28 32h-3M40 32h3M29.8 27.8l-2-2M38.2 36.2l2 2"/>')

_add("forest", 14, "Scientific Method",
     '<path d="M10 8h28"/>',
     '<path d="M24 8v20"/>',
     '<circle cx="24" cy="31" r="4"/>',
     '<path d="M24 8L13.5 25" opacity=".4"/><path d="M24 8L34.5 25" opacity=".4"/>',
     '<path d="M13 26q11 9 22 0" stroke-dasharray="2.6 2.6"/>',
     '<path d="M14.5 31v3M24 35.5v3M33.5 31v3"/>')

_add("forest", 15, "Mechanical Loom",
     '<path d="M7 8h34v30H7z"/>',
     '<path d="M13 8v30M19 8v30M25 8v30M31 8v30M37 8v30"/>',
     '<path d="M5 12h38M5 34h38"/>',
     '<path d="M7 21h34"/>',
     '<path d="M13 27l4-3h10l4 3-4 3H17z"/>')

_add("ocean", 11, "Deep Keel",
     '<path d="M10 12q-2 19 14 23 16-4 14-23"/>',
     '<path d="M13 12h22"/>',
     '<path d="M4 20h6M38 20h6"/>',
     '<path d="M21 34.5h6l-1.5 9h-3z"/>',
     '<path d="M17 16v10M31 16v10" opacity=".4"/>')

_add("ocean", 13, "Caravel",
     '<path d="M6 30h36l-5 8H11z"/>',
     '<path d="M13 30V15M24 30V9M35 30V17"/>',
     '<path d="M9 16h9l-1 8h-7z"/>',
     '<path d="M19 11h11l-1 8h-9z"/>',
     '<path d="M19.5 21h10l1 7h-12z"/>',
     '<path d="M31 19h9l-1 7h-7z"/>',
     '<path d="M24 9h7l-2 2 2 2h-7"/>',
     '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 14, "Sextant",
     '<path d="M11 6l2 5.5 5.5 2-5.5 2-2 5.5-2-5.5-5.5-2 5.5-2z"/>',
     '<path d="M36 33L14 18"/>',
     '<path d="M4 33h32"/>',
     '<path d="M24 33a12 12 0 0 1 3.6-8.6"/>',
     '<path d="M30.5 33a5.5 5.5 0 0 1 1.7-4"/>',
     '<path d="M36 33l-4-6"/>',
     '<path d="M3 41q4.5-3.2 9 0t9 0 9 0 9 0"/>')

_add("ocean", 15, "Trading Company",
     '<path d="M9 28h13v12H9zM24 28h14v12H24z"/>',
     '<path d="M9 34h13M24 34h14"/>',
     '<path d="M16 21h11v7H16z"/>',
     '<path d="M21.5 21V7"/>',
     '<path d="M21.5 8h14l-3.5 3.5L35.5 15h-14"/>',
     '<path d="M5 40h38"/>')

_add("mountain", 11, "Steel",
     '<path d="M22 2h4v4h-4z"/>',
     '<path d="M17 6h14v2H17z"/>',
     '<path d="M20 8h8v18l-4 6-4-6z"/>',
     '<path d="M24 11v13"/>',
     '<path d="M9 28h30v12H9z"/>',
     '<path d="M12 33q4.5-2.5 9 0t9 0 9 0"/>',
     '<path d="M15 26q2.5-3.5 0-7M33 26q2.5-3.5 0-7"/>',
     '<path d="M6 43h36"/>')

_add("mountain", 13, "Bastion",
     '<path d="M2 10h13l4 8 5 12 5-12 4-8h13v7H35l-4 7-7 16-7-16-4-7H2z"/>',
     '<path d="M6 10v7M10 10v7M38 10v7M42 10v7"/>',
     '<circle cx="20.4" cy="27" r="1.5" fill="currentColor" stroke="none"/>',
     '<circle cx="27.6" cy="27" r="1.5" fill="currentColor" stroke="none"/>')

_add("mountain", 14, "Gunpowder",
     '<path d="M14 17q-3.5 12 0 23h20q3.5-11 0-23z"/>',
     '<path d="M11.5 23h25M11.5 35h25"/>',
     '<path d="M24 17q0-5 5-7"/>',
     '<path d="M29 10l1.5-3M29 10l3 1M29 10l-.5-3.4M29 10l3-1.6"/>',
     '<path d="M8 40h32"/>')

_add("mountain", 15, "Cannon",
     '<path d="M11 17h22l7 3.5-7 3.5H11z"/>',
     '<path d="M8 15h5v11H8z"/>',
     '<path d="M15 26l5 8h11l-5-8"/>',
     '<circle cx="19" cy="36" r="5.5"/><circle cx="19" cy="36" r="1.7"/>',
     '<path d="M26 33h13l-2.5 6"/>',
     '<path d="M6 42h36"/>')

# ============================ AGE IV · INDUSTRY ============================

_add("plains", 16, "Sanitation",
     '<path d="M8 9h32v5H8z"/>',
     '<path d="M14 9v5M20 9v5M26 9v5M32 9v5"/>',
     '<path d="M12 14l6 8h12l6-8"/>',
     '<path d="M18 22h12v6H18z"/>',
     '<path d="M6 28h36v9H6z"/>',
     '<path d="M10 32.5h9M24 32.5h9"/>',
     '<path d="M19.5 30.5l2.5 2-2.5 2M33.5 30.5l2.5 2-2.5 2"/>',
     '<path d="M6 41h36"/>')

_add("plains", 17, "Civil Service",
     '<path d="M7 13h21v27H7z"/>',
     '<path d="M7 22h21M7 31h21"/>',
     '<path d="M15 18h5M15 27h5M15 36h5"/>',
     '<path d="M31 34h11v5H31z"/>',
     '<path d="M34.5 34v-5h4v5"/>',
     '<path d="M32 25h9v4h-9z"/>',
     '<path d="M4 40h40"/>')

_add("plains", 19, "Metropolis",
     '<path d="M5 41V21h7v20"/>',
     '<path d="M14 41V11h8v30"/>',
     '<path d="M24 41V25h6v16"/>',
     '<path d="M32 41V16h7v25"/>',
     '<path d="M41 41V29h4v12"/>',
     '<path d="M16 16h4M16 22h4M16 28h4M16 34h4M34 21h3M34 27h3M34 33h3M7 26h3M7 33h3"/>',
     '<path d="M3 41h42"/>')

_add("plains", 20, "Constitution",
     '<path d="M10 10h28v22H10z"/>',
     '<path d="M10 10q-3 0-3 2.5T10 15M38 10q3 0 3 2.5T38 15"/>',
     '<path d="M15 17h18M15 21h18M15 25h13"/>',
     '<path d="M16 32v3M24 32v3M32 32v3"/>',
     '<circle cx="16" cy="38" r="3.2"/><circle cx="24" cy="38" r="3.2"/>',
     '<circle cx="32" cy="38" r="3.2"/>')

_add("forest", 16, "Steam Engine",
     '<path d="M8 20h19v14H8z"/>',
     '<ellipse cx="8" cy="27" rx="3" ry="7"/>',
     '<path d="M14 20v-6h6v6"/>',
     '<path d="M15 12q0-3.5 3-4"/>',
     '<path d="M27 23h8v8h-8z"/>',
     '<path d="M35 27h3"/>',
     '<circle cx="39" cy="27" r="6.5"/><circle cx="39" cy="27" r="1.6"/>',
     '<path d="M6 34h38v5H6z"/>')

_add("forest", 17, "Chemistry",
     '<path d="M20 8h8v11l8 15a4.5 4.5 0 0 1-4 7H16a4.5 4.5 0 0 1-4-7l8-15z"/>',
     '<path d="M18 8h12"/>',
     '<path d="M14.6 29h18.8"/>',
     '<circle cx="20" cy="35" r="1.5"/><circle cx="26.5" cy="33" r="1.2"/>',
     '<circle cx="23" cy="25" r="1"/><circle cx="27" cy="21" r="1.3"/>')

_add("forest", 19, "Computation",
     '<path d="M8 12h28l4 4v20H8z"/>',
     '<path d="M36 12v4h4"/>',
     '<path d="M13 21h3v2.5h-3zM19 21h3v2.5h-3zM31 21h3v2.5h-3z"/>',
     '<path d="M16 27h3v2.5h-3zM25 27h3v2.5h-3zM31 27h3v2.5h-3z"/>',
     '<path d="M13 32.5h3v2.5h-3zM22 32.5h3v2.5h-3zM28 32.5h3v2.5h-3z"/>',
     '<path d="M8 17h24"/>')

_add("forest", 20, "Automation",
     '<path d="M13 40v-6h9v6"/>',
     '<circle cx="17.5" cy="31" r="2.6"/>',
     '<path d="M17.5 34v-.6"/>',
     '<path d="M16.5 28.6L13 15"/>',
     '<circle cx="12.5" cy="13" r="2.6"/>',
     '<path d="M14.8 11.8L31 8"/>',
     '<path d="M31 8l4.5-2.5M31 8l3.5 3.5"/>',
     '<path d="M26 27h18v5H26z"/>',
     '<path d="M30 27v-6h7v6"/>',
     '<path d="M6 40h38"/>')

_add("ocean", 16, "The Canal",
     '<path d="M4 13h40v5H4z"/>',
     '<path d="M14 32v-8a10 7 0 0 1 20 0v8"/>',
     '<path d="M4 18v14h10M44 18v14H34"/>',
     '<path d="M16 30h16l-2 4H18z"/>',
     '<path d="M19 30v-4h7v4"/>',
     '<path d="M3 36q4.5-3 9 0t9 0 9 0 9 0"/>')

_add("ocean", 17, "Chronometer",
     '<path d="M9 11h30v28H9z"/>',
     '<circle cx="24" cy="25" r="11"/>',
     '<path d="M24 25v-8M24 25l6 4"/>',
     '<circle cx="24" cy="25" r="1.5" fill="currentColor" stroke="none"/>',
     '<path d="M24 15v-2.5M34 25h2.5M24 35v2.5M14 25h-2.5"/>',
     '<circle cx="9" cy="25" r="2.2"/><circle cx="39" cy="25" r="2.2"/>')

_add("ocean", 19, "Telegraph",
     '<path d="M24 42V8"/>',
     '<path d="M13 13h22M15 20h18"/>',
     '<circle cx="13" cy="13" r="1.6"/><circle cx="35" cy="13" r="1.6"/>',
     '<path d="M4 16q10 4 20 0t20 0"/>',
     '<path d="M6 23q9 4 18 0t18 0"/>',
     '<path d="M8 33h5M16 33h2M21 33h5M29 33h2M34 33h5"/>',
     '<path d="M4 42h40"/>')

_add("ocean", 20, "World Market",
     '<circle cx="24" cy="25" r="14"/>',
     '<ellipse cx="24" cy="25" rx="6" ry="14"/>',
     '<path d="M10 25h28"/><path d="M13.5 17h21M13.5 33h21"/>',
     '<path d="M24 11v28"/>',
     '<path d="M7 13q17-10 34 0"/>',
     '<path d="M41 13l-4.6-1.4M41 13l-1.4 4.6"/>')

_add("mountain", 16, "The Foundry",
     '<path d="M6 15h17l-1.5 9H7.5z"/>',
     '<path d="M23 17l9-4"/>',
     '<path d="M5 15q-3 0-3 3"/>',
     '<path d="M19 24q3.5 7 4.5 11"/>',
     '<path d="M18 34l3-4h6l3 4"/>',
     '<path d="M16 34h18v9H16z"/>',
     '<path d="M27 24l2-3M32 27l3-2"/>')

_add("mountain", 17, "Fortress",
     '<path d="M4 41V16h9v25M35 41V16h9v25"/>',
     '<path d="M4 16v-4h3v4M10 16v-4h3v4M35 16v-4h3v4M41 16v-4h3v4"/>',
     '<path d="M13 41V25h22v16"/>',
     '<path d="M13 25v-4h4v4M22 25v-4h4v4M31 25v-4h4v4"/>',
     '<path d="M21 41v-8a3 3 0 0 1 6 0v8"/>',
     '<path d="M2 41h44"/>')

_add("mountain", 19, "Artillery",
     '<path d="M9 33l3.5 5.5L41 20l-3.5-5.5z"/>',
     '<path d="M11 30h9v8h-9z"/>',
     '<path d="M13 38l-7 6M15 38l9 6"/>',
     '<circle cx="14" cy="36" r="5"/><circle cx="14" cy="36" r="1.5"/>',
     '<path d="M4 44h34"/>')

_add("mountain", 20, "The Arsenal",
     '<path d="M8 39V15h4v24M36 39V15h4v24"/>',
     '<path d="M8 20h32M8 29h32"/>',
     '<path d="M13 14h22v6H13z"/><path d="M13 17h22"/>',
     '<circle cx="17" cy="25" r="3.2"/><circle cx="24" cy="25" r="3.2"/>',
     '<circle cx="31" cy="25" r="3.2"/>',
     '<path d="M14 33h10v6H14zM26 33h10v6H26z"/>',
     '<path d="M5 42h38"/>')
