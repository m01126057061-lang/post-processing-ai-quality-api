"""
Utility helpers for model provider adapters.

parse_score_response — extract quality scores from an LLM text response.
  Strategy: JSON parse first; regex extraction fallback.
  All scores are clamped to [0.0, 1.0].
"""
import contextlib
import json
import re


def parse_score_response(
    response: str,
    criteria: list[str],
) -> tuple[dict[str, float], str]:
    """
    Parse a raw LLM response into a (scores, reasoning) tuple.

    Args:
        response:  Raw text output from the LLM.
        criteria:  Expected score keys.

    Returns:
        scores    — {criterion: float} for each criterion found in the response.
        reasoning — explanation string if present, else empty string.
    """
    text = response.strip()

    # Strip markdown fences  ```json … ``` or ``` … ```
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.IGNORECASE)
    text = text.strip()

    scores: dict[str, float] = {}
    reasoning: str = ""

    # ── JSON path ─────────────────────────────────────────────────────────────
    try:
        data = json.loads(text)
        reasoning = str(data.get("reasoning", ""))
        for c in criteria:
            if c in data:
                with contextlib.suppress(ValueError, TypeError):
                    scores[c] = max(0.0, min(1.0, float(data[c])))
        return scores, reasoning
    except (json.JSONDecodeError, AttributeError):
        pass

    # ── Regex fallback ────────────────────────────────────────────────────────
    for c in criteria:
        pattern = rf'["\'\']?{re.escape(c)}["\'\']?\s*:\s*([0-9]*\.?[0-9]+)'
        m = re.search(pattern, text)
        if m:
            with contextlib.suppress(ValueError):
                scores[c] = max(0.0, min(1.0, float(m.group(1))))

    rm = re.search(r'["\'\']?reasoning["\'\']?\s*:\s*["\'\']([^"\'\']*)["\'\'\']', text)
    if rm:
        reasoning = rm.group(1)

    return scores, reasoning


def build_scoring_prompt(
    text: str,
    context: str | None,
    criteria: list[str],
) -> str:
    """Render the user-role scoring message using the shared template."""
    from app.adapters.prompts import QUALITY_SCORE_USER_TEMPLATE

    context_block = (
        f"Context/Prompt:\n\"\"\"\n{context}\n\"\"\"" if context else ""
    )
    return QUALITY_SCORE_USER_TEMPLATE.format(
        context_block=context_block,
        text=text,
        criteria=criteria,
        criteria_keys=", ".join(f'"{c}"' for c in criteria),
    )
