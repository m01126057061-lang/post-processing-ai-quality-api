"""Unit tests for adapter implementations and the adapter registry."""
import pytest

from app.adapters.anthropic_adapter import AnthropicAdapter
from app.adapters.mock_adapter import MockAdapter
from app.adapters.openai_adapter import OpenAIAdapter
from app.adapters.registry import get_adapter, list_providers
from app.adapters.utils import parse_score_response
from app.core.exceptions import ProviderNotAvailableError, UnknownProviderError

# ── MockAdapter ───────────────────────────────────────────────────────────────

def test_mock_adapter_always_available():
    assert MockAdapter().is_available is True


@pytest.mark.asyncio
async def test_mock_adapter_returns_fixed_scores():
    adapter = MockAdapter(fixed_scores={"coherence": 0.9, "fluency": 0.8})
    scores, reasoning = await adapter.score_quality(
        text="Test text.", context=None, criteria=["coherence", "fluency"]
    )
    assert scores == {"coherence": 0.9, "fluency": 0.8}
    assert isinstance(reasoning, str)


@pytest.mark.asyncio
async def test_mock_adapter_default_score():
    adapter = MockAdapter(default_score=0.6)
    scores, _ = await adapter.score_quality(
        text="Hello world.", context=None, criteria=["coherence", "relevance"]
    )
    assert all(v == pytest.approx(0.6) for v in scores.values())


@pytest.mark.asyncio
async def test_mock_adapter_complete():
    adapter = MockAdapter()
    result = await adapter.complete("Any prompt")
    assert isinstance(result, str) and len(result) > 0


# ── OpenAI / Anthropic availability ───────────────────────────────────────────

def test_openai_not_available_without_key(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.openai_api_key", None)
    assert OpenAIAdapter().is_available is False


def test_anthropic_not_available_without_key(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.anthropic_api_key", None)
    assert AnthropicAdapter().is_available is False


# ── Registry ──────────────────────────────────────────────────────────────────

def test_list_providers_returns_all_four():
    providers = list_providers()
    slugs = {p["provider"] for p in providers}
    assert {"openai", "anthropic", "huggingface", "mock"} == slugs


def test_get_adapter_mock_returns_mock_instance():
    adapter = get_adapter("mock")
    assert adapter.provider_name == "mock"


def test_get_adapter_unknown_raises():
    with pytest.raises(UnknownProviderError):
        get_adapter("does-not-exist")


def test_get_adapter_unavailable_raises(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.openai_api_key", None)
    with pytest.raises(ProviderNotAvailableError):
        get_adapter("openai")


# ── parse_score_response ──────────────────────────────────────────────────────

def test_parse_valid_json():
    raw = '{"coherence": 0.9, "fluency": 0.8, "reasoning": "Good flow."}'
    scores, reasoning = parse_score_response(raw, ["coherence", "fluency"])
    assert scores == {"coherence": pytest.approx(0.9), "fluency": pytest.approx(0.8)}
    assert reasoning == "Good flow."


def test_parse_json_with_markdown_fence():
    raw = '```json\n{"coherence": 0.7, "reasoning": "OK"}\n```'
    scores, _ = parse_score_response(raw, ["coherence"])
    assert scores["coherence"] == pytest.approx(0.7)


def test_parse_score_clamped_to_range():
    raw = '{"coherence": 1.5, "fluency": -0.2, "reasoning": ""}'
    scores, _ = parse_score_response(raw, ["coherence", "fluency"])
    assert scores["coherence"] == pytest.approx(1.0)
    assert scores["fluency"] == pytest.approx(0.0)


def test_parse_regex_fallback():
    raw = 'coherence: 0.85, fluency: 0.72'
    scores, _ = parse_score_response(raw, ["coherence", "fluency"])
    assert "coherence" in scores
    assert "fluency" in scores


def test_parse_missing_criteria_returns_empty():
    raw = '{"reasoning": "N/A"}'
    scores, _ = parse_score_response(raw, ["coherence"])
    assert scores == {}
