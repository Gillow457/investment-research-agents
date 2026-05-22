from research_agents.config import Settings
from research_agents.agents.debate import DebateOpinionOutput
from research_agents.llm import StubLLMClient, create_llm_client
from research_agents.llm.client import CachedLLMClient


def test_missing_api_key_uses_stub_llm() -> None:
    settings = Settings(openai_api_key=None, openai_base_url="https://example.test/v1", openai_model="mock")

    client = create_llm_client(settings)

    assert isinstance(client, StubLLMClient)
    assert "stub" in client.complete("anything").lower()


def test_stub_llm_returns_structured_debate_output() -> None:
    client = StubLLMClient()

    output = client.complete("You are the bull side.", response_schema=DebateOpinionOutput)

    assert isinstance(output, DebateOpinionOutput)
    assert output.confidence > 0
    assert output.key_points


class CountingLLM:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str, response_schema=None):
        self.calls += 1
        if response_schema is not None:
            return response_schema.model_validate(
                {"thesis": "cached", "key_points": ["point"], "confidence": 0.5}
            )
        return "cached text"


def test_cached_llm_reuses_structured_response(monkeypatch) -> None:
    from research_agents.cache import MemoryCache

    monkeypatch.setattr("research_agents.cache._cache", MemoryCache(ttl_seconds=60))
    client = CountingLLM()
    cached = CachedLLMClient(client, "model")

    first = cached.complete("prompt", response_schema=DebateOpinionOutput)
    second = cached.complete("prompt", response_schema=DebateOpinionOutput)

    assert first == second
    assert client.calls == 1
