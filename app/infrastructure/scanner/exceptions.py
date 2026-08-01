"""
app/infrastructure/scanner/exceptions.py
-----------------------------------------------
استثناءات واضحة للماسح (Scanner).
"""

from __future__ import annotations


class ScannerError(Exception):
    """الأصل المشترك لكل أخطاء الماسح."""
