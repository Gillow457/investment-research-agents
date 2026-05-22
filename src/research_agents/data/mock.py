from __future__ import annotations

from datetime import date, timedelta

from research_agents.graph.state import CompanyProfile, FundamentalMetrics, MarketContext, NewsItem, PricePoint


class MockMarketDataProvider:
    _profiles = {
        "AAPL": CompanyProfile(
            ticker="AAPL",
            name="Apple Inc.",
            sector="Technology",
            description="Consumer hardware, software, and services company.",
        ),
        "NVDA": CompanyProfile(
            ticker="NVDA",
            name="NVIDIA Corporation",
            sector="Semiconductors",
            description="Accelerated computing and AI infrastructure company.",
        ),
    }

    def get_company_profile(self, ticker: str) -> CompanyProfile:
        normalized = ticker.upper()
        if normalized not in self._profiles:
            raise ValueError(f"Unsupported mock ticker: {ticker}. Try AAPL or NVDA.")
        return self._profiles[normalized]

    def get_price_history(self, ticker: str, analysis_date: date) -> list[PricePoint]:
        profile = self.get_company_profile(ticker)
        base = 185.0 if profile.ticker == "AAPL" else 910.0
        moves = [0.0, 0.8, -0.3, 1.1, 0.6, -0.2, 1.4]
        prices: list[PricePoint] = []
        close = base
        start = analysis_date - timedelta(days=len(moves) - 1)
        for offset, move in enumerate(moves):
            close = round(close + move, 2)
            prices.append(
                PricePoint(
                    date=start + timedelta(days=offset),
                    open=round(close - 0.4, 2),
                    high=round(close + 1.2, 2),
                    low=round(close - 1.1, 2),
                    close=close,
                    volume=50_000_000 + offset * 1_000_000,
                )
            )
        return prices

    def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        profile = self.get_company_profile(ticker)
        if profile.ticker == "AAPL":
            return FundamentalMetrics(
                source="mock",
                market_cap=3_100_000_000_000,
                revenue=390_000_000_000,
                net_income=97_000_000_000,
                operating_income=120_000_000_000,
                total_assets=350_000_000_000,
                total_liabilities=275_000_000_000,
                operating_cash_flow=110_000_000_000,
                capital_expenditure=10_000_000_000,
                trailing_pe=31.5,
                forward_pe=28.0,
                price_to_book=45.0,
                revenue_growth=0.06,
                gross_margin=0.46,
                operating_margin=0.31,
                profit_margin=0.25,
                free_cash_flow=100_000_000_000,
                debt_to_equity=1.5,
            )
        return FundamentalMetrics(
            source="mock",
            market_cap=2_300_000_000_000,
            revenue=130_000_000_000,
            net_income=63_000_000_000,
            operating_income=75_000_000_000,
            total_assets=120_000_000_000,
            total_liabilities=30_000_000_000,
            operating_cash_flow=50_000_000_000,
            capital_expenditure=5_000_000_000,
            trailing_pe=62.0,
            forward_pe=38.0,
            price_to_book=35.0,
            revenue_growth=0.45,
            gross_margin=0.73,
            operating_margin=0.58,
            profit_margin=0.49,
            free_cash_flow=45_000_000_000,
            debt_to_equity=0.25,
        )

    def get_market_context(
        self,
        ticker: str,
        analysis_date: date,
        price_history: list[PricePoint],
    ) -> MarketContext:
        normalized = ticker.upper()
        if normalized not in self._profiles:
            raise ValueError(f"Unsupported mock ticker: {ticker}. Try AAPL or NVDA.")
        ticker_return = (price_history[-1].close - price_history[0].close) / price_history[0].close
        benchmark_return = 0.01 if normalized == "AAPL" else 0.025
        return MarketContext(
            benchmark_ticker="SPY",
            ticker_return=round(ticker_return, 4),
            benchmark_return=benchmark_return,
            relative_return=round(ticker_return - benchmark_return, 4),
            lookback_days=len(price_history),
        )


class MockNewsProvider:
    def get_news(self, ticker: str, analysis_date: date) -> list[NewsItem]:
        normalized = ticker.upper()
        if normalized not in {"AAPL", "NVDA"}:
            raise ValueError(f"Unsupported mock ticker: {ticker}. Try AAPL or NVDA.")
        return [
            NewsItem(
                date=analysis_date - timedelta(days=2),
                title=f"{normalized} reports resilient demand in core markets",
                source="MockWire",
                sentiment=0.35,
            ),
            NewsItem(
                date=analysis_date - timedelta(days=1),
                title=f"Analysts flag margin pressure risks for {normalized}",
                source="MockMarkets",
                sentiment=-0.15,
            ),
            NewsItem(
                date=analysis_date,
                title=f"{normalized} supplier checks point to stable near-term orders",
                source="MockResearch",
                sentiment=0.25,
            ),
        ]
