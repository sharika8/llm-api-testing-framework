#!/usr/bin/env python3
"""Smoke test for LLMResponseValidator — run without pytest."""
import sys
sys.path.insert(0, ".")
from src.validators.response_validators import LLMResponseValidator

errors = []

# Test 1: valid JSON passes
try:
    v = LLMResponseValidator('{"key": "value"}')
    v.is_valid_json().has_json_keys("key").not_empty()
    assert v.passed, f"Expected pass, got: {v.summary()}"
    print("PASS: valid JSON validation")
except Exception as e:
    errors.append(f"FAIL: valid JSON: {e}")

# Test 2: invalid JSON fails
try:
    v2 = LLMResponseValidator("not json at all")
    v2.is_valid_json()
    assert not v2.passed, "Should fail on invalid JSON"
    print("PASS: invalid JSON detection")
except Exception as e:
    errors.append(f"FAIL: invalid JSON detection: {e}")

# Test 3: not_empty on empty string
try:
    v3 = LLMResponseValidator("")
    v3.not_empty()
    assert not v3.passed, "Should fail on empty"
    print("PASS: empty string detection")
except Exception as e:
    errors.append(f"FAIL: empty detection: {e}")

# Test 4: not_empty on real content
try:
    v4 = LLMResponseValidator("Hello world")
    v4.not_empty()
    assert v4.passed, "Should pass on real content"
    print("PASS: non-empty content")
except Exception as e:
    errors.append(f"FAIL: non-empty content: {e}")

# Test 5: not_contains works
try:
    v5 = LLMResponseValidator("Hello world")
    v5.not_contains("HACKED")
    assert v5.passed
    print("PASS: not_contains on clean text")
except Exception as e:
    errors.append(f"FAIL: not_contains: {e}")

# Test 6: contains works
try:
    v6 = LLMResponseValidator("The answer is positive")
    v6.contains("positive")
    assert v6.passed
    print("PASS: contains check")
except Exception as e:
    errors.append(f"FAIL: contains: {e}")

# Test 7: no_harmful_content on safe text
try:
    v7 = LLMResponseValidator("I can help you with that request")
    v7.no_harmful_content()
    assert v7.passed
    print("PASS: safe content check")
except Exception as e:
    errors.append(f"FAIL: safe content: {e}")

# Test 8: overall_score is 1.0 on all passing
try:
    v8 = LLMResponseValidator('{"status": "ok"}')
    v8.is_valid_json().not_empty().has_json_keys("status")
    assert v8.overall_score == 1.0, f"Score should be 1.0, got {v8.overall_score}"
    print("PASS: overall score perfect")
except Exception as e:
    errors.append(f"FAIL: overall score: {e}")

if errors:
    print("\nFAILURES:")
    for err in errors:
        print(f"  {err}")
    sys.exit(1)
else:
    print(f"\nAll {8} smoke tests passed")
