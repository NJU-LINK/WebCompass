"""Download editing/repair subsets from HF and reconstruct local FullDataset_HTML layout.

HF layout (snapshot_download root):
  editing/{sp,mp}/data.jsonl
  editing/{sp,mp}/{instance_id}/src/...
  repair/{sp,mp}/data.jsonl
  repair/{sp,mp}/{instance_id}/{src,dst}/...

Reconstructed local layout (what eval.py expects via --base-path):
  {out_root}/{edit,repair}/{sp,mp}/{instance_id}/info.json
  {out_root}/{edit,repair}/{sp,mp}/{instance_id}/{src,dst}/...

Usage:
    python scripts/download_from_hf.py --out-root ../../data
    python scripts/download_from_hf.py --from-local ../../HF_upload --out-root ../../data
"""

import argparse
import json
import os
import shutil
from pathlib import Path

CONFIG_TO_TASK = {"editing": "edit", "repair": "repair"}
PAGE_TYPES = ["sp", "mp"]
HF_REPO_ID = "NJU-LINK/WebCompass"


def download_snapshot(repo_id: str, cache_dir: Path) -> Path:
    from huggingface_hub import snapshot_download

    print(f"snapshot_download({repo_id!r}) → {cache_dir}")
    local = snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        allow_patterns=[
            "editing/**",
            "repair/**",
        ],
        local_dir=str(cache_dir),
    )
    return Path(local)


def reconstruct_bucket(hf_root: Path, out_root: Path, config: str, page_type: str, link: bool) -> int:
    task = CONFIG_TO_TASK[config]
    src_bucket = hf_root / config / page_type
    jsonl_path = src_bucket / "data.jsonl"
    if not jsonl_path.exists():
        print(f"  skip {config}/{page_type}: no data.jsonl at {jsonl_path}")
        return 0

    dst_bucket = out_root / task / page_type
    dst_bucket.mkdir(parents=True, exist_ok=True)

    rows = 0
    with jsonl_path.open("r", encoding="utf-8") as fin:
        for line in fin:
            row = json.loads(line)
            instance_id = row.pop("instance_id")
            dst_case = dst_bucket / instance_id
            if dst_case.exists():
                shutil.rmtree(dst_case)
            dst_case.mkdir(parents=True)

            (dst_case / "info.json").write_text(
                json.dumps(row, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            for sub in ("src", "dst"):
                src_sub = src_bucket / instance_id / sub
                if not src_sub.exists():
                    continue
                dst_sub = dst_case / sub
                if link:
                    os.symlink(src_sub.resolve(), dst_sub)
                else:
                    shutil.copytree(src_sub, dst_sub)

            rows += 1

    print(f"  {task}/{page_type}: reconstructed {rows} cases → {dst_bucket}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-root",
        default="../../data",
        help="Local output root (will contain edit/ and repair/ subdirectories)",
    )
    parser.add_argument(
        "--from-local",
        default=None,
        help="Skip HF download; use this local HF-layout root (e.g. ../../HF_upload for round-trip test)",
    )
    parser.add_argument(
        "--repo-id",
        default=HF_REPO_ID,
        help="HuggingFace dataset repo id (ignored if --from-local is set)",
    )
    parser.add_argument(
        "--cache-dir",
        default="../../hf_cache",
        help="Where snapshot_download stores files (ignored if --from-local is set)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy assets instead of symlinking (default: symlink to save space)",
    )
    args = parser.parse_args()

    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if args.from_local:
        hf_root = Path(args.from_local).resolve()
        print(f"Using local HF layout: {hf_root}")
    else:
        hf_root = download_snapshot(args.repo_id, Path(args.cache_dir).resolve())

    link = not args.copy
    if link and args.from_local is None:
        print("note: assets will be symlinked from the HF cache; pass --copy to materialize them")

    total = 0
    for config in CONFIG_TO_TASK:
        for page_type in PAGE_TYPES:
            total += reconstruct_bucket(hf_root, out_root, config, page_type, link)
    print(f"\nTotal cases reconstructed: {total} → {out_root}")


if __name__ == "__main__":
    main()
