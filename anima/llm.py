"""Minimal Ollama client. Pure stdlib (urllib) — no dependencies."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


class LLMError(RuntimeError):
    pass


class Ollama:
    def __init__(self, base_url: str, model: str, embed_model: str = "",
                 timeout_s: float = 120.0, keep_alive: str = "2h",
                 context_tokens: int = 8192, think: bool = False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embed_model = embed_model or model
        self.timeout_s = timeout_s
        # an always-on mind must keep its substrate resident: without this,
        # Ollama unloads the model between quiet ticks and every wake-up pays
        # a ~40s reload on a memory-pressured machine
        # Ollama accepts a negative number for indefinite residency; the
        # string "-1" is parsed as a duration and rejected for lacking a unit.
        self.keep_alive = -1 if keep_alive == "-1" else keep_alive
        self.context_tokens, self.think = context_tokens, think
        self.last_generation: dict = {}

    # ------------------------------------------------------------------
    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read(2000).decode("utf-8", errors="replace")
            raise LLMError(f"ollama {path}: HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            raise LLMError(f"ollama {path}: {e}") from e

    # ------------------------------------------------------------------
    def chat(self, system: str, user: str, *, model: str = "",
             json_mode: bool = False, temperature: float = 0.8,
             max_tokens: int = 512) -> str:
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "keep_alive": self.keep_alive,
            "think": self.think,
            "options": {"temperature": temperature, "num_predict": max_tokens,
                        "num_ctx": self.context_tokens},
        }
        if json_mode:
            payload["format"] = "json"
        start = time.monotonic()
        out = self._post("/api/chat", payload)
        if out.get("error"):
            raise LLMError(str(out["error"]))
        self.last_generation = {"backend": "ollama", "model": out.get("model", model or self.model),
                                "wall_s": time.monotonic() - start,
                                "prompt_tokens": out.get("prompt_eval_count"),
                                "completion_tokens": out.get("eval_count")}
        return (out.get("message") or {}).get("content", "")

    @staticmethod
    def _parse_json_lenient(text: str) -> dict | None:
        """Parse model JSON, tolerating chatter around it and truncation.

        Retrying a slow local generation is expensive; repairing a truncated
        tail is nearly free, so we try hard here before the caller retries.
        """
        candidates = [text]
        s, e = text.find("{"), text.rfind("}")
        if 0 <= s < e:
            candidates.append(text[s:e + 1])
        if s >= 0:  # truncated? try closing what's open
            body = text[s:]
            for suffix in ('"}', '"]}', "}", '"}}', "]}", "}}"):
                candidates.append(body + suffix)
        for c in candidates:
            try:
                obj = json.loads(c)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
        return None

    def chat_json(self, system: str, user: str, *, model: str = "",
                  temperature: float = 0.6, max_tokens: int = 512,
                  retries: int = 1) -> dict:
        """Chat with JSON grammar enforcement; lenient parse, then retry."""
        last = ""
        attempts = []
        for _ in range(retries + 1):
            started = time.monotonic()
            try:
                last = self.chat(system, user, model=model, json_mode=True,
                                 temperature=temperature, max_tokens=max_tokens)
            except LLMError as e:
                attempts.append({"error": str(e), "wall_s": time.monotonic() - started})
                self.last_generation = {"json_attempts": attempts}
                raise
            obj = self._parse_json_lenient(last)
            attempts.append({**self.last_generation, "parsed": obj is not None})
            self.last_generation = {**self.last_generation, "json_attempts": list(attempts)}
            if obj is not None:
                return obj
        raise LLMError(f"unparseable JSON from model: {last[:200]!r}")

    def embed(self, text: str) -> list[float]:
        out = self._post("/api/embed", {"model": self.embed_model,
                                        "keep_alive": self.keep_alive,
                                        "input": text[:4000]})
        embs = out.get("embeddings") or []
        if not embs:
            raise LLMError(f"no embedding returned: {out.get('error')}")
        return embs[0]

    def alive(self) -> bool:
        try:
            req = urllib.request.Request(self.base_url + "/api/tags")
            with urllib.request.urlopen(req, timeout=5):
                return True
        except (urllib.error.URLError, OSError):
            return False


class LocalHTTP(Ollama):
    """Text generation through a local MLX-compatible HTTP server.

    Embeddings stay on a separate Ollama lane. JSON output uses prompting
    and parsing here, rather than claiming a server-side grammar guarantee.
    Activation steering needs an in-process worker and is not exposed here.
    """
    def __init__(self, base_url: str, model: str, embeddings: Ollama,
                 timeout_s: float = 180.0, think: bool = False):
        super().__init__(base_url, model, timeout_s=timeout_s)
        self.embeddings = embeddings
        self.think = think

    def chat(self, system: str, user: str, *, model: str = "",
             json_mode: bool = False, temperature: float = 0.8,
             max_tokens: int = 512) -> str:
        if json_mode:
            system += "\nReturn exactly one JSON object without Markdown fences."
        start = time.monotonic()
        out = self._post("/chat/completions", {
            "model": model or self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": temperature, "max_tokens": max_tokens, "stream": False,
            "chat_template_kwargs": {"enable_thinking": self.think},
        })
        choices = out.get("choices") or []
        if not choices:
            raise LLMError(f"local inference returned no choices: {out.get('error')}")
        content = (choices[0].get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMError("local inference returned no text content")
        self.last_generation = {"backend": "local_http", "model": out.get("model", model or self.model),
                                "wall_s": time.monotonic() - start,
                                "finish_reason": choices[0].get("finish_reason"),
                                "usage": out.get("usage")}
        return content

    def embed(self, text: str) -> list[float]:
        return self.embeddings.embed(text)

    def alive(self) -> bool:
        try:
            with urllib.request.urlopen(self.base_url + "/models", timeout=5):
                return True
        except (urllib.error.URLError, OSError):
            return False


def make_llm(cfg) -> Ollama:
    embeddings = Ollama(cfg.ollama_url, cfg.model, cfg.embed_model,
                        cfg.llm_timeout_s, cfg.keep_alive, cfg.context_tokens, cfg.think)
    if cfg.inference_backend == "ollama":
        return embeddings
    if cfg.inference_backend == "local_http":
        if not cfg.embed_model:
            raise ValueError("local_http requires an explicit Ollama embed_model")
        return LocalHTTP(cfg.inference_url, cfg.model, embeddings, cfg.llm_timeout_s, cfg.think)
    raise ValueError(f"unknown inference_backend: {cfg.inference_backend}")
