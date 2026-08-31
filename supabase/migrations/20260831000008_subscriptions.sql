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
