"""Configuration for Anima.

Everything time-related is tunable so the whole life cycle (wake, fatigue,
sleep, decay) can be compressed for testing and demos.
"""
from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # --- substrate -------------------------------------------------------
    ollama_url: str = "http://localhost:11434"
    model: str = "gemma:2b"            # waking-thought + embedding model
    deep_model: str = ""               # optional larger model for sleep work ("" = use model)
    embed_model: str = ""              # "" = use model
    llm_timeout_s: float = 180.0
    max_thought_tokens: int = 220
    temperature: float = 0.8
    inference_backend: str = "ollama"  # "local_http" for an MLX-compatible server
    inference_url: str = "http://127.0.0.1:8080/v1"
    keep_alive: str = "-1"
    context_tokens: int = 8192
    think: bool = False               # Ollama reasoning mode; JSON cycles stay bounded

    # --- experimental attention (opt in; upstream behavior remains available) ---
    experimental_attention: bool = False
    attention_slots: int = 6
    attention_age_s: float = 600.0
    attention_age_weight: float = 0.8
    attention_cooldown_s: float = 60.0
    attention_max_interests: int = 64

    # --- filesystem ------------------------------------------------------
    runtime_dir: str = ""              # resolved in load(); holds db, journal, inbox, outbox
    watch_dir: str = ""                # sensor: files dropped here get noticed

    # --- heartbeat / arousal ---------------------------------------------
    tick_base_s: float = 20.0          # tick interval right after activity
    tick_max_s: float = 300.0          # slowest idle tick
    tick_backoff: float = 1.5          # idle interval multiplier per quiet tick

    # --- fatigue / sleep pressure ----------------------------------------
    fatigue_per_tick: float = 1.0
    fatigue_sleep_threshold: float = 30.0   # sleep pressure reaches 1.0 here
    idle_before_sleep_s: float = 180.0      # don't sleep mid-conversation
    max_wake_s: float = 6 * 3600.0          # hard circadian cap on time awake

    # --- memory ----------------------------------------------------------
    retrieve_k: int = 6
    w_recency: float = 1.0
    w_importance: float = 1.0
    w_relevance: float = 1.5
    recency_tau_h: float = 24.0        # recency half-life-ish time constant (hours)
    reinforce_on_access: float = 0.10  # strength bump when a memory is retrieved
    decay_lambda: float = 0.12         # per-day base decay applied during sleep
    decay_stability_access: float = 0.6   # each access slows decay by this factor
    decay_stability_importance: float = 2.0
    archive_threshold: float = 0.15    # strength below this -> archived (forgotten)
    purge_archive_days: float = 30.0   # archived memories are erased after this

    # --- sleep architecture ----------------------------------------------
    consolidation_cluster_sim: float = 0.55  # cosine sim to group episodics
    consolidation_max_batch: int = 8
    reflection_top_k: int = 12
    dreams_per_sleep: int = 2
    dream_sample_n: int = 5

    # --- behavior ---------------------------------------------------------
    proactive_min_gap_s: float = 600.0  # min seconds between unprompted utterances
    working_memory_n: int = 12          # journal entries kept in the tick prompt
    agent_name: str = "Anima"
    user_name: str = "Dai"

    # ----------------------------------------------------------------------
    @property
    def runtime(self) -> Path:
        return Path(self.runtime_dir)

    @property
    def db_path(self) -> Path:
        return self.runtime / "mind.db"

    @property
    def journal_path(self) -> Path:
        return self.runtime / "journal.jsonl"

    @property
    def outbox_path(self) -> Path:
        return self.runtime / "outbox.jsonl"

    @property
    def inbox_dir(self) -> Path:
        return self.runtime / "inbox"

    @property
    def state_path(self) -> Path:
        return self.runtime / "state.json"

    @property
    def dream_journal_path(self) -> Path:
        return self.runtime / "dreams.jsonl"

    def ensure_dirs(self) -> None:
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        if self.watch_dir:
            Path(self.watch_dir).mkdir(parents=True, exist_ok=True)


def load(path: str | None = None) -> Config:
    """Load config: defaults <- optional JSON file (ANIMA_CONFIG) <- env vars."""
    cfg = Config()
    root = Path(__file__).resolve().parent.parent
    cfg.runtime_dir = str(root / "runtime")
    cfg.watch_dir = str(root / "runtime" / "watch")

    path = path or os.environ.get("ANIMA_CONFIG", "")
    if path and Path(path).exists():
        data = json.loads(Path(path).read_text())
        known = {f.name for f in dataclasses.fields(Config)}
        for k, v in data.items():
            if k in known:
                setattr(cfg, k, v)

    for f in dataclasses.fields(Config):
        env = os.environ.get("ANIMA_" + f.name.upper())
        if env is not None:
            cast = f.type if isinstance(f.type, type) else type(getattr(cfg, f.name))
            try:
                if cast is bool:
                    if env.lower() not in ("true", "false", "1", "0"):
                        raise ValueError(f"{f.name} must be true/false or 1/0")
                    setattr(cfg, f.name, env.lower() in ("true", "1"))
                else:
                    setattr(cfg, f.name, cast(env) if cast is not str else env)
            except (TypeError, ValueError):
                raise ValueError(f"invalid configuration value for {f.name}") from None
    return cfg
