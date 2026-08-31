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
