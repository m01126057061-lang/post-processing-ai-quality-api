"""
HuggingFace Inference API adapter.
Requires env var: HUGGINGFACE_API_KEY
"""
import asyncio

from app.adapters.base import ModelProviderAdapter
from app.adapters.prompts import QUALITY_SCORE_SYSTEM
from app.adapters.utils import build_scoring_prompt, parse_score_response
from app.core.config import settings
from app.core.exceptions import ProviderCallError

_INSTRUCT_TEMPLATE = "<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{user} [/INST]"


class HuggingFaceAdapter(ModelProviderAdapter):
    """Adapter for the HuggingFace Inference API (text-generation models)."""

    @property
    def provider_name(self) -> str:
        return "huggingface"

    @property
    def default_model(self) -> str:
        return settings.huggingface_default_model

    @property
    def is_available(self) -> bool:
        return bool(settings.huggingface_api_key)

    def _get_client(self, model: str | None = None):
        from huggingface_hub import InferenceClient  # noqa: PLC0415
        return InferenceClient(
            model=model or self.default_model,
            token=settings.huggingface_api_key,
            timeout=settings.provider_timeout_seconds,
        )

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs,
    ) -> str:
        try:
            client = self._get_client(model)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: client.text_generation(
                    prompt,
                    max_new_tokens=kwargs.get("max_new_tokens", 512),
                    temperature=kwargs.get("temperature", 0.1),
                ),
            )
            return result if isinstance(result, str) else str(result)
        except Exception as exc:
            raise ProviderCallError("huggingface", str(exc)) from exc

    async def score_quality(
        self,
        text: str,
        context: str | None,
        criteria: list[str],
        model: str | None = None,
    ) -> tuple[dict[str, float], str]:
        user_msg = build_scoring_prompt(text, context, criteria)
        full_prompt = _INSTRUCT_TEMPLATE.format(
            system=QUALITY_SCORE_SYSTEM,
            user=user_msg,
        )
        try:
            client = self._get_client(model)
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(
                None,
                lambda: client.text_generation(
                    full_prompt,
                    max_new_tokens=512,
                    temperature=0.1,
                    stop_sequences=["</s>", "[INST]"],
                ),
            )
            raw = raw if isinstance(raw, str) else str(raw)
        except Exception as exc:
            raise ProviderCallError("huggingface", str(exc)) from exc
        return parse_score_response(raw, criteria)
