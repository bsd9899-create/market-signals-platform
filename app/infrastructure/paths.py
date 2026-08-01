"""
app/infrastructure/paths.py
-------------------------------
سجل مركزي لكل مسارات المشروع - بدل الاعتماد على متغير BASE_DIR عالمي
متفرق بين الوحدات. كل وحدة تحتاج مساراً تستورد ProjectPaths مباشرة.

الجذر (ROOT) يُحسَب من موقع هذا الملف نفسه عبر Path.resolve() - لا علاقة
له بـ sys.path إطلاقاً ولا يعتمد على مجلد العمل الحالي (Working
Directory) عند التشغيل.
"""

from __future__ import annotations

from pathlib import Path


class ProjectPaths:
    """كل المسارات كخصائص صف (Class Attributes) ثابتة - لا حاجة لإنشاء
    كائن (Instance) لاستخدامها."""

    ROOT: Path = Path(__file__).resolve().parents[2]
    CONFIG_DIR: Path = ROOT / "config"
    LOG_DIR: Path = ROOT / "logs"
    DATABASE_DIR: Path = ROOT / "data"
    REPORTS_DIR: Path = ROOT / "reports"
    TEMP_DIR: Path = ROOT / "temp"

    @classmethod
    def ensure_directories(cls) -> None:
        """ينشئ كل المجلدات القابلة للإنشاء تلقائياً عند بدء التشغيل.
        CONFIG_DIR مستثنى عمداً - يجب أن يكون موجوداً مسبقاً بملفاته
        الفعلية (settings.yaml وsymbols.yaml)، وعدم وجوده خطأ حقيقي
        يجب أن يظهر بوضوح (راجع ConfigLoader) وليس أن يُخفى بإنشائه فارغاً."""
        for path in (cls.LOG_DIR, cls.DATABASE_DIR, cls.REPORTS_DIR, cls.TEMP_DIR):
            path.mkdir(parents=True, exist_ok=True)
