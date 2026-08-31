/**
 * محرّك "قرار اليوم" و"وضع الإنقاذ" — Rule Engine بسيط ومقصود، وليس AI،
 * تمامًا كما طُلب للنسخة الأولى. كل الدوال هنا صافية (pure) وقابلة
 * للاختبار بدون أي اتصال بقاعدة بيانات (راجع المرحلة 11).
 */

export type DailySignals = {
  /** نسبة (فعلي/هدف)، بدون سقف علوي — قد تتجاوز 1 لو تجاوز المستخدم هدفه. */
  waterRatio: number;
  stepsRatio: number;
  /** null = لا يوجد هدف تمرين محدد لهذا اليوم أساسًا (نادر، احتياطي فقط). */
  workoutRatio: number;
  /** null = لا توجد بيانات نوم مسجّلة اليوم بعد. */
  sleepRatio: number | null;
  /** نسب إنجاز آخر أيام سابقة (الأقدم أولًا)، بدون اليوم الحالي. */
  recentCompletionPercents: number[];
};

export type TodayDecision = {
  completionPercent: number;
  decisionText: string;
  recoveryMode: boolean;
};

const WEIGHTS = { water: 0.2, steps: 0.3, workout: 0.35, sleep: 0.15 } as const;

const RECOVERY_LOOKBACK_DAYS = 3;
const RECOVERY_THRESHOLD_PERCENT = 25;
const RECOVERY_DECISION_TEXT = 'ما خربت… نكمل من هنا 🌱';

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

/** متوسط مرجَّح لنسبة الإنجاز — يعيد توزيع وزن النوم لو لم تتوفر بياناته بعد. */
function computeCompletionPercent(signals: DailySignals): number {
  const parts: { ratio: number; weight: number }[] = [
    { ratio: clamp01(signals.waterRatio), weight: WEIGHTS.water },
    { ratio: clamp01(signals.stepsRatio), weight: WEIGHTS.steps },
    { ratio: clamp01(signals.workoutRatio), weight: WEIGHTS.workout },
  ];
  if (signals.sleepRatio !== null) {
    parts.push({ ratio: clamp01(signals.sleepRatio), weight: WEIGHTS.sleep });
  }

  const totalWeight = parts.reduce((sum, p) => sum + p.weight, 0);
  const weightedSum = parts.reduce((sum, p) => sum + p.ratio * p.weight, 0);

  return Math.round((weightedSum / totalWeight) * 100);
}

/** انقطاع فعلي = آخر أيام متتالية بإنجاز منخفض جدًا (وليس مجرد يوم سيّئ واحد). */
function detectRecoveryMode(recentCompletionPercents: number[]): boolean {
  if (recentCompletionPercents.length < 2) return false;

  const lastDays = recentCompletionPercents.slice(-RECOVERY_LOOKBACK_DAYS);
  return lastDays.length >= 2 && lastDays.every((p) => p < RECOVERY_THRESHOLD_PERCENT);
}

function pickDecisionText(signals: DailySignals, completionPercent: number): string {
  // "قريب جدًا" مقصودة تحديدًا لهذا الموقف (شبه منتهٍ والخطوات هي
  // الفجوة الوحيدة المتبقية) — لذلك تُفحص قبل تهنئة ≥90% العامة، وإلا
  // لن تظهر أبدًا في الأيام شبه المثالية التي تستحقها أكثر.
  if (signals.stepsRatio >= 0.8 && signals.stepsRatio < 1) {
    return 'اليوم: أنت قريب جدًا 👟';
  }
  if (completionPercent >= 90) {
    return 'أنت رائع اليوم 🌟 استمر بهذا الشكل';
  }
  if (signals.workoutRatio < 0.34) {
    return 'اليوم ركز على التمرين 🔥';
  }
  if (completionPercent < 20) {
    return 'اليوم: خذها بهدوء 💤';
  }
  return 'يلا نكمل يومك 💪';
}

export function computeTodayDecision(signals: DailySignals): TodayDecision {
  const completionPercent = computeCompletionPercent(signals);
  const recoveryMode = detectRecoveryMode(signals.recentCompletionPercents);

  return {
    completionPercent,
    recoveryMode,
    decisionText: recoveryMode ? RECOVERY_DECISION_TEXT : pickDecisionText(signals, completionPercent),
  };
}
