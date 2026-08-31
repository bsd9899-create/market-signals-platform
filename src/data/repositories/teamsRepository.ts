import { supabase } from '../supabase';
import { toDateKey } from '@/src/lib/date';
import type { Database } from '../database.types';

export type Team = Database['public']['Tables']['teams']['Row'];
export type TeamRosterRow = Database['public']['Views']['team_roster']['Row'];
export type TeamLeaderboardRow = Database['public']['Views']['team_leaderboard']['Row'];
export type Challenge = Database['public']['Tables']['challenges']['Row'];
export type ChallengeProgressRow = Database['public']['Tables']['challenge_progress']['Row'];

export const teamsRepository = {
  /** الفريق الأول للمستخدم — نسخة V1 تدعم فريقًا واحدًا لكل شخص فقط. */
  async getMyTeam(userId: string): Promise<Team | null> {
    const { data: membership, error: membershipError } = await supabase
      .from('team_members')
      .select('team_id')
      .eq('user_id', userId)
      .limit(1)
      .maybeSingle();
    if (membershipError) throw membershipError;
    if (!membership) return null;

    const { data: team, error: teamError } = await supabase
      .from('teams')
      .select('*')
      .eq('id', membership.team_id)
      .single();
    if (teamError) throw teamError;
    return team;
  },

  async createTeam(name: string, userId: string): Promise<Team> {
    const { data, error } = await supabase.from('teams').insert({ name, created_by: userId }).select().single();
    if (error) throw error;
    return data;
  },

  async joinByCode(inviteCode: string): Promise<string> {
    const { data, error } = await supabase.rpc('join_team_by_code', { p_invite_code: inviteCode });
    if (error) throw error;
    return data;
  },

  async getRoster(teamId: string): Promise<TeamRosterRow[]> {
    const { data, error } = await supabase.from('team_roster').select('*').eq('team_id', teamId);
    if (error) throw error;
    return data ?? [];
  },

  async getLeaderboard(teamId: string): Promise<TeamLeaderboardRow[]> {
    const { data, error } = await supabase
      .from('team_leaderboard')
      .select('*')
      .eq('team_id', teamId)
      .order('total_points', { ascending: false });
    if (error) throw error;
    return data ?? [];
  },

  async getPulseToday(teamId: string): Promise<number | null> {
    const { data, error } = await supabase
      .from('team_pulse_daily')
      .select('pulse_percent')
      .eq('team_id', teamId)
      .eq('date', toDateKey())
      .maybeSingle();
    if (error) throw error;
    return data?.pulse_percent ?? null;
  },

  async getChallenges(teamId: string): Promise<Challenge[]> {
    const { data, error } = await supabase
      .from('challenges')
      .select('*')
      .eq('team_id', teamId)
      .order('start_date', { ascending: false });
    if (error) throw error;
    return data ?? [];
  },

  async createChallenge(input: {
    teamId: string;
    title: string;
    startDate: string;
    endDate: string;
    createdBy: string;
  }): Promise<Challenge> {
    const { data, error } = await supabase
      .from('challenges')
      .insert({
        team_id: input.teamId,
        title: input.title,
        start_date: input.startDate,
        end_date: input.endDate,
        created_by: input.createdBy,
      })
      .select()
      .single();
    if (error) throw error;
    return data;
  },

  async getMyChallengeProgress(challengeId: string, userId: string): Promise<number> {
    const { data, error } = await supabase
      .from('challenge_progress')
      .select('progress_percent')
      .eq('challenge_id', challengeId)
      .eq('user_id', userId)
      .maybeSingle();
    if (error) throw error;
    return data?.progress_percent ?? 0;
  },

  async upsertMyChallengeProgress(challengeId: string, userId: string, progressPercent: number) {
    const { error } = await supabase
      .from('challenge_progress')
      .upsert(
        { challenge_id: challengeId, user_id: userId, progress_percent: progressPercent },
        { onConflict: 'challenge_id,user_id' }
      );
    if (error) throw error;
  },
};
