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

  /** متوسط إنجاز اليوم بين تاريخين (لحساب تقدم التحدي) — لا يتجاوز اليوم الحالي. */
  async getAverageCompletionInRange(userId: string, startDate: string, endDate: string) {
    const cappedEnd = endDate > toDateKey() ? toDateKey() : endDate;

    const { data, error } = await supabase
      .from('daily_progress')
      .select('completion_percent')
      .eq('user_id', userId)
      .gte('date', startDate)
      .lte('date', cappedEnd);
    if (error) throw error;

    const rows = data ?? [];
    if (rows.length === 0) return 0;
    return Math.round(rows.reduce((sum, r) => sum + r.completion_percent, 0) / rows.length);
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

  /**
   * متوسطات الأسبوع لكل مؤشر — مقسومة على عدد أيام الفترة كاملة (وليس
   * فقط الأيام المسجَّلة)، حتى تعكس الصورة الحقيقية للتقييم الأسبوعي:
   * يوم بلا سجل يُحتسب صفرًا، لا يُستبعد.
   */
  async getWeeklyRawAverages(userId: string, days: number) {
    const since = new Date();
    since.setDate(since.getDate() - (days - 1));
    const sinceISO = since.toISOString();
    const sinceKey = toDateKey(since);

    const [water, workouts, steps, sleep] = await Promise.all([
      supabase.from('water_logs').select('amount_ml').eq('user_id', userId).gte('logged_at', sinceISO),
      supabase.from('workouts').select('duration_minutes').eq('user_id', userId).gte('performed_at', sinceISO),
      supabase.from('steps_logs').select('steps').eq('user_id', userId).gte('date', sinceKey),
      supabase.from('sleep_logs').select('hours').eq('user_id', userId).gte('date', sinceKey),
    ]);

    if (water.error) throw water.error;
    if (workouts.error) throw workouts.error;
    if (steps.error) throw steps.error;
    if (sleep.error) throw sleep.error;

    const sum = <T,>(rows: T[] | null, pick: (r: T) => number) => (rows ?? []).reduce((s, r) => s + pick(r), 0);

    return {
      avgWaterMl: sum(water.data, (r) => r.amount_ml) / days,
      avgWorkoutMinutes: sum(workouts.data, (r) => r.duration_minutes) / days,
      avgSteps: sum(steps.data, (r) => r.steps) / days,
      avgSleepHours: sum(sleep.data, (r) => r.hours) / days,
    };
  },
};
