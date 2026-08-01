"""
app/infrastructure/tracking/trade_journal.py
------------------------------------------------
TradeJournal: السجل الدائم للصفقات - يغلّف DatabaseManager +
TradeRepository فقط (Session تُفتح فقط عبر db_manager.session()
المبني على session_scope الموحَّد - لا فتح يدوي هنا إطلاقاً).

صفقة تُفتح هنا فقط عند إرسال إشارة **حقيقية** إلى Telegram بنجاح (وليس
عند مجرد توليد Signal من SignalEngine) - راجع نقطة الاستدعاء في
app/main.py.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger

from app.infrastructure.database.database import DatabaseManager
from app.infrastructure.database.models import Trade
from app.infrastructure.database.repositories import TradeRepository


class TradeJournal:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def open_trade(
        self, *, symbol: str, timeframe: str, direction: str, option_type: str, strike: float, expiration: str,
        option_entry_low: float, option_entry_high: float, entry: float, stop: float, tp1: float, tp2: float,
        confidence: float, risk_reward: float, strategy: str, reasons: str,
    ) -> int:
        with self._db.session() as session:
            trade = TradeRepository(session).create(
                symbol=symbol, timeframe=timeframe, direction=direction, option_type=option_type,
                strike=strike, expiration=expiration, option_entry_low=option_entry_low,
                option_entry_high=option_entry_high, entry=entry, stop=stop, tp1=tp1, tp2=tp2,
                confidence=confidence, risk_reward=risk_reward, strategy=strategy, reasons=reasons,
                status="OPEN", entry_time=datetime.now(timezone.utc),
            )
            trade_id = trade.id
        logger.info("TradeJournal.open_trade: #{} {} {} @ {}", trade_id, symbol, option_type, entry)
        return trade_id

    def get_open_trades(self) -> list[Trade]:
        with self._db.session() as session:
            return TradeRepository(session).get_open()

    def mark_tp1_hit(self, trade_id: int, price: float, at: datetime) -> None:
        with self._db.session() as session:
            TradeRepository(session).update(trade_id, status="TP1_HIT", tp1_hit_at=at, tp1_hit_price=price)
        logger.info("TradeJournal.mark_tp1_hit: #{} @ {}", trade_id, price)

    def mark_tp2_hit(self, trade_id: int, price: float, at: datetime, profit_loss_percent: float) -> None:
        with self._db.session() as session:
            TradeRepository(session).update(
                trade_id, status="TP2_HIT", exit_price=price, exit_time=at, profit_loss_percent=profit_loss_percent,
            )
        logger.info("TradeJournal.mark_tp2_hit: #{} @ {} ({}%)", trade_id, price, profit_loss_percent)

    def mark_stopped(self, trade_id: int, price: float, at: datetime, profit_loss_percent: float) -> None:
        with self._db.session() as session:
            TradeRepository(session).update(
                trade_id, status="STOPPED", exit_price=price, exit_time=at, profit_loss_percent=profit_loss_percent,
            )
        logger.info("TradeJournal.mark_stopped: #{} @ {} ({}%)", trade_id, price, profit_loss_percent)

    def get_closed_between(self, start: datetime, end: datetime) -> list[Trade]:
        with self._db.session() as session:
            return TradeRepository(session).get_closed_between(start, end)

    def get_sent_between(self, start: datetime, end: datetime) -> list[Trade]:
        with self._db.session() as session:
            return TradeRepository(session).get_sent_between(start, end)

    def get_tp1_hits_between(self, start: datetime, end: datetime) -> list[Trade]:
        with self._db.session() as session:
            return TradeRepository(session).get_tp1_hits_between(start, end)
