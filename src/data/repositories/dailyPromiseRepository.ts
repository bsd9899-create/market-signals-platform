import { supabase } from '../supabase';
import { toDateKey } from '@/src/lib/date';
import type { Database } from '../database.types';

export type PromiseType = Database['public']['Enums']['promise_type'];
export type DailyPromise = Database['public']['Tables']['daily_promises']['Row'];

export const dailyPromiseRepository = {
  async getToday(userId: string): Promise<DailyPromise | null> {
    const { data, error } = await supabase
      .from('daily_promises')
      .select('*')
      .eq('user_id', userId)
      .eq('date', toDateKey())
      .maybeSingle();
    if (error) throw error;
    return data;
  },

  async setToday(userId: string, promiseType: PromiseType) {
    const { error } = await supabase
      .from('daily_promises')
      .upsert(
        { user_id: userId, date: toDateKey(), promise_type: promiseType, fulfilled: null },
        { onConflict: 'user_id,date' }
      );
    if (error) throw error;
  },

  async markFulfilled(userId: string, fulfilled: boolean) {
    const { error } = await supabase
      .from('daily_promises')
      .update({ fulfilled })
      .eq('user_id', userId)
      .eq('date', toDateKey());
    if (error) throw error;
  },
};
