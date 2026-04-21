"""
Inference module for WebCompass evaluation.

Provides generators for three modalities:
- TextToWebGenerator: Generate web pages from text descriptions
- ImageToWebGenerator: Generate web pages from reference screenshots
- VideoToWebGenerator: Generate web pages from video demonstrations
"""

from .text_to_web import TextToWebGenerator
from .image_to_web import ImageToWebGenerator
from .video_to_web import VideoToWebGenerator

__all__ = [
    "TextToWebGenerator",
    "ImageToWebGenerator",
    "VideoToWebGenerator",
]
