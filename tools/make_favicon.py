#!/usr/bin/env python3
"""Generate favicon.png (180x180, RGBA) — same composition as favicon.svg.

Pure stdlib (struct + zlib), no dependencies, works offline.
Run from repo root:  python3 tools/make_favicon.py
"""
import math
import struct
import zlib

N = 180          # output size (also used as apple-touch-icon)
SS = 4           # supersampling for smooth edges
OUT = "favicon.png"

# --- palettes (vertical gradients) ---
BG_TOP, BG_BOT = (193, 39, 45), (127, 29, 29)        # dota red -> dark red
FG_TOP, FG_BOT = (255, 255, 255), (215, 221, 230)    # white steel

# --- geometry, normalized to 0..1 (mirrors favicon.svg viewBox 64) ---
BG_BOX = (2 / 64, 2 / 64, 62 / 64, 62 / 64)  # rounded-square background
BG_RADIUS = 14 / 64
BAR = (17 / 64, 14 / 64, 25 / 64, 50 / 64)   # left bar of the "D"
CX, CY = 25 / 64, 32 / 64                    # arc center
R_OUT, R_IN = 18 / 64, 11 / 64               # ring radii (right half only)
SLIT_C = (33.25 / 64, 32 / 64)               # diagonal slit (dota-style cut)
SLIT_D = (math.sin(math.radians(24)), -math.cos(math.radians(24)))
SLIT_HW = 2.75 / 64                          # slit half-width


def lerp(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def in_rounded(x, y):
    x0, y0, x1, y1 = BG_BOX
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    # distance to the inner box (rounded corners cut)
    dx = max(x0 + BG_RADIUS - x, 0.0, x - (x1 - BG_RADIUS))
    dy = max(y0 + BG_RADIUS - y, 0.0, y - (y1 - BG_RADIUS))
    return dx * dx + dy * dy <= BG_RADIUS * BG_RADIUS


def in_d(x, y):
    x0, y0, x1, y1 = BAR
    if x0 <= x <= x1 and y0 <= y <= y1:
        return True
    if x >= CX:
        d = math.hypot(x - CX, y - CY)
        if R_IN <= d <= R_OUT:
            return True
    return False


def in_slit(x, y):
    # distance from point to the slit line
    px, py = x - SLIT_C[0], y - SLIT_C[1]
    dist = abs(px * SLIT_D[1] - py * SLIT_D[0])  # |cross(p, d)|, |d| == 1
    return dist < SLIT_HW


def render():
    px = bytearray()
    step = 1.0 / SS
    for j in range(N):
        for i in range(N):
            r = g = b = a = 0.0
            for sj in range(SS):
                for si in range(SS):
                    x = (i + (si + 0.5) * step) / N
                    y = (j + (sj + 0.5) * step) / N
                    if not in_rounded(x, y):
                        continue  # transparent
                    t = (y - BG_BOX[1]) / (BG_BOX[3] - BG_BOX[1])
                    t = min(max(t, 0.0), 1.0)
                    if in_d(x, y) and not in_slit(x, y):
                        c = lerp(FG_TOP, FG_BOT, t)
                    else:
                        c = lerp(BG_TOP, BG_BOT, t)
                    r += c[0]
                    g += c[1]
                    b += c[2]
                    a += 255.0
            n = SS * SS
            px += bytes((round(r / n), round(g / n), round(b / n), round(a / n)))
    return bytes(px)


def write_png(path, size, rgba):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    raw = b"".join(b"\x00" + rgba[y * size * 4:(y + 1) * size * 4]
                   for y in range(size))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    write_png(OUT, N, render())
