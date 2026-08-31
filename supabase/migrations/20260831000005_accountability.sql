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
