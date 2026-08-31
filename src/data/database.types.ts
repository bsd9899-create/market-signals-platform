/**
 * أنواع TypeScript لقاعدة بيانات Supabase — مكتوبة يدويًا لتطابق
 * migrations في supabase/migrations/. عند ربط مشروع Supabase حقيقي،
 * يُفضَّل توليدها آليًا لاحقًا عبر:
 *   npx supabase gen types typescript --project-id <id> > src/data/database.types.ts
 * وإعادة مطابقتها مع هذا الملف.
 *
 * `Relationships: []` مطلوب في كل جدول/عرض من طرف @supabase/postgrest-js
 * (يُستخدم لاستنتاج أنواع الـ embeds مثل .select('*, teams(*)')) — لا
 * نستخدم أي علاقات مُضمَّنة حاليًا فتبقى فارغة في كل مكان.
 */

type NoRelationships = { Relationships: [] };

export type GoalType = 'lose_weight' | 'gain_muscle' | 'increase_activity' | 'general_health';
export type LogSource = 'manual' | 'healthkit';
export type PromiseType = 'workout' | 'steps' | 'nutrition' | 'water' | 'sleep';
export type TeamRole = 'owner' | 'member';
export type PairStatus = 'pending' | 'active' | 'ended';
export type PingKind = 'lets_go' | 'almost_there' | 'well_done' | 'with_you';
export type SubscriptionStore = 'app_store' | 'play_store';

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          display_name: string;
          avatar_url: string | null;
          goal_type: GoalType;
          onboarding_completed_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: Partial<Database['public']['Tables']['profiles']['Row']> & { id: string; display_name: string };
        Update: Partial<Database['public']['Tables']['profiles']['Row']>;
      } & NoRelationships;
      user_goals: {
        Row: {
          user_id: string;
          target_water_ml: number;
          target_steps: number;
          target_sleep_hours: number;
          target_workouts_per_week: number;
          target_weight_kg: number | null;
          updated_at: string;
        };
        Insert: Partial<Database['public']['Tables']['user_goals']['Row']> & { user_id: string };
        Update: Partial<Database['public']['Tables']['user_goals']['Row']>;
      } & NoRelationships;
      workouts: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          performed_at: string;
          duration_minutes: number;
          exercises: unknown;
          source: LogSource;
          created_at: string;
        };
        Insert: Partial<Database['public']['Tables']['workouts']['Row']> & {
          user_id: string;
          title: string;
          duration_minutes: number;
        };
        Update: Partial<Database['public']['Tables']['workouts']['Row']>;
      } & NoRelationships;
      nutrition_logs: {
        Row: {
          id: string;
          user_id: string;
          meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
          description: string;
          calories: number | null;
          logged_at: string;
          source: LogSource;
          created_at: string;
        };
        Insert: Partial<Database['public']['Tables']['nutrition_logs']['Row']> & {
          user_id: string;
          meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
          description: string;
        };
        Update: Partial<Database['public']['Tables']['nutrition_logs']['Row']>;
      } & NoRelationships;
      water_logs: {
        Row: {
          id: string;
          user_id: string;
          amount_ml: number;
          logged_at: string;
          created_at: string;
        };
        Insert: Partial<Database['public']['Tables']['water_logs']['Row']> & {
          user_id: string;
          amount_ml: number;
        };
        Update: Partial<Database['public']['Tables']['water_logs']['Row']>;
      } & NoRelationships;
      steps_logs: {
        Row: { user_id: string; date: string; steps: number; source: LogSource; updated_at: string };
        Insert: Partial<Database['public']['Tables']['steps_logs']['Row']> & {
          user_id: string;
          date: string;
          steps: number;
        };
        Update: Partial<Database['public']['Tables']['steps_logs']['Row']>;
      } & NoRelationships;
      sleep_logs: {
        Row: { user_id: string; date: string; hours: number; source: LogSource; updated_at: string };
        Insert: Partial<Database['public']['Tables']['sleep_logs']['Row']> & {
          user_id: string;
          date: string;
          hours: number;
        };
        Update: Partial<Database['public']['Tables']['sleep_logs']['Row']>;
      } & NoRelationships;
      weight_logs: {
        Row: {
          id: string;
          user_id: string;
          weight_kg: number;
          logged_at: string;
          source: LogSource;
          created_at: string;
        };
        Insert: Partial<Database['public']['Tables']['weight_logs']['Row']> & {
          user_id: string;
          weight_kg: number;
        };
        Update: Partial<Database['public']['Tables']['weight_logs']['Row']>;
      } & NoRelationships;
      daily_promises: {
        Row: {
          id: string;
          user_id: string;
          date: string;
          promise_type: PromiseType;
          fulfilled: boolean | null;
          created_at: string;
        };
        Insert: Partial<Database['public']['Tables']['daily_promises']['Row']> & {
          user_id: string;
          date: string;
          promise_type: PromiseType;
        };
        Update: Partial<Database['public']['Tables']['daily_promises']['Row']>;
      } & NoRelationships;
      daily_progress: {
        Row: {
          user_id: string;
          date: string;
          completion_percent: number;
          decision_text: string | null;
          recovery_mode: boolean;
          updated_at: string;
        };
        Insert: Partial<Database['public']['Tables']['daily_progress']['Row']> & { user_id: string; date: string };
        Update: Partial<Database['public']['Tables']['daily_progress']['Row']>;
      } & NoRelationships;
      teams: {
        Row: { id: string; name: string; invite_code: string; created_by: string; created_at: string };
        Insert: Partial<Database['public']['Tables']['teams']['Row']> & { name: string; created_by: string };
        Update: Partial<Database['public']['Tables']['teams']['Row']>;
      } & NoRelationships;
      team_members: {
        Row: { team_id: string; user_id: string; role: TeamRole; joined_at: string };
        Insert: Partial<Database['public']['Tables']['team_members']['Row']> & { team_id: string; user_id: string };
        Update: Partial<Database['public']['Tables']['team_members']['Row']>;
      } & NoRelationships;
      challenges: {
        Row: {
          id: string;
          team_id: string;
          title: string;
          description: string | null;
          start_date: string;
          end_date: string;
          created_by: string;
          created_at: string;
        };
        Insert: Partial<Database['public']['Tables']['challenges']['Row']> & {
          team_id: string;
          title: string;
          start_date: string;
          end_date: string;
          created_by: string;
        };
        Update: Partial<Database['public']['Tables']['challenges']['Row']>;
      } & NoRelationships;
      challenge_progress: {
        Row: { challenge_id: string; user_id: string; progress_percent: number; updated_at: string };
        Insert: Partial<Database['public']['Tables']['challenge_progress']['Row']> & {
          challenge_id: string;
          user_id: string;
        };
        Update: Partial<Database['public']['Tables']['challenge_progress']['Row']>;
      } & NoRelationships;
      accountability_pairs: {
        Row: {
          id: string;
          requester_id: string;
          partner_id: string;
          status: PairStatus;
          created_at: string;
          responded_at: string | null;
        };
        Insert: Partial<Database['public']['Tables']['accountability_pairs']['Row']> & {
          requester_id: string;
          partner_id: string;
        };
        Update: Partial<Database['public']['Tables']['accountability_pairs']['Row']>;
      } & NoRelationships;
      accountability_pings: {
        Row: { id: string; pair_id: string; sender_id: string; kind: PingKind; created_at: string };
        Insert: Partial<Database['public']['Tables']['accountability_pings']['Row']> & {
          pair_id: string;
          sender_id: string;
          kind: PingKind;
        };
        Update: Partial<Database['public']['Tables']['accountability_pings']['Row']>;
      } & NoRelationships;
      points_ledger: {
        Row: { id: string; user_id: string; delta: number; reason: string; created_at: string };
        Insert: Partial<Database['public']['Tables']['points_ledger']['Row']> & {
          user_id: string;
          delta: number;
          reason: string;
        };
        Update: Partial<Database['public']['Tables']['points_ledger']['Row']>;
      } & NoRelationships;
      notifications: {
        Row: {
          id: string;
          user_id: string;
          type: string;
          title: string;
          body: string | null;
          data: unknown;
          read_at: string | null;
          created_at: string;
        };
        Insert: Partial<Database['public']['Tables']['notifications']['Row']> & {
          user_id: string;
          type: string;
          title: string;
        };
        Update: Partial<Database['public']['Tables']['notifications']['Row']>;
      } & NoRelationships;
      subscriptions: {
        Row: {
          user_id: string;
          is_premium: boolean;
          product_id: string | null;
          store: SubscriptionStore | null;
          will_renew: boolean;
          expires_at: string | null;
          revenuecat_app_user_id: string | null;
          last_synced_at: string;
        };
        Insert: Partial<Database['public']['Tables']['subscriptions']['Row']> & { user_id: string };
        Update: Partial<Database['public']['Tables']['subscriptions']['Row']>;
      } & NoRelationships;
    };
    Views: {
      team_roster: {
        Row: {
          team_id: string;
          user_id: string;
          role: TeamRole;
          display_name: string;
          avatar_url: string | null;
        };
      } & NoRelationships;
      team_pulse_daily: {
        Row: { team_id: string; date: string; pulse_percent: number; contributing_members: number };
      } & NoRelationships;
      team_leaderboard: {
        Row: {
          team_id: string;
          user_id: string;
          display_name: string;
          avatar_url: string | null;
          total_points: number;
        };
      } & NoRelationships;
    };
    Functions: {
      join_team_by_code: {
        Args: { p_invite_code: string };
        Returns: string;
      };
      shares_team_with: {
        Args: { target_user: string };
        Returns: boolean;
      };
    };
    Enums: {
      goal_type: GoalType;
      log_source: LogSource;
      promise_type: PromiseType;
      team_role: TeamRole;
      pair_status: PairStatus;
      ping_kind: PingKind;
      subscription_store: SubscriptionStore;
    };
  };
}
