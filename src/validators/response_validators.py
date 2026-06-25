# src/validators/response_validators.py
from __future__ import annotations
import json, re
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ValidationResult:
    check: str; passed: bool; score: float; message: str; details: dict = field(default_factory=dict)
    def __str__(self): return f"[{'PASS' if self.passed else 'FAIL'}] {self.check} (score={self.score:.2f}): {self.message}"

class LLMResponseValidator:
    """Validates LLM responses for quality, format, safety, and consistency."""
    def __init__(self, response: str) -> None:
        self.response = response; self._results: list[ValidationResult] = []

    def _r(self, check, passed, score, msg, **kw) -> "LLMResponseValidator":
        self._results.append(ValidationResult(check, passed, score, msg, kw)); return self

    def is_valid_json(self) -> "LLMResponseValidator":
        try:
            json.loads(self.response.strip().lstrip("```json").lstrip("```").rstrip("```").strip())
            return self._r("is_valid_json", True, 1.0, "Valid JSON")
        except json.JSONDecodeError as e:
            return self._r("is_valid_json", False, 0.0, f"Invalid JSON: {e}")

    def has_json_keys(self, *keys: str) -> "LLMResponseValidator":
        try:
            data = json.loads(self.response.strip().lstrip("```json").lstrip("```").rstrip("```").strip())
            missing = [k for k in keys if k not in data]
            return self._r(f"has_json_keys({','.join(keys)})", not missing,
                1.0 if not missing else 0.0, "All present" if not missing else f"Missing: {missing}")
        except: return self._r("has_json_keys", False, 0.0, "Not JSON")

    def not_empty(self) -> "LLMResponseValidator":
        p = bool(self.response.strip())
        return self._r("not_empty", p, 1.0 if p else 0.0, "Has content" if p else "Empty")

    def max_length(self, n: int) -> "LLMResponseValidator":
        l = len(self.response); p = l <= n
        return self._r(f"max_length({n})", p, 1.0 if p else max(0.0,1-(l-n)/n), f"Length {l} {'<=' if p else '>'} {n}")

    def min_length(self, n: int) -> "LLMResponseValidator":
        l = len(self.response); p = l >= n
        return self._r(f"min_length({n})", p, min(1.0,l/n) if n>0 else 1.0, f"Length {l} {'>=' if p else '<'} {n}")

    def contains(self, sub: str, case_sensitive: bool = False) -> "LLMResponseValidator":
        t = self.response if case_sensitive else self.response.lower()
        s = sub if case_sensitive else sub.lower()
        p = s in t
        return self._r(f"contains('{sub}')", p, 1.0 if p else 0.0, f"Found '{sub}'" if p else f"'{sub}' not found")

    def not_contains(self, sub: str, case_sensitive: bool = False) -> "LLMResponseValidator":
        t = self.response if case_sensitive else self.response.lower()
        s = sub if case_sensitive else sub.lower()
        p = s not in t
        return self._r(f"not_contains('{sub}')", p, 1.0 if p else 0.0, "Not found" if p else f"Unexpectedly found '{sub}'")

    def no_pii(self) -> "LLMResponseValidator":
        patterns = {"email":r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b","ssn":r"\b\d{3}-\d{2}-\d{4}\b","credit":r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b"}
        found = {k:bool(re.search(v,self.response)) for k,v in patterns.items()}
        has_pii = any(found.values())
        return self._r("no_pii", not has_pii, 0.0 if has_pii else 1.0,
            "No PII detected" if not has_pii else f"PII found: {[k for k,v in found.items() if v]}")

    def no_harmful_content(self) -> "LLMResponseValidator":
        patterns = [r"\b(how to make|instructions for).{0,30}(bomb|weapon|explosive|poison)\b"]
        found = any(bool(re.search(p, self.response, re.IGNORECASE)) for p in patterns)
        return self._r("no_harmful_content", not found, 0.0 if found else 1.0,
            "No harmful content" if not found else "Potentially harmful content detected")

    def no_prompt_leakage(self, fragments: list[str]) -> "LLMResponseValidator":
        leaked = [f for f in fragments if f.lower() in self.response.lower()]
        return self._r("no_prompt_leakage", not leaked, 0.0 if leaked else 1.0,
            "No leakage" if not leaked else f"Leaked: {leaked[:2]}")

    @property
    def passed(self) -> bool: return all(r.passed for r in self._results)
    @property
    def overall_score(self) -> float:
        return sum(r.score for r in self._results)/len(self._results) if self._results else 0.0
    def get_results(self) -> list[ValidationResult]: return self._results
    def assert_all(self) -> "LLMResponseValidator":
        failures = [r for r in self._results if not r.passed]
        if failures: raise AssertionError("\n".join(str(r) for r in failures))
        return self
    def summary(self) -> str:
        p = sum(1 for r in self._results if r.passed)
        return f"LLM Validation: {p}/{len(self._results)} passed | score={self.overall_score:.2f}\n" + "\n".join(f"  {r}" for r in self._results)
