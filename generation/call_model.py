import os
from openai import OpenAI
import base64


def encode_file_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _build_user_content(prompt, vidoe_path=None, image_path=None):
    """Build OpenAI compatible multimodal user content."""
    user_messages = [{"type": "text", "text": prompt}]

    if vidoe_path:
        b64_vid = encode_file_base64(vidoe_path)
        user_messages.append(
            {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64_vid}"}}
        )

    if image_path:
        paths = image_path if isinstance(image_path, (list, tuple)) else [image_path]
        for p in paths:
            b64_img = encode_file_base64(p)
            user_messages.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
            )

    return user_messages


def call_api_stream(prompt, model="gpt-4o", vidoe_path=None, image_path=None):
    """流式输出：逐段 yield 文本增量。"""
    client, model_id = create_client(model)
    user_messages = _build_user_content(prompt, vidoe_path=vidoe_path, image_path=image_path)

    stream = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": user_messages}],
        stream=True,
    )

    for event in stream:
        try:
            choice0 = event.choices[0]
        except Exception:
            continue

        delta = getattr(choice0, "delta", None)
        if delta is not None:
            chunk = getattr(delta, "content", None)
            if chunk:
                yield chunk
                continue

        msg = getattr(choice0, "message", None)
        if msg is not None:
            chunk = getattr(msg, "content", None)
            if chunk:
                yield chunk


def call_api(
    prompt,
    model="gpt-4o",
    vidoe_path=None,
    image_path=None,
    *,
    on_chunk=None,
    stream_print: bool = False,
    print_fn=None,
):
    """统一入口（外部兼容返回完整字符串，内部走流式）。

    参数：
    - on_chunk: 可选回调。每收到一个增量 chunk 就调用一次
    - stream_print: 是否默认把增量实时输出到 stdout
    - print_fn: 自定义打印函数
    """
    if on_chunk is None and stream_print:
        if print_fn is None:
            def print_fn(t: str):
                print(t, end="", flush=True)
        on_chunk = print_fn

    pieces = []
    for chunk in call_api_stream(prompt, model=model, vidoe_path=vidoe_path, image_path=image_path):
        pieces.append(chunk)
        if on_chunk is not None:
            on_chunk(chunk)
    return "".join(pieces)


def create_client(model: str):
    """Create an OpenAI-compatible client.

    Environment variables:
    - OPENAI_BASE_URL: API base URL (default: https://api.openai.com/v1)
    - OPENAI_API_KEY: API key (required)

    Args:
        model: Model name/ID to use

    Returns:
        Tuple of (client, model_id)
    """
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it before using the API."
        )

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    return client, model


if __name__ == '__main__':
    # Test the API
    full = call_api("Hello, what model are you?", "gpt-4o")
    print("\n\n[full]", full)
