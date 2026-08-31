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
