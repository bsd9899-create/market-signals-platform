import { computeTodayDecision, type DailySignals } from '../decisionEngine';

const baseSignals: DailySignals = {
  waterRatio: 0,
  stepsRatio: 0,
  workoutRatio: 0,
  sleepRatio: 0,
  recentCompletionPercents: [],
};

describe('computeTodayDecision — إنجاز اليوم', () => {
  it('يعيد 0% عندما كل المؤشرات صفر', () => {
    const result = computeTodayDecision(baseSignals);
    expect(result.completionPercent).toBe(0);
  });

  it('يعيد 100% عندما كل المؤشرات مكتملة', () => {
    const result = computeTodayDecision({
      ...baseSignals,
      waterRatio: 1,
      stepsRatio: 1,
      workoutRatio: 1,
      sleepRatio: 1,
    });
    expect(result.completionPercent).toBe(100);
  });

  it('يحسب متوسطًا مرجّحًا صحيحًا (ماء 20%، خطوات 30%، تمرين 35%، نوم 15%)', () => {
    const result = computeTodayDecision({
      ...baseSignals,
      waterRatio: 1,
      stepsRatio: 0,
      workoutRatio: 0,
      sleepRatio: 0,
    });
    expect(result.completionPercent).toBe(20);
  });

  it('يعيد توزيع وزن النوم على بقية المؤشرات عند غياب بيانات النوم', () => {
    // بدون بيانات نوم: الأوزان تصبح ماء 20/85، خطوات 30/85، تمرين 35/85
    // من إجمالي 85 بدل 100. هنا كلها مكتملة فيجب أن تبقى 100%.
    const result = computeTodayDecision({
      ...baseSignals,
      waterRatio: 1,
      stepsRatio: 1,
      workoutRatio: 1,
      sleepRatio: null,
    });
    expect(result.completionPercent).toBe(100);
  });

  it('لا يتجاوز 100% حتى لو تخطّى المستخدم أهدافه', () => {
    const result = computeTodayDecision({
      ...baseSignals,
      waterRatio: 2,
      stepsRatio: 1.5,
      workoutRatio: 3,
      sleepRatio: 1.2,
    });
    expect(result.completionPercent).toBe(100);
  });
});

describe('computeTodayDecision — قرار اليوم', () => {
  it('يقترح التركيز على التمرين عندما نسبته منخفضة جدًا', () => {
    const result = computeTodayDecision({ ...baseSignals, workoutRatio: 0.1 });
    expect(result.decisionText).toContain('التمرين');
  });

  it('يقول "قريب جدًا" عندما الخطوات بين 80% و100%', () => {
    const result = computeTodayDecision({
      ...baseSignals,
      workoutRatio: 1,
      sleepRatio: 1,
      waterRatio: 1,
      stepsRatio: 0.85,
    });
    expect(result.decisionText).toContain('قريب جدًا');
  });

  it('يهنّئ المستخدم عندما الإنجاز 90% فأكثر', () => {
    const result = computeTodayDecision({
      ...baseSignals,
      waterRatio: 1,
      stepsRatio: 1,
      workoutRatio: 1,
      sleepRatio: 0.4,
    });
    expect(result.completionPercent).toBeGreaterThanOrEqual(90);
    expect(result.decisionText).toContain('رائع');
  });
});

describe('computeTodayDecision — وضع الإنقاذ', () => {
  it('لا يفعَّل لمستخدم جديد بدون سجل سابق', () => {
    const result = computeTodayDecision({ ...baseSignals, recentCompletionPercents: [] });
    expect(result.recoveryMode).toBe(false);
  });

  it('لا يفعَّل بيوم سيّئ واحد فقط', () => {
    const result = computeTodayDecision({ ...baseSignals, recentCompletionPercents: [80, 10] });
    expect(result.recoveryMode).toBe(false);
  });

  it('يُفعَّل بعد انقطاع فعلي (عدة أيام منخفضة جدًا)', () => {
    const result = computeTodayDecision({
      ...baseSignals,
      recentCompletionPercents: [5, 0, 10],
    });
    expect(result.recoveryMode).toBe(true);
    expect(result.decisionText).toContain('ما خربت');
  });

  it('يتجاوز رسالة وضع الإنقاذ أي قرار آخر حتى لو تحسّن أداء اليوم فجأة', () => {
    const result = computeTodayDecision({
      ...baseSignals,
      waterRatio: 1,
      stepsRatio: 1,
      workoutRatio: 1,
      sleepRatio: 1,
      recentCompletionPercents: [0, 0, 0],
    });
    expect(result.recoveryMode).toBe(true);
    expect(result.decisionText).toContain('ما خربت');
  });
});
