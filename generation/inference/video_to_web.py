"""
Video-to-Web Generator

Generate web pages from video demonstrations by extracting frames
and using multimodal models to understand the UI/interactions.
"""

import os
import time
import glob
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..model_client import ModelClient
from ..prompts import VIDEO_TO_WEB_PROMPT
from ..utils import parse_and_save_markdown, atomic_mark_done, is_done


class VideoFrameExtractor:
    """Extract frames from video files using ffmpeg."""

    def __init__(
        self,
        target_fps: float = 3.0,
        max_frames: int = 60,
        output_format: str = "jpg",
        image_quality: int = 95,
    ):
        """Initialize the frame extractor.

        Args:
            target_fps: Target frames per second to extract.
            max_frames: Maximum number of frames to extract.
            output_format: Output image format (jpg, png).
            image_quality: JPEG quality (1-100).
        """
        self.target_fps = target_fps
        self.max_frames = max_frames
        self.output_format = output_format
        self.image_quality = image_quality

    def extract_frames(self, video_path: str, output_dir: str) -> List[str]:
        """Extract frames from a video file.

        Args:
            video_path: Path to the input video.
            output_dir: Directory to save extracted frames.

        Returns:
            List of paths to extracted frame images.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Get video duration
        probe_cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
        except Exception:
            duration = 60.0  # Default fallback

        # Calculate fps to stay within max_frames
        total_frames_at_target = int(duration * self.target_fps)
        if total_frames_at_target > self.max_frames:
            actual_fps = self.max_frames / duration
        else:
            actual_fps = self.target_fps

        # Build ffmpeg command
        output_pattern = os.path.join(output_dir, f"frame_%04d.{self.output_format}")

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={actual_fps}",
            "-q:v", str(max(1, min(31, int((100 - self.image_quality) * 31 / 100)))),
            "-y",  # Overwrite
            output_pattern,
        ]

        try:
            subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}")

        # Collect extracted frames
        frames = sorted(glob.glob(os.path.join(output_dir, f"frame_*.{self.output_format}")))

        # Limit to max_frames
        if len(frames) > self.max_frames:
            frames = frames[: self.max_frames]

        return frames


class VideoToWebGenerator:
    """Generate web repositories from video demonstrations."""

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        max_retries: int = 5,
        target_fps: float = 3.0,
        max_frames: int = 60,
    ):
        """Initialize the generator.

        Args:
            model: Model name.
            base_url: Override base URL.
            api_key: Override API key.
            model_id: Override model ID.
            max_retries: Maximum retry attempts on failure.
            target_fps: Target frames per second for extraction.
            max_frames: Maximum number of frames to use.
        """
        self.client = ModelClient(
            model=model,
            base_url=base_url,
            api_key=api_key,
            model_id=model_id,
        )
        self.max_retries = max_retries
        self.frame_extractor = VideoFrameExtractor(
            target_fps=target_fps,
            max_frames=max_frames,
        )

    def _downsample_frames(self, frame_paths: List[str], target_count: int) -> List[str]:
        """Uniformly sample frames to reduce count."""
        if target_count <= 0 or target_count >= len(frame_paths):
            return list(frame_paths)

        total = len(frame_paths)
        indices = [int(i * total / target_count) for i in range(target_count)]
        return [frame_paths[i] for i in indices]

    def generate(
        self,
        video_path: str,
        output_dir: str,
        skip_if_done: bool = True,
    ) -> Dict[str, Any]:
        """Generate a web repository from a video.

        Args:
            video_path: Path to the input video.
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

        if not os.path.exists(video_path):
            return {
                "status": "error",
                "repo_path": output_dir,
                "error": f"Video not found: {video_path}",
                "count": 0,
            }

        os.makedirs(output_dir, exist_ok=True)

        # Extract frames
        frames_dir = os.path.join(output_dir, "frames")
        try:
            frame_paths = self.frame_extractor.extract_frames(video_path, frames_dir)
        except Exception as e:
            return {
                "status": "error",
                "repo_path": output_dir,
                "error": f"Frame extraction failed: {e}",
                "count": 0,
            }

        if not frame_paths:
            return {
                "status": "error",
                "repo_path": output_dir,
                "error": "No frames extracted",
                "count": 0,
            }

        # Generate with retries
        current_frames = list(frame_paths)
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.call(
                    VIDEO_TO_WEB_PROMPT,
                    image_path=current_frames,
                )

                if not response or len(response) < 1000:
                    last_error = f"Response too short: {len(response)} chars"
                    time.sleep(min((attempt + 1) * 3, 15))
                    continue

                count = parse_and_save_markdown(response, output_dir)

                if count == 0:
                    last_error = "No files parsed from response"
                    time.sleep(min((attempt + 1) * 3, 15))
                    continue

                atomic_mark_done(output_dir)
                return {
                    "status": "ok",
                    "repo_path": output_dir,
                    "count": count,
                    "frames_used": len(current_frames),
                }

            except Exception as e:
                error_text = str(e).lower()
                last_error = f"{type(e).__name__}: {e}"

                # Handle message size limits by reducing frames
                if any(kw in error_text for kw in ["message size", "too large", "limit", "exceeds"]):
                    if len(current_frames) > 12:
                        target_count = max(12, int(len(current_frames) * 0.7))
                        current_frames = self._downsample_frames(current_frames, target_count)
                        continue

                if "too many images" in error_text:
                    if len(current_frames) > 30:
                        target_count = min(30, int(len(current_frames) * 0.7))
                        current_frames = self._downsample_frames(current_frames, target_count)
                        continue

                if attempt < self.max_retries - 1:
                    time.sleep(min((attempt + 1) * 3, 15))

        return {
            "status": "error",
            "repo_path": output_dir,
            "error": last_error,
            "count": 0,
        }

    def generate_from_video_file(
        self,
        video_path: str,
        output_base_dir: str,
    ) -> Dict[str, Any]:
        """Generate from a video file, using filename as instance ID.

        Args:
            video_path: Path to the video file.
            output_base_dir: Base directory for outputs.

        Returns:
            Result dict with id, status, repo_path, etc.
        """
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(output_base_dir, video_name)

        result = self.generate(video_path, output_dir)
        result["id"] = video_name
        result["video_path"] = video_path
        result["timestamp"] = datetime.now().isoformat()
        return result
