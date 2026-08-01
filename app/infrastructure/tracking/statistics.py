"""
app/infrastructure/tracking/statistics.py
------------------------------------------------
TradeStatisticsCalculator: حسابات إحصائية بحتة (رياضيات فقط) على قائمة
صفقات مُغلَقة جاهزة (Trade من قاعدة البيانات) - بلا أي استعلام قاعدة
بيانات هنا (ذلك في TradeJournal).

Profit/Loss هنا = profit_loss_percent المحفوظ عند إغلاق كل صفقة (نسبة
تحرك السهم الأساسي - راجع قيد التوثيق في database/models/trade.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.database.models import Trade


@dataclass(frozen=True)
class TradeStatistics:
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    average_rr: float
    average_profit: float
    average_loss: float
    profit_factor: float
    total_profit: float
    total_loss: float
    best_trade_symbol: str | None
    best_trade_profit: float | None
    worst_trade_symbol: str | None
    worst_trade_profit: float | None
    best_symbol: str | None
    best_strategy: str | None
    best_timeframe: str | None


_EMPTY_STATS = TradeStatistics(
    total_trades=0, wins=0, losses=0, win_rate=0.0, average_rr=0.0, average_profit=0.0, average_loss=0.0,
    profit_factor=0.0, total_profit=0.0, total_loss=0.0, best_trade_symbol=None, best_trade_profit=None,
    worst_trade_symbol=None, worst_trade_profit=None, best_symbol=None, best_strategy=None, best_timeframe=None,
)


class TradeStatisticsCalculator:
    def calculate(self, closed_trades: list[Trade]) -> TradeStatistics:
        if not closed_trades:
            return _EMPTY_STATS

        wins_list = [t for t in closed_trades if (t.profit_loss_percent or 0.0) > 0]
        losses_list = [t for t in closed_trades if (t.profit_loss_percent or 0.0) <= 0]

        total_profit = sum(t.profit_loss_percent or 0.0 for t in wins_list)
        total_loss = abs(sum(t.profit_loss_percent or 0.0 for t in losses_list))

        average_profit = round(total_profit / len(wins_list), 2) if wins_list else 0.0
        average_loss = round(total_loss / len(losses_list), 2) if losses_list else 0.0
        if total_loss > 0:
            profit_factor = round(total_profit / total_loss, 2)
        else:
            profit_factor = round(total_profit, 2) if total_profit > 0 else 0.0

        best = max(closed_trades, key=lambda t: t.profit_loss_percent or 0.0)
        worst = min(closed_trades, key=lambda t: t.profit_loss_percent or 0.0)

        by_symbol: dict[str, float] = {}
        by_strategy: dict[str, float] = {}
        by_timeframe: dict[str, float] = {}
        for trade in closed_trades:
            pnl = trade.profit_loss_percent or 0.0
            by_symbol[trade.symbol] = by_symbol.get(trade.symbol, 0.0) + pnl
            by_timeframe[trade.timeframe] = by_timeframe.get(trade.timeframe, 0.0) + pnl
            for strategy_name in (trade.strategy.split(",") if trade.strategy else []):
                strategy_name = strategy_name.strip()
                if strategy_name:
                    by_strategy[strategy_name] = by_strategy.get(strategy_name, 0.0) + pnl

        return TradeStatistics(
            total_trades=len(closed_trades), wins=len(wins_list), losses=len(losses_list),
            win_rate=round(len(wins_list) / len(closed_trades) * 100, 2),
            average_rr=round(sum(t.risk_reward for t in closed_trades) / len(closed_trades), 2),
            average_profit=average_profit, average_loss=average_loss, profit_factor=profit_factor,
            total_profit=round(total_profit, 2), total_loss=round(total_loss, 2),
            best_trade_symbol=best.symbol, best_trade_profit=round(best.profit_loss_percent or 0.0, 2),
            worst_trade_symbol=worst.symbol, worst_trade_profit=round(worst.profit_loss_percent or 0.0, 2),
            best_symbol=max(by_symbol, key=by_symbol.get) if by_symbol else None,
            best_strategy=max(by_strategy, key=by_strategy.get) if by_strategy else None,
            best_timeframe=max(by_timeframe, key=by_timeframe.get) if by_timeframe else None,
        )
