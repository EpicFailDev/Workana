"""
Script para geração autônoma de ícones profissionais de alta resolução para a extensão
Workana Accelerator AI. Gera tamanhos 16x16, 32x32, 48x48 e 128x128 com supersampling 4x.
"""

import os
import zlib
import struct
import math

def create_png(width, height, rgba_data):
    png = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data)
    png += struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # Filter none
        for x in range(width):
            raw.extend(rgba_data[y * width + x])
    compressed = zlib.compress(bytes(raw), 9)
    idat_crc = zlib.crc32(b"IDAT" + compressed)
    png += struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)

    iend_crc = zlib.crc32(b"IEND")
    png += struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)
    return png

def point_in_polygon(px, py, poly):
    inside = False
    n = len(poly)
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if py > min(p1y, p2y):
            if py <= max(p1y, p2y):
                if px <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or px <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def render_icon(target_size):
    scale = 4  # 4x supersampling for crisp edges
    w = target_size * scale
    h = target_size * scale

    # High-resolution buffer
    buf = []

    cx, cy = w / 2.0, h / 2.0
    corner_radius = w * 0.24
    half_w = w * 0.46
    half_h = h * 0.46

    # Stylized lightning bolt polygon normalized to [-1, 1]
    # Representing speed, precision and accelerator
    bolt_normalized = [
        (-0.08, -0.68),
        (0.38, -0.68),
        (0.04, -0.06),
        (0.44, -0.06),
        (-0.36, 0.70),
        (-0.10, 0.12),
        (-0.42, 0.12),
    ]
    bolt_poly = [(cx + px * w * 0.58, cy + py * h * 0.58) for px, py in bolt_normalized]

    # Star / AI accent polygon in top right
    star_cx, star_cy = cx + w * 0.28, cy - h * 0.28
    star_r1 = w * 0.10
    star_r2 = w * 0.04
    star_poly = []
    for i in range(8):
        angle = i * math.pi / 4.0
        r = star_r1 if i % 2 == 0 else star_r2
        star_poly.append((star_cx + math.cos(angle) * r, star_cy + math.sin(angle) * r))

    for y in range(h):
        for x in range(w):
            # Signed distance to rounded rectangle
            dx = abs(x - cx) - (half_w - corner_radius)
            dy = abs(y - cy) - (half_h - corner_radius)
            outside_x = max(dx, 0)
            outside_y = max(dy, 0)
            dist_outside = math.sqrt(outside_x * outside_x + outside_y * outside_y)
            inside_dist = min(max(dx, dy), 0)
            sd = dist_outside + inside_dist - corner_radius

            if sd > 0:
                # Transparent outside
                buf.append((0, 0, 0, 0))
                continue

            # Normalized progress for gradients
            diag = (x + y) / (w + h)

            # Check border
            border_width = w * 0.045
            is_border = -border_width < sd <= 0

            # Background Gradient: Dark Indigo Obsidian -> Deep Royal Purple
            # (11, 17, 32) -> (30, 27, 75)
            bg_r = int(11 + diag * (30 - 11))
            bg_g = int(17 + diag * (27 - 17))
            bg_b = int(32 + diag * (75 - 32))
            alpha = 255

            if is_border:
                # Border Gradient: Electric Indigo (#6366f1) -> Vibrant Violet (#a855f7) -> Cyan
                br = int(99 + diag * (168 - 99))
                bg_col = int(102 + diag * (85 - 102))
                bb = int(241 + diag * (247 - 241))
                buf.append((br, bg_col, bb, alpha))
                continue

            # Check inside elements
            in_bolt = point_in_polygon(x, y, bolt_poly)
            in_star = point_in_polygon(x, y, star_poly)

            if in_star:
                # Brilliant Cyan / White Star
                buf.append((165, 243, 252, 255))
            elif in_bolt:
                # Vibrant Energy Gradient for Bolt: Amber Gold -> Pure Lightning White
                # (#fbbf24 to #ffffff to #60a5fa)
                bolt_diag = y / float(h)
                bolt_r = int(255 - bolt_diag * 30)
                bolt_g = int(230 + bolt_diag * 25)
                bolt_b = int(100 + bolt_diag * 155)
                buf.append((bolt_r, min(255, bolt_g), min(255, bolt_b), 255))
            else:
                # Subtle Inner Glow near center
                dist_center = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) / (w * 0.5)
                glow = max(0.0, 1.0 - dist_center) * 25
                buf.append((min(255, int(bg_r + glow)), min(255, int(bg_g + glow * 0.8)), min(255, int(bg_b + glow * 1.5)), 255))

    # Downsample buffer by scale factor (Box filter averaging)
    final_pixels = []
    for ty in range(target_size):
        for tx in range(target_size):
            sum_r = sum_g = sum_b = sum_a = 0
            count = scale * scale
            for sy in range(scale):
                for sx in range(scale):
                    px = tx * scale + sx
                    py = ty * scale + sy
                    r, g, b, a = buf[py * w + px]
                    sum_r += r * (a / 255.0)
                    sum_g += g * (a / 255.0)
                    sum_b += b * (a / 255.0)
                    sum_a += a

            avg_a = int(sum_a / count)
            if avg_a > 0:
                avg_r = int(sum_r / (sum_a / 255.0))
                avg_g = int(sum_g / (sum_a / 255.0))
                avg_b = int(sum_b / (sum_a / 255.0))
                final_pixels.append((min(255, avg_r), min(255, avg_g), min(255, avg_b), avg_a))
            else:
                final_pixels.append((0, 0, 0, 0))

    return create_png(target_size, target_size, final_pixels)

def main():
    icons_dir = os.path.join(os.path.dirname(__file__), "..", "extension", "icons")
    os.makedirs(icons_dir, exist_ok=True)

    sizes = [16, 32, 48, 128]
    for size in sizes:
        png_bytes = render_icon(size)
        out_path = os.path.join(icons_dir, f"icon{size}.png")
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        print(f"Gerado: {out_path} ({len(png_bytes)} bytes)")

if __name__ == "__main__":
    main()
