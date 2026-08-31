import { useCallback, useEffect, useState } from 'react';
import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import { dailyProgressRepository } from '@/src/data/repositories/dailyProgressRepository';
import { goalsRepository, type UserGoals } from '@/src/data/repositories/goalsRepository';
import { computeTodayDecision, type TodayDecision } from '@/src/domain/decisionEngine';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

/** "يوم تمرين كامل" مرجعي لحساب نسبة إنجاز التمرين — لا يوجد هدف تمرين يومي بالدقائق في user_goals (الهدف أسبوعي بعدد الأيام). */
const REFERENCE_WORKOUT_MINUTES = 30;
const RECOVERY_LOOKBACK_DAYS = 7;

export type TodaySummary = TodayDecision & {
  waterMl: number;
  waterTargetMl: number;
  steps: number;
  stepsTarget: number;
  workoutMinutes: number;
  mealsLogged: number;
  goals: UserGoals;
};

export function useTodayData(userId: string | undefined) {
  const [summary, setSummary] = useState<TodaySummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setIsLoading(true);
    setError(null);
    try {
      const [goals, waterMl, steps, workoutMinutes, mealsLogged, sleepHours, recentProgress] = await Promise.all([
        goalsRepository.getCurrent(userId),
        dailyLogsRepository.getTodayWaterMl(userId),
        dailyLogsRepository.getTodaySteps(userId),
        dailyLogsRepository.getTodayWorkoutMinutes(userId),
        dailyLogsRepository.getTodayMealsCount(userId),
        dailyLogsRepository.getTodaySleepHours(userId),
        dailyLogsRepository.getRecentProgress(userId, RECOVERY_LOOKBACK_DAYS),
      ]);

      const decision = computeTodayDecision({
        waterRatio: waterMl / goals.target_water_ml,
        stepsRatio: steps / goals.target_steps,
        workoutRatio: workoutMinutes / REFERENCE_WORKOUT_MINUTES,
        sleepRatio: sleepHours !== null ? sleepHours / goals.target_sleep_hours : null,
        recentCompletionPercents: recentProgress.map((p) => p.completion_percent),
      });

      await dailyProgressRepository.upsertToday(userId, {
        completion_percent: decision.completionPercent,
        decision_text: decision.decisionText,
        recovery_mode: decision.recoveryMode,
      });

      setSummary({
        ...decision,
        waterMl,
        waterTargetMl: goals.target_water_ml,
        steps,
        stepsTarget: goals.target_steps,
        workoutMinutes,
        mealsLogged,
        goals,
      });
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّر تحميل بيانات اليوم'));
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    // جلب أولي عند التركيب (يستدعي setIsLoading داخل load) — نمط قياسي
    // ومختبَر في هذا المشروع، وليس اشتقاق حالة من props.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  return { summary, isLoading, error, refetch: load };
}
