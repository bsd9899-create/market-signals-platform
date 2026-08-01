"""
app/infrastructure/reports/exceptions.py
-------------------------------------------------
استثناءات واضحة لمحرك التقارير.
"""

from __future__ import annotations


class ReportError(Exception):
    """الأصل المشترك لكل أخطاء محرك التقارير."""


class EmptyReportDataError(ReportError):
    """لا توجد بيانات كافية لتوليد التقرير المطلوب (مثال: قائمة فارغة)."""
