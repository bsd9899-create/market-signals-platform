# Supabase — هِمّة

## تطبيق الـ migrations على مشروع حقيقي

بعد إنشاء مشروع Supabase (لوحة التحكم أو `supabase projects create`):

```bash
npx supabase login
npx supabase link --project-ref <project-ref>
npx supabase db push
```

هذا يطبّق كل ملفات `migrations/*.sql` بالترتيب الزمني في اسمها.

## توليد أنواع TypeScript من المشروع الفعلي

بعد الربط، لمطابقة `src/data/database.types.ts` (المكتوب يدويًا الآن)
مع المخطط الحقيقي:

```bash
npx supabase gen types typescript --project-id <project-ref> > src/data/database.types.ts
```

## ملخص المخطط

| الملف | المحتوى |
|---|---|
| `20260831000001_profiles_and_goals.sql` | profiles + user_goals + trigger إنشاء تلقائي عند التسجيل |
| `20260831000002_daily_logs.sql` | workouts, nutrition_logs, water_logs, steps_logs, sleep_logs, weight_logs |
| `20260831000003_daily_promises_and_progress.sql` | daily_promises (وعدك اليوم) + daily_progress (إنجاز اليوم) |
| `20260831000004_teams_and_challenges.sql` | teams, team_members, challenges, challenge_progress + `join_team_by_code()` + view `team_roster` |
| `20260831000005_accountability.sql` | رفيق هِمّة: accountability_pairs + accountability_pings |
| `20260831000006_points_and_leaderboard.sql` | points_ledger + views: `user_points_totals` (داخلية)، `team_pulse_daily`، `team_leaderboard` |
| `20260831000007_notifications.sql` | notifications (كتابة من الخادم فقط) |
| `20260831000008_subscriptions.sql` | subscriptions — حالة هِمّة+ (كتابة من الخادم فقط عبر RevenueCat webhook) |
| `20260831000009_realtime.sql` | تفعيل Realtime على الجداول التي تحتاج تحديثًا فوريًا |

## قواعد أمان أساسية مطبَّقة من البداية

- **RLS مفعّلة على كل جدول** بلا استثناء.
- بيانات صحية شخصية (تمرين/تغذية/ماء/خطوات/نوم/وزن) **خاصة تمامًا بصاحبها**.
- رؤية بيانات زميل الفريق (الاسم/الصورة) تمر حصرًا عبر views مقيّدة
  (`team_roster`, `team_leaderboard`, `team_pulse_daily`) تفرض تقييدها
  صراحة بـ `auth.uid()` — وليس عبر فتح جدول `profiles` نفسه.
- **`subscriptions` غير قابل للتعديل من العميل إطلاقًا** — لو سُمح بذلك
  لاستطاع أي مستخدم منح نفسه Premium مجانًا. الكتابة فقط من Edge
  Function موثوقة تستخدم service role key عند استقبال RevenueCat webhook
  (تُبنى في المرحلة 9).
- الانضمام لفريق يمر عبر دالة `join_team_by_code()` فقط، وليس إدراجًا
  مباشرًا في `team_members`، لمنع الانضمام بدون كود دعوة صحيح.

## بانتظار مشروع Supabase حقيقي

هذه الـ migrations جاهزة كاملة لكنها لم تُطبَّق بعد على أي مشروع فعلي
(لا توجد بيانات اعتماد Supabase في هذه البيئة). راجع طلب التوقف في
ملخص المرحلة 2 للتفاصيل.
