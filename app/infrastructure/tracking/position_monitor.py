"""
app/infrastructure/tracking/position_monitor.py
------------------------------------------------------
PositionMonitor: يراقب كل الصفقات المفتوحة (OPEN/TP1_HIT) في
TradeJournal كل دورة - يقارن سعر السهم الأساسي الحالي (عبر
MarketService.get_quote() العامة، **بلا أي تعديل عليها**) بمستويات
stop/tp1/tp2 المحفوظة عند فتح الصفقة، ويُحدِّث السجل + يُرجِع
PositionEvent لكل حدث فعلي (Telegram تُرسِل بناءً عليه - راجع app/main.py).

الوقف (Stop) يبقى نفسه بعد TP1 (بلا Trailing Stop تلقائي في هذه
المرحلة - غير مطلوب صراحةً، ويمكن إضافته لاحقاً كتحسين منفصل بلا أي
تعديل على هذا التصميم).
"""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger

from app.infrastructure.market.services import MarketService
from app.infrastructure.tracking.models import PositionEvent
from app.infrastructure.tracking.trade_journal import TradeJournal


class PositionMonitor:
    def __init__(self, market_service: MarketService, journal: TradeJournal) -> None:
        self._market_service = market_service
        self._journal = journal

    def check_open_positions(self) -> list[PositionEvent]:
        events: list[PositionEvent] = []

        for trade in self._journal.get_open_trades():
            try:
                quote = self._market_service.get_quote(trade.symbol)
            except Exception as exc:  # noqa: BLE001 - فشل مراقبة صفقة واحدة لا يجب أن يوقف البقية
                logger.warning("PositionMonitor: تعذّر جلب سعر {} لمراقبة الصفقة #{}: {}", trade.symbol, trade.id, exc)
                continue

            price = quote.last
            now = datetime.now(timezone.utc)
            is_buy = trade.direction == "buy"

            stop_hit = price <= trade.stop if is_buy else price >= trade.stop
            if stop_hit:
                profit_pct = self._profit_pct(trade.entry, price, is_buy)
                self._journal.mark_stopped(trade.id, price, now, profit_pct)
                events.append(
                    PositionEvent("STOP_HIT", trade.id, trade.symbol, trade.option_type, trade.strike, price, now, profit_pct)
                )
                continue

            if trade.status == "OPEN":
                tp1_hit = price >= trade.tp1 if is_buy else price <= trade.tp1
                if tp1_hit:
                    self._journal.mark_tp1_hit(trade.id, price, now)
                    profit_pct = self._profit_pct(trade.entry, price, is_buy)
                    events.append(
                        PositionEvent("TP1_HIT", trade.id, trade.symbol, trade.option_type, trade.strike, price, now, profit_pct)
                    )
            elif trade.status == "TP1_HIT":
                tp2_hit = price >= trade.tp2 if is_buy else price <= trade.tp2
                if tp2_hit:
                    profit_pct = self._profit_pct(trade.entry, price, is_buy)
                    self._journal.mark_tp2_hit(trade.id, price, now, profit_pct)
                    events.append(
                        PositionEvent("TP2_HIT", trade.id, trade.symbol, trade.option_type, trade.strike, price, now, profit_pct)
                    )

        return events

    @staticmethod
    def _profit_pct(entry: float, price: float, is_buy: bool) -> float:
        change = (price - entry) / entry * 100 if is_buy else (entry - price) / entry * 100
        return round(change, 2)
