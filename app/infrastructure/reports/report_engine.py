"""
app/infrastructure/reports/report_engine.py
--------------------------------------------------
ReportEngine: حسابات تقارير بحتة (رياضيات فقط) - لا اتصال بقاعدة
بيانات، ولا API خارجي. يعمل على بيانات مُمرَّرة إليه (DailyStats/Signal).
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.reports.exceptions import EmptyReportDataError
from app.infrastructure.reports.models import (
    DailyReportSummary,
    DailyStats,
    MonthlyReportSummary,
    PerformanceReportSummary,
    SignalStatistics,
    StrategyStatistics,
    WeeklyReportSummary,
)
from app.infrastructure.signals.models import Signal, SignalDirection


class ReportEngine:
    def win_rate(self, wins: int, losses: int) -> float:
        total = wins + losses
        if total == 0:
            return 0.0
        return round(wins / total * 100, 2)

    def average_risk_reward(self, risk_reward_ratios: list[float]) -> float:
        if not risk_reward_ratios:
            return 0.0
        return round(sum(risk_reward_ratios) / len(risk_reward_ratios), 2)

    def daily_report(self, stats: DailyStats) -> DailyReportSummary:
        summary = DailyReportSummary(
            report_date=stats.report_date, total_scans=stats.total_scans, signals_sent=stats.signals_sent,
            wins=stats.wins, losses=stats.losses, win_rate=self.win_rate(stats.wins, stats.losses),
        )
        logger.info("ReportEngine.daily_report: {} -> win_rate={}%", stats.report_date, summary.win_rate)
        return summary

    def weekly_report(self, daily_stats_list: list[DailyStats]) -> WeeklyReportSummary:
        if not daily_stats_list:
            raise EmptyReportDataError("لا توجد بيانات يومية لتوليد تقرير أسبوعي.")

        sorted_days = sorted(daily_stats_list, key=lambda d: d.report_date)
        summary = WeeklyReportSummary(
            week_start=sorted_days[0].report_date,
            week_end=sorted_days[-1].report_date,
            total_scans=sum(d.total_scans for d in daily_stats_list),
            signals_sent=sum(d.signals_sent for d in daily_stats_list),
            wins=sum(d.wins for d in daily_stats_list),
            losses=sum(d.losses for d in daily_stats_list),
            win_rate=self.win_rate(sum(d.wins for d in daily_stats_list), sum(d.losses for d in daily_stats_list)),
        )
        logger.info("ReportEngine.weekly_report: {}..{} -> win_rate={}%", summary.week_start, summary.week_end, summary.win_rate)
        return summary

    def monthly_report(self, daily_stats_list: list[DailyStats]) -> MonthlyReportSummary:
        if not daily_stats_list:
            raise EmptyReportDataError("لا توجد بيانات يومية لتوليد تقرير شهري.")

        sorted_days = sorted(daily_stats_list, key=lambda d: d.report_date)
        summary = MonthlyReportSummary(
            month_start=sorted_days[0].report_date,
            month_end=sorted_days[-1].report_date,
            total_scans=sum(d.total_scans for d in daily_stats_list),
            signals_sent=sum(d.signals_sent for d in daily_stats_list),
            wins=sum(d.wins for d in daily_stats_list),
            losses=sum(d.losses for d in daily_stats_list),
            win_rate=self.win_rate(sum(d.wins for d in daily_stats_list), sum(d.losses for d in daily_stats_list)),
        )
        logger.info("ReportEngine.monthly_report: {}..{} -> win_rate={}%", summary.month_start, summary.month_end, summary.win_rate)
        return summary

    def signal_statistics(self, signals: list[Signal]) -> SignalStatistics:
        if not signals:
            return SignalStatistics(total=0, buy_count=0, sell_count=0, neutral_count=0, average_confidence=0.0)

        buy_count = sum(1 for s in signals if s.direction == SignalDirection.BUY)
        sell_count = sum(1 for s in signals if s.direction == SignalDirection.SELL)
        neutral_count = sum(1 for s in signals if s.direction == SignalDirection.NEUTRAL)
        average_confidence = round(sum(s.confidence for s in signals) / len(signals), 2)

        strategy_confidences: dict[str, list[float]] = {}
        for signal in signals:
            for strategy_name in signal.strategy_used:
                strategy_confidences.setdefault(strategy_name, []).append(signal.confidence)

        strategy_stats = [
            StrategyStatistics(
                strategy_name=name, signal_count=len(confidences),
                average_confidence=round(sum(confidences) / len(confidences), 2),
            )
            for name, confidences in sorted(strategy_confidences.items())
        ]

        stats = SignalStatistics(
            total=len(signals), buy_count=buy_count, sell_count=sell_count, neutral_count=neutral_count,
            average_confidence=average_confidence, strategy_statistics=strategy_stats,
        )
        logger.info(
            "ReportEngine.signal_statistics: total={}, BUY={}, SELL={}, NEUTRAL={}, avg_confidence={}",
            stats.total, buy_count, sell_count, neutral_count, average_confidence,
        )
        return stats

    def performance_report(
        self, daily_stats_list: list[DailyStats], risk_reward_ratios: list[float], signals: list[Signal] | None = None,
    ) -> PerformanceReportSummary:
        if not daily_stats_list:
            raise EmptyReportDataError("لا توجد بيانات يومية لتوليد تقرير الأداء.")

        total_scans = sum(d.total_scans for d in daily_stats_list)
        signals_sent = sum(d.signals_sent for d in daily_stats_list)
        wins = sum(d.wins for d in daily_stats_list)
        losses = sum(d.losses for d in daily_stats_list)
        average_confidence = round(sum(s.confidence for s in signals) / len(signals), 2) if signals else 0.0

        summary = PerformanceReportSummary(
            total_scans=total_scans, signals_sent=signals_sent, wins=wins, losses=losses,
            win_rate=self.win_rate(wins, losses),
            average_risk_reward=self.average_risk_reward(risk_reward_ratios),
            average_confidence=average_confidence,
        )
        logger.info(
            "ReportEngine.performance_report: win_rate={}%, avg_rr={}, avg_confidence={}",
            summary.win_rate, summary.average_risk_reward, summary.average_confidence,
        )
        return summary
