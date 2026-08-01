"""
app/infrastructure/database
------------------------------
طبقة قاعدة البيانات الكاملة: DatabaseManager (اتصال/جلسات/جداول)،
BaseModel، Repository عام، والنماذج (models/). SQLite حالياً - التبديل
لاحقاً إلى PostgreSQL يتم فقط بتغيير DATABASE_URL في .env، بدون أي
تعديل على الكود (كل شيء هنا مستقل عن نوع قاعدة البيانات الفعلي عبر
SQLAlchemy Engine).
"""
