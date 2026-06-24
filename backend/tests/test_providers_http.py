"""HTTP-level tests for cloud/local provider adapters using mocked httpx.

These prove each adapter builds the right request and correctly parses the
provider's real response shape (text + token usage), without hitting any API.
"""
from __future__ import annotations

import httpx
import respx

from app.ai.schemas import AIRequest


def _req():
    return AIRequest.simple("system", "analyze this alert", max_tokens=64)


@respx.mock
def test_openai_compatible_parses_choices_and_usage():
    import app.core.config as cfg
    cfg.settings.openai_api_key = "sk-test"
    from app.ai.providers.openai_provider import OpenAIProvider

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "model": "gpt-4.1-mini",
            "choices": [{"message": {"content": "verdict: needs review"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7},
        })
    )
    import asyncio
    resp = asyncio.run(OpenAIProvider().generate(_req()))
    assert resp.text == "verdict: needs review"
    assert resp.usage.input_tokens == 11 and resp.usage.output_tokens == 7
    assert resp.provider == "openai"


@respx.mock
def test_openai_error_is_normalized_without_leaking_key():
    import app.core.config as cfg
    cfg.settings.openai_api_key = "sk-secret-key"
    from app.ai.providers.openai_provider import OpenAIProvider
    from app.ai.schemas import AIProviderError

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(401, text="unauthorized")
    )
    import asyncio
    try:
        asyncio.run(OpenAIProvider().generate(_req()))
        assert False, "should have raised"
    except AIProviderError as e:
        assert "sk-secret-key" not in str(e)
        assert e.provider == "openai"


@respx.mock
def test_anthropic_parses_content_blocks():
    import app.core.config as cfg
    cfg.settings.anthropic_api_key = "test"
    cfg.settings.anthropic_base_url = "https://api.anthropic.test/v1"  # pin (env may override)
    from app.ai.providers.anthropic_provider import AnthropicProvider

    respx.post("https://api.anthropic.test/v1/messages").mock(
        return_value=httpx.Response(200, json={
            "content": [{"type": "text", "text": "analysis"}],
            "usage": {"input_tokens": 20, "output_tokens": 5},
        })
    )
    import asyncio
    resp = asyncio.run(AnthropicProvider().generate(_req()))
    assert resp.text == "analysis"
    assert resp.usage.output_tokens == 5


@respx.mock
def test_gemini_parses_candidates():
    import app.core.config as cfg
    cfg.settings.gemini_api_key = "test"
    from app.ai.providers.gemini_provider import GeminiProvider

    respx.post(url__regex=r"https://generativelanguage\.googleapis\.com/.*").mock(
        return_value=httpx.Response(200, json={
            "candidates": [{"content": {"parts": [{"text": "gem analysis"}]}}],
            "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 3},
        })
    )
    import asyncio
    resp = asyncio.run(GeminiProvider().generate(_req()))
    assert resp.text == "gem analysis"
    assert resp.usage.input_tokens == 9


def test_mock_provider_streams_chunks():
    import asyncio

    from app.ai.providers.mock_provider import MockAIProvider

    async def collect():
        chunks = []
        async for c in MockAIProvider().stream(_req()):
            chunks.append(c)
        return chunks

    chunks = asyncio.run(collect())
    assert len(chunks) > 1
    assert "".join(chunks).strip()


def test_chat_stream_endpoint(client, auth_headers):
    r = client.post("/ai/chat/stream", json={"prompt": "summarize this alert", "provider": "mock"},
                    headers=auth_headers)
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    assert "[DONE]" in r.text


@respx.mock
def test_ollama_native_api_parsing_and_zero_cost():
    from app.ai.providers.ollama_provider import OllamaProvider

    respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(200, json={
            "message": {"content": "local verdict"},
            "prompt_eval_count": 30, "eval_count": 12,
        })
    )
    import asyncio
    resp = asyncio.run(OllamaProvider().generate(_req()))
    assert resp.text == "local verdict"
    assert resp.estimated_cost == 0.0  # local models are free
    assert resp.usage.input_tokens == 30
