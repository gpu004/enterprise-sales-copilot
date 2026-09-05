"""Regression checks for text-only sessions and visible pipeline errors."""

import unittest
from unittest.mock import AsyncMock, patch

from backend import main


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_text_failure_is_visible_and_does_not_start_deepgram(self):
        ws = AsyncMock()
        ws.receive.side_effect = [
            {"type": "websocket.receive", "text": '{"type":"text_input","text":"hello"}'},
            {"type": "websocket.disconnect"},
        ]
        with (
            patch.object(
                main, "process_transcript", new=AsyncMock(side_effect=RuntimeError("quota"))
            ),
            patch.object(main, "DeepgramTranscriber") as transcriber,
            self.assertLogs(main.logger, level="ERROR"),
        ):
            await main.websocket_session(ws)
        transcriber.assert_not_called()
        self.assertEqual(ws.send_json.call_args_list[-1].args[0]["type"], "error")
        self.assertEqual(ws.receive.await_count, 2)

    async def test_audio_starts_transcriber_once_and_stops_on_disconnect(self):
        ws = AsyncMock()
        ws.receive.side_effect = [
            {"type": "websocket.receive", "bytes": b"pcm"},
            {"type": "websocket.receive", "bytes": b"more"},
            {"type": "websocket.disconnect"},
        ]
        transcriber = AsyncMock()
        with (
            patch.object(main.settings, "deepgram_api_key", "test"),
            patch.object(main, "DeepgramTranscriber", return_value=transcriber),
        ):
            await main.websocket_session(ws)
        transcriber.start.assert_awaited_once()
        self.assertEqual(transcriber.send_audio.await_count, 2)
        transcriber.stop.assert_awaited_once()
