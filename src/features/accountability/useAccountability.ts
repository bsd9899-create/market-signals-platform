import { useCallback, useEffect, useState } from 'react';
import {
  accountabilityRepository,
  type AccountabilityPair,
  type AccountabilityPing,
  type PingKind,
} from '@/src/data/repositories/accountabilityRepository';

export function useAccountability(userId: string | undefined) {
  const [pair, setPair] = useState<AccountabilityPair | null>(null);
  const [pings, setPings] = useState<AccountabilityPing[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      const currentPair = await accountabilityRepository.getMyPair(userId);
      setPair(currentPair);
      setPings(currentPair && currentPair.status === 'active' ? await accountabilityRepository.getPings(currentPair.id) : []);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  async function sendRequest(partnerId: string) {
    if (!userId) return;
    await accountabilityRepository.sendRequest(userId, partnerId);
    await load();
  }

  async function respond(accept: boolean) {
    if (!pair) return;
    await accountabilityRepository.respond(pair.id, accept);
    await load();
  }

  async function endPair() {
    if (!pair) return;
    await accountabilityRepository.endPair(pair.id);
    await load();
  }

  async function sendPing(kind: PingKind) {
    if (!pair || !userId) return;
    await accountabilityRepository.sendPing(pair.id, userId, kind);
    await load();
  }

  const otherUserId = pair && userId ? (pair.requester_id === userId ? pair.partner_id : pair.requester_id) : null;
  const isIncomingRequest = pair?.status === 'pending' && pair.partner_id === userId;
  const isOutgoingRequest = pair?.status === 'pending' && pair.requester_id === userId;

  return {
    pair,
    pings,
    otherUserId,
    isIncomingRequest,
    isOutgoingRequest,
    isLoading,
    sendRequest,
    respond,
    endPair,
    sendPing,
    refetch: load,
  };
}
