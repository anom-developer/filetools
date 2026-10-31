"""Image conversions via Pillow."""
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:
    raise ImportError("Pillow is required for image conversion. Run: pip install Pillow") from exc


# JPEG doesn't support alpha channel — we flatten to white background
_NEEDS_RGB = {"jpg", "jpeg"}


def convert_image(input_path: Path, output_path: Path, *, quality: int = 90) -> None:
    """
    Convert an image to the format inferred from *output_path* suffix.

    Parameters
    ----------
    input_path  : source image file
    output_path : destination file (format determined by suffix)
    quality     : compression quality 1–100, used for JPEG/WebP
    """
    dst_ext = output_path.suffix.lstrip(".").lower()

    with Image.open(input_path) as img:
        # Preserve animated GIF frames where possible
        if getattr(img, "is_animated", False) and dst_ext == "webp":
            frames = []
            try:
                while True:
                    frames.append(img.copy().convert("RGBA"))
                    img.seek(img.tell() + 1)
            except EOFError:
                pass
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                quality=quality,
            )
            return

        # Flatten alpha for JPEG
        if dst_ext in _NEEDS_RGB:
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            img.save(output_path, quality=quality, optimize=True)
        elif dst_ext == "webp":
            img.save(output_path, quality=quality, method=6)
        elif dst_ext == "png":
            img.save(output_path, optimize=True)
        else:
            img.save(output_path)
