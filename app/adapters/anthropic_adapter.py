"""
Anthropic model provider adapter.
Requires env var: ANTHROPIC_API_KEY
"""
from typing import Optional

from app.adapters.base import ModelProviderAdapter
from app.adapters.prompts import QUALITY_SCORE_SYSTEM
from app.adapters.utils import build_scoring_prompt, parse_score_response
from app.core.config import settings
from app.core.exceptions import ProviderCallError


class AnthropicAdapter(ModelProviderAdapter):
    """Adapter for the Anthropic Messages API."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return settings.anthropic_default_model

    @property
    def is_available(self) -> bool:
        return bool(settings.anthropic_api_key)

    def _get_client(self):
        from anthropic import AsyncAnthropic  # noqa: PLC0415
        return AsyncAnthropic(
            api_key=settings.anthropic_api_key,
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
            resp = await client.messages.create(
                model=model or self.default_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return resp.content[0].text
        except Exception as exc:
            raise ProviderCallError("anthropic", str(exc)) from exc

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
            resp = await client.messages.create(
                model=model or self.default_model,
                max_tokens=512,
                system=QUALITY_SCORE_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
                temperature=0,
            )
            raw = resp.content[0].text
        except Exception as exc:
            raise ProviderCallError("anthropic", str(exc)) from exc
        return parse_score_response(raw, criteria)
