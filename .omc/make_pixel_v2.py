from pathlib import Path
from collections import deque
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]


def pixel_polish(
    src_rel: str,
    out_rel: str,
    scale: int,
    colors: int,
    contrast: float = 1.08,
    saturation: float = 0.92,
    background_mode: str = "all_edges",
    asset_kind: str = "default",
):
    src = ROOT / src_rel
    out = ROOT / out_rel
    img = Image.open(src).convert("RGBA")

    alpha = img.getchannel("A")
    rgb = img.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Color(rgb).enhance(saturation)

    small_size = (max(1, img.width // scale), max(1, img.height // scale))
    small = rgb.resize(small_size, Image.Resampling.BOX)
    pal = small.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    polished = pal.resize(img.size, Image.Resampling.NEAREST).convert("RGBA")

    # Keep transparent or cutout edges clean, then add a restrained warm outline for readability.
    polished.putalpha(alpha)
    edge = alpha.filter(ImageFilter.FIND_EDGES).point(lambda p: 180 if p > 18 else 0)
    outline = Image.new("RGBA", img.size, (43, 26, 17, 0))
    outline.putalpha(edge)
    polished = Image.alpha_composite(outline, polished)

    polished = remove_border_background(polished, mode=background_mode)
    if asset_kind == "weapon":
        polished = boost_weapon_sprite(polished)

    out.parent.mkdir(parents=True, exist_ok=True)
    polished.save(out, quality=95, method=6)


def remove_border_background(img: Image.Image, mode: str = "all_edges") -> Image.Image:
    img = img.convert("RGBA")
    alpha = img.getchannel("A")

    if mode in ("checker", "checker_dark"):
        out = img.copy()
        out_pix = out.load()
        w, h = out.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = out_pix[x, y]
                if a > 0 and is_checker_gray((r, g, b), dark=(mode == "checker_dark")):
                    out_pix[x, y] = (r, g, b, 0)
        return out

    w, h = img.size
    pix = img.load()
    alpha_pix = alpha.load()
    border = []
    for x in range(w):
        if alpha_pix[x, 0] > 0:
            border.append(pix[x, 0][:3])
        if mode != "portrait" and alpha_pix[x, h - 1] > 0:
            border.append(pix[x, h - 1][:3])
    for y in range(h):
        if alpha_pix[0, y] > 0:
            border.append(pix[0, y][:3])
        if alpha_pix[w - 1, y] > 0:
            border.append(pix[w - 1, y][:3])
    if not border:
        return img

    # Deduplicate border colors. Baked checkerboard backgrounds usually use
    # several close gray/purple tones; the dark subject outline blocks flood-in.
    seeds = []
    for c in border:
        if all(color_distance(c, s) > 10 for s in seeds):
            seeds.append(c)

    def is_background(c):
        r, g, b = c
        seed_match = any(color_distance(c, s) <= (34 if mode == "portrait" else 42) for s in seeds)
        gray_checker = mode != "portrait" and (max(c) - min(c) <= 18 and 70 <= (r + g + b) / 3 <= 235)
        return seed_match or gray_checker

    seen = [[False] * w for _ in range(h)]
    mask = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.append((x, 0))
        if mode != "portrait":
            q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if x < 0 or x >= w or y < 0 or y >= h or seen[y][x]:
            continue
        seen[y][x] = True
        if alpha_pix[x, y] == 0:
            continue
        if not is_background(pix[x, y][:3]):
            continue
        mask[y][x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    out = img.copy()
    out_pix = out.load()
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                out_pix[x, y] = out_pix[x, y][:3] + (0,)
    return out


def color_distance(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def is_checker_gray(c, dark=False):
    r, g, b = c
    avg = (r + g + b) / 3
    if dark:
        return max(c) - min(c) <= 32 and 10 <= avg <= 230
    return max(c) - min(c) <= 20 and 65 <= avg <= 225


def boost_weapon_sprite(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return img

    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    crop = img.crop(bbox)

    # Thin weapons need more screen presence after the baked checkerboard is removed.
    long_edge = max(bw, bh)
    target_long = 220 if long_edge < 170 else min(230, long_edge)
    scale = max(1.0, target_long / max(1, long_edge))
    nw, nh = max(1, int(round(bw * scale))), max(1, int(round(bh * scale)))
    crop = crop.resize((nw, nh), Image.Resampling.NEAREST)

    crop_alpha = crop.getchannel("A")
    outline_radius = 5 if min(nw, nh) < 42 else 3
    expanded = crop_alpha.filter(ImageFilter.MaxFilter(outline_radius))
    outline = Image.new("RGBA", crop.size, (42, 25, 17, 0))
    outline.putalpha(expanded)
    crop = Image.alpha_composite(outline, crop)

    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ox = (img.width - nw) // 2
    oy = (img.height - nh) // 2
    out.alpha_composite(crop, (ox, oy))
    return out


def make_v2_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}_v2{path.suffix}")


def make_asset_set():
    for src in sorted((ROOT / "assets" / "portraits").glob("*.webp")):
      if src.stem.endswith("_v2"):
          continue
      pixel_polish(
          str(src.relative_to(ROOT)),
          str(make_v2_path(src).relative_to(ROOT)),
          scale=2,
          colors=42,
          contrast=1.12,
          saturation=0.86,
          background_mode="portrait",
      )

    for src in sorted((ROOT / "assets" / "weapons").glob("*.webp")):
      if src.stem.endswith("_v2"):
          continue
      bg_mode = "checker_dark" if src.stem == "wand" else "checker"
      pixel_polish(
          str(src.relative_to(ROOT)),
          str(make_v2_path(src).relative_to(ROOT)),
          scale=2,
          colors=24,
          contrast=1.15,
          saturation=0.88,
          background_mode=bg_mode,
          asset_kind="weapon",
      )

    for src in sorted((ROOT / "assets" / "ui").glob("*.webp")):
      if src.stem.endswith("_v2"):
          continue
      is_badge = src.stem.startswith("badge_")
      pixel_polish(
          str(src.relative_to(ROOT)),
          str(make_v2_path(src).relative_to(ROOT)),
          scale=2,
          colors=28 if is_badge else 22,
          contrast=1.12 if is_badge else 1.14,
          saturation=0.9 if is_badge else 0.88,
      )


def make_sheet():
    pairs = []
    for name in ["knight", "paladin", "mage", "rogue", "ranger", "healer", "mercenary"]:
        pairs.append((name, ROOT / f"assets/portraits/{name}.webp", ROOT / f"assets/portraits/{name}_v2.webp"))
    pairs.extend([
        ("sword_1h", ROOT / "assets/weapons/sword_1h.webp", ROOT / "assets/weapons/sword_1h_v2.webp"),
        ("hammer", ROOT / "assets/ui/hammer.webp", ROOT / "assets/ui/hammer_v2.webp"),
    ])
    cell = 256
    label_h = 30
    sheet = Image.new("RGB", (cell * 2, (cell + label_h) * len(pairs)), (28, 22, 17))
    for row, (name, old_path, new_path) in enumerate(pairs):
        y = row * (cell + label_h)
        for col, path in enumerate([old_path, new_path]):
            img = Image.open(path).convert("RGBA")
            img.thumbnail((cell - 24, cell - 24), Image.Resampling.NEAREST)
            bg = Image.new("RGBA", (cell, cell), (38, 30, 24, 255))
            x = (cell - img.width) // 2
            yy = (cell - img.height) // 2
            bg.alpha_composite(img, (x, yy))
            sheet.paste(bg.convert("RGB"), (col * cell, y + label_h))
        # Minimal labels are enough for local review; no font dependency.
        label = f"{name}: original".encode("ascii", "ignore").decode()
        label2 = f"{name}: v2".encode("ascii", "ignore").decode()
        # Use default bitmap font through Pillow if available.
        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(sheet)
            draw.text((10, y + 8), label, fill=(240, 222, 190))
            draw.text((cell + 10, y + 8), label2, fill=(255, 210, 74))
        except Exception:
            pass
    out = ROOT / "assets" / "sample_pixel_v2_comparison.jpg"
    sheet.save(out, quality=92)


make_asset_set()
make_sheet()
