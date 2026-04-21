#!/usr/bin/env python3
"""
Batch-convert PDF files to PNG images.

Default behavior:
- Input directory:  Paper/figures
- Output directory: same as input
- Resolution:       300 DPI

Dependency:
    pip install pypdfium2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch convert PDF files to PNG files."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        default="Paper/figures",
        help="Directory containing PDF files. Default: Paper/figures",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directory to write PNG files. Default: same as input directory",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Render resolution in DPI. Default: 300",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PNG files.",
    )
    parser.add_argument(
        "--first-page-only",
        action="store_true",
        help="Only convert the first page of each PDF.",
    )
    return parser.parse_args()


def convert_pdf_file(
    pdf_path: Path,
    output_dir: Path,
    scale: float,
    overwrite: bool,
    first_page_only: bool,
) -> tuple[int, int]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    page_count = len(pdf)
    if page_count == 0:
        return 0, 0

    pages_to_convert = 1 if first_page_only else page_count
    saved = 0

    for page_index in range(pages_to_convert):
        page = pdf[page_index]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()

        if pages_to_convert == 1:
            out_name = f"{pdf_path.stem}.png"
        else:
            out_name = f"{pdf_path.stem}-p{page_index + 1}.png"
        out_path = output_dir / out_name

        if out_path.exists() and not overwrite:
            print(f"Skip existing: {out_path}")
            continue

        image.save(out_path, format="PNG")
        saved += 1
        print(f"Saved: {out_path}")

    return saved, pages_to_convert


def main() -> int:
    args = parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else input_dir

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dpi <= 0:
        print("--dpi must be a positive integer.", file=sys.stderr)
        return 1
    scale = args.dpi / 72.0

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in: {input_dir}")
        return 0

    try:
        import pypdfium2  # noqa: F401
    except ImportError:
        print(
            "Missing dependency: pypdfium2\n"
            "Install with: pip install pypdfium2",
            file=sys.stderr,
        )
        return 2

    total_saved = 0
    total_candidates = 0

    for pdf_path in pdf_files:
        saved, candidates = convert_pdf_file(
            pdf_path=pdf_path,
            output_dir=output_dir,
            scale=scale,
            overwrite=args.overwrite,
            first_page_only=args.first_page_only,
        )
        total_saved += saved
        total_candidates += candidates

    print(
        f"\nDone. PDFs: {len(pdf_files)}, "
        f"target pages: {total_candidates}, "
        f"newly saved PNGs: {total_saved}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
