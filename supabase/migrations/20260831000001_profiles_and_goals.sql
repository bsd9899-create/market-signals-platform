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
