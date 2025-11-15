from __future__ import annotations

import time
from typing import Any

import httpx

from .config import get_settings


class ArkImageError(RuntimeError):
    pass


def generate_image(prompt: str, *, retries: int = 3, delay_seconds: float = 2.0) -> str:
    """Call Volcengine Ark to generate an image and return the first URL."""

    settings = get_settings()
    if not settings.ark_api_key:
        raise ArkImageError("ARK_API_KEY 尚未配置，无法生成图片")

    # 通过环境变量读取 key，并在此处实现带重试的调用逻辑，避免把敏感信息写入仓库。
    payload: dict[str, Any] = {
        "model": settings.ark_model,
        "prompt": prompt,
        "sequential_image_generation": settings.ark_sequential_mode,
        "response_format": settings.ark_response_format,
        "size": settings.ark_image_size,
        "stream": settings.ark_stream,
        "watermark": settings.ark_watermark,
    }

    headers = {
        "Authorization": f"Bearer {settings.ark_api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = httpx.post(settings.ark_base_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            url = data["data"][0]["url"]
            return url
        except Exception as exc:  # pragma: no cover - network errors can't be reproduced in tests
            last_error = exc
            if attempt < retries:
                time.sleep(delay_seconds)
    raise ArkImageError(f"生成图片失败: {last_error}")
