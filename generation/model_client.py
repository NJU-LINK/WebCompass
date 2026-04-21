"""
Model client abstraction for WebCompass evaluation.

Supports multiple backends:
- OpenAI-compatible APIs (default)
- Custom model endpoints
"""

import os
import base64
from typing import List, Optional, Tuple
from openai import OpenAI


def encode_file_base64(file_path: str) -> str:
    """Encode a file to base64 string."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class ModelClient:
    """Unified model client supporting text and multimodal inputs."""

    # Default model configurations (can be overridden)
    MODEL_CONFIGS = {
        # Example configurations - users should add their own
        "gpt-4o": {
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "model_id": "gpt-4o",
        },
        "claude-sonnet": {
            "base_url": "https://api.anthropic.com/v1",
            "api_key_env": "ANTHROPIC_API_KEY",
            "model_id": "claude-sonnet-4-20250514",
        },
        # Qwen models via DashScope
        "qwen3.6-plus": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "***REMOVED***",
            "model_id": "qwen3.6-plus",
        },
    }

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        """Initialize the model client.

        Args:
            model: Model name (key in MODEL_CONFIGS or custom name).
            base_url: Override base URL.
            api_key: Override API key.
            model_id: Override model ID for the API call.
        """
        self.model = model

        # Try to get config from MODEL_CONFIGS
        config = self.MODEL_CONFIGS.get(model, {})

        self.base_url = base_url or config.get("base_url")
        self.model_id = model_id or config.get("model_id", model)

        # Get API key from parameter, config, or environment
        if api_key:
            self.api_key = api_key
        elif config.get("api_key"):
            self.api_key = config["api_key"]
        elif config.get("api_key_env"):
            self.api_key = os.environ.get(config["api_key_env"], "")
        else:
            self.api_key = os.environ.get("OPENAI_API_KEY", "")

        if not self.base_url:
            raise ValueError(f"No base_url configured for model: {model}")

        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    @classmethod
    def register_model(
        cls,
        name: str,
        base_url: str,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        """Register a new model configuration.

        Args:
            name: Model name to register.
            base_url: API base URL.
            api_key: Direct API key (not recommended for security).
            api_key_env: Environment variable name for API key.
            model_id: Model ID to use in API calls.
        """
        cls.MODEL_CONFIGS[name] = {
            "base_url": base_url,
            "api_key": api_key,
            "api_key_env": api_key_env,
            "model_id": model_id or name,
        }

    def _build_user_content(
        self,
        prompt: str,
        video_path: Optional[str] = None,
        image_path: Optional[List[str] | str] = None,
    ) -> List[dict]:
        """Build OpenAI-compatible multimodal user content."""
        user_messages = [{"type": "text", "text": prompt}]

        if video_path:
            b64_vid = encode_file_base64(video_path)
            user_messages.append(
                {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64_vid}"}}
            )

        if image_path:
            paths = image_path if isinstance(image_path, (list, tuple)) else [image_path]
            for p in paths:
                b64_img = encode_file_base64(p)
                # Determine MIME type from extension
                ext = p.lower().split(".")[-1]
                mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
                mime = mime_map.get(ext, "image/png")
                user_messages.append(
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_img}"}}
                )

        return user_messages

    def call(
        self,
        prompt: str,
        video_path: Optional[str] = None,
        image_path: Optional[List[str] | str] = None,
        stream: bool = False,
    ) -> str:
        """Call the model with optional multimodal inputs.

        Args:
            prompt: Text prompt.
            video_path: Optional path to video file.
            image_path: Optional path(s) to image file(s).
            stream: Whether to stream the response.

        Returns:
            Model response as a string.
        """
        user_messages = self._build_user_content(prompt, video_path=video_path, image_path=image_path)

        if stream:
            return self._call_stream(user_messages)
        else:
            response = self._client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": user_messages}],
            )
            return response.choices[0].message.content or ""

    def _call_stream(self, user_messages: List[dict]) -> str:
        """Internal streaming call implementation."""
        stream = self._client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": user_messages}],
            stream=True,
        )

        pieces = []
        for event in stream:
            try:
                choice0 = event.choices[0]
            except Exception:
                continue

            delta = getattr(choice0, "delta", None)
            if delta is not None:
                chunk = getattr(delta, "content", None)
                if chunk:
                    pieces.append(chunk)
                    continue

            msg = getattr(choice0, "message", None)
            if msg is not None:
                chunk = getattr(msg, "content", None)
                if chunk:
                    pieces.append(chunk)

        return "".join(pieces)
