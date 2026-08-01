"""
app/infrastructure/scanner
------------------------------
Scanner: يفحص عدة رموز عبر عدة أطر زمنية بالتوازي (ThreadPoolExecutor)،
ينتج Signal لكل تركيبة (رمز، إطار زمني) عبر SignalEngine. Scheduler
بسيط يُشغِّل الفحص دورياً في Thread خلفي.
"""
