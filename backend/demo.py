"""Demo mode: scripted insurance sales conversation streamed over WebSocket.

Flow: The conversation follows a script of customer lines. After each
customer question, the AI pipeline runs (question detection + retrieval +
suggestion card), then the LLM generates a natural sales rep response
using that retrieved info.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Literal

from fastapi import WebSocket

from backend.answer_generator import AnswerGenerator
from backend.config import settings
from backend.conversation import ConversationManager
from backend.models import SuggestionCard, TranscriptUpdate, WSMessage, WSMessageType
from backend.pipeline import run_pipeline
from backend.question_detector import QuestionDetector
from backend.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)

Speaker = Literal["sales", "customer"]

SALES_RESPONSE_PROMPT = """\
You are Sarah, an insurance sales rep on a phone call. You have the answer below on your screen. Tell the customer in 2-4 spoken sentences. Do not mention a database or system.

Customer asked: {question}
Retrieved answer: {answer}

Your spoken response:"""

# "customer" / fixed "sales" lines are scripted.
# sales + None means "generate from the last AI suggestion".
DEMO_SCRIPT: list[tuple[Speaker, str | None]] = [
    (
        "sales",
        "Hello! Thank you for calling SecureLife Insurance. My name is Sarah. How can I help you today?",
    ),
    (
        "customer",
        "Hi Sarah! I'm looking into getting some insurance coverage for my family. I've been thinking about life insurance and maybe health insurance too.",
    ),
    (
        "sales",
        "That's great that you're thinking about protecting your family! We have several options. Are you looking for any specific type of coverage?",
    ),
    (
        "customer",
        "Well, I'm 32 years old with two kids. I want to make sure they're taken care of if anything happens to me. What term life options do you have?",
    ),
    ("sales", None),
    ("customer", "How much does SecureLife Premium Term 30 cost per month for a 32-year-old with a family?"),
    ("sales", None),
    ("customer", "And what's the coverage amount for that plan?"),
    ("sales", None),
    (
        "customer",
        "Also, I'm curious — what happens if I get diagnosed with a terminal illness during the policy? Is there any early payout option?",
    ),
    ("sales", None),
    (
        "customer",
        "OK great. I'm also interested in health insurance. What's the deductible for your health plan?",
    ),
    ("sales", None),
    (
        "customer",
        "Does your health plan cover mental health services? My wife has been seeing a therapist.",
    ),
    ("sales", None),
    (
        "customer",
        "And what about prescription drugs? We have some ongoing prescriptions. What are the copays like?",
    ),
    ("sales", None),
    (
        "customer",
        "One last question — we're planning a family trip to Europe next month. Do you offer travel insurance that covers medical emergencies abroad?",
    ),
    ("sales", None),
    (
        "customer",
        "What about COVID-19? Is that covered under the travel insurance if we get sick overseas?",
    ),
    ("sales", None),
    ("customer", "Great, thank you Sarah. This has been really helpful!"),
    (
        "sales",
        "You're welcome! I'll prepare a complete quote with all these options and email it to you. Is there anything else I can help with?",
    ),
    ("customer", "No, that covers everything. Thanks so much!"),
    ("sales", "Thank you for calling SecureLife Insurance! Have a wonderful day."),
]


async def _wait_for_next(ws: WebSocket, timeout: float = 120.0) -> bool:
    """Wait for the client to send a 'demo_next' message."""
    try:
        data = await asyncio.wait_for(ws.receive_text(), timeout=timeout)
        msg = json.loads(data)
        return msg.get("type") == "demo_next"
    except (TimeoutError, Exception):
        return False


async def _generate_audio(text: str, speaker: Speaker) -> str | None:
    """Generate TTS audio via ElevenLabs. Returns base64-encoded MP3 or None."""
    if not settings.elevenlabs_api_key:
        return None
    try:
        from backend.tts import synthesize

        audio_bytes = await synthesize(text, speaker)
        return base64.b64encode(audio_bytes).decode("ascii")
    except Exception:
        logger.exception("ElevenLabs TTS failed for: %s", text[:50])
        return None


async def _send_json(ws: WebSocket, msg: WSMessage) -> None:
    await ws.send_json(msg.model_dump(mode="json"))


async def _send_audio(ws: WebSocket, speaker: Speaker, text: str) -> None:
    audio_b64 = await _generate_audio(text, speaker)
    if audio_b64:
        await _send_json(
            ws,
            WSMessage(
                type=WSMessageType.AUDIO_PLAY,
                payload={"audio": audio_b64, "format": "mp3", "speaker": speaker},
            ),
        )


async def _send_turn(ws: WebSocket, speaker: Speaker, text: str) -> None:
    """Send a transcript update + TTS audio for one conversation turn."""
    audio_task = asyncio.create_task(_send_audio(ws, speaker, text))
    await _send_json(
        ws,
        WSMessage(
            type=WSMessageType.TRANSCRIPT_UPDATE,
            payload=TranscriptUpdate(text=text, is_final=True, speaker=speaker).model_dump(
                mode="json"
            ),
        ),
    )
    await audio_task


async def _generate_sales_response(llm_client, question: str, answer: str) -> str:
    """Use LLM to generate a natural sales rep response from the AI suggestion."""
    prompt = SALES_RESPONSE_PROMPT.format(question=question, answer=answer)
    try:
        response = await llm_client.complete(
            system_prompt="You are a helpful insurance sales representative named Sarah.",
            user_prompt=prompt,
            temperature=0.7,
            max_tokens=300,
        )
        return response.strip()
    except Exception:
        logger.exception("Failed to generate sales response")
        return f"Based on what I'm seeing here, {answer}"


async def run_demo(
    ws: WebSocket,
    conversation: ConversationManager,
    question_detector: QuestionDetector,
    retriever: KnowledgeRetriever,
    answer_generator: AnswerGenerator,
    llm_client=None,
) -> None:
    """Stream the demo conversation. Sales rep answers use AI-retrieved info."""
    await _send_json(ws, WSMessage(type=WSMessageType.STATUS, payload={"message": "demo_started"}))

    last_suggestion: SuggestionCard | None = None

    for speaker, text in DEMO_SCRIPT:
        if not await _wait_for_next(ws):
            logger.info("Demo: client disconnected or timed out, stopping")
            return

        if speaker == "customer":
            assert text is not None
            update = TranscriptUpdate(text=text, is_final=True, speaker=speaker)
            last_suggestion = None
            audio_task = asyncio.create_task(_send_audio(ws, speaker, text))

            await _send_json(
                ws,
                WSMessage(
                    type=WSMessageType.TRANSCRIPT_UPDATE,
                    payload=update.model_dump(mode="json"),
                ),
            )
            card = await run_pipeline(
                update, conversation, question_detector, retriever, answer_generator
            )
            if card:
                last_suggestion = card
                await _send_json(
                    ws,
                    WSMessage(
                        type=WSMessageType.SUGGESTION_CARD,
                        payload=card.model_dump(mode="json"),
                    ),
                )
            await audio_task

        elif speaker == "sales" and text is None:
            if last_suggestion and llm_client:
                sales_text = await _generate_sales_response(
                    llm_client, last_suggestion.question, last_suggestion.answer
                )
            else:
                sales_text = "Let me look into that for you..."

            conversation.add_transcript(
                TranscriptUpdate(text=sales_text, is_final=True, speaker="sales")
            )
            await _send_turn(ws, "sales", sales_text)
            last_suggestion = None

        else:
            assert text is not None
            conversation.add_transcript(TranscriptUpdate(text=text, is_final=True, speaker="sales"))
            await _send_turn(ws, "sales", text)

        await _send_json(
            ws, WSMessage(type=WSMessageType.STATUS, payload={"message": "turn_complete"})
        )

    await _send_json(ws, WSMessage(type=WSMessageType.STATUS, payload={"message": "demo_ended"}))
