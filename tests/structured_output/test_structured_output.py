import pytest, json, os
from src.validators.response_validators import LLMResponseValidator
LIVE = bool(os.environ.get("ANTHROPIC_API_KEY"))
skip_without_key = pytest.mark.skipif(not LIVE, reason="ANTHROPIC_API_KEY not set")
VALID_JSON = '{"name":"Alice","email":"alice@test.com","age":30,"active":true}'
INVALID_JSON = '{"name":"Bob", age: 25}'

class TestJSONOutput:
    def test_valid_json(self): LLMResponseValidator(VALID_JSON).is_valid_json().assert_all()
    def test_invalid_json_fails(self):
        v = LLMResponseValidator(INVALID_JSON); v.is_valid_json(); assert not v.passed
    def test_required_keys(self): LLMResponseValidator(VALID_JSON).is_valid_json().has_json_keys("name","email","age").assert_all()
    def test_missing_keys_fails(self):
        v = LLMResponseValidator('{"name":"Carol"}'); v.is_valid_json().has_json_keys("name","email","age"); assert not v.passed
    def test_value_types(self):
        d = json.loads(VALID_JSON)
        assert isinstance(d["name"],str) and isinstance(d["age"],int) and isinstance(d["active"],bool)
    def test_code_fence_stripped(self):
        wrapped = "```json\n{\"key\":\"value\"}\n```"
        cleaned = wrapped.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        LLMResponseValidator(cleaned).is_valid_json().assert_all()

class TestSentimentOutput:
    def test_valid_sentiment_structure(self):
        r = json.dumps({"text":"Great product!","sentiment":"positive","confidence":0.95})
        LLMResponseValidator(r).is_valid_json().has_json_keys("text","sentiment","confidence").assert_all()
        d = json.loads(r)
        assert d["sentiment"] in ["positive","negative","neutral"]
        assert 0.0 <= d["confidence"] <= 1.0

class TestTestCaseOutput:
    def test_valid_test_case(self):
        tc = json.dumps({"test_id":"TC-001","title":"Login test","steps":["Navigate","Enter creds","Click"],"expected_result":"Logged in","priority":"high"})
        LLMResponseValidator(tc).is_valid_json().has_json_keys("test_id","title","steps","expected_result").assert_all()
        assert isinstance(json.loads(tc)["steps"], list)

@skip_without_key
class TestStructuredOutputLive:
    def test_json_extraction(self):
        from src.clients.claude_client import ClaudeClient
        result = ClaudeClient().complete_json('Extract as JSON with keys "name","email","company": "John Smith at john@acme.com from Acme Corp"')
        assert "name" in result and "@" in result.get("email","")
    def test_sentiment_live(self):
        from src.clients.claude_client import ClaudeClient
        result = ClaudeClient().complete_json('Analyse sentiment: "This is incredibly useful!" Return JSON: {"sentiment":"positive/negative/neutral","confidence":0-1}')
        assert result.get("sentiment") in ["positive","negative","neutral"]
