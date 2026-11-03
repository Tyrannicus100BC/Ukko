"""Summarize an existing real run without opening a mind or modifying its DB."""
import argparse
import json
import sqlite3
import statistics
from collections import Counter
from pathlib import Path


def distribution(values):
    return ({"n": len(values), "min": min(values),
             "median": statistics.median(values), "max": max(values)}
            if values else {"n": 0})


def summarize(runtime):
    rows = [json.loads(line) for line in (runtime / "journal.jsonl").read_text().splitlines()]
    manifest = json.loads((runtime / "manifest.json").read_text())
    choices = [row for row in rows if row["kind"] == "attention.choice"]
    cycles, episodes = [], []
    episode = None
    for row in rows:
        if row["kind"] == "awake":
            episode = {"started_ts": row["ts"], "decisions": 0, "errors": 0}
            episodes.append(episode)
        elif episode is not None:
            if row["kind"] == "attention.choice":
                episode["decisions"] += 1
            if row["kind"] in ("error", "generation.error"):
                episode["errors"] += 1
            if row["kind"] == "shutdown":
                episode.update(stopped_ts=row["ts"], checkpoint_tick=row["tick"])
                episode = None
    for choice in choices:
        metrics = choice.get("metrics", {})
        selection, thought = metrics.get("selection", {}), metrics.get("thought", {})
        cycles.append({
            "ts": choice["ts"], "selected_id": choice["selected_id"],
            "selector": choice["selector"],
            "selected_top_rank": choice["selected_id"] == choice["shortlist"][0]["id"],
            "selected_kind": next(c["kind"] for c in choice["shortlist"]
                                  if c["id"] == choice["selected_id"]),
            "thought_completed": choice["thought_completed"],
            "selection": selection, "thought": thought,
            "generation_wall_s": selection.get("wall_s", 0) + thought.get("wall_s", 0),
        })
    attempts = [a for c in cycles for lane in ("selection", "thought")
                for a in c[lane].get("json_attempts", [])]
    with sqlite3.connect(f"file:{runtime / 'mind.db'}?mode=ro", uri=True) as db:
        memory_groups = [dict(zip(("kind", "source", "epistemic", "count"), row))
                         for row in db.execute("SELECT kind,source,epistemic,COUNT(*) "
                                               "FROM memories GROUP BY kind,source,epistemic")]
        attention_groups = [dict(zip(("kind", "status", "count"), row))
                            for row in db.execute("SELECT kind,status,COUNT(*) "
                                                  "FROM attention_items GROUP BY kind,status")]
        integrity = db.execute("PRAGMA quick_check").fetchone()[0]
        embedding_groups = [dict(zip(("bytes_per_vector", "count"), row))
                            for row in db.execute("SELECT LENGTH(embedding),COUNT(*) "
                                                  "FROM memories GROUP BY LENGTH(embedding)")]
        recalled = db.execute("SELECT COUNT(*) FROM memories WHERE access_count>0").fetchone()[0]
    return {
        "model": manifest["model"], "model_digest": manifest["model_digest"],
        "runtime": str(runtime), "episodes": episodes, "cycles": cycles,
        "counts": dict(Counter(row["kind"] for row in rows)),
        "completed_thoughts": sum(c["thought_completed"] for c in cycles),
        "selection_fallbacks": sum(c["selector"] != "model" for c in cycles),
        "top_rank_choices": sum(c["selected_top_rank"] for c in cycles),
        "json_attempts": len(attempts),
        "accepted_json_attempts": sum(a.get("parsed", False) for a in attempts),
        "parse_measure": "Accepted by the existing lenient parser; strict JSON and truncation are not separately measured",
        "generation_wall_s": distribution([c["generation_wall_s"] for c in cycles]),
        "memory_groups": memory_groups, "attention_groups": attention_groups,
        "database_quick_check": integrity,
        "stored_embedding_groups": embedding_groups, "memories_recalled": recalled,
        "startup_issue": manifest.get("startup_issue"),
        "restart_check": (json.loads((runtime / "restart_check.json").read_text())
                          if (runtime / "restart_check.json").exists() else None),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.runtime.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("completed_thoughts", "selection_fallbacks",
                                           "json_attempts", "generation_wall_s")}))


if __name__ == "__main__":
    main()
