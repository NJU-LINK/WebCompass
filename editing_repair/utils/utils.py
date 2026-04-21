import os
import base64
import cairosvg
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI
import traceback
import shutil
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from utils.config import CODE_EXTENSIONS
from utils.webhandler import save_screenshots

import io
from PIL import Image


# 常量定义
MAX_IMAGE_DIMENSION = 4000  # API 允许的最大边长
Image.MAX_IMAGE_PIXELS = None  # 禁用 Pillow 的像素总数限制（处理超大图片）


def encode_image(image_path):
    """
    将图片文件编码为 base64 字符串。
    如果图片尺寸超过 MAX_IMAGE_DIMENSION，则按比例缩放。
    支持常见图片格式和 SVG（SVG 先转为 PNG）。
    """
    file_ext = os.path.splitext(image_path)[1].lower()

    # ---------- SVG 处理 ----------
    if file_ext == ".svg":
        # SVG 转 PNG 字节流
        png_content = cairosvg.svg2png(url=image_path)
        img = Image.open(io.BytesIO(png_content))
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            ratio = min(
                MAX_IMAGE_DIMENSION / img.width,
                MAX_IMAGE_DIMENSION / img.height,
            )
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img.thumbnail(new_size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            png_content = buffer.getvalue()
        return base64.b64encode(png_content).decode("utf-8")

    # ---------- 普通图片 ----------
    with Image.open(image_path) as img:
        original_format = img.format
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            ratio = min(
                MAX_IMAGE_DIMENSION / img.width,
                MAX_IMAGE_DIMENSION / img.height,
            )
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img.thumbnail(new_size, Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format=original_format)
            image_data = buffer.getvalue()
        else:
            with open(image_path, "rb") as f:
                image_data = f.read()
        return base64.b64encode(image_data).decode("utf-8")


def chat_with_retry(
    client: OpenAI,
    messages: list,
    model: str,
    max_tokens: int = 2000,
    temperature: float = 0.7,
    max_retries: int = 3,
    retry_delay: int = 2,
    stream: bool = True,  # 默认开启流式
    **kwargs,
) -> Optional[str]:
    """
    带重试机制的聊天函数（支持流式输出，默认开启）

    Returns:
        成功时返回完整响应内容,失败时抛异常
    """
    # 若调用方在 kwargs 里显式传了 stream，以调用方为准
    if "stream" in kwargs:
        stream = kwargs.pop("stream")

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=1200,
                stream=stream,
                **kwargs,
            )

            if stream:
                full_content = []
                for chunk in response:
                    if not chunk or not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    content_piece = (
                        getattr(delta, "content", None) if delta else None
                    )
                    if content_piece:
                        full_content.append(content_piece)

                content = "".join(full_content)
                if not content:
                    raise ValueError(
                        "Empty response content received from API (stream mode)"
                    )
                return content

            # 非流式分支
            if (
                not response
                or not response.choices
                or not response.choices[0].message.content
            ):
                raise ValueError("Empty response content received from API")

            return response.choices[0].message.content

        except Exception as e:
            print(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            print(f"Full traceback: {traceback.format_exc()}")

            if attempt < max_retries - 1:
                wait_time = retry_delay * attempt
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                raise ValueError("达到最大重试次数，API调用失败")

def copy_resources(
    origin_path: Path,
    workspace_path: Path,
    resources_info: List[Dict[str, Any]],
    ) -> None:
    # 创建workspace目录
    
    workspace_path.mkdir(parents=True, exist_ok=True)

    if not origin_path.exists():
        return

    # 根据 resources_info 复制资源文件
    for resource in resources_info:
        resource_path = resource.get("path", "")

        if resource_path:
            # 源文件路径
            origin_file = origin_path / resource_path

            if origin_file.exists():
                # 目标路径
                workspace_file = workspace_path / resource_path
                workspace_file.parent.mkdir(parents=True, exist_ok=True)

                # 复制文件
                shutil.copy2(origin_file, workspace_file)


def apply_search_replace(
    code_list: List[Dict], modified_files: List[Dict], strict_mode: bool = True
) -> tuple:
    """
    将 search/replace 块应用到源代码

    Args:
        code_list: 原始代码文件列表
        modified_files: search/replace 块列表
        strict_mode: 是否使用严格模式
            - True: 硬匹配，任何失败都抛出异常（默认）
            - False: 软匹配，跳过失败的块，返回错误信息列表

    Returns:
        tuple: (修改后的代码文件列表, 错误信息列表)
            - 严格模式下，errors 列表始终为空（失败会抛异常）
            - 软匹配模式下，errors 列表包含所有失败信息

    Raises:
        ValueError: 当使用严格模式且无法找到要替换的文本时

    Examples:
        # 硬匹配模式（默认）
        result_code, _ = apply_search_replace(code_list, modified_files)

        # 软匹配模式
        result_code, errors = apply_search_replace(code_list, modified_files, strict_mode=False)
        if errors:
            print(f"警告: {len(errors)} 个代码块替换失败")
    """
    # 创建代码的副本
    result_code = []
    code_map = {item["path"]: item["code"] for item in code_list}
    errors = []
    success_count = 0
    total_blocks = len(modified_files)

    # 按路径分组 modified_files
    blocks_by_path = {}
    for block in modified_files:
        path = block["path"]
        if path not in blocks_by_path:
            blocks_by_path[path] = []
        blocks_by_path[path].append(block)

    # 应用每个文件的修改
    for path, blocks in blocks_by_path.items():
        if path not in code_map:
            # 检查是否是新建文件的情况
            # 如果是新建文件，第一个块的 search 应该为空
            if len(blocks) > 0 and blocks[0]["search"] == "":
                code_map[path] = ""
            else:
                error_msg = f"File path not found in code_list: {path}"
                if strict_mode:
                    raise ValueError(error_msg)
                else:
                    # 为该路径下每个块记录对应的 block_index，便于后续忽略
                    for block_idx, _ in enumerate(blocks):
                        errors.append(
                            {
                                "path": path,
                                "block_index": block_idx,
                                "error_type": "path_not_found",
                                "error": error_msg,
                            }
                        )
                    continue

        code = code_map[path]
        for block_idx, block in enumerate(blocks):
            search_text = block["search"]
            replace_text = block["replace"]

            # search/replace 相等，视为错误
            if search_text.strip() == replace_text.strip():
                error_msg = f"Search and replace are identical in {path} (block {block_idx})."
                if strict_mode:
                    raise ValueError(error_msg)
                else:
                    errors.append(
                        {
                            "path": path,
                            "block_index": block_idx,
                            "error_type": "identical_search_replace",
                            "error": error_msg,
                        }
                    )
                    print(f"⚠️  跳过无效代码块: {path} (block {block_idx + 1})")
                    continue

            if search_text == "" and code == "":
                # 新文件创建
                code = replace_text
                success_count += 1
            elif search_text in code:
                code = code.replace(search_text, replace_text, 1)
                success_count += 1
            else:
                error_msg = (
                    f"Failed to apply search/replace in {path} (block {block_idx}).\n"
                    f"Search text (first 200 chars): {search_text[:200]}...\n"
                    f"This may indicate LLM generated invalid modifications."
                )
                if strict_mode:
                    raise ValueError(error_msg)
                else:
                    errors.append(
                        {
                            "path": path,
                            "block_index": block_idx,
                            "error_type": "search_not_found",
                            "error": error_msg,
                        }
                    )
                    print(
                        f"⚠️  跳过失败的代码块: {path} (block {block_idx + 1})"
                    )
                    # 跳过这个块，继续处理下一个
                    continue

        code_map[path] = code

    # 构建结果列表
    for item in code_list:
        new_item = item.copy()
        if item["path"] in code_map:
            new_item["code"] = code_map[item["path"]]
        result_code.append(new_item)

    # 添加新创建的文件
    existing_paths = set(item["path"] for item in code_list)
    for path, content in code_map.items():
        if path not in existing_paths:
            result_code.append({"path": path, "code": content})

    return result_code, errors


def normalize_whitespace(text: str) -> str:
    """
    标准化空白字符以进行模糊匹配
    """
    # 移除行尾空白,标准化换行
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def get_image_mime_type(file_path: str) -> str:
    """
    根据文件扩展名返回对应的MIME类型

    Args:
        file_path: 图片文件路径

    Returns:
        str: MIME类型字符串,如 "image/png", "image/jpeg" 等

    Note:
        - SVG文件返回 "image/png" (因为会被转换为PNG)
        - 不支持的格式默认返回 "image/png"
    """

    file_ext = os.path.splitext(file_path)[1].lower()

    mime_type_map = {
        ".svg": "image/png",  # SVG已转换为PNG
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    return mime_type_map[file_ext]
