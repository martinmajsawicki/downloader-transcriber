"""Generate Copysight app icon — Minimalist Archive style.

Creates an .iconset folder with all required sizes for macOS.
Uses Pillow to draw a manila-paper icon with a red "C" and gear accent.

Usage: python build_icon.py <output_iconset_dir>
"""

import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

# ── Brand colors ──
MANILA = (247, 233, 193)       # #F7E9C1
MANILA_DARK = (235, 218, 170)  # edge vignette
RED = (209, 52, 75)            # #D1344B
INK = (43, 43, 43)             # #2B2B2B
GEAR_COLOR = (196, 170, 120, 40)  # watercolor gear, semi-transparent


def find_font(size):
    """Try to find a good serif font for the icon."""
    candidates = [
        # Playfair Display if installed locally
        "/Users/marcinmajsawicki/Library/Fonts/PlayfairDisplay-Black.ttf",
        "/Users/marcinmajsawicki/Library/Fonts/PlayfairDisplay-Bold.ttf",
        # System serif fonts
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/Library/Fonts/Georgia Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # Fallback — built-in font
    return ImageFont.load_default()


def draw_gear(draw, cx, cy, outer_r, inner_r, teeth, color):
    """Draw a simplified gear shape."""
    points = []
    for i in range(teeth * 2):
        angle = (i * math.pi) / teeth
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(angle - math.pi / 2)
        y = cy + r * math.sin(angle - math.pi / 2)
        points.append((x, y))
    draw.polygon(points, fill=color)
    # Inner circle (hole)
    hole_r = inner_r * 0.45
    draw.ellipse(
        [cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r],
        fill=MANILA,
    )


def generate_icon(size):
    """Generate a single icon at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Rounded rectangle background (manila paper) ──
    corner_r = int(size * 0.22)  # macOS icon corner radius ~22%
    # Fill with manila gradient (approximate with solid + overlay)
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1],
        radius=corner_r,
        fill=MANILA,
    )

    # Subtle darker edge (vignette effect)
    for i in range(3):
        inset = i
        alpha = 8 - i * 2
        draw.rounded_rectangle(
            [inset, inset, size - 1 - inset, size - 1 - inset],
            radius=corner_r - inset,
            outline=(*MANILA_DARK, alpha),
            width=1,
        )

    # ── Watercolor gear (top-right, subtle) ──
    gear_size = size * 0.28
    gear_cx = size * 0.78
    gear_cy = size * 0.22
    # Draw on a separate layer for transparency
    gear_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gear_draw = ImageDraw.Draw(gear_layer)
    draw_gear(
        gear_draw,
        gear_cx, gear_cy,
        outer_r=gear_size * 0.5,
        inner_r=gear_size * 0.38,
        teeth=8,
        color=GEAR_COLOR,
    )
    img = Image.alpha_composite(img, gear_layer)
    draw = ImageDraw.Draw(img)

    # ── Red accent line (bottom) ──
    line_y = int(size * 0.78)
    line_x1 = int(size * 0.15)
    line_x2 = int(size * 0.85)
    line_h = max(2, int(size * 0.005))
    draw.rectangle(
        [line_x1, line_y, line_x2, line_y + line_h],
        fill=(*RED, 140),
    )

    # ── Letter "C" — bold serif ──
    font_size = int(size * 0.52)
    font = find_font(font_size)

    letter = "C"
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (size - text_w) / 2 - bbox[0]
    text_y = (size - text_h) / 2 - bbox[1] - size * 0.02  # slightly above center

    # Subtle text shadow
    draw.text(
        (text_x + 1, text_y + 1),
        letter,
        font=font,
        fill=(0, 0, 0, 18),
    )
    # Main letter
    draw.text(
        (text_x, text_y),
        letter,
        font=font,
        fill=(*INK, 230),
    )

    # ── Small red dot (period after C — archival stamp feel) ──
    dot_r = max(2, int(size * 0.03))
    dot_x = text_x + text_w + size * 0.02
    dot_y = text_y + text_h - dot_r
    draw.ellipse(
        [dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
        fill=RED,
    )

    return img


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_icon.py <output_iconset_dir>")
        sys.exit(1)

    output_dir = sys.argv[1]
    os.makedirs(output_dir, exist_ok=True)

    # macOS required icon sizes
    sizes = [
        (16, 1), (16, 2),
        (32, 1), (32, 2),
        (128, 1), (128, 2),
        (256, 1), (256, 2),
        (512, 1), (512, 2),
    ]

    for base_size, scale in sizes:
        pixel_size = base_size * scale
        icon = generate_icon(pixel_size)

        if scale == 1:
            filename = f"icon_{base_size}x{base_size}.png"
        else:
            filename = f"icon_{base_size}x{base_size}@{scale}x.png"

        icon.save(os.path.join(output_dir, filename), "PNG")

    print(f"  Generated {len(sizes)} icon sizes in {output_dir}")


if __name__ == "__main__":
    main()
