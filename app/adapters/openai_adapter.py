"""
OpenAI model provider adapter.
Requires env var: OPENAI_API_KEY
"""
from typing import Optional

from app.adapters.base import ModelProviderAdapter
from app.adapters.prompts import QUALITY_SCORE_SYSTEM
from app.adapters.utils import build_scoring_prompt, parse_score_response
from app.core.config import settings
from app.core.exceptions import ProviderCallError


class OpenAIAdapter(ModelProviderAdapter):
    """Adapter for the OpenAI Chat Completions API."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return settings.openai_default_model

    @property
    def is_available(self) -> bool:
        return bool(settings.openai_api_key)

    def _get_client(self):
        from openai import AsyncOpenAI  # noqa: PLC0415
        return AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.provider_timeout_seconds,
            max_retries=settings.provider_max_retries,
        )

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        try:
            client = self._get_client()
            resp = await client.chat.completions.create(
                model=model or self.default_model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            raise ProviderCallError("openai", str(exc)) from exc

    async def score_quality(
        self,
        text: str,
        context: Optional[str],
        criteria: list[str],
        model: Optional[str] = None,
    ) -> tuple[dict[str, float], str]:
        user_msg = build_scoring_prompt(text, context, criteria)
        try:
            client = self._get_client()
            resp = await client.chat.completions.create(
                model=model or self.default_model,
                messages=[
                    {"role": "system", "content": QUALITY_SCORE_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            raw = resp.choices[0].message.content or ""
        except Exception as exc:
            raise ProviderCallError("openai", str(exc)) from exc
        return parse_score_response(raw, criteria)
