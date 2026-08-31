-- شغّل هذا في Supabase SQL Editor على المشروع الفعلي، وأرسل لي النتيجة
-- كاملة (صف واحد لكل فحص) — يتحقق من: عدد الجداول، تفعيل RLS على
-- الكل، وجود الدوال/الـ views الحرجة، ووجود publication الـ Realtime.

select 'الجداول في public' as check_name,
       count(*)::text as result,
       '19 متوقعة' as expected
from information_schema.tables
where table_schema = 'public' and table_type = 'BASE TABLE'

union all

select 'جداول بدون RLS مفعّلة (يجب أن تكون صفر)',
       coalesce(string_agg(relname, ', '), '0 - ممتاز'),
       '0'
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity

union all

select 'الدوال الحرجة الموجودة',
       count(*)::text,
       '4 متوقعة: handle_new_user, join_team_by_code, shares_team_with, handle_new_team'
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in ('handle_new_user', 'join_team_by_code', 'shares_team_with', 'handle_new_team')

union all

select 'الـ views الحرجة الموجودة',
       count(*)::text,
       '4 متوقعة: team_roster, team_pulse_daily, team_leaderboard, user_points_totals'
from information_schema.views
where table_schema = 'public'
  and table_name in ('team_roster', 'team_pulse_daily', 'team_leaderboard', 'user_points_totals')

union all

select 'عمود onboarding_completed_at في profiles',
       count(*)::text,
       '1 (migration 10 طُبِّقت)'
from information_schema.columns
where table_schema = 'public' and table_name = 'profiles' and column_name = 'onboarding_completed_at'

union all

select 'subscriptions بدون أي insert/update policy للعميل (أمان حرج)',
       coalesce(string_agg(policyname, ', '), '0 - ممتاز (كما هو مطلوب)'),
       '0 صفوف (لا insert/update لـ authenticated)'
from pg_policies
where schemaname = 'public' and tablename = 'subscriptions' and cmd in ('INSERT', 'UPDATE')

union all

select 'جدول team_members بدون أي insert policy مباشر (أمان حرج)',
       coalesce(string_agg(policyname, ', '), '0 - ممتاز (الانضمام عبر الدالة فقط)'),
       '0 صفوف'
from pg_policies
where schemaname = 'public' and tablename = 'team_members' and cmd = 'INSERT';
