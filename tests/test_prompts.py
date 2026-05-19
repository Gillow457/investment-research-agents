from research_agents.prompts import DEBATE_PROMPT, EVIDENCE_RULES, JSON_RULES, PORTFOLIO_PROMPT, SYSTEM_PROMPT


def test_prompt_constraints_include_evidence_and_advice_guardrails() -> None:
    combined = "\n".join([SYSTEM_PROMPT, EVIDENCE_RULES, JSON_RULES, DEBATE_PROMPT, PORTFOLIO_PROMPT]).lower()

    assert "use only" in combined
    assert "do not invent" in combined
    assert "financial advice" in combined
    assert "lower confidence" in combined
    assert "return only json" in combined
