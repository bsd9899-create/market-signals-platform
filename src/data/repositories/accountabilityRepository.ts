import { supabase } from '../supabase';
import type { Database } from '../database.types';

export type AccountabilityPair = Database['public']['Tables']['accountability_pairs']['Row'];
export type AccountabilityPing = Database['public']['Tables']['accountability_pings']['Row'];
export type PingKind = Database['public']['Enums']['ping_kind'];

export const accountabilityRepository = {
  /** أي شراكة تخصّني (نشطة أو قيد الانتظار) — واحدة كحد أقصى بحكم فهرس قاعدة البيانات. */
  async getMyPair(userId: string): Promise<AccountabilityPair | null> {
    const { data, error } = await supabase
      .from('accountability_pairs')
      .select('*')
      .or(`requester_id.eq.${userId},partner_id.eq.${userId}`)
      .in('status', ['pending', 'active'])
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();
    if (error) throw error;
    return data;
  },

  async sendRequest(requesterId: string, partnerId: string) {
    const { error } = await supabase
      .from('accountability_pairs')
      .insert({ requester_id: requesterId, partner_id: partnerId });
    if (error) throw error;
  },

  async respond(pairId: string, accept: boolean) {
    const { error } = await supabase
      .from('accountability_pairs')
      .update({ status: accept ? 'active' : 'ended', responded_at: new Date().toISOString() })
      .eq('id', pairId);
    if (error) throw error;
  },

  async endPair(pairId: string) {
    const { error } = await supabase
      .from('accountability_pairs')
      .update({ status: 'ended', responded_at: new Date().toISOString() })
      .eq('id', pairId);
    if (error) throw error;
  },

  async getPings(pairId: string, limit = 20): Promise<AccountabilityPing[]> {
    const { data, error } = await supabase
      .from('accountability_pings')
      .select('*')
      .eq('pair_id', pairId)
      .order('created_at', { ascending: false })
      .limit(limit);
    if (error) throw error;
    return data ?? [];
  },

  async sendPing(pairId: string, senderId: string, kind: PingKind) {
    const { error } = await supabase.from('accountability_pings').insert({ pair_id: pairId, sender_id: senderId, kind });
    if (error) throw error;
  },
};
