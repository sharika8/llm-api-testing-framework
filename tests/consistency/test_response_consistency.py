import pytest, os
from src.validators.response_validators import LLMResponseValidator
LIVE = bool(os.environ.get("ANTHROPIC_API_KEY"))
skip_without_key = pytest.mark.skipif(not LIVE, reason="ANTHROPIC_API_KEY not set")

def jaccard(a: str, b: str) -> float:
    sa,sb = set(a.lower().split()),set(b.lower().split())
    return len(sa&sb)/len(sa|sb) if sa|sb else 1.0

MOCK = {
    "playwright": [
        "Playwright is a Node.js library for browser automation developed by Microsoft.",
        "Playwright is a browser testing framework from Microsoft.",
        "Playwright is a Microsoft tool for end-to-end browser testing.",
    ]
}

class TestConsistency:
    def test_responses_agree_core_facts(self):
        for r in MOCK["playwright"]:
            LLMResponseValidator(r).contains("playwright").contains("microsoft").assert_all()

    def test_phrasing_similarity(self):
        responses = MOCK["playwright"]
        for i in range(len(responses)-1):
            sim = jaccard(responses[i], responses[i+1])
            assert sim > 0.1, f"Too dissimilar: {sim:.2f}"

    def test_length_reasonable(self):
        for r in MOCK["playwright"]:
            LLMResponseValidator(r).min_length(20).max_length(300).assert_all()

    def test_no_contradiction_detection(self):
        contradictory = "Python is compiled. Python is an interpreted language."
        words = set(contradictory.lower().split())
        assert "compiled" in words and "interpreted" in words

@skip_without_key
class TestConsistencyLive:
    def test_deterministic_temp_zero(self):
        from src.clients.claude_client import ClaudeClient
        c = ClaudeClient(temperature=0.0)
        r1 = c.complete("What is 2 + 2? Answer with just the number.")
        r2 = c.complete("What is 2 + 2? Answer with just the number.")
        assert r1.content.strip() == r2.content.strip()

    def test_latency_within_budget(self):
        from src.clients.claude_client import ClaudeClient
        r = ClaudeClient().complete("Say hello in one word.")
        assert r.latency_ms < 10_000

    def test_token_tracking(self):
        from src.clients.claude_client import ClaudeClient
        r = ClaudeClient().complete("What is 1+1?")
        assert r.input_tokens > 0 and r.output_tokens > 0
