from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen

from research_agents.graph.state import FundamentalMetrics
from research_agents.rate_limit import rate_limit


class SECCompanyFactsProvider:
    tickers_endpoint = "https://www.sec.gov/files/company_tickers.json"
    facts_endpoint = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        cik = self._lookup_cik(ticker)
        if cik is None:
            raise ValueError(f"SEC CIK not found for ticker: {ticker.upper()}.")
        payload = self._load_json(self.facts_endpoint.format(cik=f"{cik:010d}"))
        facts = payload.get("facts", {}).get("us-gaap", {})

        revenue_values = _values(facts, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"])
        revenue = _latest_value(revenue_values)
        previous_revenue = _previous_value(revenue_values)
        revenue_growth = _growth(revenue, previous_revenue)
        net_income = _latest_value(_values(facts, ["NetIncomeLoss"]))
        operating_income = _latest_value(_values(facts, ["OperatingIncomeLoss"]))
        gross_profit = _latest_value(_values(facts, ["GrossProfit"]))
        total_assets = _latest_value(_values(facts, ["Assets"]))
        total_liabilities = _latest_value(_values(facts, ["Liabilities"]))
        operating_cash_flow = _latest_value(
            _values(facts, ["NetCashProvidedByUsedInOperatingActivities"])
        )
        capital_expenditure = _latest_value(
            _values(facts, ["PaymentsToAcquirePropertyPlantAndEquipment"])
        )
        free_cash_flow = None
        if operating_cash_flow is not None:
            capex = abs(capital_expenditure or 0)
            free_cash_flow = operating_cash_flow - capex

        return FundamentalMetrics(
            source="sec_companyfacts",
            revenue=revenue,
            net_income=net_income,
            operating_income=operating_income,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            operating_cash_flow=operating_cash_flow,
            capital_expenditure=capital_expenditure,
            revenue_growth=revenue_growth,
            gross_margin=_ratio(gross_profit, revenue),
            operating_margin=_ratio(operating_income, revenue),
            profit_margin=_ratio(net_income, revenue),
            free_cash_flow=free_cash_flow,
            debt_to_equity=_debt_to_equity(total_liabilities, total_assets),
        )

    def _lookup_cik(self, ticker: str) -> int | None:
        normalized = ticker.upper()
        payload = self._load_json(self.tickers_endpoint)
        for item in payload.values():
            if str(item.get("ticker", "")).upper() == normalized:
                return int(item["cik_str"])
        return None

    def _load_json(self, url: str) -> dict[str, Any]:
        rate_limit("sec")
        request = Request(url, headers={"User-Agent": _user_agent()})
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))


def _user_agent() -> str:
    return os.getenv("SEC_USER_AGENT", "investment-research-agents/0.1 contact@example.com")


def _values(facts: dict[str, Any], concepts: list[str]) -> list[dict[str, Any]]:
    for concept in concepts:
        units = facts.get(concept, {}).get("units", {})
        if "USD" in units:
            return [item for item in units["USD"] if item.get("val") is not None and item.get("end")]
        if "shares" in units:
            return [item for item in units["shares"] if item.get("val") is not None and item.get("end")]
    return []


def _latest_value(values: list[dict[str, Any]]) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values, key=lambda item: str(item.get("end", "")))
    return float(sorted_values[-1]["val"])


def _previous_value(values: list[dict[str, Any]]) -> float | None:
    if len(values) < 2:
        return None
    sorted_values = sorted(values, key=lambda item: str(item.get("end", "")))
    return float(sorted_values[-2]["val"])


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return numerator / denominator


def _growth(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in {None, 0}:
        return None
    return (current - previous) / abs(previous)


def _debt_to_equity(liabilities: float | None, assets: float | None) -> float | None:
    if liabilities is None or assets is None:
        return None
    equity = assets - liabilities
    if equity <= 0:
        return None
    return liabilities / equity
