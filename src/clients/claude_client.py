# src/clients/claude_client.py
from __future__ import annotations
import os, time, logging
from dataclasses import dataclass
from typing import Any
log = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    content: str; model: str; input_tokens: int; output_tokens: int
    stop_reason: str; latency_ms: float
    @property
    def total_tokens(self) -> int: return self.input_tokens + self.output_tokens

class ClaudeClient:
    """Wrapper around Anthropic Claude API for LLM testing."""
    def __init__(self, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 1024, temperature: float = 0.0) -> None:
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY",""))
        except ImportError:
            self._client = None
        self.model = model; self.max_tokens = max_tokens; self.temperature = temperature

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY")) and self._client is not None

    def complete(self, prompt: str, system: str | None = None, max_retries: int = 3) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        messages = [{"role": "user", "content": prompt}]
        kwargs: dict[str, Any] = {"model": self.model, "max_tokens": self.max_tokens, "messages": messages}
        if system: kwargs["system"] = system
        for attempt in range(1, max_retries + 1):
            try:
                start = time.perf_counter()
                response = self._client.messages.create(**kwargs)
                latency_ms = (time.perf_counter() - start) * 1000
                content = "".join(b.text for b in response.content if hasattr(b, "text"))
                return LLMResponse(content=content, model=response.model, input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens, stop_reason=response.stop_reason or "end_turn", latency_ms=latency_ms)
            except Exception as exc:
                log.warning("Attempt %d/%d: %s", attempt, max_retries, exc)
                if attempt == max_retries: raise
                time.sleep(2 ** attempt)
        raise RuntimeError("unreachable")

    def complete_json(self, prompt: str, system: str | None = None) -> dict:
        import json
        sys = ((system or "") + "\nRespond with valid JSON only. No explanation, no markdown.").strip()
        response = self.complete(prompt, system=sys)
        cleaned = response.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(cleaned)
