import { getNextTask } from '../nextTask';
import type { TodaySummary } from '../useTodayData';

function makeSummary(overrides: Partial<TodaySummary>): TodaySummary {
  return {
    completionPercent: 0,
    decisionText: '',
    recoveryMode: false,
    waterMl: 2000,
    waterTargetMl: 2000,
    steps: 8000,
    stepsTarget: 8000,
    workoutMinutes: 30,
    mealsLogged: 2,
    goals: {
      user_id: 'u1',
      target_water_ml: 2000,
      target_steps: 8000,
      target_sleep_hours: 7.5,
      target_workouts_per_week: 3,
      target_weight_kg: null,
      updated_at: '',
    },
    ...overrides,
  };
}

describe('getNextTask', () => {
  it('يقترح التمرين أولًا لو ما فيه تمرين اليوم — حتى لو باقي المؤشرات مكتملة', () => {
    const task = getNextTask(makeSummary({ workoutMinutes: 0 }));
    expect(task.title).toBe('تمرين اليوم');
    expect(task.ctaLabel).not.toBeNull();
  });

  it('يقترح إكمال الماء لو التمرين تم لكن الماء ناقص', () => {
    const task = getNextTask(makeSummary({ workoutMinutes: 30, waterMl: 500, waterTargetMl: 2000 }));
    expect(task.title).toBe('أكمل الماء');
    expect(task.subtitle).toContain('1500');
  });

  it('يقترح إكمال الخطوات لو التمرين والماء تمّا لكن الخطوات ناقصة', () => {
    const task = getNextTask(makeSummary({ workoutMinutes: 30, waterMl: 2000, steps: 3000, stepsTarget: 8000 }));
    expect(task.title).toBe('أكمل خطواتك');
  });

  it('يهنّئ المستخدم بدون CTA لو كل الأساسيات منجزة', () => {
    const task = getNextTask(makeSummary({}));
    expect(task.ctaLabel).toBeNull();
  });
});
