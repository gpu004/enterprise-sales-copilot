"""Conversation manager — rolling transcript buffer with deduplication."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.models import TranscriptUpdate


class ConversationManager:
    """Maintains a rolling transcript buffer and triggers question detection."""

    def __init__(self, buffer_duration_seconds: float = 60.0):
        self._buffer_duration = timedelta(seconds=buffer_duration_seconds)
        self._segments: list[TranscriptUpdate] = []
        self._processed_text: set[str] = set()

    def add_transcript(self, update: TranscriptUpdate) -> bool:
        """Add a transcript segment.

        Returns True if this is a new final segment that should trigger
        question detection.
        """
        self._segments.append(update)
        self._prune()

        if not update.is_final:
            return False

        text = update.text.strip()
        if not text or text in self._processed_text:
            return False

        self._processed_text.add(text)
        return True

    def get_recent_context(self, max_chars: int = 2000) -> str:
        """Return recent final transcript text, trimmed to *max_chars* from the end."""
        if max_chars <= 0:
            return ""
        parts = [s.text for s in self._segments if s.is_final]
        combined = " ".join(parts)
        if len(combined) > max_chars:
            combined = combined[-max_chars:]
        return combined

    def clear(self) -> None:
        """Reset the buffer."""
        self._segments.clear()
        self._processed_text.clear()

    def _prune(self) -> None:
        """Remove segments older than the buffer duration and drop stale dedup keys."""
        if not self._segments:
            return
        cutoff = datetime.now(UTC) - self._buffer_duration
        self._segments = [
            s
            for s in self._segments
            if (s.timestamp.replace(tzinfo=UTC) if s.timestamp.tzinfo is None else s.timestamp)
            >= cutoff
        ]
        live = {s.text.strip() for s in self._segments if s.is_final}
        self._processed_text &= live
