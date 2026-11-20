"""Draw docs/social-preview.png (1280 x 640) with the standard library only.

A tiny 5 x 7 pixel font is scaled up. Run it again to rebuild the image.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "social-preview.png"
W, H = 1280, 640
BG, FG, ACCENT, MUTED = (22, 24, 28), (236, 236, 236), (76, 201, 160), (150, 158, 168)

FONT = {  # each glyph is 7 rows of 5 bits
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01111 10000 10000 10000 10000 10000 01111", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01111 10000 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10011 10101 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100", ",": "00000 00000 00000 00000 01100 00100 01000",
    "-": "00000 00000 00000 11111 00000 00000 00000", " ": "00000 00000 00000 00000 00000 00000 00000",
}


def draw_text(pixels, text, x, y, scale, color):
    for char in text.upper():
        rows = FONT[char].split()
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    for dy in range(scale):
                        start = (y + r * scale + dy) * W + x + c * scale
                        pixels[start:start + scale] = [color] * scale
        x += 6 * scale


def png(pixels) -> bytes:
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in pixels[y * W:(y + 1) * W])
                   for y in range(H))

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main() -> None:
    counts = json.loads((ROOT / "results" / "call_counts.json").read_text())
    calls = sum(p["example"]["calls"] for p in counts["patterns"])
    pixels = [BG] * (W * H)
    for y in range(96, 104):
        pixels[y * W + 96:y * W + 336] = [ACCENT] * 240
    draw_text(pixels, "agentbook", 96, 150, 16, FG)
    draw_text(pixels, "twelve agent patterns", 96, 300, 7, ACCENT)
    draw_text(pixels, "small tested python. no framework.", 96, 380, 5, FG)
    draw_text(pixels, f"12 lessons. 36 exercises. {calls} model calls.", 96, 470, 4, MUTED)
    OUT.write_bytes(png(pixels))
    print(f"wrote {OUT.relative_to(ROOT)} ({W} x {H})")


if __name__ == "__main__":
    main()
