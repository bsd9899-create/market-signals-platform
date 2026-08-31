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
