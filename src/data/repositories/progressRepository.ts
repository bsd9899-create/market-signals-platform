import { supabase } from '../supabase';
import { toDateKey } from '@/src/lib/date';

export const progressRepository = {
  /** آخر `days` يومًا من إنجاز اليوم (الأقدم أولًا) — لرسم شريط الأسبوع. */
  async getCompletionHistory(userId: string, days: number) {
    const since = new Date();
    since.setDate(since.getDate() - (days - 1));

    const { data, error } = await supabase
      .from('daily_progress')
      .select('date, completion_percent')
      .eq('user_id', userId)
      .gte('date', toDateKey(since))
      .order('date', { ascending: true });
    if (error) throw error;
    return data ?? [];
  },

  /** أحدث وزن مسجَّل، وأقدم وزن خلال `days` يومًا (لحساب فرق الاتجاه). */
  async getWeightTrend(userId: string, days: number) {
    const since = new Date();
    since.setDate(since.getDate() - days);

    const { data, error } = await supabase
      .from('weight_logs')
      .select('weight_kg, logged_at')
      .eq('user_id', userId)
      .gte('logged_at', since.toISOString())
      .order('logged_at', { ascending: true });
    if (error) throw error;

    const rows = data ?? [];
    return {
      latestKg: rows.at(-1)?.weight_kg ?? null,
      earliestKg: rows.at(0)?.weight_kg ?? null,
    };
  },

  async getWorkoutCount(userId: string, days: number) {
    const since = new Date();
    since.setDate(since.getDate() - days);

    const { count, error } = await supabase
      .from('workouts')
      .select('id', { count: 'exact', head: true })
      .eq('user_id', userId)
      .gte('performed_at', since.toISOString());
    if (error) throw error;
    return count ?? 0;
  },

  async getAverageSteps(userId: string, days: number) {
    const since = new Date();
    since.setDate(since.getDate() - (days - 1));

    const { data, error } = await supabase
      .from('steps_logs')
      .select('steps')
      .eq('user_id', userId)
      .gte('date', toDateKey(since));
    if (error) throw error;

    const rows = data ?? [];
    if (rows.length === 0) return 0;
    return Math.round(rows.reduce((sum, r) => sum + r.steps, 0) / rows.length);
  },
};
