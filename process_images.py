#!/usr/bin/env python3
import argparse
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PIL import ImageColor


DEFAULT_TARGET_W = 1920
DEFAULT_TARGET_H = 1080


def parse_bg_color(color_value: str | None) -> tuple[int, int, int, int]:
    if not color_value:
        return (0, 0, 0, 0)
    try:
        rgb = ImageColor.getrgb(color_value)
    except ValueError as exc:
        raise SystemExit(
            f"Colore non valido: {color_value}. Esempi validi: #C0714B, red, rgb(192,113,75)"
        ) from exc
    return (rgb[0], rgb[1], rgb[2], 255)


def parse_size(size_value: str | None) -> tuple[int, int]:
    if not size_value:
        return (DEFAULT_TARGET_W, DEFAULT_TARGET_H)
    raw = size_value.lower().replace(" ", "")
    if "x" not in raw:
        raise SystemExit("Invalid size format. Use WIDTHxHEIGHT, e.g. 1920x1080")
    w_str, h_str = raw.split("x", 1)
    try:
        width = int(w_str)
        height = int(h_str)
    except ValueError as exc:
        raise SystemExit("Invalid size format. Use WIDTHxHEIGHT, e.g. 1920x1080") from exc
    if width <= 0 or height <= 0:
        raise SystemExit("Width and height must be positive integers.")
    return (width, height)


def parse_output_format(fmt_value: str | None) -> str:
    if not fmt_value:
        return "png"
    fmt = fmt_value.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    if fmt not in {"png", "jpeg", "webp"}:
        raise SystemExit("Invalid --format. Use: png, jpg, jpeg, webp")
    return fmt


def parse_resize_mode(mode_value: str | None) -> str:
    if not mode_value:
        return "fit"
    mode = mode_value.lower()
    if mode not in {"fit", "cover"}:
        raise SystemExit("Invalid --resize-mode. Use: fit, cover")
    return mode


def save_image(im: Image.Image, dst_path: Path, output_format: str, quality: int) -> None:
    if output_format == "png":
        im.save(dst_path, "PNG")
    elif output_format == "jpeg":
        im.convert("RGB").save(dst_path, "JPEG", quality=quality, optimize=True)
    else:
        im.save(dst_path, "WEBP", quality=quality)


def process_image(
    src_path: Path,
    dst_path: Path,
    bg_color: tuple[int, int, int, int],
    target_w: int,
    target_h: int,
    output_format: str,
    quality: int,
    resize_mode: str,
) -> None:
    with Image.open(src_path) as im:
        # Ensure alpha channel so empty areas stay transparent.
        im = im.convert("RGBA")
        src_w, src_h = im.size

        scale = (
            min(target_w / src_w, target_h / src_h)
            if resize_mode == "fit"
            else max(target_w / src_w, target_h / src_h)
        )
        new_w = max(1, int(round(src_w * scale)))
        new_h = max(1, int(round(src_h * scale)))

        resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (target_w, target_h), bg_color)
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        canvas.paste(resized, (x, y), resized)
        save_image(canvas, dst_path, output_format, quality)


def paste_fit(canvas: Image.Image, im: Image.Image, x: int, y: int, w: int, h: int) -> None:
    src_w, src_h = im.size
    scale = min(w / src_w, h / src_h)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    px = x + (w - new_w) // 2
    py = y + (h - new_h) // 2
    canvas.paste(resized, (px, py), resized)


def paste_cover(canvas: Image.Image, im: Image.Image, x: int, y: int, w: int, h: int) -> None:
    src_w, src_h = im.size
    scale = max(w / src_w, h / src_h)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = max(0, (new_w - w) // 2)
    top = max(0, (new_h - h) // 2)
    cropped = resized.crop((left, top, left + w, top + h))
    canvas.paste(cropped, (x, y), cropped)


def process_side_by_side(
    src_paths: list[Path],
    dst_path: Path,
    bg_color: tuple[int, int, int, int],
    target_w: int,
    target_h: int,
    output_format: str,
    quality: int,
    resize_mode: str,
) -> None:
    with Image.new("RGBA", (target_w, target_h), bg_color) as canvas:
        count = len(src_paths)
        used_w = 0
        for idx, src_path in enumerate(src_paths):
            col_w = (target_w - used_w) if idx == count - 1 else target_w // count
            with Image.open(src_path) as im:
                im = im.convert("RGBA")
                if resize_mode == "cover":
                    paste_cover(canvas, im, used_w, 0, col_w, target_h)
                else:
                    paste_fit(canvas, im, used_w, 0, col_w, target_h)
            used_w += col_w
        save_image(canvas, dst_path, output_format, quality)


def get_orientation_and_ratio(src_path: Path) -> tuple[str, float]:
    with Image.open(src_path) as im:
        w, h = im.size
        return ("vertical", w / h) if h > w else ("other", w / h)


def verticals_per_canvas(ratio_w_over_h: float, target_w: int, target_h: int) -> int:
    # Number of vertical images that can fit side-by-side at full height.
    target_ratio = target_w / target_h
    fit = int(target_ratio / max(0.01, ratio_w_over_h))
    return max(2, fit)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Converte tutte le immagini di una cartella in PNG 1920x1080 "
            "senza distorsione e con bordi trasparenti."
        )
    )
    parser.add_argument("input_dir", help="Percorso della cartella con le immagini")
    parser.add_argument(
        "--output-dir-name",
        help="Output subfolder name inside input_dir (default: png_WIDTHxHEIGHT)",
    )
    parser.add_argument(
        "--side-by-side-vertical",
        action="store_true",
        help=(
            "Se attivo, combina due immagini verticali in un unico PNG 1920x1080 "
            "affiancandole. Se il numero e' dispari, l'ultima resta singola."
        ),
    )
    parser.add_argument(
        "--side-by-side-vertical-cyclic",
        action="store_true",
        help=(
            "Like --side-by-side-vertical, but without single vertical images: "
            "se dispari, l'ultima viene affiancata alla prima (ripetuta)."
        ),
    )
    parser.add_argument(
        "--bg-color",
        help=(
            "Colore sfondo. Se omesso, sfondo trasparente. "
            "Accetta formati tipo #C0714B, red, rgb(192,113,75)."
        ),
    )
    parser.add_argument(
        "--size",
        help="Custom output size in WIDTHxHEIGHT format (example: 1920x1080)",
    )
    parser.add_argument("--recursive", action="store_true", help="Process subfolders recursively")
    parser.add_argument("--format", help="Output format: png, jpg, jpeg, webp (default: png)")
    parser.add_argument("--quality", type=int, default=92, help="Quality for jpg/webp (1-100)")
    parser.add_argument(
        "--resize-mode",
        help="Resize mode: fit (default) or cover",
    )
    args = parser.parse_args()
    bg_color = parse_bg_color(args.bg_color)
    target_w, target_h = parse_size(args.size)
    output_format = parse_output_format(args.format)
    resize_mode = parse_resize_mode(args.resize_mode)
    if not (1 <= args.quality <= 100):
        raise SystemExit("--quality must be between 1 and 100")
    if output_format in {"jpeg", "webp"} and bg_color[3] == 0:
        raise SystemExit("JPEG/WEBP output requires --bg-color (transparent background is not supported).")

    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Cartella non valida: {input_dir}")

    output_dir_name = args.output_dir_name or f"png_{target_w}x{target_h}"
    output_dir = input_dir / output_dir_name
    output_dir.mkdir(exist_ok=True)

    all_files = sorted(input_dir.rglob("*") if args.recursive else input_dir.iterdir())
    all_files = [p for p in all_files if p.is_file() and output_dir not in p.parents]

    count = 0
    skipped = 0
    valid_files: list[tuple[Path, Path, str, float]] = []
    for item in all_files:
        try:
            orientation, ratio = get_orientation_and_ratio(item)
            valid_files.append((item, item.relative_to(input_dir).parent, orientation, ratio))
        except (UnidentifiedImageError, OSError):
            skipped += 1

    if args.side_by_side_vertical and args.side_by_side_vertical_cyclic:
        raise SystemExit(
            "Use only one mode: --side-by-side-vertical or --side-by-side-vertical-cyclic"
        )

    if args.side_by_side_vertical_cyclic:
        verticals = [(item, rel_dir, ratio) for item, rel_dir, orientation, ratio in valid_files if orientation == "vertical"]
        others = [(item, rel_dir) for item, rel_dir, orientation, _ in valid_files if orientation != "vertical"]

        for item, rel_dir in others:
            dst_dir = output_dir / rel_dir
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_dir / f"{item.stem}.{output_format if output_format != 'jpeg' else 'jpg'}"
            process_image(item, dst_path, bg_color, target_w, target_h, output_format, args.quality, resize_mode)
            count += 1

        i = 0
        while i < len(verticals):
            base_path, rel_dir, base_ratio = verticals[i]
            per_canvas = verticals_per_canvas(base_ratio, target_w, target_h)
            selected = [p for p, _, _ in verticals[i : i + per_canvas]]
            if len(selected) < per_canvas and len(verticals) > 0:
                need = per_canvas - len(selected)
                selected.extend([p for p, _, _ in verticals[:need]])
            name = "__".join(p.stem for p in selected)
            dst_dir = output_dir / rel_dir
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_dir / f"{name}.{output_format if output_format != 'jpeg' else 'jpg'}"
            process_side_by_side(
                selected, dst_path, bg_color, target_w, target_h, output_format, args.quality, resize_mode
            )
            count += 1
            i += per_canvas
    elif args.side_by_side_vertical:
        pending_vertical: list[Path] = []
        pending_rel_dir: Path | None = None
        pending_per_canvas = 0
        for item, rel_dir, orientation, ratio in valid_files:
            if orientation == "vertical":
                if not pending_vertical:
                    pending_per_canvas = verticals_per_canvas(ratio, target_w, target_h)
                    pending_rel_dir = rel_dir
                pending_vertical.append(item)
                if len(pending_vertical) == pending_per_canvas:
                    dst_dir = output_dir / (pending_rel_dir or Path("."))
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    dst_path = dst_dir / f"{'__'.join(p.stem for p in pending_vertical)}.{output_format if output_format != 'jpeg' else 'jpg'}"
                    process_side_by_side(
                        pending_vertical,
                        dst_path,
                        bg_color,
                        target_w,
                        target_h,
                        output_format,
                        args.quality,
                        resize_mode,
                    )
                    count += 1
                    pending_vertical = []
            else:
                dst_dir = output_dir / rel_dir
                dst_dir.mkdir(parents=True, exist_ok=True)
                dst_path = dst_dir / f"{item.stem}.{output_format if output_format != 'jpeg' else 'jpg'}"
                process_image(item, dst_path, bg_color, target_w, target_h, output_format, args.quality, resize_mode)
                count += 1

        if pending_vertical:
            if len(pending_vertical) == 1:
                dst_dir = output_dir / (pending_rel_dir or Path("."))
                dst_dir.mkdir(parents=True, exist_ok=True)
                dst_path = dst_dir / f"{pending_vertical[0].stem}.{output_format if output_format != 'jpeg' else 'jpg'}"
                process_image(
                    pending_vertical[0],
                    dst_path,
                    bg_color,
                    target_w,
                    target_h,
                    output_format,
                    args.quality,
                    resize_mode,
                )
            else:
                dst_dir = output_dir / (pending_rel_dir or Path("."))
                dst_dir.mkdir(parents=True, exist_ok=True)
                dst_path = dst_dir / f"{'__'.join(p.stem for p in pending_vertical)}.{output_format if output_format != 'jpeg' else 'jpg'}"
                process_side_by_side(
                    pending_vertical,
                    dst_path,
                    bg_color,
                    target_w,
                    target_h,
                    output_format,
                    args.quality,
                    resize_mode,
                )
            count += 1
    else:
        for item, rel_dir, _, _ in valid_files:
            dst_dir = output_dir / rel_dir
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_dir / f"{item.stem}.{output_format if output_format != 'jpeg' else 'jpg'}"
            process_image(item, dst_path, bg_color, target_w, target_h, output_format, args.quality, resize_mode)
            count += 1

    print(f"Elaborate: {count}")
    print(f"Saltate (non immagini o file non leggibili): {skipped}")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
