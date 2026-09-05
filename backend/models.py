"""Shared data models used across backend modules and the WebSocket protocol."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TranscriptUpdate(BaseModel):
    text: str
    is_final: bool = False
    speaker: str = ""  # "sales" or "customer" (empty for mic input)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DetectedQuestion(BaseModel):
    question: str
    category: str = ""  # e.g. "coverage", "pricing", "policy_terms"
    confidence: float = 0.0


class SuggestionCard(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    question: str
    answer: str
    source: str = ""  # e.g. "faqs", "coverage_details"
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WSMessageType(StrEnum):
    TRANSCRIPT_UPDATE = "transcript_update"
    SUGGESTION_CARD = "suggestion_card"
    STATUS = "status"
    TEXT_INPUT = "text_input"
    AUDIO_PLAY = "audio_play"
    ERROR = "error"


class WSMessage(BaseModel):
    type: WSMessageType
    payload: dict[str, Any] = {}
