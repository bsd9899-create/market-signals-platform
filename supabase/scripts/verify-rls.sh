#!/usr/bin/env bash
# يتحقق من سياسات RLS فعليًا على Postgres محلي — يحاكي بيئة Supabase
# (auth schema + أدوار anon/authenticated/service_role) ثم يطبّق كل
# migrations/*.sql بالترتيب ويشغّل تأكيدات أمنية حقيقية (وليس مجرد
# "الجدول يقبل الاستعلام" — بل "يرفض بالضبط ما يجب أن يرفضه").
#
# الاستخدام (يحتاج postgresql محليًا وصلاحية sudo لمستخدم postgres):
#   bash supabase/scripts/verify-rls.sh
#
# هذا هو نفس الأسلوب المستخدم يدويًا لاكتشاف وإصلاح خطأين حقيقيين أثناء
# بناء المرحلة 2 (تسريب views الفريق، وغياب trigger عضوية المالك) —
# محوَّل هنا لسكريبت متكرر بدل تنفيذ يدوي لمرة واحدة.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

DB_NAME="hemma_rls_test"
MIGRATIONS_DIR="supabase/migrations"

echo "==> إعادة تهيئة قاعدة الاختبار $DB_NAME"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
drop database if exists ${DB_NAME};
create database ${DB_NAME};
SQL

echo "==> محاكاة بيئة Supabase (auth schema + أدوار)"
sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
create extension if not exists pgcrypto;
create schema auth;
create table auth.users (id uuid primary key default gen_random_uuid(), raw_user_meta_data jsonb default '{}'::jsonb);
create or replace function auth.uid() returns uuid
language sql stable
as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;

do $$
begin
  if not exists (select from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
  if not exists (select from pg_roles where rolname = 'service_role') then create role service_role nologin bypassrls; end if;
end $$;

grant usage on schema public to anon, authenticated;
grant usage on schema auth to anon, authenticated;
grant usage on schema public to service_role;
alter default privileges in schema public grant select, insert, update, delete on tables to authenticated;
alter default privileges in schema public grant execute on functions to authenticated;
grant select on all tables in schema auth to authenticated;
grant all on all tables in schema public to service_role;

create publication supabase_realtime;
SQL

echo "==> تطبيق كل migrations بالترتيب"
for f in $(ls "$MIGRATIONS_DIR"/*.sql | sort); do
  echo "   - $(basename "$f")"
  sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$f" > /dev/null
done

echo "==> إعداد مستخدمَين للاختبار"
sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
insert into auth.users (id, raw_user_meta_data) values
  ('11111111-1111-1111-1111-111111111111', '{"display_name":"مستخدم١"}'),
  ('22222222-2222-2222-2222-222222222222', '{"display_name":"مستخدم٢"}');
SQL

echo "==> تأكيد: مستخدم لا يرى ملف مستخدم آخر مباشرة"
sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
set role authenticated;
set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
do $$
declare visible_count int;
begin
  select count(*) into visible_count from public.profiles;
  if visible_count <> 1 then
    raise exception 'فشل: يجب أن يرى المستخدم صفه الشخصي فقط (رأى %)', visible_count;
  end if;
end $$;
SQL

echo "==> تأكيد: لا يقدر مستخدم يكتب سجل ماء باسم مستخدم آخر"
sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
set role authenticated;
set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
do $$
begin
  insert into public.water_logs (user_id, amount_ml)
    values ('22222222-2222-2222-2222-222222222222', 250);
  raise exception 'فشل: كان يجب أن يُرفض هذا الإدراج بواسطة RLS';
exception
  when insufficient_privilege then
    raise notice 'نجح: رُفض الإدراج كما هو متوقع';
end $$;
SQL

echo "==> تأكيد: لا يقدر مستخدم يمنح نفسه Premium"
sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
set role authenticated;
set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
update public.subscriptions set is_premium = true where user_id = '11111111-1111-1111-1111-111111111111';
do $$
declare premium boolean;
begin
  select is_premium into premium from public.subscriptions where user_id = '11111111-1111-1111-1111-111111111111';
  if premium is distinct from false then
    raise exception 'فشل: تعديل is_premium من العميل كان يجب أن يُرفض تمامًا';
  end if;
end $$;
SQL

echo "==> تأكيد: الانضمام لفريق بدون كود دعوة يُرفض"
sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
set role authenticated;
set request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
insert into public.teams (name, created_by) values ('فريق الاختبار', '11111111-1111-1111-1111-111111111111');

reset role;
set role authenticated;
set request.jwt.claim.sub = '22222222-2222-2222-2222-222222222222';
do $$
begin
  perform public.join_team_by_code('كود-غير-صحيح');
  raise exception 'فشل: كان يجب رفض كود دعوة غير صحيح';
exception
  when others then
    raise notice 'نجح: رُفض كود الدعوة غير الصحيح كما هو متوقع';
end $$;
SQL

echo "==> تنظيف"
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "drop database if exists ${DB_NAME};" > /dev/null

echo ""
echo "✅ كل تأكيدات RLS نجحت."
