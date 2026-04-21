"""
WebCompass Evaluation Framework

A unified evaluation framework for web generation tasks across multiple modalities:
- Text-to-Web: Generate web pages from text descriptions
- Image-to-Web: Generate web pages from reference screenshots
- Video-to-Web: Generate web pages from video demonstrations

"""

__version__ = "1.0.0"
__author__ = "WebCompass Team"

from .inference import (
    TextToWebGenerator,
    ImageToWebGenerator,
    VideoToWebGenerator,
)
from .utils import parse_and_save_markdown, load_jsonl, append_jsonl
from .call_model import call_api, call_api_stream, create_client
from .checklist import (
    generate_text_checklist,
    generate_image_checklist,
    generate_video_checklist,
    TextChecklistGenerator,
    ImageChecklistGenerator,
    VideoChecklistGenerator,
)

__all__ = [
    # Inference
    "TextToWebGenerator",
    "ImageToWebGenerator",
    "VideoToWebGenerator",
    # Utilities
    "parse_and_save_markdown",
    "load_jsonl",
    "append_jsonl",
    # Model API
    "call_api",
    "call_api_stream",
    "create_client",
    # Checklist Generation
    "generate_text_checklist",
    "generate_image_checklist",
    "generate_video_checklist",
    "TextChecklistGenerator",
    "ImageChecklistGenerator",
    "VideoChecklistGenerator",
]
