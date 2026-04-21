"""
Utility functions for WebCompass evaluation.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List


def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    """Load a JSONL file and return a list of dictionaries."""
    items: List[Dict[str, Any]] = []
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    """Append a dictionary to a JSONL file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def parse_and_save_markdown(markdown_text: str, repo_path: str) -> int:
    """Parse Markdown output with file blocks and save to disk.

    Expected format (repeated N times):
    # path/to/file.ext
    ```lang
    ...content...
    ```

    Args:
        markdown_text: The raw markdown response from the model.
        repo_path: Target directory to write files.

    Returns:
        Number of files written.
    """
    text = markdown_text.strip("\n")

    pattern = (
        r"^#\s+([^\n]+)\n"  # file path
        r"(?:\s*\n)*"        # optional blank lines
        r"```([^\n`]*)\n"    # language (optional)
        r"(.*?)\n```\s*(?:\n|$)"  # content
    )

    matches = re.findall(pattern, text, flags=re.DOTALL | re.MULTILINE)
    count = 0
    for file_path, _lang, content in matches:
        file_path = file_path.strip()
        if not file_path:
            continue

        abs_path = os.path.join(repo_path, file_path)
        os.makedirs(os.path.dirname(abs_path) or repo_path, exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1
    return count


def atomic_mark_done(repo_path: str) -> None:
    """Create a .done marker file to indicate successful generation."""
    marker = os.path.join(repo_path, ".done")
    tmp = marker + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("ok\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, marker)


def is_done(repo_path: str) -> bool:
    """Check if a repo has been successfully generated."""
    return os.path.exists(os.path.join(repo_path, ".done"))


def list_image_paths(dir_path: Path, max_images: int = 30) -> List[str]:
    """List image files in a directory, sorted by name.

    Args:
        dir_path: Directory to scan.
        max_images: Maximum number of images to return (-1 for unlimited).

    Returns:
        List of absolute paths to image files.
    """
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    files = [p for p in dir_path.iterdir() if p.is_file() and p.suffix.lower() in exts]
    files = sorted(files, key=lambda p: p.name)
    if max_images > 0:
        files = files[:max_images]
    return [str(p.resolve()) for p in files]
