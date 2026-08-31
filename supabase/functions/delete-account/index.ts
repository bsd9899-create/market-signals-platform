// Supabase Edge Function — حذف حساب المستخدم نفسه (مطلوب من Apple لأي
// تطبيق يسمح بإنشاء حساب: يجب توفير حذف من داخل التطبيق).
//
// أمان: تُستدعى بتوكن المستخدم نفسه (Authorization header من العميل)
// لتحديد هويته أولًا، ثم تستخدم service role key فقط لتنفيذ حذف
// auth.users الذي يتطلّب صلاحية admin — لا يمكن لمستخدم حذف غيره لأن
// الهوية تُشتق من توكنه هو حصرًا، وليست معطى يرسله العميل.
//
// حذف auth.users يُفعِّل ON DELETE CASCADE على profiles، وهذا بدوره
// يحذف تلقائيًا كل شيء مرتبط (user_goals, workouts, water_logs,
// team_members, notifications, subscriptions, ...) — راجع
// supabase/migrations لكل foreign key.
//
// النشر لاحقًا:
//   supabase functions deploy delete-account

import { createClient } from 'npm:@supabase/supabase-js@2';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

Deno.serve(async (req) => {
  const authHeader = req.headers.get('Authorization');
  if (!authHeader) {
    return new Response('Missing Authorization header', { status: 401 });
  }

  // عميل بصلاحية المستخدم نفسه (anon key + توكنه) — فقط للتحقق من هويته.
  const userClient = createClient(SUPABASE_URL, Deno.env.get('SUPABASE_ANON_KEY')!, {
    global: { headers: { Authorization: authHeader } },
  });

  const {
    data: { user },
    error: userError,
  } = await userClient.auth.getUser();

  if (userError || !user) {
    return new Response('Unauthorized', { status: 401 });
  }

  const adminClient = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);
  const { error: deleteError } = await adminClient.auth.admin.deleteUser(user.id);

  if (deleteError) {
    console.error('delete-account failed', deleteError);
    return new Response('Internal error', { status: 500 });
  }

  return new Response('OK', { status: 200 });
});
