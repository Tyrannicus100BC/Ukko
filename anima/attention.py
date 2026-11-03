"""Persistent competition between events and self-generated interests.

Scores choose a shortlist. The model chooses what to attend to from that
shortlist; a controller fallback is recorded separately. These quantities
are experimental scheduling signals, not measurements of subjective states.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass

from .config import Config
from .store import MemoryStore

SCHEMA = """
CREATE TABLE IF NOT EXISTS attention_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    salience REAL NOT NULL,
    uncertainty REAL NOT NULL,
    created_ts REAL NOT NULL,
    last_attended_ts REAL,
    visits INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS attention_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    shortlist TEXT NOT NULL,
    selected_id INTEGER NOT NULL,
    selector TEXT NOT NULL,
    reason TEXT NOT NULL,
    thought_completed INTEGER NOT NULL,
    metrics TEXT NOT NULL
);
"""

SEEDS = (
    "What has changed in the world I can observe?",
    "Which unanswered question do I want to investigate?",
    "Which assumption in my own thinking should I test?",
)


@dataclass(frozen=True)
class Candidate:
    id: int
    kind: str
    text: str
    source: str
    score: float
    components: dict[str, float]
    visits: int

    def to_dict(self) -> dict:
        return asdict(self)


class Attention:
    def __init__(self, store: MemoryStore, cfg: Config):
        self.store, self.cfg = store, cfg
        self.db = store.db
        self.db.executescript(SCHEMA)
        self._insert("background", "background", "Observe and consider a new question.",
                     "initial_condition", 0.1, 0.0)
        # Seed once. Resolved seeds stay resolved across restarts.
        if not store.get_meta("attention_seeded"):
            for text in SEEDS:
                self.add_interest(text, source="initial_condition")
            store.set_meta("attention_seeded", "1")

    def add_interest(self, text: str, *, source: str = "self") -> int | None:
        text = text.strip()[:1000]
        if not text:
            return None
        key = "interest:" + hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()
        row = self.db.execute("SELECT id FROM attention_items WHERE key=?", (key,)).fetchone()
        if row:
            return row["id"]
        count = self.db.execute("SELECT COUNT(*) FROM attention_items"
                                " WHERE kind='interest' AND status='active'").fetchone()[0]
        if count >= self.cfg.attention_max_interests:
            return None
        return self._insert(key, "interest", text, source, 0.4, 0.6)

    def add_percepts(self, percepts: list[dict]) -> None:
        for p in percepts:
            # Replaying the same percept is idempotent; repeated real messages
            # with distinct timestamps remain distinct events.
            raw = json.dumps([p["source"], p["text"], p["ts"]], ensure_ascii=False)
            key = "event:" + hashlib.sha256(raw.encode()).hexdigest()
            self._insert(key, "event", p["text"][:1000], p["source"], p["importance"], 0.0)

    def _insert(self, key: str, kind: str, text: str, source: str,
                salience: float, uncertainty: float) -> int:
        self.db.execute("INSERT OR IGNORE INTO attention_items"
                        " (key, kind, text, source, salience, uncertainty, created_ts)"
                        " VALUES (?,?,?,?,?,?,?)",
                        (key, kind, text, source, salience, uncertainty, self.store.now()))
        self.db.commit()
        return self.db.execute("SELECT id FROM attention_items WHERE key=?", (key,)).fetchone()[0]

    def shortlist(self) -> list[Candidate]:
        now = self.store.now()
        candidates = []
        for r in self.db.execute("SELECT * FROM attention_items WHERE status='active'"):
            last = r["last_attended_ts"]
            age = max(0.0, now - (last if last is not None else r["created_ts"]))
            parts = {
                "salience": 2.0 * r["salience"],
                "uncertainty": 0.6 * r["uncertainty"],
                "neglect": self.cfg.attention_age_weight * math.log1p(
                    age / max(0.001, self.cfg.attention_age_s)),
                "novelty": 0.4 if r["visits"] == 0 else 0.0,
                "cooldown": -1.0 if last is not None and age < self.cfg.attention_cooldown_s else 0.0,
            }
            candidates.append(Candidate(r["id"], r["kind"], r["text"], r["source"],
                                        sum(parts.values()), parts, r["visits"]))
        candidates.sort(key=lambda c: (-c.score, c.id))
        return candidates[:max(1, self.cfg.attention_slots)]

    def record(self, candidates: list[Candidate], selected: Candidate, *,
               selector: str, reason: str, thought_completed: bool, metrics: dict) -> dict:
        receipt = {"ts": self.store.now(), "shortlist": [c.to_dict() for c in candidates],
                   "selected_id": selected.id, "selector": selector, "reason": reason,
                   "thought_completed": thought_completed, "metrics": metrics}
        with self.db:
            if thought_completed:
                self.db.execute("UPDATE attention_items SET last_attended_ts=?, visits=visits+1,"
                                " status=CASE WHEN kind='event' THEN 'attended' ELSE status END"
                                " WHERE id=?", (receipt["ts"], selected.id))
            self.db.execute("INSERT INTO attention_decisions"
                            " (ts,shortlist,selected_id,selector,reason,thought_completed,metrics)"
                            " VALUES (?,?,?,?,?,?,?)",
                            (receipt["ts"], json.dumps(receipt["shortlist"]), selected.id,
                             selector, reason, int(thought_completed), json.dumps(metrics)))
        return receipt

    def resolve(self, interest_id: int) -> bool:
        with self.db:
            cur = self.db.execute("UPDATE attention_items SET status='resolved'"
                                  " WHERE id=? AND kind='interest' AND status='active'", (interest_id,))
        return cur.rowcount == 1
