"""
app/infrastructure/signals
------------------------------
Signal Engine: يدمج مخرجات محرك المؤشرات (IndicatorService) في إشارة
موحَّدة واحدة (Signal) بدرجة ثقة (Confidence 0-100) واتجاه
(BUY/SELL/NEUTRAL). لا يستخدم أي API خارجي - يعمل فقط على Candle.
"""
