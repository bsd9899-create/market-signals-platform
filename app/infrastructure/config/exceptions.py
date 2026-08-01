"""
app/infrastructure/config/exceptions.py
-------------------------------------------
استثناءات واضحة ومفهومة لأخطاء تحميل الإعدادات - بدل ترك FileNotFoundError
عام أو yaml.YAMLError خام ينفجر بدون سياق. كل استثناء هنا يذكر المسار
الدقيق والسبب.
"""

from __future__ import annotations

from pathlib import Path


class ConfigurationError(Exception):
    """الأصل المشترك لكل أخطاء الإعدادات - يمكن التقاطه وحده لالتقاط أي
    خطأ إعدادات بغض النظر عن نوعه الدقيق."""


class ConfigFileNotFoundError(ConfigurationError):
    """ملف إعدادات مطلوب غير موجود على القرص."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"ملف الإعدادات غير موجود: {path}")
        self.path = path


class ConfigParseError(ConfigurationError):
    """ملف الإعدادات موجود لكن صيغة YAML بداخله غير صحيحة."""

    def __init__(self, path: Path, original_error: Exception) -> None:
        super().__init__(f"صيغة YAML غير صحيحة في الملف: {path}\nالسبب: {original_error}")
        self.path = path
        self.original_error = original_error
