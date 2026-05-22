import json

from research_agents.data.sec_companyfacts import SECCompanyFactsProvider


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_sec_companyfacts_provider_maps_company_facts(monkeypatch) -> None:
    ticker_payload = {"0": {"ticker": "AAPL", "cik_str": 320193}}
    facts_payload = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"end": "2025-09-30", "val": 380_000_000_000},
                            {"end": "2026-09-30", "val": 400_000_000_000},
                        ]
                    }
                },
                "NetIncomeLoss": {"units": {"USD": [{"end": "2026-09-30", "val": 100_000_000_000}]}},
                "OperatingIncomeLoss": {"units": {"USD": [{"end": "2026-09-30", "val": 120_000_000_000}]}},
                "GrossProfit": {"units": {"USD": [{"end": "2026-09-30", "val": 180_000_000_000}]}},
                "Assets": {"units": {"USD": [{"end": "2026-09-30", "val": 350_000_000_000}]}},
                "Liabilities": {"units": {"USD": [{"end": "2026-09-30", "val": 250_000_000_000}]}},
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {"USD": [{"end": "2026-09-30", "val": 115_000_000_000}]}
                },
                "PaymentsToAcquirePropertyPlantAndEquipment": {
                    "units": {"USD": [{"end": "2026-09-30", "val": 12_000_000_000}]}
                },
            }
        }
    }

    def fake_urlopen(request, timeout):
        url = request.full_url
        if url.endswith("company_tickers.json"):
            return FakeResponse(ticker_payload)
        return FakeResponse(facts_payload)

    monkeypatch.setattr("research_agents.data.sec_companyfacts.urlopen", fake_urlopen)

    fundamentals = SECCompanyFactsProvider().get_fundamentals("AAPL")

    assert fundamentals.source == "sec_companyfacts"
    assert fundamentals.revenue == 400_000_000_000
    assert fundamentals.net_income == 100_000_000_000
    assert fundamentals.free_cash_flow == 103_000_000_000
    assert fundamentals.gross_margin == 0.45
    assert round(fundamentals.revenue_growth or 0, 4) == 0.0526
