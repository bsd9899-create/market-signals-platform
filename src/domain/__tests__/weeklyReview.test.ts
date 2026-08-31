import { computeWeeklyReview } from '../weeklyReview';

const goals = { targetWaterMl: 2000, targetSteps: 8000, targetSleepHours: 7.5 };

describe('computeWeeklyReview', () => {
  it('يعطي 10/10 عندما كل المؤشرات مكتملة', () => {
    const result = computeWeeklyReview(
      { avgWaterMl: 2000, avgWorkoutMinutes: 30, avgSteps: 8000, avgSleepHours: 7.5 },
      goals
    );
    expect(result.score).toBe(10);
  });

  it('يعطي 0/10 عندما كل المؤشرات صفر', () => {
    const result = computeWeeklyReview({ avgWaterMl: 0, avgWorkoutMinutes: 0, avgSteps: 0, avgSleepHours: 0 }, goals);
    expect(result.score).toBe(0);
  });

  it('يحدد أضعف وأقوى نقطة بشكل صحيح', () => {
    const result = computeWeeklyReview(
      { avgWaterMl: 2000, avgWorkoutMinutes: 30, avgSteps: 8000, avgSleepHours: 2 },
      goals
    );
    expect(result.weakestLabel).toContain('النوم');
    expect(result.focusNextWeekLabel).toContain('النوم');
  });

  it('لا يمنح نقاطًا إضافية لتجاوز الهدف (Cap عند 100% لكل مؤشر)', () => {
    const result = computeWeeklyReview(
      { avgWaterMl: 4000, avgWorkoutMinutes: 30, avgSteps: 8000, avgSleepHours: 7.5 },
      goals
    );
    expect(result.score).toBe(10);
  });
});
