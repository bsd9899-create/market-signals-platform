"""
app/infrastructure/indicators
----------------------------------
محرك التحليل الفني (Indicator Engine) - مستقل تماماً عن أي API خارجي؛
يعمل فقط على app.infrastructure.market.models.Candle.

كل مؤشر هو صف مستقل يطبّق واجهة Indicator (base.py) ويُسجَّل في
IndicatorRegistry - إضافة مؤشر جديد لاحقاً لا تتطلب تعديل أي كود قائم
(Open/Closed Principle): فقط ملف جديد + استدعاء register() واحد.
"""
