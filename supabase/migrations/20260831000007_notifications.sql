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
