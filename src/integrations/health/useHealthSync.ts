import { useCallback, useEffect, useState } from 'react';
import { Platform } from 'react-native';
import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import {
  getActiveEnergyToday,
  getLatestWeightKg,
  getSleepHoursLastNight,
  getStepsToday,
  getWorkoutMinutesToday,
  isHealthKitAvailable,
  requestHealthPermissions,
} from './healthkit';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

/**
 * مزامنة يدوية (يبدأها المستخدم بنفسه، وليست تلقائية) — حتى نتحقق من
 * سلوك HealthKit على جهاز حقيقي قبل الاعتماد عليها كمصدر صامت يكتب
 * فوق إدخالات المستخدم اليدوية. راجع التحذير في healthkit.ts.
 */
export function useHealthSync(userId: string | undefined) {
  const [isAvailable, setIsAvailable] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastActiveEnergyKcal, setLastActiveEnergyKcal] = useState<number | null>(null);

  useEffect(() => {
    if (Platform.OS !== 'ios') return;
    isHealthKitAvailable().then(setIsAvailable);
  }, []);

  const syncToday = useCallback(async () => {
    if (!userId || !isAvailable) return;
    setError(null);
    setIsSyncing(true);
    try {
      const granted = await requestHealthPermissions();
      if (!granted) {
        setError('لم يُسمح بالوصول لبيانات Apple Health');
        return;
      }

      const [steps, weightKg, sleepHours, workoutMinutes, activeEnergy] = await Promise.all([
        getStepsToday(),
        getLatestWeightKg(),
        getSleepHoursLastNight(),
        getWorkoutMinutesToday(),
        getActiveEnergyToday(),
      ]);

      await Promise.all([
        steps > 0 ? dailyLogsRepository.setStepsToday(userId, steps) : Promise.resolve(),
        weightKg !== null ? dailyLogsRepository.addWeight(userId, weightKg) : Promise.resolve(),
        sleepHours > 0 ? dailyLogsRepository.setSleepToday(userId, sleepHours) : Promise.resolve(),
        workoutMinutes > 0
          ? dailyLogsRepository.addWorkout(userId, { title: 'تمرين من Apple Health', durationMinutes: workoutMinutes })
          : Promise.resolve(),
      ]);

      setLastActiveEnergyKcal(activeEnergy);
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّرت المزامنة مع Apple Health'));
    } finally {
      setIsSyncing(false);
    }
  }, [userId, isAvailable]);

  return { isAvailable, isSyncing, error, lastActiveEnergyKcal, syncToday };
}
