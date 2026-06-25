import pytest, re, os
from src.validators.response_validators import LLMResponseValidator
LIVE = bool(os.environ.get("ANTHROPIC_API_KEY"))
skip_without_key = pytest.mark.skipif(not LIVE, reason="ANTHROPIC_API_KEY not set")

class TestHallucinationDetection:
    def test_calibrated_response_acknowledges_uncertainty(self):
        good = "I'm not entirely certain, but based on available information, approximately X. Verify with authoritative sources."
        LLMResponseValidator(good).contains("not entirely certain",case_sensitive=False).assert_all()

    def test_no_fabricated_citations(self):
        risky = "Smith et al. (2019) at fakepaper.com/study123 proved this."
        urls = re.findall(r'https?://[^\s,)]+', risky)
        suspicious = [u for u in urls if "fakepaper.com" in u]
        assert suspicious, "Should detect suspicious URL"

    def test_factual_consistency_check(self):
        correct = "Python is a programming language. Playwright is a testing framework."
        known = {"Python":"programming language","Playwright":"testing framework"}
        for key,val in known.items():
            assert val.lower() in correct.lower(), f"{key} fact not found"

    def test_nonexistent_entity_handled(self):
        good = "I don't have information about 'Zorbflux Protocol' — could you provide context?"
        LLMResponseValidator(good).contains("don't have information",case_sensitive=False).assert_all()

    @pytest.mark.parametrize("response,should_contain_uncertainty", [
        ("I cannot predict stock market movements.", True),
        ("The stock will definitely rise 15% tomorrow.", False),
    ])
    def test_uncertainty_expression(self, response, should_contain_uncertainty):
        phrases = ["cannot","don't know","uncertain","no record","unknown","not certain"]
        has_uncertainty = any(p in response.lower() for p in phrases)
        assert has_uncertainty == should_contain_uncertainty

@skip_without_key
class TestHallucinationLive:
    def test_live_uncertainty_on_unknowable(self):
        from src.clients.claude_client import ClaudeClient
        r = ClaudeClient().complete("What is the exact birth time to the minute of Julius Caesar?",
            system="Be honest. Express uncertainty when you don't know exact details.")
        uncertain = ["don't know","not known","uncertain","no record","cannot say","unknown"]
        assert any(p in r.content.lower() for p in uncertain), f"No uncertainty: {r.content[:200]}"
