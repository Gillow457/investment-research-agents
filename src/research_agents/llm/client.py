from __future__ import annotations

import json
from typing import Any, Protocol, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from research_agents.config import Settings
from research_agents.prompts import SYSTEM_PROMPT

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    def complete(self, prompt: str, response_schema: type[T] | None = None) -> str | T:
        ...


class StubLLMClient:
    def complete(self, prompt: str, response_schema: type[T] | None = None) -> str | T:
        if response_schema is not None:
            return response_schema.model_validate(self._structured_response(prompt, response_schema))
        text = self._deterministic_response(prompt)
        return text

    @staticmethod
    def _deterministic_response(prompt: str) -> str:
        if "news sentiment" in prompt.lower():
            return "News flow is modestly constructive, with demand strength partly offset by margin concerns."
        if "investment research summary" in prompt.lower():
            return "The aggregated signals support a cautious, research-oriented stance with explicit risk review."
        return "Deterministic stub response."

    @staticmethod
    def _structured_response(prompt: str, response_schema: type[T]) -> dict[str, Any]:
        schema_name = response_schema.__name__
        prompt_lower = prompt.lower()
        if schema_name == "DebateOpinionOutput":
            if "you are the bull side" in prompt_lower:
                return {
                    "thesis": "Bull case: positive signal momentum and resilient fundamentals support selective upside.",
                    "key_points": [
                        "Technical, sentiment, and fundamental inputs are not negative.",
                        "No high-severity risk blocks the research stance.",
                    ],
                    "confidence": 0.63,
                }
            if "you are the bear side" in prompt_lower:
                return {
                    "thesis": "Bear case: valuation and evidence quality can still limit upside.",
                    "key_points": [
                        "Valuation can offset otherwise healthy fundamentals.",
                        "Risk controls should prevent overconfident positioning.",
                    ],
                    "confidence": 0.57,
                }
            return {
                "thesis": "Risk view: proceed only with explicit valuation, volatility, and sentiment caveats.",
                "key_points": [
                    "Valuation and volatility remain the primary control points.",
                    "Final stance should account for evidence quality.",
                ],
                "confidence": 0.61,
            }
        if schema_name == "PortfolioDecisionOutput":
            if "baseline rule decision=BUY".lower() in prompt_lower:
                decision = "BUY"
                confidence = 0.68
            elif "baseline rule decision=SELL".lower() in prompt_lower:
                decision = "SELL"
                confidence = 0.61
            else:
                decision = "HOLD"
                confidence = 0.58
            return {
                "decision": decision,
                "confidence": confidence,
                "summary": "The four-agent debate supports a measured research stance grounded in market, news, fundamental, and risk evidence.",
            }
        return {}


class OpenAICompatibleLLMClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def complete(self, prompt: str, response_schema: type[T] | None = None) -> str | T:
        user_content = prompt
        response_format = None
        if response_schema is not None:
            user_content = (
                f"{prompt}\n\n"
                "Return only valid JSON matching this JSON schema. "
                "Do not wrap the JSON in Markdown.\n"
                f"{json.dumps(response_schema.model_json_schema(), ensure_ascii=True)}"
            )
            response_format = {"type": "json_object"}

        request: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }
        if response_format is not None:
            request["response_format"] = response_format

        response = self._client.chat.completions.create(**request)
        content = response.choices[0].message.content or ""
        if response_schema is not None:
            return response_schema.model_validate_json(content)
        return content.strip()


def create_llm_client(settings: Settings) -> LLMClient:
    if not settings.openai_api_key:
        return StubLLMClient()
    return OpenAICompatibleLLMClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
    )
