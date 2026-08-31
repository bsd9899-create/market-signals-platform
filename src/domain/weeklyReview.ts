/** التقييم الأسبوعي — دالة صافية تحوّل متوسطات الأسبوع الخام إلى ملخص. */

export type WeeklyRawAverages = {
  avgWaterMl: number;
  avgWorkoutMinutes: number;
  avgSteps: number;
  avgSleepHours: number;
};

export type WeeklyGoals = {
  targetWaterMl: number;
  targetSteps: number;
  targetSleepHours: number;
};

export type WeeklyReview = {
  /** من 0 إلى 10 */
  score: number;
  strongestLabel: string;
  weakestLabel: string;
  focusNextWeekLabel: string;
};

const REFERENCE_WORKOUT_MINUTES_PER_DAY = 30;

const METRIC_LABELS = {
  workout: 'التمارين 🔥',
  water: 'الماء 💧',
  steps: 'الخطوات 👟',
  sleep: 'النوم 💤',
} as const;

export function computeWeeklyReview(raw: WeeklyRawAverages, goals: WeeklyGoals): WeeklyReview {
  const ratios: Record<keyof typeof METRIC_LABELS, number> = {
    workout: raw.avgWorkoutMinutes / REFERENCE_WORKOUT_MINUTES_PER_DAY,
    water: raw.avgWaterMl / goals.targetWaterMl,
    steps: raw.avgSteps / goals.targetSteps,
    sleep: raw.avgSleepHours / goals.targetSleepHours,
  };

  const entries = Object.entries(ratios) as [keyof typeof METRIC_LABELS, number][];
  const overallRatio = entries.reduce((sum, [, ratio]) => sum + Math.min(1, ratio), 0) / entries.length;

  const [strongestKey] = entries.reduce((best, curr) => (curr[1] > best[1] ? curr : best));
  const [weakestKey] = entries.reduce((worst, curr) => (curr[1] < worst[1] ? curr : worst));

  return {
    score: Math.round(overallRatio * 100) / 10,
    strongestLabel: METRIC_LABELS[strongestKey],
    weakestLabel: METRIC_LABELS[weakestKey],
    focusNextWeekLabel: METRIC_LABELS[weakestKey],
  };
}
