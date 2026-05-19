from research_agents.config import Settings
from research_agents.agents.debate import DebateOpinionOutput
from research_agents.llm import StubLLMClient, create_llm_client


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
