"""
app/infrastructure/reports
-------------------------------
Report Engine: تقارير يومية/أسبوعية/شهرية/أداء + إحصائيات (Win Rate،
متوسط RR، متوسط الثقة، إحصائيات الاستراتيجيات). حسابات رياضية بحتة على
بيانات مُمرَّرة (DailyStats/Signal) - **مستقلة عمداً عن
app.infrastructure.database** حتى تبقى قابلة للاختبار بلا قاعدة بيانات
حقيقية؛ تحويل صفوف قاعدة البيانات الفعلية (DailyReport ORM) إلى
DailyStats مسؤولية طبقة تكامل لاحقة (مثال: app/main.py أو Use Case
مستقبلي في app/application).
"""
