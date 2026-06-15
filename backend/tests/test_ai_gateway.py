"""Tests for the upgraded AI gateway: capabilities, validation, routing policies."""
from __future__ import annotations

from app.ai.capabilities import (
    estimate_cost_tokens,
    get_capability,
    models_for_provider,
    supports,
)
from app.ai.router import AIRouter, CustomerPolicy, normalize_mode, select_model
from app.ai.validation import (
    coerce_investigation,
    completeness_warnings,
    is_valid_investigation,
    parse_json_lenient,
    repair_json,
)


# --- Capability registry ---------------------------------------------------
def test_local_model_is_zero_cost_and_private():
    cap = get_capability("llama3.1", "ollama")
    assert cap.privacy_level == "local"
    assert cap.cost_per_input_token == 0.0
    assert estimate_cost_tokens("llama3.1", 1000, 1000, "ollama") == 0.0


def test_cloud_model_has_cost_and_capabilities():
    assert supports("gpt-4.1", "supports_json")
    assert supports("gpt-4.1", "supports_vision")
    assert estimate_cost_tokens("gpt-4.1", 1_000_000, 1_000_000) > 0


def test_unknown_model_falls_back_to_provider_default():
    cap = get_capability("some-unknown", "ollama")
    assert cap.privacy_level == "local"
    assert models_for_provider("openai")


# --- Routing policy aliases ------------------------------------------------
def test_routing_policy_aliases_normalize():
    assert normalize_mode("cost_optimized") == "cost"
    assert normalize_mode("quality_optimized") == "quality"
    assert normalize_mode("privacy_optimized") == "privacy"
    assert normalize_mode("local_only") == "privacy"
    assert normalize_mode("speed_optimized") == "speed"
    assert normalize_mode("critical_alert_mode") == "soc_critical"
    assert normalize_mode("offline_demo") == "offline"
    assert normalize_mode("nonsense") == "auto"


def test_router_accepts_public_policy_name():
    r = AIRouter(mode="local_only")
    assert r.mode == "privacy"
    chain = r.build_chain(CustomerPolicy())
    assert "openai" not in chain and "mock" in chain


def test_select_model_prefers_intent():
    # cost intent → a cheap/fast model from the provider's catalog
    m = select_model("openai", "cost", None)
    assert m in {"gpt-4.1-mini", "gpt-4o-mini"}
    # explicit request always wins
    assert select_model("openai", "quality", "gpt-4o") == "gpt-4o"


# --- JSON repair & validation ----------------------------------------------
def test_repair_json_handles_fences_and_trailing_commas():
    raw = '```json\n{"verdict": "Needs Review", "confidence_score": 40,}\n```'
    data = parse_json_lenient(raw)
    assert data["verdict"] == "Needs Review"


def test_repair_json_extracts_from_prose():
    raw = 'Here is the result: {"verdict":"Escalated","confidence_score":"55"} thanks!'
    data = parse_json_lenient(raw)
    assert data["confidence_score"] == "55"


def test_coerce_normalizes_types_and_invalid_verdict():
    out = coerce_investigation({"verdict": "Hacked", "confidence_score": "150", "evidence": "x"})
    assert out["verdict"] == "Needs Review"
    assert out["confidence_score"] == 100
    assert out["evidence"] == []  # non-list coerced to list


def test_is_valid_and_completeness():
    assert not is_valid_investigation(None)
    assert not is_valid_investigation({"verdict": "Needs Review"})
    warnings = completeness_warnings(coerce_investigation({"verdict": "True Positive", "confidence_score": 90, "executive_summary": ""}))
    assert any("evidence" in w.lower() for w in warnings)
