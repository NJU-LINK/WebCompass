"""
Text-to-Web Generator

Generate web pages from text descriptions (design documents).
"""

import os
import time
import shutil
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from ..model_client import ModelClient
from ..prompts import TEXT_TO_WEB_PROMPT
from ..utils import parse_and_save_markdown, atomic_mark_done, is_done


class TextToWebGenerator:
    """Generate web repositories from text design documents."""

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        max_retries: int = 3,
    ):
        """Initialize the generator.

        Args:
            model: Model name.
            base_url: Override base URL.
            api_key: Override API key.
            model_id: Override model ID.
            max_retries: Maximum retry attempts on failure.
        """
        self.client = ModelClient(
            model=model,
            base_url=base_url,
            api_key=api_key,
            model_id=model_id,
        )
        self.max_retries = max_retries

    def generate(
        self,
        document: str,
        output_dir: str,
        skip_if_done: bool = True,
    ) -> Dict[str, Any]:
        """Generate a web repository from a text document.

        Args:
            document: Web design document text.
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

        os.makedirs(output_dir, exist_ok=True)

        prompt = TEXT_TO_WEB_PROMPT.format(document=document)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.call(prompt)

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

        # All retries failed
        return {
            "status": "error",
            "repo_path": output_dir,
            "error": last_error,
            "count": 0,
        }

    def generate_from_item(
        self,
        item: Dict[str, Any],
        output_base_dir: str,
        instruction_key: str = "instruction",
        id_key: str = "instance_id",
    ) -> Dict[str, Any]:
        """Generate from a dataset item (dict).

        Args:
            item: Dataset item with instruction and ID.
            output_base_dir: Base directory for outputs.
            instruction_key: Key for the instruction/document field.
            id_key: Key for the instance ID field.

        Returns:
            Result dict with id, status, repo_path, etc.
        """
        instance_id = str(item.get(id_key, "unknown"))
        document = item.get(instruction_key, "")
        output_dir = os.path.join(output_base_dir, instance_id)

        result = self.generate(document, output_dir)
        result["id"] = instance_id
        result["timestamp"] = datetime.now().isoformat()
        return result
