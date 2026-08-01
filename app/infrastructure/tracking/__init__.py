"""
app/infrastructure/tracking
--------------------------------
طبقة تتبّع الصفقات (Trade Journal + مراقبة المراكز المفتوحة +
إحصائيات) - جديدة بالكامل، لا تلمس Scanner/SignalEngine/RiskManager/
MarketService إطلاقاً؛ تستهلك MarketService.get_quote() العامة فقط
(بلا أي تعديل عليها) وSignal الجاهز فقط.
"""
