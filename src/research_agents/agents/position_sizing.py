from __future__ import annotations

from research_agents.reports.models import PortfolioContext, PositionSizingRecommendation, ResearchReport


class PositionSizingAgent:
    name = "PositionSizingAgent"

    def run(self, report: ResearchReport, portfolio_context: PortfolioContext | None) -> ResearchReport:
        if portfolio_context is None:
            return report.model_copy(
                update={
                    "position_sizing": PositionSizingRecommendation(
                        action="NO_TRADE_PLAN",
                        rationale=(
                            "Portfolio context was not provided, so the system cannot estimate "
                            "trade size or target position without inventing user capital."
                        ),
                        constraints=["Missing portfolio_value, cash, and current positions."],
                    )
                }
            )

        recommendation = self._recommend(report, portfolio_context)
        return report.model_copy(update={"position_sizing": recommendation})

    def _recommend(self, report: ResearchReport, context: PortfolioContext) -> PositionSizingRecommendation:
        current_value = sum(
            position.market_value for position in context.positions if position.ticker.upper() == report.ticker.upper()
        )
        current_shares = sum(
            position.shares for position in context.positions if position.ticker.upper() == report.ticker.upper()
        )
        current_weight = current_value / context.portfolio_value
        latest_price = _latest_price(report)
        constraints: list[str] = ["Research planning only; this is not financial advice."]
        high_risk = any(risk.level == "high" for risk in report.risks)

        target_weight = _base_target_weight(report.decision, report.confidence, context.risk_profile)
        if high_risk:
            target_weight *= 0.5
            constraints.append("High risk flag reduced target weight by 50%.")
        if report.confidence < 0.6:
            target_weight *= 0.6
            constraints.append("Confidence below 60% reduced target weight.")
        target_weight = min(target_weight, context.max_position_pct)

        target_value = target_weight * context.portfolio_value
        raw_trade_value = target_value - current_value

        if report.decision == "SELL":
            sell_value = -current_value if report.confidence >= 0.65 else -min(current_value, context.portfolio_value * 0.5 * current_weight)
            return _finalize(
                action="SELL",
                current_weight=current_weight,
                target_weight=0.0 if report.confidence >= 0.65 else max(0.0, current_weight * 0.5),
                trade_value=sell_value,
                latest_price=latest_price,
                rationale="Research stance is SELL, so the plan reduces exposure rather than adding capital.",
                constraints=constraints,
                min_trade_value=context.min_trade_value,
                current_shares=current_shares,
            )

        if raw_trade_value < -context.min_trade_value:
            return _finalize(
                action="TRIM",
                current_weight=current_weight,
                target_weight=target_weight,
                trade_value=raw_trade_value,
                latest_price=latest_price,
                rationale="Current position is above the rule-based target weight.",
                constraints=constraints,
                min_trade_value=context.min_trade_value,
                current_shares=current_shares,
            )

        if report.decision == "BUY" and raw_trade_value > 0:
            buy_cap = min(context.cash, context.portfolio_value * context.max_new_buy_pct)
            trade_value = min(raw_trade_value, buy_cap)
            if trade_value < raw_trade_value:
                constraints.append("Buy amount capped by available cash or max_new_buy_pct.")
            return _finalize(
                action="BUY",
                current_weight=current_weight,
                target_weight=target_weight,
                trade_value=trade_value,
                latest_price=latest_price,
                rationale="Research stance is BUY and current weight is below the rule-based target.",
                constraints=constraints,
                min_trade_value=context.min_trade_value,
                current_shares=current_shares,
            )

        return PositionSizingRecommendation(
            action="HOLD",
            current_weight=round(current_weight, 4),
            target_weight=round(target_weight, 4),
            trade_value=0.0,
            trade_shares=0.0,
            rationale="No trade is suggested because the research stance or position gap does not justify action.",
            constraints=constraints,
        )


def _base_target_weight(decision: str, confidence: float, risk_profile: str) -> float:
    profile_multiplier = {"conservative": 0.75, "moderate": 1.0, "aggressive": 1.25}[risk_profile]
    if decision == "BUY":
        if confidence >= 0.7:
            return 0.08 * profile_multiplier
        if confidence >= 0.6:
            return 0.05 * profile_multiplier
        return 0.03 * profile_multiplier
    if decision == "HOLD":
        return 0.03 * profile_multiplier
    return 0.0


def _latest_price(report: ResearchReport) -> float | None:
    price_signal = next((signal for signal in report.signals if signal.name == "latest_close"), None)
    if price_signal is None:
        return None
    try:
        return float(price_signal.value)
    except ValueError:
        return None


def _finalize(
    action: str,
    current_weight: float,
    target_weight: float,
    trade_value: float,
    latest_price: float | None,
    rationale: str,
    constraints: list[str],
    min_trade_value: float,
    current_shares: float,
) -> PositionSizingRecommendation:
    if abs(trade_value) < min_trade_value:
        return PositionSizingRecommendation(
            action="HOLD",
            current_weight=round(current_weight, 4),
            target_weight=round(target_weight, 4),
            trade_value=0.0,
            trade_shares=0.0,
            rationale="Suggested trade is below the configured minimum trade value.",
            constraints=[*constraints, f"Minimum trade value is {min_trade_value:.2f}."],
        )
    trade_shares = None
    if latest_price and latest_price > 0:
        trade_shares = trade_value / latest_price
        if action in {"SELL", "TRIM"}:
            trade_shares = max(-current_shares, trade_shares)
    return PositionSizingRecommendation(
        action=action,  # type: ignore[arg-type]
        current_weight=round(current_weight, 4),
        target_weight=round(target_weight, 4),
        trade_value=round(trade_value, 2),
        trade_shares=round(trade_shares, 4) if trade_shares is not None else None,
        rationale=rationale,
        constraints=constraints,
    )
