"""
Custom scorer plugins directory.

Drop any .py file here that defines one or more QualityScorer subclasses.
The registry auto-discovers and registers them at startup — no core changes needed.

Example — app/scorers/plugins/brevity.py
-----------------------------------------
    from app.scorers.base import QualityScorer


    class BrevityScorer(QualityScorer):
        "Scores texts higher when they are concise (10-50 words is ideal)."

        name = "brevity"
        weight = 1.0

        def score(self, text: str, context: str | None = None) -> float:
            words = len(text.split())
            if 10 <= words <= 50:
                return 1.0
            return max(0.0, 1.0 - abs(words - 30) / 100)

After adding this file, restart the server and "brevity" will appear in
GET /api/v1/providers and be accepted as a valid metric everywhere.
"""
