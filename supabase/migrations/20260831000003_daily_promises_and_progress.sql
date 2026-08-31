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
