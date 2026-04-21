"""
Image-to-Web Generator

Generate web pages from reference screenshots.
"""

import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..model_client import ModelClient
from ..prompts import IMAGE_TO_WEB_PROMPT
from ..utils import parse_and_save_markdown, atomic_mark_done, is_done, list_image_paths


class ImageToWebGenerator:
    """Generate web repositories from reference screenshots."""

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        max_retries: int = 3,
        max_images: int = 30,
    ):
        """Initialize the generator.

        Args:
            model: Model name.
            base_url: Override base URL.
            api_key: Override API key.
            model_id: Override model ID.
            max_retries: Maximum retry attempts on failure.
            max_images: Maximum number of images to send per request.
        """
        self.client = ModelClient(
            model=model,
            base_url=base_url,
            api_key=api_key,
            model_id=model_id,
        )
        self.max_retries = max_retries
        self.max_images = max_images

    def _build_document(
        self,
        instance_id: str,
        screenshot_paths: List[str],
    ) -> str:
        """Build a web design document from screenshots only.

        Note: Checklist is NOT included in the prompt - it's only used for evaluation.
        The model should generate the website based purely on the reference screenshots.

        Args:
            instance_id: Instance identifier.
            screenshot_paths: List of screenshot file paths.

        Returns:
            Formatted document string.
        """
        screenshot_names = [Path(p).name for p in screenshot_paths]
        names_block = "\n".join([f"- {n}" for n in screenshot_names])

        return (
            "# Goal\n"
            "Generate a runnable website that matches the provided reference screenshots as closely as possible.\n\n"
            f"# Instance\n{instance_id}\n\n"
            "# Reference screenshots (sorted)\n"
            f"{names_block}\n\n"
            "# Instructions\n"
            "Study the reference screenshots carefully and implement:\n"
            "- The exact visual layout, colors, typography, and spacing shown\n"
            "- All UI components visible in the screenshots\n"
            "- Any interactive elements implied by the design (buttons, forms, navigation, etc.)\n"
            "- Responsive behavior if multiple viewport sizes are shown\n"
        )

    def _resolve_screenshots_dir(self, images_root: Path, instruction: str) -> Path:
        """Resolve the screenshots directory for an instance.

        Supports:
        - <images_root>/<instruction>/screenshots
        - <images_root>/<instruction>
        """
        base = (images_root / instruction).resolve()
        cand = base / "screenshots"
        if cand.exists() and cand.is_dir():
            return cand
        return base

    def _copy_screenshots(self, src_dir: Path, repo_path: str) -> None:
        """Copy screenshots to the output repository."""
        if not src_dir.exists() or not src_dir.is_dir():
            return
        dest_dir = Path(repo_path) / "screenshots"
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)

    def generate(
        self,
        document: str,
        image_paths: List[str],
        output_dir: str,
        skip_if_done: bool = True,
    ) -> Dict[str, Any]:
        """Generate a web repository from document and images.

        Args:
            document: Web design document text.
            image_paths: List of screenshot paths.
            output_dir: Target directory to write files.
            skip_if_done: Skip if already successfully generated.

        Returns:
            Dict with status, repo_path, count, and optional error.
        """
        if skip_if_done and is_done(output_dir):
            return {
                "status": "skipped",
                "repo_path": output_dir,
                "message": "Already completed",
            }

        if not image_paths:
            return {
                "status": "error",
                "repo_path": output_dir,
                "error": "No images provided",
                "count": 0,
            }

        os.makedirs(output_dir, exist_ok=True)

        prompt = IMAGE_TO_WEB_PROMPT.format(document=document)

        # Limit images if needed
        images_to_send = image_paths
        if self.max_images > 0 and len(image_paths) > self.max_images:
            images_to_send = image_paths[: self.max_images]

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.call(prompt, image_path=images_to_send)

                if not response or len(response) < 500:
                    last_error = "Response too short"
                    time.sleep(0.8 * (2 ** attempt))
                    continue

                count = parse_and_save_markdown(response, output_dir)

                if count == 0:
                    last_error = "No files parsed from response"
                    time.sleep(0.8 * (2 ** attempt))
                    continue

                atomic_mark_done(output_dir)
                return {
                    "status": "ok",
                    "repo_path": output_dir,
                    "count": count,
                }

            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                if attempt < self.max_retries - 1:
                    time.sleep(0.8 * (2 ** attempt))

        return {
            "status": "error",
            "repo_path": output_dir,
            "error": last_error,
            "count": 0,
        }

    def generate_from_item(
        self,
        item: Dict[str, Any],
        images_root: str,
        output_base_dir: str,
        id_key: str = "instance_id",
        instruction_key: str = "instruction",
    ) -> Dict[str, Any]:
        """Generate from a dataset item.

        Note: Checklist is NOT used during generation - only for evaluation later.

        Args:
            item: Dataset item with ID.
            images_root: Root directory containing screenshot folders.
            output_base_dir: Base directory for outputs.
            id_key: Key for the instance ID field.
            instruction_key: Key for the instruction (folder name) field.

        Returns:
            Result dict with id, status, repo_path, etc.
        """
        instance_id = str(item.get(id_key, "unknown"))
        instruction = str(item.get(instruction_key) or instance_id)

        output_dir = os.path.join(output_base_dir, instance_id)
        images_root_path = Path(images_root)
        screenshots_dir = self._resolve_screenshots_dir(images_root_path, instruction)
        image_paths = list_image_paths(screenshots_dir, max_images=self.max_images)

        if not image_paths:
            return {
                "id": instance_id,
                "status": "error",
                "repo_path": output_dir,
                "error": f"No images found under: {screenshots_dir}",
                "count": 0,
                "timestamp": datetime.now().isoformat(),
            }

        document = self._build_document(instance_id, image_paths)
        result = self.generate(document, image_paths, output_dir)
        result["id"] = instance_id
        result["timestamp"] = datetime.now().isoformat()

        # Copy screenshots to output
        if result.get("status") == "ok":
            self._copy_screenshots(screenshots_dir, output_dir)

        return result
