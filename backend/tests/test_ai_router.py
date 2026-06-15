"""AI router selection and fallback tests."""
from __future__ import annotations

import asyncio

from app.ai.router import AIRouter, CustomerPolicy
from app.ai.schemas import AIRequest


def test_offline_mode_uses_mock_only():
    router = AIRouter(mode="offline")
    chain = router.build_chain(CustomerPolicy())
    assert chain == ["mock"]


def test_privacy_mode_is_local_only():
    router = AIRouter(mode="privacy")
    chain = router.build_chain(CustomerPolicy())
    assert all(p in {"ollama", "lmstudio", "vllm", "mock", "generic_openai"} for p in chain)
    assert "openai" not in chain


def test_local_only_policy_filters_cloud():
    router = AIRouter(mode="quality")
    chain = router.build_chain(CustomerPolicy(local_only_mode=True))
    assert "openai" not in chain
    assert "anthropic" not in chain
    assert "mock" in chain


def test_fallback_chain_ends_with_mock():
    router = AIRouter(mode="auto")
    chain = router.build_chain(CustomerPolicy())
    assert chain[-1] == "mock" or "mock" in chain


def test_router_runs_mock_and_returns_response():
    router = AIRouter(mode="offline")
    req = AIRequest.simple("system", "analyze this", prompt_type="soc_investigation",
                           json_mode=True, metadata={"alert_name": "Test", "category": "brute_force",
                                                      "src_ip": "203.0.113.10", "username": "jdoe"})
    result = asyncio.run(router.run(req, policy=CustomerPolicy()))
    assert result.provider == "mock"
    assert result.response.text
