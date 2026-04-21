"""
Checklist generators for text, image, and video modalities.

Each generator calls an LLM to produce a structured checklist with three dimensions:
- Runnability
- Spec Implementation
- Design Quality
"""

from __future__ import annotations

import json
import re
import concurrent.futures
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .prompts import TEXT_CHECKLIST_PROMPT, IMAGE_CHECKLIST_PROMPT, VIDEO_CHECKLIST_PROMPT


# Image extensions for multimodal input
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def parse_json_output(output: str) -> Optional[List[Dict[str, Any]]]:
    """Extract JSON array from LLM output (handles ```json blocks)."""
    if not output:
        return None

    # Try to find ```json block first
    match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            result = json.loads(json_str)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Fallback: find first '[' and last ']'
    left = output.find("[")
    right = output.rfind("]")
    if left != -1 and right != -1 and right > left:
        try:
            result = json.loads(output[left:right + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return None


@dataclass(frozen=True)
class ImageInfo:
    """Information about a reference image."""
    filename: str
    path: str


def list_images(screenshots_dir: Path, max_images: int = 30) -> List[ImageInfo]:
    """List images in a directory, sorted by filename."""
    if not screenshots_dir.exists() or not screenshots_dir.is_dir():
        return []

    files = [
        p for p in screenshots_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    files = sorted(files, key=lambda p: p.name)

    if max_images > 0:
        files = files[:max_images]

    return [ImageInfo(filename=p.name, path=str(p.resolve())) for p in files]


def generate_text_checklist(
    query: str,
    model: str = "Gemini-3-Pro",
    call_api: Optional[Callable[..., str]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Generate checklist from a text design document.

    Args:
        query: The text design document/instruction
        model: Model name to use for generation
        call_api: Optional custom API caller (defaults to generation.call_model.call_api)

    Returns:
        List of checklist items or None if generation fails
    """
    if call_api is None:
        from generation.call_model import call_api

    prompt = TEXT_CHECKLIST_PROMPT.replace("[QUERY]", query)
    response = call_api(prompt, model=model)
    return parse_json_output(response)


def generate_image_checklist(
    image_paths: List[str],
    model: str = "Gemini-3-Pro",
    call_api: Optional[Callable[..., str]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Generate checklist from reference screenshots.

    Args:
        image_paths: List of paths to reference screenshot images
        model: Model name to use for generation
        call_api: Optional custom API caller (defaults to generation.call_model.call_api)

    Returns:
        List of checklist items or None if generation fails
    """
    if call_api is None:
        from generation.call_model import call_api

    # Build filename list for the prompt
    filenames = [Path(p).name for p in image_paths]
    fn_list = "\n".join([f"- {fn}" for fn in filenames])

    prompt = IMAGE_CHECKLIST_PROMPT.replace("[SCREENSHOT_FILENAMES]", fn_list)
    response = call_api(prompt, model=model, image_path=image_paths)
    return parse_json_output(response)


def generate_video_checklist(
    query: str,
    model: str = "Gemini-3-Pro",
    call_api: Optional[Callable[..., str]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Generate checklist from a video description.

    Note: Video frames should be pre-processed into a text description
    before calling this function.

    Args:
        query: Text description derived from video content
        model: Model name to use for generation
        call_api: Optional custom API caller

    Returns:
        List of checklist items or None if generation fails
    """
    # Video uses the same logic as text
    return generate_text_checklist(query, model=model, call_api=call_api)


class TextChecklistGenerator:
    """Generator for text-to-web checklists with batch processing support."""

    def __init__(
        self,
        model: str = "Gemini-3-Pro",
        max_workers: int = 10,
    ):
        self.model = model
        self.max_workers = max_workers

    def generate(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Generate a single checklist."""
        return generate_text_checklist(query, model=self.model)

    def generate_batch(
        self,
        items: List[Dict[str, Any]],
        instruction_key: str = "instruction",
        output_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Generate checklists for multiple items in parallel.

        Args:
            items: List of dicts containing instructions
            instruction_key: Key to extract instruction from each item
            output_path: Optional path to write results as JSONL

        Returns:
            List of items with 'checklist' field added
        """
        def process_item(idx: int, item: Dict[str, Any]) -> Dict[str, Any]:
            instruction = item.get(instruction_key) or item.get("webdoc_combined") or ""
            checklist = self.generate(instruction) if instruction else None
            result = dict(item)
            result["id"] = idx
            result["checklist"] = checklist
            return result

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_item, idx, item): idx
                for idx, item in enumerate(items, start=1)
            }
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        results.sort(key=lambda x: x["id"])

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                for item in results:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

        return results


class ImageChecklistGenerator:
    """Generator for image-to-web checklists with batch processing support."""

    def __init__(
        self,
        model: str = "Gemini-3-Pro",
        max_images: int = 30,
        max_workers: int = 4,
    ):
        self.model = model
        self.max_images = max_images
        self.max_workers = max_workers

    def generate(self, screenshots_dir: Path) -> Optional[List[Dict[str, Any]]]:
        """Generate checklist from a screenshots directory."""
        images = list_images(screenshots_dir, self.max_images)
        if not images:
            return None

        image_paths = [img.path for img in images]
        return generate_image_checklist(image_paths, model=self.model)

    def generate_from_paths(self, image_paths: List[str]) -> Optional[List[Dict[str, Any]]]:
        """Generate checklist from explicit image paths."""
        return generate_image_checklist(image_paths, model=self.model)

    def generate_batch(
        self,
        image_data_root: Path,
        output_root: Path,
        force: bool = False,
    ) -> List[Dict[str, Any]]:
        """Generate checklists for all subdirectories in batch.

        Args:
            image_data_root: Root directory containing subdirectories with screenshots
            output_root: Output directory for results
            force: If True, regenerate even if output exists

        Returns:
            List of generated records
        """
        global_jsonl = output_root / "checklist.jsonl"

        subdirs = [
            p for p in image_data_root.iterdir()
            if p.is_dir() and not p.name.startswith('.')
        ]
        subdirs = sorted(subdirs, key=lambda p: p.name)

        if not force:
            existing_ids = set()
            if global_jsonl.exists():
                with global_jsonl.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            existing_ids.add(str(rec.get("instance_id")))
                        except Exception:
                            continue
            subdirs = [sd for sd in subdirs if sd.name not in existing_ids]

        results = []

        def process_sample(sample_dir: Path) -> Optional[Dict[str, Any]]:
            # Find screenshots directory
            screenshots_dir = sample_dir / "screenshots"
            if not screenshots_dir.exists():
                screenshots_dir = sample_dir

            checklist = self.generate(screenshots_dir)
            if checklist is None:
                return None

            record = {
                "meta": {"class": "image_generation", "difficulty": "N/A"},
                "working_dir": "/testbed",
                "repo": "claude/webcoding",
                "instance_id": sample_dir.name,
                "base_commit": "main",
                "problem_statement": checklist,
                "instruction": sample_dir.name,
            }
            return record

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_sample, sd): sd.name
                for sd in subdirs
            }
            for future in concurrent.futures.as_completed(futures):
                sample_id = futures[future]
                try:
                    record = future.result()
                    if record:
                        results.append(record)
                        # Append to global JSONL
                        global_jsonl.parent.mkdir(parents=True, exist_ok=True)
                        with global_jsonl.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        print(f"[{sample_id}] OK -> {global_jsonl}")
                except Exception as e:
                    print(f"[{sample_id}] ERROR: {e}")

        return results


class VideoChecklistGenerator:
    """Generator for video-to-web checklists.

    Note: This is essentially the same as TextChecklistGenerator since
    video frames are expected to be pre-processed into text descriptions.
    """

    def __init__(
        self,
        model: str = "Gemini-3-Pro",
        max_workers: int = 10,
    ):
        self.model = model
        self.max_workers = max_workers
        self._text_generator = TextChecklistGenerator(model=model, max_workers=max_workers)

    def generate(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Generate a single checklist from video description."""
        return generate_video_checklist(query, model=self.model)

    def generate_batch(
        self,
        items: List[Dict[str, Any]],
        instruction_key: str = "instruction",
        output_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Generate checklists for multiple items in parallel."""
        return self._text_generator.generate_batch(
            items,
            instruction_key=instruction_key,
            output_path=output_path,
        )
