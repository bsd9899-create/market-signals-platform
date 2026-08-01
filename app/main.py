"""
app/main.py
-------------
نقطة تشغيل المشروع الوحيدة - بوت إشارات مستمر (Composition Root فقط):
Scanner (كل دقيقة، أثناء ساعات السوق الأمريكي العادية فقط) -> أفضل فرصة
واحدة (ثقة >= 70%) مع سياق أخبار/أرباح حقيقي -> Telegram -> Trade
Journal دائم -> مراقبة كل دقيقة (TP1/TP2/Stop) -> تقارير يومية/أسبوعية/
شهرية تلقائية بعد إغلاق السوق.

**لا يعدّل IndicatorEngine/SignalEngine/StrategyEngine/RiskManager/
MarketService/Scanner إطلاقاً** - كل هذه الأسماء تُستدعى هنا فقط عبر
واجهاتها العامة الموجودة أصلاً (Scanner.scan_all،
MarketService.get_quote/get_market_status) بلا أي تعديل على تعريفها.

التشغيل: python -m app.main   (من جذر المشروع)
Ctrl+C لإيقاف الحلقة بأمان (يُغلق Telegram + قاعدة البيانات).

**لا يُعدَّل sys.path هنا إطلاقاً** - "python -m app.main" يضيف مجلد
العمل الحالي إلى sys.path تلقائياً (سلوك بايثون نفسه).
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime
from zoneinfo import ZoneInfo

# ترميز UTF-8 + line_buffering=True: العملية تعمل الآن بحلقة مستمرة
# (فحص كل دقيقة) - بلا line_buffering تبقى أسطر print() عالقة في الذاكرة
# ولا تظهر في أي ملف/سجل مُعاد توجيهه إليه إلا عند إغلاق العملية.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from app.infrastructure.config.loader import ConfigLoader
from app.infrastructure.database.database import DatabaseManager
from app.infrastructure.logging.logger import LoggerService
from app.infrastructure.paths import ProjectPaths
from app.infrastructure.reports.schedule import is_friday, is_in_daily_report_window, is_last_trading_day_of_month

_FALLBACK_SYMBOLS = ["AAPL", "NVDA", "TSLA"]  # يُستخدَم فقط إذا كان config/symbols.yaml فارغاً
_MIN_CONFIDENCE_TO_ALERT = 70.0
_SCAN_INTERVAL_SECONDS = 60.0
_NO_OPPORTUNITY_KEY = "__NO_OPPORTUNITY__"
_NO_OPPORTUNITY_MESSAGE = "🔍 تم فحص السوق بالكامل.\nلم يتم العثور على فرصة تستحق الدخول حاليًا."
_RECENT_CLOSE_RE_ENTRY_WINDOW_HOURS = 24.0
_ET = ZoneInfo("America/New_York")


def _resolve_env(key: str, config: ConfigLoader) -> str:
    """os.environ أولاً، ثم .env - نفس أولوية send_test_message.py."""
    return os.environ.get(key) or config.env.get(key) or ""


# ---------------------------------------------------------------------
# سياق الأخبار/الأرباح (المطلب 2) - لا يمنع أي إشارة أبداً، عرض + تعديل
# ثقة العرض فقط عند تعارض واضح.
# ---------------------------------------------------------------------


def _build_news_and_earnings_context(news_provider, symbol: str):
    """يفحص: أخبار حديثة + Earnings القادمة + SEC Filings + Analyst
    Upgrades/Downgrades (المطلب 3) - **لا يحسب أي تعديل ثقة هنا** (ذلك
    حصراً عبر FinalScoreCalculator في _run_scan_cycle) - فقط يجلب
    البيانات الخام ونصوص العرض الجاهزة (News/Earnings) للرسالة."""
    from app.infrastructure.news.scoring import NewsScorer

    news_items = news_provider.get_latest_news(symbol, limit=5)
    news_score = NewsScorer().score_items(news_items)
    news_note = None
    if news_items:
        latest = news_items[0]
        news_note = (
            f"{latest.headline}\n"
            f"المصدر: {latest.source}\n"
            f"الوقت: {latest.published_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )

    earnings_info = news_provider.get_earnings_info(symbol)
    earnings_note = None
    if earnings_info is not None and earnings_info.hours_until < 48:
        earnings_note = f"Earnings خلال {earnings_info.hours_until:.0f} ساعة."

    # SEC Filings + Analyst Actions: تُفحَص فعلياً (متطلب صريح) لكنها لا
    # تظهر خاماً في الرسالة (فقط News/Earnings حسب تنسيق Telegram
    # المطلوب) - محجوزة لاستخدام لاحق إن لزم (لا تدخل في Final Score
    # حالياً لتفادي إشارات ضعيفة الدلالة من عدد محدود من السجلات).
    news_provider.get_sec_filings(symbol, limit=5)
    news_provider.get_analyst_actions(symbol, limit=3)

    return news_note, earnings_note, news_score, earnings_info


# ---------------------------------------------------------------------
# قرار نوع الإشارة الجديدة: فتح صفقة جديدة / Better Entry / تخطٍّ
# ---------------------------------------------------------------------


def _decide_entry_kind(journal, symbol: str, direction_value: str, entry: float) -> str:
    open_trades = [t for t in journal.get_open_trades() if t.symbol == symbol]
    if not open_trades:
        return "OPEN_NEW"

    current = open_trades[0]
    if current.direction != direction_value:
        return "OPEN_NEW"  # الاتجاه تغيّر فعلياً - فرصة جديدة رغم وجود صفقة سابقة معاكسة

    is_buy = direction_value == "buy"
    improved = entry < current.entry if is_buy else entry > current.entry
    return "BETTER_ENTRY" if improved else "SKIP"


def _is_recently_closed(recently_closed: dict, symbol: str, now: datetime) -> bool:
    closed_at = recently_closed.get(symbol)
    if closed_at is None:
        return False
    if (now - closed_at).total_seconds() > _RECENT_CLOSE_RE_ENTRY_WINDOW_HOURS * 3600:
        del recently_closed[symbol]
        return False
    return True


def _compute_stock_t1(signal) -> float | None:
    from app.infrastructure.signals.models import SignalDirection

    if signal.stop_loss is None or signal.take_profit is None:
        return None
    if signal.direction == SignalDirection.BUY:
        return round(signal.entry + (signal.take_profit - signal.entry) / 2, 4)
    if signal.direction == SignalDirection.SELL:
        return round(signal.entry - (signal.entry - signal.take_profit) / 2, 4)
    return None


def _dispatch(tracker, key: str, text: str, telegram_service, sender, chat_id) -> None:
    if not tracker.should_send(key, text):
        print(f"⏭️ [{key}] نفس الرسالة أُرسِلت خلال آخر 5 دقائق - تخطٍّ.")
        return
    if sender is None or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID فارغان - تعذّر الإرسال. نص الرسالة:")
        print(text)
        return
    success = telegram_service.send_message(chat_id, text)
    if success:
        tracker.record_sent(key, text)
    icon = "✅" if success else "❌"
    print(f"{icon} [{key}] (HTTP {sender.last_status_code})")


# ---------------------------------------------------------------------
# دورة فحص واحدة (Scanner: أفضل فرصة فقط - المطلب 1)
# ---------------------------------------------------------------------


def _run_scan_cycle(
    config, logger, provider, market_service, scanner, news_provider, journal,
    event_counters, tracker, telegram_service, sender, chat_id, recently_closed,
) -> None:
    from app.infrastructure.signals.models import SignalDirection
    from app.infrastructure.telegram.signal_formatter import SignalFormatter

    symbols = list(config.symbols) or _FALLBACK_SYMBOLS
    report = scanner.scan_all(symbols)
    stats = report.statistics
    logger.info(
        "دورة فحص: {} فحص ({} نجح، {} فشل) - BUY={}, SELL={}, NEUTRAL={} - {:.1f}ms",
        stats.total_scans, stats.successful_scans, stats.failed_scans,
        stats.buy_signals, stats.sell_signals, stats.neutral_signals, stats.duration_ms,
    )

    candidates = [r for r in report.results if r.signal is not None and r.signal.direction != SignalDirection.NEUTRAL]
    if not candidates:
        print("ℹ️ لا توجد إشارة BUY/SELL في هذا الفحص.")
        _dispatch(tracker, _NO_OPPORTUNITY_KEY, _NO_OPPORTUNITY_MESSAGE, telegram_service, sender, chat_id)
        return

    best = max(candidates, key=lambda r: r.signal.confidence)
    signal = best.signal
    symbol = best.symbol
    direction_value = signal.direction.value

    entry_kind = _decide_entry_kind(journal, symbol, direction_value, signal.entry)
    if entry_kind == "SKIP":
        print(f"⏭️ {symbol}: صفقة مفتوحة بسعر مساوٍ أو أفضل بالفعل - لا إشعار جديد.")
        return

    is_better_entry = entry_kind == "BETTER_ENTRY"
    now = datetime.now(timezone.utc)
    is_re_entry = entry_kind == "OPEN_NEW" and _is_recently_closed(recently_closed, symbol, now)

    option_contract = provider.get_best_option_contract(symbol, signal.direction, signal.entry)
    news_note, earnings_note, news_score, earnings_info = _build_news_and_earnings_context(news_provider, symbol)

    from app.infrastructure.telegram.quality_score import FinalScoreCalculator

    breakdown = FinalScoreCalculator().calculate(
        technical_confidence=signal.confidence, direction=signal.direction, news_score=news_score,
        earnings_info=earnings_info, option_contract=option_contract, is_estimated_contract=option_contract is None,
    )
    logger.info(
        "{}: Final Score={} (technical={}, news={}, earnings={}, liquidity={})",
        symbol, breakdown.final_score, breakdown.technical_score, breakdown.news_adjustment,
        breakdown.earnings_adjustment, breakdown.liquidity_adjustment,
    )

    if breakdown.final_score < _MIN_CONFIDENCE_TO_ALERT:
        print(f"ℹ️ {symbol}: Final Score={breakdown.final_score}% < 70% - لا إرسال.")
        _dispatch(tracker, _NO_OPPORTUNITY_KEY, _NO_OPPORTUNITY_MESSAGE, telegram_service, sender, chat_id)
        return

    formatter = SignalFormatter()
    levels = formatter.compute_levels(signal, option_contract)
    text = formatter.format(
        signal, option_contract, better_entry=is_better_entry, re_entry=is_re_entry,
        news_note=news_note, earnings_note=earnings_note, confidence_override=breakdown.final_score,
    )

    if not tracker.should_send(symbol, text):
        print(f"⏭️ [{symbol}] نفس الرسالة أُرسِلت خلال آخر 5 دقائق - تخطٍّ.")
        return
    if sender is None or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID فارغان - تعذّر الإرسال. نص الرسالة:")
        print(text)
        return

    success = telegram_service.send_message(chat_id, text)
    if not success:
        print(f"❌ فشل إرسال {symbol} إلى Telegram (HTTP {sender.last_status_code})")
        return

    tracker.record_sent(symbol, text, signal)
    today_et = datetime.now(_ET).date()
    event_counters.record_signal_sent(today_et, levels.option_type, is_better_entry, is_re_entry)

    if entry_kind == "OPEN_NEW" and signal.stop_loss is not None and signal.take_profit is not None:
        tp1_stock = _compute_stock_t1(signal) or signal.take_profit
        trade_id = journal.open_trade(
            symbol=symbol, timeframe=best.timeframe, direction=direction_value, option_type=levels.option_type,
            strike=levels.strike, expiration=levels.expiration_text, option_entry_low=levels.entry_low,
            option_entry_high=levels.entry_high, entry=signal.entry, stop=signal.stop_loss, tp1=tp1_stock,
            tp2=signal.take_profit, confidence=breakdown.final_score, risk_reward=signal.risk_reward or 0.0,
            strategy=",".join(signal.strategy_used), reasons=" | ".join(signal.reasons),
        )
        recently_closed.pop(symbol, None)
        print(f"📒 فُتِحت صفقة #{trade_id} في Trade Journal: {symbol} {levels.option_type}")

    tag = "RE-ENTRY" if is_re_entry else ("BETTER-ENTRY" if is_better_entry else "NEW")
    print(f"✅ [{symbol}] {levels.option_type} أُرسِلت ({tag}) إلى Telegram (HTTP {sender.last_status_code})")


# ---------------------------------------------------------------------
# مراقبة المراكز المفتوحة كل دقيقة (المطلب 5)
# ---------------------------------------------------------------------


def _run_position_monitoring_cycle(position_monitor, telegram_service, sender, chat_id, recently_closed) -> None:
    from app.infrastructure.telegram.position_event_formatter import PositionEventFormatter

    events = position_monitor.check_open_positions()
    if not events:
        return

    formatter = PositionEventFormatter()
    for event in events:
        text = formatter.format(event)
        print(f"📍 {event.kind} {event.symbol} @ {event.price} ({event.profit_loss_percent}%)")
        if sender is not None and chat_id:
            success = telegram_service.send_message(chat_id, text)
            icon = "✅" if success else "❌"
            print(f"{icon} إرسال {event.kind} [{event.symbol}] (HTTP {sender.last_status_code})")
        else:
            print("⚠️ TELEGRAM فارغ - نص الحدث:")
            print(text)

        if event.kind in ("TP2_HIT", "STOP_HIT"):
            recently_closed[event.symbol] = event.occurred_at


# ---------------------------------------------------------------------
# تقارير يومية/أسبوعية/شهرية (المطالب 8-10) بعد إغلاق السوق مباشرة
# ---------------------------------------------------------------------


def _send_period_report(
    journal, stats_calculator, event_counters, counter_store, telegram_service, sender, chat_id,
    period_label: str, period_value: str, start_date: date, today: date,
) -> None:
    from app.infrastructure.telegram.trade_report_formatter import TradeReportFormatter
    from app.infrastructure.tracking.models import TradeReportData

    start_utc = datetime.combine(start_date, dtime.min, tzinfo=_ET).astimezone(timezone.utc)
    end_utc = datetime.now(timezone.utc)

    closed = journal.get_closed_between(start_utc, end_utc)
    sent = journal.get_sent_between(start_utc, end_utc)
    tp1_hits = journal.get_tp1_hits_between(start_utc, end_utc)
    tp2_count = sum(1 for t in closed if t.status == "TP2_HIT")
    stop_count = sum(1 for t in closed if t.status == "STOPPED")
    call_count = sum(1 for t in sent if t.option_type == "CALL")
    put_count = sum(1 for t in sent if t.option_type == "PUT")

    counters_days = counter_store.load_range(start_date, today)
    signals_sent = sum(c.signals_sent for c in counters_days)
    better_entry_count = sum(c.better_entry_count for c in counters_days)
    re_entry_count = sum(c.re_entry_count for c in counters_days)
    if today not in {c.trading_date for c in counters_days}:
        live = event_counters.snapshot(today)
        signals_sent += live.signals_sent
        better_entry_count += live.better_entry_count
        re_entry_count += live.re_entry_count

    stats = stats_calculator.calculate(closed)
    data = TradeReportData(
        period_label=period_label, period_value=period_value, signals_sent=signals_sent, total_trades=len(sent),
        call_count=call_count, put_count=put_count, tp1_count=len(tp1_hits), tp2_count=tp2_count,
        stop_count=stop_count, better_entry_count=better_entry_count, re_entry_count=re_entry_count, statistics=stats,
    )
    text = TradeReportFormatter().format(data)
    print(f"--- تقرير {period_label} ({period_value}) ---")
    print(text)
    if sender is not None and chat_id:
        success = telegram_service.send_message(chat_id, text)
        icon = "✅" if success else "❌"
        print(f"{icon} إرسال تقرير {period_label} (HTTP {sender.last_status_code})")
    else:
        print(f"⚠️ TELEGRAM فارغ - لم يُرسَل تقرير {period_label} فعلياً.")


def _maybe_send_reports(
    journal, stats_calculator, event_counters, counter_store, telegram_service, sender, chat_id, report_state,
) -> None:
    now_et = datetime.now(_ET)
    today = now_et.date()

    if report_state["last_tracking_date"] is not None and report_state["last_tracking_date"] != today:
        counter_store.save(event_counters.snapshot(report_state["last_tracking_date"]))
    report_state["last_tracking_date"] = today

    if not is_in_daily_report_window(now_et.hour):
        return

    if report_state.get("daily_sent_date") != today:
        _send_period_report(
            journal, stats_calculator, event_counters, counter_store, telegram_service, sender, chat_id,
            "يومي", today.isoformat(), today, today,
        )
        report_state["daily_sent_date"] = today

    if is_friday(today) and report_state.get("weekly_sent_date") != today:
        week_start = today - timedelta(days=today.weekday())
        _send_period_report(
            journal, stats_calculator, event_counters, counter_store, telegram_service, sender, chat_id,
            "أسبوعي", f"{week_start.isoformat()} → {today.isoformat()}", week_start, today,
        )
        report_state["weekly_sent_date"] = today

    if is_last_trading_day_of_month(today) and report_state.get("monthly_sent_date") != today:
        month_start = today.replace(day=1)
        _send_period_report(
            journal, stats_calculator, event_counters, counter_store, telegram_service, sender, chat_id,
            "شهري", today.strftime("%Y-%m"), month_start, today,
        )
        report_state["monthly_sent_date"] = today


# ---------------------------------------------------------------------
# الحلقة الرئيسية
# ---------------------------------------------------------------------


def _run_notification_loop(config: ConfigLoader, logger) -> None:
    from app.infrastructure.market.providers.yahoo_provider import YahooFinanceProvider
    from app.infrastructure.market.services import MarketService
    from app.infrastructure.news.providers.yahoo_news_provider import YahooNewsProvider
    from app.infrastructure.scanner.scanner import Scanner
    from app.infrastructure.telegram.notification_tracker import NotificationTracker
    from app.infrastructure.telegram.real_sender import RealTelegramSender
    from app.infrastructure.telegram.telegram_service import TelegramService
    from app.infrastructure.tracking.counter_store import DailyCounterStore
    from app.infrastructure.tracking.event_counters import EventCounterTracker
    from app.infrastructure.tracking.position_monitor import PositionMonitor
    from app.infrastructure.tracking.statistics import TradeStatisticsCalculator
    from app.infrastructure.tracking.trade_journal import TradeJournal

    bot_token = _resolve_env("TELEGRAM_BOT_TOKEN", config)
    chat_id = _resolve_env("TELEGRAM_CHAT_ID", config)
    if not bot_token or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID فارغان - سيعمل البوت لكن بلا إرسال فعلي إلى Telegram.")

    db_manager = DatabaseManager(config.settings.database.url)
    db_manager.connect()
    db_manager.test_connection()
    db_manager.create_tables()

    provider = YahooFinanceProvider()
    market_service = MarketService(provider)
    scanner = Scanner(market_service)
    news_provider = YahooNewsProvider()
    journal = TradeJournal(db_manager)
    position_monitor = PositionMonitor(market_service, journal)
    tracker = NotificationTracker()
    event_counters = EventCounterTracker()
    counter_store = DailyCounterStore(db_manager)
    stats_calculator = TradeStatisticsCalculator()
    sender = RealTelegramSender(bot_token=bot_token) if bot_token else None
    telegram_service = TelegramService(sender=sender) if sender is not None else TelegramService()

    recently_closed: dict[str, datetime] = {}
    report_state: dict[str, object] = {
        "last_tracking_date": None, "daily_sent_date": None, "weekly_sent_date": None, "monthly_sent_date": None,
    }

    print(f"🕒 بدء الفحص الدوري كل {int(_SCAN_INTERVAL_SECONDS)} ثانية (Ctrl+C للإيقاف)...")
    try:
        while True:
            try:
                market_status = market_service.get_market_status()
                if market_status.is_open:
                    _run_scan_cycle(
                        config, logger, provider, market_service, scanner, news_provider, journal,
                        event_counters, tracker, telegram_service, sender, chat_id, recently_closed,
                    )
                else:
                    print("💤 السوق الأمريكي مغلق حالياً (خارج ساعات التداول العادية) - لا فحص جديد.")

                _run_position_monitoring_cycle(position_monitor, telegram_service, sender, chat_id, recently_closed)
                _maybe_send_reports(
                    journal, stats_calculator, event_counters, counter_store, telegram_service, sender, chat_id,
                    report_state,
                )
            except Exception:
                logger.exception("دورة فحص/إشعار فشلت - سيُعاد المحاولة في الدورة القادمة.")
            time.sleep(_SCAN_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف الفحص الدوري.")
    finally:
        if sender is not None:
            sender.close()
        db_manager.close()


def main() -> None:
    ProjectPaths.ensure_directories()

    config = ConfigLoader()

    logger_service = LoggerService()
    logger_service.setup(config.settings.logging)
    logger = logger_service.get_logger()

    logger.info(
        "بدء تشغيل {} (v{}) | البيئة: {}",
        config.settings.app.name, config.settings.app.version, config.settings.environment.value,
    )
    logger.info("عدد الرموز المُحمَّلة من config/symbols.yaml: {}", len(config.symbols))
    print(
        f"✅ {config.settings.app.name} v{config.settings.app.version} بدأ التشغيل بنجاح "
        f"(البيئة: {config.settings.environment.value})."
    )

    _run_notification_loop(config, logger)


if __name__ == "__main__":
    main()
