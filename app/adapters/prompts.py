"""Shared prompt templates used by all model provider adapters."""

QUALITY_SCORE_SYSTEM = (
    "You are an expert quality evaluator for AI-generated text. "
    "Your only job is to score text quality on specific criteria. "
    "Always respond with valid JSON and nothing else."
)

QUALITY_SCORE_USER_TEMPLATE = (
    "Score the following AI-generated text on each listed criterion.\n"
    "Use a scale from 0.0 (very poor) to 1.0 (excellent).\n"
    "{context_block}\n"
    "Text to evaluate:\n"
    '"""\n{text}\n"""\n\n'
    "Criteria: {criteria}\n\n"
    "Respond ONLY with a JSON object. "
    "Required keys: {criteria_keys}, \"reasoning\" (one sentence).\n"
    'Example: {{"coherence": 0.85, "fluency": 0.90, "reasoning": "Flows naturally."}}'
)
