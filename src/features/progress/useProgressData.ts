import { useCallback, useEffect, useState } from 'react';
import { progressRepository } from '@/src/data/repositories/progressRepository';

const HISTORY_DAYS = 7;

export type ProgressSummary = {
  history: { date: string; completion_percent: number }[];
  weightNowKg: number | null;
  weightDeltaKg: number | null;
  workoutsThisWeek: number;
  averageSteps: number;
};

export function useProgressData(userId: string | undefined) {
  const [summary, setSummary] = useState<ProgressSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setIsLoading(true);
    setError(null);
    try {
      const [history, weightTrend, workoutsThisWeek, averageSteps] = await Promise.all([
        progressRepository.getCompletionHistory(userId, HISTORY_DAYS),
        progressRepository.getWeightTrend(userId, 30),
        progressRepository.getWorkoutCount(userId, HISTORY_DAYS),
        progressRepository.getAverageSteps(userId, HISTORY_DAYS),
      ]);

      const weightDeltaKg =
        weightTrend.latestKg !== null && weightTrend.earliestKg !== null
          ? Math.round((weightTrend.latestKg - weightTrend.earliestKg) * 10) / 10
          : null;

      setSummary({
        history,
        weightNowKg: weightTrend.latestKg,
        weightDeltaKg,
        workoutsThisWeek,
        averageSteps,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'تعذّر تحميل التقدم');
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  return { summary, isLoading, error, refetch: load };
}
