import type { TodaySummary } from './useTodayData';

export type NextTask = {
  emoji: string;
  title: string;
  subtitle: string;
  ctaLabel: string | null;
};

/** أهم مهمة قادمة واحدة — أول عنصر أساسي لم يُنجز بعد، بترتيب أولوية ثابت. */
export function getNextTask(summary: TodaySummary): NextTask {
  if (summary.workoutMinutes === 0) {
    return {
      emoji: '🏋️',
      title: 'تمرين اليوم',
      subtitle: 'ما سجّلت تمرينًا بعد',
      ctaLabel: 'ابدأ التمرين',
    };
  }

  if (summary.waterMl < summary.waterTargetMl) {
    const remainingMl = summary.waterTargetMl - summary.waterMl;
    return {
      emoji: '💧',
      title: 'أكمل الماء',
      subtitle: `${remainingMl} مل متبقية`,
      ctaLabel: 'أضف ماء',
    };
  }

  if (summary.steps < summary.stepsTarget) {
    const remainingSteps = summary.stepsTarget - summary.steps;
    return {
      emoji: '👟',
      title: 'أكمل خطواتك',
      subtitle: `${remainingSteps.toLocaleString('ar')} خطوة متبقية`,
      ctaLabel: 'سجّل خطواتك',
    };
  }

  return {
    emoji: '🎉',
    title: 'أنجزت أساسيات اليوم',
    subtitle: 'استمر بهذا الشكل',
    ctaLabel: null,
  };
}
