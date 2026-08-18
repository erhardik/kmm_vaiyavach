"""Optimize hero carousel images for the KMM landing page.

Place your original images as src/hero-1.jpg ... src/hero-6.jpg
(next to this script), then run:

    python deployment/optimize_hero_images.py

It resizes each to max 1920px wide, converts to WebP (quality 82)
and writes static/images/hero/hero-N.webp, keeping visual quality
while shrinking file size dramatically.

Then deploy:

    python manage.py collectstatic --noinput
    # and Reload the web app
"""

from pathlib import Path
from PIL import Image

SRC_DIR = Path(__file__).resolve().parent / "src"
OUT_DIR = Path(__file__).resolve().parent.parent / "static" / "images" / "hero"
MAX_WIDTH = 1920
QUALITY = 82


def main() -> None:
    if not SRC_DIR.exists():
        print(f"Create {SRC_DIR} and put hero-1.jpg .. hero-6.jpg in it.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(SRC_DIR.glob("hero-*.jp*g")) + sorted(SRC_DIR.glob("hero-*.png"))
    if not images:
        print(f"No images found in {SRC_DIR} (hero-1.jpg .. hero-6.jpg).")
        return

    for path in images:
        num = path.stem.split("-")[-1]
        with Image.open(path) as im:
            im = im.convert("RGB")
            if im.width > MAX_WIDTH:
                ratio = MAX_WIDTH / im.width
                im = im.resize((MAX_WIDTH, round(im.height * ratio)), Image.LANCZOS)
            out = OUT_DIR / f"hero-{num}.webp"
            im.save(out, "WEBP", quality=QUALITY, method=6)
        kb = round(out.stat().st_size / 1024, 1)
        print(f"{path.name} -> {out.name}  ({im.width}x{im.height}px, {kb} KB)")


if __name__ == "__main__":
    main()