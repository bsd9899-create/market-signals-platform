import { supabase } from '../supabase';
import { startOfTodayISO, toDateKey } from '@/src/lib/date';

/**
 * قراءات "اليوم" المجمَّعة من جداول السجلات الفعلية — تغذّي شاشة اليوم
 * ومحرّك قرار اليوم (src/domain/decisionEngine.ts). عمليات الإضافة
 * (Quick Add) تُبنى في المرحلة 5 في نفس هذا الملف.
 */
export const dailyLogsRepository = {
  async getTodayWaterMl(userId: string): Promise<number> {
    const { data, error } = await supabase
      .from('water_logs')
      .select('amount_ml')
      .eq('user_id', userId)
      .gte('logged_at', startOfTodayISO());
    if (error) throw error;
    return (data ?? []).reduce((sum, row) => sum + row.amount_ml, 0);
  },

  async getTodaySteps(userId: string): Promise<number> {
    const { data, error } = await supabase
      .from('steps_logs')
      .select('steps')
      .eq('user_id', userId)
      .eq('date', toDateKey())
      .maybeSingle();
    if (error) throw error;
    return data?.steps ?? 0;
  },

  async getTodayWorkoutMinutes(userId: string): Promise<number> {
    const { data, error } = await supabase
      .from('workouts')
      .select('duration_minutes')
      .eq('user_id', userId)
      .gte('performed_at', startOfTodayISO());
    if (error) throw error;
    return (data ?? []).reduce((sum, row) => sum + row.duration_minutes, 0);
  },

  async getTodayMealsCount(userId: string): Promise<number> {
    const { count, error } = await supabase
      .from('nutrition_logs')
      .select('id', { count: 'exact', head: true })
      .eq('user_id', userId)
      .gte('logged_at', startOfTodayISO());
    if (error) throw error;
    return count ?? 0;
  },

  async getTodaySleepHours(userId: string): Promise<number | null> {
    const { data, error } = await supabase
      .from('sleep_logs')
      .select('hours')
      .eq('user_id', userId)
      .eq('date', toDateKey())
      .maybeSingle();
    if (error) throw error;
    return data?.hours ?? null;
  },

  /** آخر `days` يومًا من daily_progress (الأقدم أولًا) — لاكتشاف الانقطاع لوضع الإنقاذ. */
  async getRecentProgress(userId: string, days: number) {
    const since = new Date();
    since.setDate(since.getDate() - days);

    const { data, error } = await supabase
      .from('daily_progress')
      .select('date, completion_percent')
      .eq('user_id', userId)
      .gte('date', toDateKey(since))
      .order('date', { ascending: true });
    if (error) throw error;
    return data ?? [];
  },
};
