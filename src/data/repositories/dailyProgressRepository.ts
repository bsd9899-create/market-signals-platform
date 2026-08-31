import { supabase } from '../supabase';
import { toDateKey } from '@/src/lib/date';

export const dailyProgressRepository = {
  /**
   * يحفظ نتيجة محرّك القرار لهذا اليوم — يُبقي daily_progress مصدر
   * حقيقة تاريخيًا (يُستخدم لاحقًا في نبض الفريق والتقييم الأسبوعي)
   * بدل إعادة حسابه من الصفر في كل مكان يحتاجه.
   */
  async upsertToday(
    userId: string,
    patch: { completion_percent: number; decision_text: string; recovery_mode: boolean }
  ) {
    const { error } = await supabase.from('daily_progress').upsert(
      {
        user_id: userId,
        date: toDateKey(),
        ...patch,
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'user_id,date' }
    );
    if (error) throw error;
  },
};
