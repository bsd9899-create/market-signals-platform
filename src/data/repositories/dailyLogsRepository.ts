import { supabase } from '../supabase';
import { startOfTodayISO, toDateKey } from '@/src/lib/date';

/**
 * قراءات وإضافات "اليوم" من جداول السجلات الفعلية — تغذّي شاشة اليوم
 * ومحرّك قرار اليوم (src/domain/decisionEngine.ts)، وتُستخدم من شاشات
 * الإضافة السريعة (app/log/*).
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

  // ---- Quick Add (المرحلة 5) ----

  async addWater(userId: string, amountMl: number) {
    const { error } = await supabase.from('water_logs').insert({ user_id: userId, amount_ml: amountMl });
    if (error) throw error;
  },

  async addWeight(userId: string, weightKg: number) {
    const { error } = await supabase.from('weight_logs').insert({ user_id: userId, weight_kg: weightKg });
    if (error) throw error;
  },

  /** إجمالي اليوم (استبدال وليس إضافة) — نفس مبدأ steps_logs (صف واحد لكل يوم). */
  async setStepsToday(userId: string, steps: number) {
    const { error } = await supabase
      .from('steps_logs')
      .upsert({ user_id: userId, date: toDateKey(), steps }, { onConflict: 'user_id,date' });
    if (error) throw error;
  },

  async setSleepToday(userId: string, hours: number) {
    const { error } = await supabase
      .from('sleep_logs')
      .upsert({ user_id: userId, date: toDateKey(), hours }, { onConflict: 'user_id,date' });
    if (error) throw error;
  },

  async addNutritionLog(
    userId: string,
    meal: { mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack'; description: string; calories?: number }
  ) {
    const { error } = await supabase.from('nutrition_logs').insert({
      user_id: userId,
      meal_type: meal.mealType,
      description: meal.description,
      calories: meal.calories,
    });
    if (error) throw error;
  },

  async addWorkout(userId: string, workout: { title: string; durationMinutes: number }) {
    const { error } = await supabase.from('workouts').insert({
      user_id: userId,
      title: workout.title,
      duration_minutes: workout.durationMinutes,
    });
    if (error) throw error;
  },
};
