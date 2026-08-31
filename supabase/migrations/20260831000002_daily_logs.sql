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
