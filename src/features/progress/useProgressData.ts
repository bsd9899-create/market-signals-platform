import { useCallback, useEffect, useState } from 'react';
import { progressRepository } from '@/src/data/repositories/progressRepository';
import { goalsRepository } from '@/src/data/repositories/goalsRepository';
import { computeWeeklyReview, type WeeklyReview } from '@/src/domain/weeklyReview';

const HISTORY_DAYS = 7;

export type ProgressSummary = {
  history: { date: string; completion_percent: number }[];
  weightNowKg: number | null;
  weightDeltaKg: number | null;
  workoutsThisWeek: number;
  averageSteps: number;
  weeklyReview: WeeklyReview;
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
      const [history, weightTrend, workoutsThisWeek, averageSteps, weeklyRaw, goals] = await Promise.all([
        progressRepository.getCompletionHistory(userId, HISTORY_DAYS),
        progressRepository.getWeightTrend(userId, 30),
        progressRepository.getWorkoutCount(userId, HISTORY_DAYS),
        progressRepository.getAverageSteps(userId, HISTORY_DAYS),
        progressRepository.getWeeklyRawAverages(userId, HISTORY_DAYS),
        goalsRepository.getCurrent(userId),
      ]);

      const weightDeltaKg =
        weightTrend.latestKg !== null && weightTrend.earliestKg !== null
          ? Math.round((weightTrend.latestKg - weightTrend.earliestKg) * 10) / 10
          : null;

      const weeklyReview = computeWeeklyReview(weeklyRaw, {
        targetWaterMl: goals.target_water_ml,
        targetSteps: goals.target_steps,
        targetSleepHours: goals.target_sleep_hours,
      });

      setSummary({
        history,
        weightNowKg: weightTrend.latestKg,
        weightDeltaKg,
        workoutsThisWeek,
        averageSteps,
        weeklyReview,
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
