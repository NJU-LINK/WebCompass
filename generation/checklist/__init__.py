"""
WebCompass Checklist Generation Module

Provides tools for generating evaluation checklists from different input modalities:
- Text-to-Web: Generate checklists from text design documents
- Image-to-Web: Generate checklists from reference screenshots
- Video-to-Web: Generate checklists from video demonstrations
"""

from .generator import (
    generate_text_checklist,
    generate_image_checklist,
    generate_video_checklist,
    TextChecklistGenerator,
    ImageChecklistGenerator,
    VideoChecklistGenerator,
)
from .prompts import (
    TEXT_CHECKLIST_PROMPT,
    IMAGE_CHECKLIST_PROMPT,
)

__all__ = [
    "generate_text_checklist",
    "generate_image_checklist",
    "generate_video_checklist",
    "TextChecklistGenerator",
    "ImageChecklistGenerator",
    "VideoChecklistGenerator",
    "TEXT_CHECKLIST_PROMPT",
    "IMAGE_CHECKLIST_PROMPT",
]
