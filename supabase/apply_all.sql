-- تشغيل يدوي مُجمَّع لكل الـ migrations دفعة واحدة عبر Supabase SQL Editor.
-- هذا الملف مساعد فقط وليس migration متتبَّعًا بحد ذاته — لا تضعه داخل
-- مجلد migrations الحقيقي، ولا تشغّله مرتين على نفس المشروع.

-- ============================================================
-- 20260831000001_profiles_and_goals.sql
-- ============================================================
-- ============================================================
-- الملفات الشخصية والأهداف الشخصية
-- ============================================================
-- profiles تمتد من auth.users (Supabase Auth). صف واحد لكل مستخدم
-- يُنشأ تلقائيًا عبر trigger عند التسجيل.

create type public.goal_type as enum (
  'lose_weight',
  'gain_muscle',
  'increase_activity',
  'general_health'
);

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null,
  avatar_url text,
  goal_type public.goal_type not null default 'general_health',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.profiles is 'ملف شخصي عام لكل مستخدم — يمتد من auth.users.';

-- أهداف قابلة للقياس يوميًا (تُستخدم لحساب "إنجاز اليوم" و% الالتزام
-- بالفريق — راجع 20260831000006_points_and_leaderboard.sql).
create table public.user_goals (
  user_id uuid primary key references public.profiles (id) on delete cascade,
  target_water_ml integer not null default 2000,
  target_steps integer not null default 8000,
  target_sleep_hours numeric(4, 1) not null default 7.5,
  target_workouts_per_week integer not null default 3,
  target_weight_kg numeric(5, 1),
  updated_at timestamptz not null default now()
);

comment on table public.user_goals is 'أهداف قابلة للقياس لكل مستخدم — أساس حساب نسبة الالتزام الشخصية.';

-- إنشاء profile + user_goals تلقائيًا عند تسجيل مستخدم جديد.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', 'مستخدم هِمّة'));

  insert into public.user_goals (user_id) values (new.id);

  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger set_profiles_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

create trigger set_user_goals_updated_at
  before update on public.user_goals
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------
-- Row Level Security: كل مستخدم يرى/يعدّل ملفه وأهدافه فقط.
-- رؤية ملفات الآخرين (زملاء الفريق) تمر عبر view مقيّدة فقط
-- (راجع 20260831000004_teams_and_challenges.sql) وليس هذا الجدول مباشرة.
-- ---------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.user_goals enable row level security;

create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = id);

create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

create policy "user_goals_select_own" on public.user_goals
  for select using (auth.uid() = user_id);

create policy "user_goals_upsert_own" on public.user_goals
  for insert with check (auth.uid() = user_id);

create policy "user_goals_update_own" on public.user_goals
  for update using (auth.uid() = user_id);

-- ============================================================
-- 20260831000002_daily_logs.sql
-- ============================================================
-- ============================================================
-- سجلات البيانات اليومية: تمرين، تغذية، ماء، خطوات، وزن، نوم
-- ============================================================
-- كل جدول يحمل source ('manual' | 'healthkit') لأن المرحلة 10 ستضيف
-- مزامنة HealthKit دون الحاجة لأي تغيير هيكلي هنا.

create type public.log_source as enum ('manual', 'healthkit');

create table public.workouts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  title text not null,
  performed_at timestamptz not null default now(),
  duration_minutes integer not null check (duration_minutes > 0),
  exercises jsonb not null default '[]'::jsonb,
  source public.log_source not null default 'manual',
  created_at timestamptz not null default now()
);

create table public.nutrition_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  meal_type text not null check (meal_type in ('breakfast', 'lunch', 'dinner', 'snack')),
  description text not null,
  calories integer check (calories >= 0),
  logged_at timestamptz not null default now(),
  source public.log_source not null default 'manual',
  created_at timestamptz not null default now()
);

create table public.water_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  amount_ml integer not null check (amount_ml > 0),
  logged_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

-- الخطوات والنوم إجمالي يومي واحد (وليس أحداثًا متعددة) — upsert لكل يوم.
create table public.steps_logs (
  user_id uuid not null references public.profiles (id) on delete cascade,
  date date not null,
  steps integer not null check (steps >= 0),
  source public.log_source not null default 'manual',
  updated_at timestamptz not null default now(),
  primary key (user_id, date)
);

create table public.sleep_logs (
  user_id uuid not null references public.profiles (id) on delete cascade,
  date date not null,
  hours numeric(3, 1) not null check (hours >= 0 and hours <= 24),
  source public.log_source not null default 'manual',
  updated_at timestamptz not null default now(),
  primary key (user_id, date)
);

create table public.weight_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  weight_kg numeric(5, 1) not null check (weight_kg > 0),
  logged_at timestamptz not null default now(),
  source public.log_source not null default 'manual',
  created_at timestamptz not null default now()
);

create index workouts_user_performed_idx on public.workouts (user_id, performed_at desc);
create index nutrition_logs_user_logged_idx on public.nutrition_logs (user_id, logged_at desc);
create index water_logs_user_logged_idx on public.water_logs (user_id, logged_at desc);
create index weight_logs_user_logged_idx on public.weight_logs (user_id, logged_at desc);

-- ---------------------------------------------------------------
-- RLS: كل سجلات هذه الشاشة خاصة تمامًا بصاحبها — بيانات صحية حسّاسة.
-- ---------------------------------------------------------------
alter table public.workouts enable row level security;
alter table public.nutrition_logs enable row level security;
alter table public.water_logs enable row level security;
alter table public.steps_logs enable row level security;
alter table public.sleep_logs enable row level security;
alter table public.weight_logs enable row level security;

do $$
declare
  t text;
begin
  foreach t in array array[
    'workouts', 'nutrition_logs', 'water_logs', 'steps_logs', 'sleep_logs', 'weight_logs'
  ]
  loop
    execute format(
      'create policy "%1$s_owner_all" on public.%1$s for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
      t
    );
  end loop;
end $$;

-- ============================================================
-- 20260831000003_daily_promises_and_progress.sql
-- ============================================================
-- ============================================================
-- وعدك اليوم + إنجاز اليوم (قرار اليوم / وضع الإنقاذ محسوبان في التطبيق
-- بواسطة Rule Engine — هذا الجدول يخزّن النتيجة اليومية فقط للتاريخ
-- والتقييم الأسبوعي، وليس منطق القرار نفسه).
-- ============================================================

create type public.promise_type as enum (
  'workout',
  'steps',
  'nutrition',
  'water',
  'sleep'
);

create table public.daily_promises (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  date date not null,
  promise_type public.promise_type not null,
  fulfilled boolean,
  created_at timestamptz not null default now(),
  unique (user_id, date)
);

create table public.daily_progress (
  user_id uuid not null references public.profiles (id) on delete cascade,
  date date not null,
  completion_percent numeric(5, 2) not null default 0 check (completion_percent between 0 and 100),
  decision_text text,
  recovery_mode boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (user_id, date)
);

comment on column public.daily_progress.recovery_mode is
  'true عندما يفعّل Rule Engine "وضع الإنقاذ" لهذا اليوم بسبب انقطاع سابق.';

alter table public.daily_promises enable row level security;
alter table public.daily_progress enable row level security;

create policy "daily_promises_owner_all" on public.daily_promises
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "daily_progress_owner_all" on public.daily_progress
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ============================================================
-- 20260831000004_teams_and_challenges.sql
-- ============================================================
-- ============================================================
-- الفرق والتحديات ونبض الفريق
-- ============================================================

create type public.team_role as enum ('owner', 'member');

create table public.teams (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  invite_code text not null unique default substr(replace(gen_random_uuid()::text, '-', ''), 1, 8),
  created_by uuid not null references public.profiles (id),
  created_at timestamptz not null default now()
);

create table public.team_members (
  team_id uuid not null references public.teams (id) on delete cascade,
  user_id uuid not null references public.profiles (id) on delete cascade,
  role public.team_role not null default 'member',
  joined_at timestamptz not null default now(),
  primary key (team_id, user_id)
);

create table public.challenges (
  id uuid primary key default gen_random_uuid(),
  team_id uuid not null references public.teams (id) on delete cascade,
  title text not null,
  description text,
  start_date date not null,
  end_date date not null check (end_date >= start_date),
  created_by uuid not null references public.profiles (id),
  created_at timestamptz not null default now()
);

-- نسبة التزام كل عضو بهدفه الشخصي داخل التحدي — وليس رقمًا مطلقًا
-- (وزن/سعرات)، حتى يتنافس من يريد التنحيف مع من يريد التضخم بعدالة.
create table public.challenge_progress (
  challenge_id uuid not null references public.challenges (id) on delete cascade,
  user_id uuid not null references public.profiles (id) on delete cascade,
  progress_percent numeric(5, 2) not null default 0 check (progress_percent between 0 and 100),
  updated_at timestamptz not null default now(),
  primary key (challenge_id, user_id)
);

create index team_members_user_idx on public.team_members (user_id);
create index challenges_team_idx on public.challenges (team_id);

-- ---------------------------------------------------------------
-- دالة مساعدة: هل يشارك المستخدم الحالي نفس الفريق مع صف معيّن؟
-- تُستخدم داخل سياسات RLS لعدة جداول لتفادي التكرار.
-- ---------------------------------------------------------------
create function public.shares_team_with(target_user uuid)
returns boolean
language sql
stable
security definer set search_path = public
as $$
  select exists (
    select 1
    from public.team_members me
    join public.team_members them on them.team_id = me.team_id
    where me.user_id = auth.uid() and them.user_id = target_user
  );
$$;

-- ---------------------------------------------------------------
-- إنشاء الفريق يضيف صاحبه تلقائيًا كـ owner في team_members — بدلاً
-- من انتظار إدراج ثانٍ من العميل قد يُنسى أو يفشل جزئيًا.
-- ---------------------------------------------------------------
create function public.handle_new_team()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.team_members (team_id, user_id, role)
  values (new.id, new.created_by, 'owner');
  return new;
end;
$$;

create trigger on_team_created
  after insert on public.teams
  for each row execute function public.handle_new_team();

-- ---------------------------------------------------------------
-- الانضمام لفريق عبر كود الدعوة فقط — دالة موثوقة (Security Definer)
-- بدل السماح بإدراج مباشر في team_members، لمنع أي مستخدم من ضمّ
-- نفسه لفريق لا يملك كوده.
-- ---------------------------------------------------------------
create function public.join_team_by_code(p_invite_code text)
returns uuid
language plpgsql
security definer set search_path = public
as $$
declare
  v_team_id uuid;
begin
  select id into v_team_id from public.teams where invite_code = p_invite_code;

  if v_team_id is null then
    raise exception 'كود الدعوة غير صحيح';
  end if;

  insert into public.team_members (team_id, user_id, role)
  values (v_team_id, auth.uid(), 'member')
  on conflict (team_id, user_id) do nothing;

  return v_team_id;
end;
$$;

-- ---------------------------------------------------------------
-- Views مقيّدة لعرض بيانات الزملاء (اسم/صورة/نقاط) بدون فتح الجداول
-- الأساسية الحساسة مباشرة — هذا هو المسار الوحيد لرؤية بيانات الآخرين.
--
-- ملاحظة أمان مهمة: هذه الـ views تُنشأ بدون security_invoker، أي أنها
-- تُنفَّذ بصلاحية مالك الـ view (postgres) فتتجاوز RLS الخاصة بجدول
-- profiles (الذي يقصر القراءة على صاحب الصف فقط). لذلك كل تقييد
-- الوصول هنا مكتوب صراحة داخل شرط where (عبر auth.uid())، وليس
-- معتمِدًا على RLS الجداول الأساسية إطلاقًا.
-- ---------------------------------------------------------------
create view public.team_roster
as
select
  tm.team_id,
  tm.user_id,
  tm.role,
  p.display_name,
  p.avatar_url
from public.team_members tm
join public.profiles p on p.id = tm.user_id
where exists (
  select 1 from public.team_members me
  where me.team_id = tm.team_id and me.user_id = auth.uid()
);

comment on view public.team_roster is
  'المسار الوحيد المسموح به لرؤية اسم/صورة زميل فريق — لا كشف مباشر لجدول profiles. التقييد صريح عبر auth.uid() وليس عبر RLS.';

grant select on public.team_roster to authenticated;

-- ---------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------
alter table public.teams enable row level security;
alter table public.team_members enable row level security;
alter table public.challenges enable row level security;
alter table public.challenge_progress enable row level security;

create policy "teams_select_member" on public.teams
  for select using (public.shares_team_with(created_by) or created_by = auth.uid());

create policy "teams_insert_self" on public.teams
  for insert with check (created_by = auth.uid());

create policy "teams_update_owner" on public.teams
  for update using (
    exists (
      select 1 from public.team_members
      where team_id = teams.id and user_id = auth.uid() and role = 'owner'
    )
  );

create policy "team_members_select_same_team" on public.team_members
  for select using (public.shares_team_with(user_id));

-- لا توجد سياسة insert لدور authenticated عمدًا: كل إدراج في
-- team_members يمر حصرًا عبر دوال SECURITY DEFINER موثوقة
-- (handle_new_team عند إنشاء الفريق، join_team_by_code عند الانضمام)
-- بدلاً من الاعتماد على إدراج مباشر من العميل.

create policy "challenges_select_team_member" on public.challenges
  for select using (public.shares_team_with(created_by) or created_by = auth.uid());

create policy "challenges_insert_team_owner" on public.challenges
  for insert with check (
    exists (
      select 1 from public.team_members
      where team_id = challenges.team_id and user_id = auth.uid() and role = 'owner'
    )
  );

create policy "challenge_progress_select_team_member" on public.challenge_progress
  for select using (
    exists (
      select 1 from public.challenges c
      where c.id = challenge_progress.challenge_id and public.shares_team_with(c.created_by)
    )
    or user_id = auth.uid()
  );

create policy "challenge_progress_upsert_own" on public.challenge_progress
  for insert with check (user_id = auth.uid());

create policy "challenge_progress_update_own" on public.challenge_progress
  for update using (user_id = auth.uid());

-- ============================================================
-- 20260831000005_accountability.sql
-- ============================================================
-- ============================================================
-- رفيق هِمّة — شريك التزام واحد اختياري + تفاعلات سريعة (بدون شات)
-- ============================================================

create type public.pair_status as enum ('pending', 'active', 'ended');
create type public.ping_kind as enum ('lets_go', 'almost_there', 'well_done', 'with_you');

create table public.accountability_pairs (
  id uuid primary key default gen_random_uuid(),
  requester_id uuid not null references public.profiles (id) on delete cascade,
  partner_id uuid not null references public.profiles (id) on delete cascade,
  status public.pair_status not null default 'pending',
  created_at timestamptz not null default now(),
  responded_at timestamptz,
  check (requester_id <> partner_id)
);

-- شريك نشط واحد فقط لكل مستخدم في نفس الوقت.
create unique index accountability_pairs_one_active_per_requester
  on public.accountability_pairs (requester_id) where status = 'active';
create unique index accountability_pairs_one_active_per_partner
  on public.accountability_pairs (partner_id) where status = 'active';

create table public.accountability_pings (
  id uuid primary key default gen_random_uuid(),
  pair_id uuid not null references public.accountability_pairs (id) on delete cascade,
  sender_id uuid not null references public.profiles (id),
  kind public.ping_kind not null,
  created_at timestamptz not null default now()
);

create index accountability_pings_pair_idx on public.accountability_pings (pair_id, created_at desc);

alter table public.accountability_pairs enable row level security;
alter table public.accountability_pings enable row level security;

create policy "pairs_select_participant" on public.accountability_pairs
  for select using (auth.uid() in (requester_id, partner_id));

create policy "pairs_insert_requester" on public.accountability_pairs
  for insert with check (auth.uid() = requester_id);

-- الطرف الآخر فقط يقبل/يرفض/ينهي الشراكة (لا يعدّل الطالب حالتها بنفسه).
create policy "pairs_update_partner_responds" on public.accountability_pairs
  for update using (auth.uid() = partner_id or auth.uid() = requester_id);

create policy "pings_select_participant" on public.accountability_pings
  for select using (
    exists (
      select 1 from public.accountability_pairs p
      where p.id = accountability_pings.pair_id
        and auth.uid() in (p.requester_id, p.partner_id)
        and p.status = 'active'
    )
  );

create policy "pings_insert_participant" on public.accountability_pings
  for insert with check (
    sender_id = auth.uid()
    and exists (
      select 1 from public.accountability_pairs p
      where p.id = accountability_pings.pair_id
        and auth.uid() in (p.requester_id, p.partner_id)
        and p.status = 'active'
    )
  );

-- ============================================================
-- 20260831000006_points_and_leaderboard.sql
-- ============================================================
-- ============================================================
-- النقاط، نبض الفريق، والترتيب — كلها views محسوبة من البيانات
-- الفعلية بدل جداول تُزامَن يدويًا (يمنع تعارض الحالة).
--
-- ملاحظة أمان: هذه الـ views (باستثناء user_points_totals الداخلية)
-- بدون security_invoker — تتجاوز RLS الجداول الأساسية عمدًا، وتفرض
-- تقييد الوصول صراحة عبر auth.uid() داخل كل view (راجع تعليق مشابه
-- في 20260831000004_teams_and_challenges.sql).
-- ============================================================

create table public.points_ledger (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  delta integer not null,
  reason text not null,
  created_at timestamptz not null default now()
);

create index points_ledger_user_idx on public.points_ledger (user_id, created_at desc);

alter table public.points_ledger enable row level security;

create policy "points_ledger_select_own" on public.points_ledger
  for select using (auth.uid() = user_id);

-- الإدراج في points_ledger يتم فقط عبر دوال SECURITY DEFINER موثوقة
-- (تُضاف عند بناء منطق كل ميزة تمنح نقاطًا) — لا insert مباشر للعميل،
-- لمنع أي مستخدم من منح نفسه نقاطًا.

-- view داخلية فقط (تجميع عبر كل المستخدمين) — لا تُمنح صلاحية وصول
-- مباشرة لها؛ تُستخدم حصرًا داخل team_leaderboard الذي يقيّد النتيجة
-- بأعضاء نفس الفريق عبر team_roster.
create view public.user_points_totals
as
select user_id, coalesce(sum(delta), 0) as total_points
from public.points_ledger
group by user_id;

revoke all on public.user_points_totals from public, anon, authenticated;

-- نبض الفريق: متوسط إنجاز اليوم لكل أعضاء الفريق في تاريخ معيّن،
-- مقيّد بفرق المستخدم الحالي فقط.
create view public.team_pulse_daily
as
select
  tm.team_id,
  dp.date,
  round(avg(dp.completion_percent), 2) as pulse_percent,
  count(dp.user_id) as contributing_members
from public.team_members tm
join public.daily_progress dp on dp.user_id = tm.user_id
where exists (
  select 1 from public.team_members me
  where me.team_id = tm.team_id and me.user_id = auth.uid()
)
group by tm.team_id, dp.date;

comment on view public.team_pulse_daily is
  'نبض الفريق = متوسط إنجاز اليوم لأعضائه، وليس مجموعًا مطلقًا — عادل بين الأهداف المختلفة.';

grant select on public.team_pulse_daily to authenticated;

-- ترتيب الفريق: نقاط + اسم لكل عضو (يرث تقييد team_roster تلقائيًا).
create view public.team_leaderboard
as
select
  r.team_id,
  r.user_id,
  r.display_name,
  r.avatar_url,
  coalesce(t.total_points, 0) as total_points
from public.team_roster r
left join public.user_points_totals t on t.user_id = r.user_id;

grant select on public.team_leaderboard to authenticated;

-- ============================================================
-- 20260831000007_notifications.sql
-- ============================================================
-- ============================================================
-- الإشعارات
-- ============================================================
-- الإدراج يتم فقط من الخادم (service role / Edge Functions / triggers)
-- — لا يوجد insert policy لدور authenticated عمدًا.

create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  type text not null,
  title text not null,
  body text,
  data jsonb not null default '{}'::jsonb,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create index notifications_user_idx on public.notifications (user_id, created_at desc);

alter table public.notifications enable row level security;

create policy "notifications_select_own" on public.notifications
  for select using (auth.uid() = user_id);

-- السماح فقط بتعليم الإشعار كمقروء (read_at) — أي تحديث آخر لا يزال
-- مسموحًا تقنيًا هنا (RLS لا يقيّد أعمدة)، لكن العميل الرسمي لا يستخدم
-- إلا هذا المسار؛ لا insert/delete من العميل نهائيًا.
create policy "notifications_mark_read_own" on public.notifications
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ============================================================
-- 20260831000008_subscriptions.sql
-- ============================================================
-- ============================================================
-- حالة الاشتراك (هِمّة+) — مصدر الحقيقة الوحيد لحالة Premium
-- ============================================================
-- أمان حرج: لا توجد أي سياسة insert/update لدور authenticated. حالة
-- الاشتراك تُكتب حصرًا من Edge Function موثوقة تستقبل RevenueCat
-- webhook وتستخدم service role key (يتجاوز RLS). لو سمحنا للعميل
-- بتعديل هذا الجدول لأمكن لأي مستخدم منح نفسه Premium مجانًا.

create type public.subscription_store as enum ('app_store', 'play_store');

create table public.subscriptions (
  user_id uuid primary key references public.profiles (id) on delete cascade,
  is_premium boolean not null default false,
  product_id text,
  store public.subscription_store,
  will_renew boolean not null default false,
  expires_at timestamptz,
  revenuecat_app_user_id text unique,
  last_synced_at timestamptz not null default now()
);

comment on table public.subscriptions is
  'مصدر الحقيقة لحالة هِمّة+. تُكتب فقط عبر Edge Function (service role) تستقبل RevenueCat webhooks.';

alter table public.subscriptions enable row level security;

create policy "subscriptions_select_own" on public.subscriptions
  for select using (auth.uid() = user_id);

-- إنشاء صف subscriptions افتراضي (غير مشترك) لكل مستخدم جديد.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', 'مستخدم هِمّة'));

  insert into public.user_goals (user_id) values (new.id);

  insert into public.subscriptions (user_id) values (new.id);

  return new;
end;
$$;

-- ============================================================
-- 20260831000009_realtime.sql
-- ============================================================
-- ============================================================
-- أساس Realtime — الجداول التي تحتاج تحديثًا فوريًا في الواجهة:
-- نبض الفريق (عبر daily_progress)، تقدم التحدي، تفاعلات رفيق هِمّة،
-- والإشعارات. RLS تبقى سارية على قنوات Realtime في Supabase تلقائيًا.
-- ============================================================

alter publication supabase_realtime add table public.daily_progress;
alter publication supabase_realtime add table public.challenge_progress;
alter publication supabase_realtime add table public.accountability_pings;
alter publication supabase_realtime add table public.notifications;
alter publication supabase_realtime add table public.team_members;

alter table public.daily_progress replica identity full;
alter table public.challenge_progress replica identity full;
alter table public.accountability_pings replica identity full;
alter table public.notifications replica identity full;

-- ============================================================
-- 20260831000010_onboarding_flag.sql
-- ============================================================
-- ============================================================
-- علم onboarding — يمنع الاعتماد على قيمة display_name الافتراضية
-- لمعرفة هل أنهى المستخدم شاشات الترحيب أم لا.
-- ============================================================

alter table public.profiles
  add column onboarding_completed_at timestamptz;

