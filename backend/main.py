"""FastAPI application with WebSocket-based real-time sales copilot pipeline."""

from __future__ import annotations

import json
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.answer_generator import AnswerGenerator
from backend.config import settings
from backend.conversation import ConversationManager
from backend.database import init_db
from backend.demo import run_demo
from backend.llm_client import LLMClient
from backend.models import SuggestionCard, TranscriptUpdate, WSMessage, WSMessageType
from backend.pipeline import run_pipeline
from backend.question_detector import QuestionDetector
from backend.retriever import KnowledgeRetriever
from backend.transcription import DeepgramTranscriber

logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise Sales Copilot")


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    frontend_url = os.environ.get("FRONTEND_URL", "").strip()
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=os.environ.get("CORS_ORIGIN_REGEX") or None,
    allow_methods=["*"],
    allow_headers=["*"],
)

_llm_client: LLMClient | None = None
_retriever: KnowledgeRetriever | None = None
_question_detector: QuestionDetector | None = None
_answer_generator: AnswerGenerator | None = None


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    global _llm_client, _retriever, _question_detector, _answer_generator

    await init_db()
    _llm_client = LLMClient(provider=settings.llm_provider, model=settings.llm_model)
    _retriever = KnowledgeRetriever(_llm_client)
    _question_detector = QuestionDetector(_llm_client)
    _answer_generator = AnswerGenerator(_llm_client)
    logger.info("Startup complete")


async def _send_json(ws: WebSocket, msg: WSMessage) -> None:
    await ws.send_json(msg.model_dump(mode="json"))


async def process_transcript(
    update: TranscriptUpdate,
    ws: WebSocket,
    conversation: ConversationManager,
) -> SuggestionCard | None:
    """Send the transcript update and run the suggestion pipeline."""
    await _send_json(
        ws,
        WSMessage(
            type=WSMessageType.TRANSCRIPT_UPDATE,
            payload=update.model_dump(mode="json"),
        ),
    )

    assert _question_detector and _retriever and _answer_generator
    card = await run_pipeline(
        update,
        conversation,
        _question_detector,
        _retriever,
        _answer_generator,
    )
    if card:
        await _send_json(
            ws,
            WSMessage(
                type=WSMessageType.SUGGESTION_CARD,
                payload=card.model_dump(mode="json"),
            ),
        )
    return card


@app.websocket("/ws/demo")
async def websocket_demo(ws: WebSocket):
    """Demo mode: streams a scripted sales conversation with AI suggestions."""
    await ws.accept()
    assert _question_detector and _retriever and _answer_generator
    try:
        await run_demo(
            ws,
            ConversationManager(),
            _question_detector,
            _retriever,
            _answer_generator,
            llm_client=_llm_client,
        )
    except WebSocketDisconnect:
        logger.info("Demo WebSocket disconnected")
    except Exception:
        logger.exception("Demo error")
        await _send_json(
            ws,
            WSMessage(
                type=WSMessageType.ERROR,
                payload={
                    "message": "Demo failed. Check the LLM provider quota and voice configuration."
                },
            ),
        )
        await ws.close(code=1011)


@app.websocket("/ws/session")
async def websocket_session(ws: WebSocket):
    await ws.accept()

    conversation = ConversationManager()
    transcriber: DeepgramTranscriber | None = None

    async def on_transcript(update: TranscriptUpdate):
        try:
            await process_transcript(update, ws, conversation)
        except Exception:
            logger.exception("Pipeline error in transcription callback")
            await _send_json(
                ws,
                WSMessage(
                    type=WSMessageType.ERROR,
                    payload={
                        "message": "Could not generate an answer. Check the LLM provider quota and configuration."
                    },
                ),
            )

    await _send_json(
        ws,
        WSMessage(type=WSMessageType.STATUS, payload={"message": "session_ready"}),
    )

    try:
        while True:
            data = await ws.receive()
            if data["type"] == "websocket.disconnect":
                break
            if data.get("bytes") is not None:
                if not transcriber:
                    if not settings.deepgram_api_key:
                        await _send_json(
                            ws,
                            WSMessage(
                                type=WSMessageType.ERROR,
                                payload={
                                    "message": "Microphone transcription requires a Deepgram API key. Text input is available."
                                },
                            ),
                        )
                        continue
                    transcriber = DeepgramTranscriber(settings.deepgram_api_key)
                    await transcriber.start(on_transcript)
                await transcriber.send_audio(data["bytes"])
            elif data.get("text") is not None:
                msg = json.loads(data["text"])
                if msg.get("type") == "text_input":
                    update = TranscriptUpdate(text=msg["text"], is_final=True)
                    await on_transcript(update)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception:
        logger.exception("WebSocket error")
        await _send_json(
            ws,
            WSMessage(
                type=WSMessageType.ERROR,
                payload={"message": "Voice connection failed. Reconnect or use text input."},
            ),
        )
        await ws.close(code=1011)
    finally:
        if transcriber:
            try:
                await transcriber.stop()
            except Exception:
                logger.exception("Error stopping transcriber")
