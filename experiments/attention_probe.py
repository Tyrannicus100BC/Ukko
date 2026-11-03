"""Deterministic scheduler ablation. No model, no emergent-behavior claim.

Run from the repository: python3 -m experiments.attention_probe
"""
import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path

from anima.attention import Attention
from anima.config import Config
from anima.store import MemoryStore


def scenario(age_weight: float, steps: int) -> dict:
    now = [1_000_000.0]
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(Path(tmp) / "probe.db", lambda _: [], lambda: now[0])
        cfg = Config(attention_age_weight=age_weight)
        attention = Attention(store, cfg)
        for i in range(16):
            attention.add_interest(f"Unanswered inquiry {i}")
        counts = Counter()
        for step in range(steps):
            now[0] += 20
            attention.add_percepts([{"source": "fixture", "text": f"Fresh stimulus {step}",
                                     "importance": 0.99, "ts": now[0]}])
            candidates = attention.shortlist()
            selected = candidates[0]
            counts[selected.kind] += 1
            attention.record(candidates, selected, selector="greedy_fixture",
                              reason="Highest controller score", thought_completed=True,
                              metrics={"model_calls": 0})
        coverage = store.db.execute("SELECT COUNT(*) FROM attention_items"
                                   " WHERE kind='interest' AND visits > 0").fetchone()[0]
        store.close()
        return {"age_weight": age_weight, "steps": steps, "selected_by_kind": dict(counts),
                "interests_attended": coverage, "total_interests": 19}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error("steps must be positive")
    result = {"experiment": "attention_age_ablation", "model_calls": 0,
              "claim": "Controller behavior under synthetic event pressure only",
              "without_aging": scenario(0.0, args.steps),
              "with_aging": scenario(0.8, args.steps)}
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
