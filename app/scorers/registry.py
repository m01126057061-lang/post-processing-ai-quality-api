"""
Central scorer registry.

Built-in scorers are singletons — created once and reused across requests.
ML-backed scorers lazy-load their models on first call.

Custom scorers can be added without touching core code:
  1. Create a .py file in  app/scorers/plugins/
  2. Define a class that inherits from QualityScorer and sets a unique `name`
  3. Restart the server — the registry auto-discovers and registers it

Built-in metrics:
  coherence    — adjacent-sentence embedding similarity
  relevance    — output vs. context embedding similarity (requires context)
  fluency      — heuristic + readability signals (language-aware)
  toxicity     — BERT-based safety score via detoxify
  hallucination— NLI-based groundedness score (requires context)
"""
from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

from app.scorers.base import QualityScorer
from app.scorers.coherence import CoherenceScorer
from app.scorers.fluency import FluencyScorer
from app.scorers.hallucination import HallucinationScorer
from app.scorers.relevance import RelevanceScorer
from app.scorers.toxicity import ToxicityScorer

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, QualityScorer] = {
    "coherence":     CoherenceScorer(),
    "relevance":     RelevanceScorer(),
    "fluency":       FluencyScorer(),
    "toxicity":      ToxicityScorer(),
    "hallucination": HallucinationScorer(),
}

# ── Plugin discovery ─────────────────────────────────────────────────────────

_PLUGINS_DIR = Path(__file__).parent / "plugins"


def _load_plugins() -> None:
    """
    Scan the plugins directory for .py files and register any QualityScorer
    subclass with a non-empty `name` attribute that is not already registered.
    Silently skips __init__.py and any file that starts with an underscore.
    """
    if not _PLUGINS_DIR.exists():
        return

    for plugin_file in sorted(_PLUGINS_DIR.glob("*.py")):
        if plugin_file.name.startswith("_"):
            continue

        module_name = f"app.scorers.plugins.{plugin_file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[attr-defined]

            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, QualityScorer)
                    and obj is not QualityScorer
                    and getattr(obj, "name", "") not in ("", "base")
                ):
                    instance = obj()
                    if instance.name in _REGISTRY:
                        logger.warning(
                            "Plugin scorer %r in %s conflicts with an existing "
                            "scorer — skipping.",
                            instance.name,
                            plugin_file.name,
                        )
                    else:
                        _REGISTRY[instance.name] = instance
                        logger.info(
                            "Registered plugin scorer %r from %s",
                            instance.name,
                            plugin_file.name,
                        )
        except Exception:
            logger.exception("Failed to load scorer plugin: %s", plugin_file.name)


# Auto-load plugins at import time
_load_plugins()


# ── Public API ───────────────────────────────────────────────────────────────

def get_scorer(name: str) -> QualityScorer:
    """Return the scorer for *name*, or raise KeyError if unknown."""
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown metric: {name!r}. Available metrics: {available_metrics()}"
        )
    return _REGISTRY[name]


def available_metrics() -> list[str]:
    """Return names of all registered metrics (built-in + plugins)."""
    return list(_REGISTRY)


def get_context_required_metrics() -> list[str]:
    """Return names of metrics that require a context string for meaningful scores."""
    return [name for name, scorer in _REGISTRY.items()
            if getattr(scorer, "requires_context", False)]


def reload_plugins() -> None:
    """Re-scan the plugins directory and register any newly added scorers."""
    _load_plugins()
