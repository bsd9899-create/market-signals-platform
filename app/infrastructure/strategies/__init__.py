"""
app/infrastructure/strategies
----------------------------------
Strategy Engine: استراتيجيات مستقلة قابلة للإضافة (Open/Closed) - كل
استراتيجية في ملفها المستقل تحت strategies/، تطبّق واجهة Strategy
(base.py) وتُسجَّل في StrategyRegistry، بنفس أسلوب محرك المؤشرات تماماً.
"""
