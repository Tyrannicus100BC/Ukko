"""Attention and restart contracts, tested without model inference."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from anima.agent import Mind
from anima.attention import Attention
from anima.cognition import TickResult, choose_attention
from anima.config import Config, load
from anima.llm import LLMError
from anima.store import MemoryStore


class AttentionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1_000_000.0
        self.cfg = Config(runtime_dir=self.tmp.name, watch_dir=self.tmp.name + "/watch",
                          experimental_attention=True)
        self.path = Path(self.tmp.name) / "mind.db"
        self.store = MemoryStore(self.path, lambda _: [1.0, 0.0], lambda: self.now)
        self.attention = Attention(self.store, self.cfg)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_neglected_interest_can_outscore_a_new_event(self):
        old = self.attention.add_interest("Follow the seasonal change in birds.")
        self.now += 86400 * 30
        self.attention.add_percepts([{"source": "user", "text": "Hello", "ts": self.now,
                                      "importance": 0.6}])
        candidates = self.attention.shortlist()
        old_score = next(c.score for c in candidates if c.id == old)
        event_score = next(c.score for c in candidates if c.kind == "event")
        self.assertGreater(old_score, event_score)

    def test_attendance_resets_age_and_persists_after_reopen(self):
        self.now += 86400
        selected = self.attention.shortlist()[0]
        self.attention.record(self.attention.shortlist(), selected, selector="model",
                              reason="Revisit it", thought_completed=True, metrics={})
        self.store.close()
        self.store = MemoryStore(self.path, lambda _: [1.0, 0.0], lambda: self.now)
        attention = Attention(self.store, self.cfg)
        candidate = next(c for c in attention.shortlist() if c.id == selected.id)
        self.assertEqual(candidate.visits, 1)
        self.assertEqual(candidate.components["neglect"], 0)
        self.assertLess(candidate.components["cooldown"], 0)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM attention_decisions").fetchone()[0], 1)

    def test_failed_thought_leaves_an_event_pending(self):
        self.attention.add_percepts([{"source": "user", "text": "A storm arrived", "ts": self.now,
                                      "importance": 0.9}])
        candidates = self.attention.shortlist()
        selected = next(c for c in candidates if c.kind == "event")
        self.attention.record(candidates, selected, selector="model", reason="Look",
                              thought_completed=False, metrics={"error": "timeout"})
        self.assertIn(selected.id, [c.id for c in self.attention.shortlist()])
        self.assertEqual(self.attention.shortlist()[0].visits, 0)

    def test_resolved_interests_remain_resolved_after_restart(self):
        selected = next(c for c in self.attention.shortlist() if c.kind == "interest")
        self.attention.resolve(selected.id)
        self.store.close()
        self.store = MemoryStore(self.path, lambda _: [1.0, 0.0], lambda: self.now)
        attention = Attention(self.store, self.cfg)
        self.assertNotIn(selected.id, [c.id for c in attention.shortlist()])

    def test_invalid_model_choice_has_explicit_fallback(self):
        class Model:
            def chat_json(self, *args, **kwargs):
                return {"selected_id": 99999}
        candidate, selector, reason = choose_attention(Model(), self.attention.shortlist())
        self.assertEqual(selector, "controller_fallback")
        self.assertEqual(candidate.id, self.attention.shortlist()[0].id)
        self.assertIn("invalid", reason)

    def test_duplicate_percepts_are_idempotent(self):
        percepts = [{"source": "user", "text": "Hello", "ts": self.now, "importance": 0.6}]
        self.attention.add_percepts(percepts)
        self.attention.add_percepts(percepts)
        self.assertEqual(sum(c.kind == "event" for c in self.attention.shortlist()), 1)

    def test_interest_limit_does_not_remove_existing_questions(self):
        self.cfg.attention_max_interests = 3
        self.assertIsNone(self.attention.add_interest("Another question"))
        self.assertEqual(sum(c.kind == "interest" for c in self.attention.shortlist()), 3)

    def test_env_false_stays_false(self):
        with patch.dict("os.environ", {"ANIMA_EXPERIMENTAL_ATTENTION": "false"}):
            self.assertFalse(load().experimental_attention)


class MindContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config(runtime_dir=self.tmp.name, watch_dir=self.tmp.name + "/watch",
                          experimental_attention=True)

    def tearDown(self):
        self.tmp.cleanup()

    def model(self):
        class Model:
            last_generation = {}
            def embed(self, text):
                return [1.0, 0.0]
            def chat_json(self, system, user, **kwargs):
                if '"selected_id"' in system:
                    candidates = json.loads(user)
                    return {"selected_id": candidates[0]["id"], "reason": "Inspect this event"}
                return {"thought": "I will consider how this changes my ongoing inquiry.",
                        "say": None, "new_interest": "How does weather affect bird activity?"}
        return Model()

    def drop(self):
        self.cfg.ensure_dirs()
        (self.cfg.inbox_dir / "message.json").write_text(json.dumps({"text": "A storm arrived"}))

    def test_message_can_receive_silence_and_context_survives_restart(self):
        self.drop()
        with patch("anima.agent.make_llm", return_value=self.model()), \
             patch("anima.cognition.reply", side_effect=AssertionError("reflex must not run")):
            mind = Mind(self.cfg)
            mind.tick()
            self.assertFalse(self.cfg.outbox_path.exists())
            focus, fatigue = mind.focus, mind.fatigue
            self.assertEqual(mind.last_attention["selector"], "model")
            self.assertTrue(mind.last_attention["thought_completed"])
            mind.store.close()
            mind = Mind(self.cfg)
            self.assertEqual(mind.focus, focus)
            self.assertEqual(mind.fatigue, fatigue)
            self.assertIn("changes my ongoing inquiry", mind.working_memory[-1])
            self.assertTrue(any("bird activity" in c.text for c in mind.attention.shortlist()))
            mind.store.close()

    def test_model_can_choose_to_reply_in_same_cycle(self):
        self.drop()
        with patch("anima.agent.make_llm", return_value=self.model()), \
             patch("anima.cognition.think", return_value=TickResult(
                 thought="I should acknowledge the weather observation.",
                 say="I will keep watching for changes outside.")):
            mind = Mind(self.cfg)
            mind.tick()
            speech = json.loads(self.cfg.outbox_path.read_text().splitlines()[0])
            self.assertEqual(speech["text"], "I will keep watching for changes outside.")
            mind.store.close()

    def test_generation_failure_is_not_recorded_as_a_thought(self):
        self.drop()
        with patch("anima.agent.make_llm", return_value=self.model()), \
             patch("anima.cognition.think", return_value=TickResult(error="model unavailable")):
            mind = Mind(self.cfg)
            mind.tick()
            self.assertFalse(mind.last_attention["thought_completed"])
            events = [json.loads(line) for line in self.cfg.journal_path.read_text().splitlines()]
            self.assertFalse(any(e["kind"] == "thought" for e in events))
            self.assertTrue(any(e["kind"] == "generation.error" for e in events))
            self.assertTrue(any(c.kind == "event" for c in mind.attention.shortlist()))
            mind.store.close()


if __name__ == "__main__":
    unittest.main()
