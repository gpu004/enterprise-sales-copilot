import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from backend.conversation import ConversationManager
from backend.llm_parse import parse_json
from backend.models import TranscriptUpdate
from backend.question_detector import QuestionDetector
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule

json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda children: (
        st.lists(children, max_size=5) | st.dictionaries(st.text(), children, max_size=5)
    ),
    max_leaves=15,
)


@given(json_values, st.sampled_from(["", "json"]))
def test_json_fences_round_trip(value, language):
    assert parse_json(f"```{language}\n{json.dumps(value)}\n```") == value


@given(st.text(min_size=1), st.integers(min_value=0, max_value=100))
def test_context_respects_character_budget(text, budget):
    manager = ConversationManager()
    manager.add_transcript(TranscriptUpdate(text=text, is_final=True))
    assert manager.get_recent_context(budget) == (text[-budget:] if budget else "")


@given(st.sampled_from([None, UTC]))
def test_accepts_naive_and_aware_timestamps(tz):
    manager = ConversationManager()
    assert manager.add_transcript(
        TranscriptUpdate(text="coverage?", is_final=True, timestamp=datetime.now(tz))
    )


@given(json_values.filter(lambda value: not isinstance(value, dict)))
def test_detector_ignores_non_object_json(value):
    detector = QuestionDetector(AsyncMock(complete=AsyncMock(return_value=json.dumps(value))))
    assert asyncio.run(detector.detect("coverage?")) is None


@given(st.sampled_from([None, [], {}, "bad", "NaN", "Infinity", -1, 2]))
def test_detector_ignores_invalid_confidence(confidence):
    raw = json.dumps({"detected": True, "question": "coverage?", "confidence": confidence})
    detector = QuestionDetector(AsyncMock(complete=AsyncMock(return_value=raw)))
    assert asyncio.run(detector.detect("coverage?")) is None


class ConversationSequence(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.manager = ConversationManager(buffer_duration_seconds=3600)
        self.seen = set()
        self.finals = []

    @rule(text=st.text(max_size=30), final=st.booleans())
    def add(self, text, final):
        expected = final and bool(text.strip()) and text.strip() not in self.seen
        assert self.manager.add_transcript(TranscriptUpdate(text=text, is_final=final)) == expected
        if final:
            self.finals.append(text)
        if expected:
            self.seen.add(text.strip())
        assert self.manager.get_recent_context() == " ".join(self.finals)[-2000:]

    @rule()
    def clear(self):
        self.manager.clear()
        self.seen.clear()
        self.finals.clear()


TestConversationSequence = ConversationSequence.TestCase


@given(
    st.text(min_size=1).filter(lambda s: bool(s.strip())),
    st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
)
def test_detector_preserves_valid_questions(question, confidence):
    raw = json.dumps({"detected": True, "question": question, "confidence": confidence})
    detector = QuestionDetector(AsyncMock(complete=AsyncMock(return_value=raw)))
    result = asyncio.run(detector.detect("coverage?"))
    assert result is not None
    assert result.question == question
    assert result.confidence == confidence


@given(st.lists(st.text(max_size=50), max_size=10))
def test_database_parameter_round_trip(values):
    import tempfile
    from pathlib import Path
    from unittest.mock import patch

    from backend import database

    async def check():
        db = await database.get_db()
        try:
            await db.execute("CREATE TABLE samples (id INTEGER PRIMARY KEY, value TEXT)")
            await db.executemany("INSERT INTO samples(value) VALUES (?)", [(v,) for v in values])
            await db.commit()
        finally:
            await db.close()
        rows = await database.execute_query("SELECT value FROM samples ORDER BY id", source="test")
        assert rows == [{"value": v, "_source": "test"} for v in values]
        for value in values:
            matches = await database.execute_query(
                "SELECT value FROM samples WHERE value = ?", [value]
            )
            assert matches == [{"value": v} for v in values if v == value]

    with (
        tempfile.TemporaryDirectory() as directory,
        patch.object(database.settings, "db_path", str(Path(directory) / "test.sqlite")),
    ):
        asyncio.run(check())
