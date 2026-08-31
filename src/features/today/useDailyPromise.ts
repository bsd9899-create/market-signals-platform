import { useCallback, useEffect, useState } from 'react';
import { dailyPromiseRepository, type DailyPromise, type PromiseType } from '@/src/data/repositories/dailyPromiseRepository';

export const PROMISE_LABELS: Record<PromiseType, string> = {
  workout: 'أتمرن اليوم',
  steps: 'أكمل خطواتي',
  nutrition: 'ألتزم بأكلي',
  water: 'أكمل الماء',
  sleep: 'أنام بشكل أفضل',
};

export function useDailyPromise(userId: string | undefined) {
  const [promise, setPromise] = useState<DailyPromise | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      setPromise(await dailyPromiseRepository.getToday(userId));
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  async function choose(promiseType: PromiseType) {
    if (!userId) return;
    await dailyPromiseRepository.setToday(userId, promiseType);
    await load();
  }

  async function markFulfilled(fulfilled: boolean) {
    if (!userId) return;
    await dailyPromiseRepository.markFulfilled(userId, fulfilled);
    await load();
  }

  return { promise, isLoading, choose, markFulfilled, refetch: load };
}
