import { supabase } from '../supabase';
import type { Database } from '../database.types';

export type SubscriptionRow = Database['public']['Tables']['subscriptions']['Row'];

/**
 * قراءة فقط — عمدًا لا توجد دوال update/insert هنا. الكتابة الوحيدة
 * المسموحة على هذا الجدول تمر عبر Edge Function بصلاحية service role
 * تستقبل RevenueCat webhook (راجع supabase/functions/revenuecat-webhook
 * وRLS policies في 20260831000008_subscriptions.sql).
 */
export const subscriptionsRepository = {
  async getCurrent(userId: string): Promise<SubscriptionRow | null> {
    const { data, error } = await supabase.from('subscriptions').select('*').eq('user_id', userId).maybeSingle();
    if (error) throw error;
    return data;
  },
};
