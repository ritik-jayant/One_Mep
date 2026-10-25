from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.config import settings

SYSTEM = (
    "You are a senior fire-protection engineer working to India's National Building Code "
    "(NBC Part 4 Fire and Life Safety) and typical local fire-authority practice. "
    "Return ONLY valid JSON that matches the requested schema. Prefer conservative, "
    "code-compliant layouts. Never invent NBC clause numbers you are unsure of."
)


_PLACEHOLDERS = {"", "sk-your-key", "changeme", "your-key"}


def available() -> bool:
    key = (settings.llm_api_key or "").strip()
    return bool(key) and key.lower() not in _PLACEHOLDERS


def _client() -> OpenAI:
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


def complete_json(
    user_prompt: str,
    *,
    image_path: str | None = None,
    schema_hint: str = "{}",
) -> dict[str, Any]:
    if not available():
        raise RuntimeError("LLM_API_KEY is not set")

    content: list[dict[str, Any]] = [
        {"type": "text", "text": f"{user_prompt}\n\nJSON schema hint:\n{schema_hint}"}
    ]
    if image_path and Path(image_path).exists():
        import base64

        mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
        b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})

    response = _client().chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": content},
        ],
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)
