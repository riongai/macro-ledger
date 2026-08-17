#!/usr/bin/env python3
"""Generate the app icons: four macro gauge bars on the ledger's dark ground.

Pure stdlib — no Pillow — so it re-runs anywhere. Rewrite the icons with:
    python3 make-icons.py
"""
import zlib, struct

BG    = (0x12, 0x19, 0x1E)
TRACK = (0x23, 0x2E, 0x35)
BARS  = [(0.80, (0x7F, 0x95, 0xFF)),   # calories  — accent
         (0.60, (0x4C, 0xC4, 0x8F)),   # protein   — good
         (0.44, (0xE3, 0xA9, 0x3F)),   # carbs     — warn
         (0.30, (0x93, 0xA3, 0xAA))]   # fat       — muted


def rounded_rect_hit(px, py, x, y, w, h, r):
    """True when the pixel centre falls inside a rounded rectangle."""
    if not (x <= px <= x + w and y <= py <= y + h):
        return False
    cx = min(max(px, x + r), x + w - r)
    cy = min(max(py, y + r), y + h - r)
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def render(size):
    m    = size * 0.17
    w    = size - m * 2
    h    = size * 0.088
    gap  = size * 0.058
    top  = (size - (len(BARS) * h + (len(BARS) - 1) * gap)) / 2
    r    = h / 2

    rows = []
    for py in range(size):
        row = bytearray()
        yc = py + 0.5
        for px in range(size):
            xc = px + 0.5
            colour = BG
            for i, (frac, bar) in enumerate(BARS):
                y = top + i * (h + gap)
                if rounded_rect_hit(xc, yc, m, y, w, h, r):
                    colour = TRACK
                    if rounded_rect_hit(xc, yc, m, y, max(w * frac, h), h, r):
                        colour = bar
                    break
            row += bytes(colour)
        rows.append(row)

    raw = b"".join(b"\x00" + bytes(r_) for r_ in rows)
    return png(size, size, raw)


def png(w, h, raw):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


for size in (180, 192, 512):
    open(f"icon-{size}.png", "wb").write(render(size))
    print(f"icon-{size}.png")
