"""Deepgram streaming transcription client."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions, LiveTranscriptionEvents

from backend.config import settings
from backend.models import TranscriptUpdate

logger = logging.getLogger(__name__)


class DeepgramTranscriber:
    """Streams audio to Deepgram and yields TranscriptUpdate objects."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.deepgram_api_key
        self._client = DeepgramClient(
            self._api_key, DeepgramClientOptions(options={"keepalive": "true"})
        )
        self._connection = None

    async def start(
        self,
        on_transcript: Callable[[TranscriptUpdate], Awaitable[None]],
    ) -> None:
        """Initialize Deepgram live connection and wire up event handlers."""
        self._connection = self._client.listen.asynclive.v("1")

        async def _on_message(_conn, result, **_kwargs):
            if not result.channel.alternatives:
                return
            transcript = result.channel.alternatives[0].transcript
            if not transcript:
                return
            update = TranscriptUpdate(
                text=transcript,
                is_final=result.is_final,
            )
            await on_transcript(update)

        async def _on_error(_conn, error, **_kwargs):
            logger.error("Deepgram error: %s", error)

        self._connection.on(LiveTranscriptionEvents.Transcript, _on_message)
        self._connection.on(LiveTranscriptionEvents.Error, _on_error)

        options = LiveOptions(
            model="nova-2",
            language="en",
            smart_format=True,
            interim_results=True,
            utterance_end_ms="1500",
            encoding="linear16",
            sample_rate=16000,
        )

        try:
            if not await self._connection.start(options):
                raise RuntimeError("Failed to start Deepgram live connection")
            if not await self._connection.is_connected():
                raise RuntimeError("Deepgram live connection is not ready")
        except BaseException:
            await self.stop()
            raise

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Send an audio chunk to Deepgram."""
        if self._connection is None:
            raise RuntimeError("Connection not started — call start() first")
        if not await self._connection.is_connected():
            raise RuntimeError("Deepgram live connection is closed")
        if not await self._connection.send(audio_bytes):
            raise RuntimeError("Failed to send audio to Deepgram")

    async def stop(self) -> None:
        """Close the Deepgram connection."""
        if self._connection is not None:
            connection = self._connection
            self._connection = None
            await connection.finish()
