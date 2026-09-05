"""A demo turn must advance even when TTS is unavailable."""

import unittest
from unittest.mock import AsyncMock, patch

from backend import demo
from backend.conversation import ConversationManager


class DemoTests(unittest.IsolatedAsyncioTestCase):
    async def test_turn_completes_without_audio(self):
        ws = AsyncMock()
        ws.receive_text.return_value = '{"type":"demo_next"}'
        with (
            patch.object(demo, "DEMO_SCRIPT", [("sales", "Hello")]),
            patch.object(demo, "_generate_audio", new=AsyncMock(return_value=None)),
        ):
            await demo.run_demo(ws, ConversationManager(), None, None, None)
        messages = [call.args[0] for call in ws.send_json.call_args_list]
        self.assertEqual(
            [m["payload"]["message"] for m in messages if m["type"] == "status"],
            ["demo_started", "turn_complete", "demo_ended"],
        )
        self.assertFalse(any(m["type"] == "audio_play" for m in messages))
