import { supabase } from '../supabase';
import type { Database } from '../database.types';

export type UserGoals = Database['public']['Tables']['user_goals']['Row'];

export const goalsRepository = {
  async getCurrent(userId: string): Promise<UserGoals> {
    const { data, error } = await supabase.from('user_goals').select('*').eq('user_id', userId).single();
    if (error) throw error;
    return data;
  },
};
