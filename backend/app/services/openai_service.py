from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.services.ai_prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class AIResult:
    data: dict[str, Any]
    ai_used: bool
    fallback_used: bool


class OpenAIService:
    def __init__(self):
        self.enabled = settings.openai_enabled and settings.ai_provider.lower() == "openai"
        self._client: OpenAI | None = None
        if self.enabled and settings.openai_api_key:
            self._client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)

    def ask_json(self, task_prompt: str, fallback: dict[str, Any]) -> AIResult:
        if not self.enabled or not self._client:
            return AIResult(data=fallback, ai_used=False, fallback_used=True)
        try:
            response = self._client.responses.create(
                model=settings.openai_model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": task_prompt},
                ],
                response_format={"type": "json_object"},
            )
            text = response.output_text or "{}"
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("AI response is not JSON object")
            return AIResult(data=parsed, ai_used=True, fallback_used=False)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI call failed, falling back to deterministic logic: %s", exc)
            return AIResult(data=fallback, ai_used=False, fallback_used=True)


openai_service = OpenAIService()
