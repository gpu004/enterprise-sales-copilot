"""LLM-based question detection for live insurance sales calls."""

from __future__ import annotations

import math

from backend.llm_parse import parse_json
from backend.models import DetectedQuestion

SYSTEM_PROMPT = """\
You are a real-time question detector for an insurance sales call. Analyze the recent conversation transcript and determine if the customer just asked a product-related question.

Focus on questions about:
- Coverage details (what's covered, limits, deductibles)
- Pricing (premiums, costs, payment options)
- Policy terms (duration, renewal, cancellation)
- Claims process
- Eligibility and conditions

Respond in JSON format only:
{"detected": true/false, "question": "the extracted question", "category": "coverage|pricing|policy_terms|claims|general", "confidence": 0.0-1.0}

If no product question was asked, respond: {"detected": false}
Do not detect greetings, small talk, or non-product questions."""


class QuestionDetector:
    """Uses an LLM to detect product-related questions in the transcript."""

    def __init__(self, llm_client):
        self._llm = llm_client

    async def detect(self, recent_transcript: str) -> DetectedQuestion | None:
        """Analyze transcript and return a DetectedQuestion if found."""
        if not recent_transcript.strip():
            return None

        raw = await self._llm.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=recent_transcript,
        )
        data = parse_json(raw)
        if not isinstance(data, dict) or data.get("detected") is not True:
            return None

        question = data.get("question")
        category = data.get("category", "general")
        if not isinstance(question, str) or not question.strip() or not isinstance(category, str):
            return None
        try:
            confidence = float(data.get("confidence", 0.0))
        except (TypeError, ValueError, OverflowError):
            return None
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            return None

        return DetectedQuestion(question=question, category=category, confidence=confidence)
