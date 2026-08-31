// Supabase Edge Function — يستقبل RevenueCat Webhook ويحدّث حالة
// الاشتراك في جدول subscriptions باستخدام service role key (يتجاوز
// RLS عمدًا — هذا هو المسار الوحيد الموثوق لتعديل هذا الجدول، راجع
// supabase/migrations/20260831000008_subscriptions.sql).
//
// النشر لاحقًا (يحتاج مشروع RevenueCat فعلي):
//   supabase functions deploy revenuecat-webhook
//   supabase secrets set REVENUECAT_WEBHOOK_AUTH_HEADER=<قيمة سرية تُضبط أيضًا في RevenueCat>
// ثم في RevenueCat Dashboard → Integrations → Webhooks: أضف رابط الدالة
// وضع نفس القيمة في Authorization header.

import { createClient } from 'npm:@supabase/supabase-js@2';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const WEBHOOK_AUTH_HEADER = Deno.env.get('REVENUECAT_WEBHOOK_AUTH_HEADER');

type RevenueCatEvent = {
  type: string;
  app_user_id: string;
  product_id?: string;
  store?: 'APP_STORE' | 'PLAY_STORE' | string;
  expiration_at_ms?: number | null;
};

/** أحداث RevenueCat التي تعني "أصبح/بقي مشتركًا فعليًا". */
const PREMIUM_ACTIVE_EVENTS = new Set(['INITIAL_PURCHASE', 'RENEWAL', 'PRODUCT_CHANGE', 'UNCANCELLATION']);
/** CANCELLATION فقط تعني إيقاف التجديد التلقائي وليس انتهاء الاشتراك فورًا. */
const PREMIUM_INACTIVE_EVENTS = new Set(['EXPIRATION', 'BILLING_ISSUE']);

Deno.serve(async (req) => {
  if (WEBHOOK_AUTH_HEADER && req.headers.get('Authorization') !== WEBHOOK_AUTH_HEADER) {
    return new Response('Unauthorized', { status: 401 });
  }

  const body = await req.json();
  const event: RevenueCatEvent = body.event;

  if (!event?.app_user_id) {
    return new Response('Missing app_user_id', { status: 400 });
  }

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  const patch: Record<string, unknown> = {
    revenuecat_app_user_id: event.app_user_id,
    product_id: event.product_id ?? null,
    store: event.store === 'PLAY_STORE' ? 'play_store' : 'app_store',
    expires_at: event.expiration_at_ms ? new Date(event.expiration_at_ms).toISOString() : null,
    will_renew: event.type === 'RENEWAL' || event.type === 'INITIAL_PURCHASE',
    last_synced_at: new Date().toISOString(),
  };

  if (PREMIUM_ACTIVE_EVENTS.has(event.type)) {
    patch.is_premium = true;
  } else if (PREMIUM_INACTIVE_EVENTS.has(event.type)) {
    patch.is_premium = false;
    patch.will_renew = false;
  }
  // أنواع أخرى (مثل CANCELLATION وTRANSFER) تُحدَّث بالحقول أعلاه فقط
  // بدون تغيير is_premium — الإلغاء لا يعني انتهاء الاشتراك فورًا.

  // app_user_id في RevenueCat = auth.users.id (نمرّره كـ appUserID عند
  // initPurchases في src/subscriptions/revenuecat.ts) — لذلك user_id
  // هو نفسه event.app_user_id مباشرة.
  const { error } = await supabase
    .from('subscriptions')
    .update(patch)
    .eq('user_id', event.app_user_id);

  if (error) {
    console.error('revenuecat-webhook update failed', error);
    return new Response('Internal error', { status: 500 });
  }

  return new Response('OK', { status: 200 });
});
