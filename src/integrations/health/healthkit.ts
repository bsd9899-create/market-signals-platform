/**
 * طبقة تكامل Apple HealthKit — معزولة تمامًا عن باقي التطبيق (لا
 * يستوردها أي كود آخر مباشرة سوى usePremiumStatus-جاره: useHealthSync).
 *
 * ⚠️ غير مُختبرة على جهاز حقيقي بعد: HealthKit غير متاح إطلاقًا في
 * المحاكي/Expo Go، ويحتاج EAS Dev Client + حساب Apple Developor فعّال
 * (لصلاحية HealthKit entitlement) — كلاهما غير متوفر في بيئة التطوير
 * الحالية. الشيفرة هنا مطابقة لتوثيق المكتبة والـ API الرسمي لـ Apple،
 * لكنها تحتاج تحققًا فعليًا على جهاز قبل الاعتماد الكامل عليها.
 *
 * صلاحيات القراءة فقط لما نحتاجه فعلًا (خطوات، سعرات نشطة، وزن، نوم،
 * تمارين) — بلا صلاحيات كتابة وبلا Background Delivery (راجع app.json).
 */
import {
  isHealthDataAvailableAsync,
  requestAuthorization,
  queryStatisticsForQuantity,
  getMostRecentQuantitySample,
  queryCategorySamples,
  queryWorkoutSamples,
  WorkoutTypeIdentifier,
  CategoryValueSleepAnalysis,
} from '@kingstinct/react-native-healthkit';
import { Platform } from 'react-native';

const READ_TYPES = [
  'HKQuantityTypeIdentifierStepCount',
  'HKQuantityTypeIdentifierActiveEnergyBurned',
  'HKQuantityTypeIdentifierBodyMass',
  'HKCategoryTypeIdentifierSleepAnalysis',
  WorkoutTypeIdentifier,
] as const;

export async function isHealthKitAvailable(): Promise<boolean> {
  if (Platform.OS !== 'ios') return false;
  try {
    return await isHealthDataAvailableAsync();
  } catch {
    return false;
  }
}

export async function requestHealthPermissions(): Promise<boolean> {
  if (!(await isHealthKitAvailable())) return false;
  return requestAuthorization({ toRead: [...READ_TYPES] });
}

function startOfToday(): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

export async function getStepsToday(): Promise<number> {
  const stats = await queryStatisticsForQuantity(
    'HKQuantityTypeIdentifierStepCount',
    ['cumulativeSum'],
    { filter: { date: { startDate: startOfToday(), endDate: new Date() } }, unit: 'count' }
  );
  return Math.round(stats.sumQuantity?.quantity ?? 0);
}

export async function getActiveEnergyToday(): Promise<number> {
  const stats = await queryStatisticsForQuantity(
    'HKQuantityTypeIdentifierActiveEnergyBurned',
    ['cumulativeSum'],
    { filter: { date: { startDate: startOfToday(), endDate: new Date() } }, unit: 'kcal' }
  );
  return Math.round(stats.sumQuantity?.quantity ?? 0);
}

export async function getLatestWeightKg(): Promise<number | null> {
  const sample = await getMostRecentQuantitySample('HKQuantityTypeIdentifierBodyMass', 'kg');
  return sample ? Math.round(sample.quantity * 10) / 10 : null;
}

/** إجمالي ساعات النوم الفعلي (asleep*) لآخر 24 ساعة — يستبعد inBed وawake. */
export async function getSleepHoursLastNight(): Promise<number> {
  const since = new Date();
  since.setHours(since.getHours() - 24);

  const samples = await queryCategorySamples('HKCategoryTypeIdentifierSleepAnalysis', {
    filter: { date: { startDate: since, endDate: new Date() } },
    limit: 0,
  });

  const asleepValues = new Set<number>([
    CategoryValueSleepAnalysis.asleepUnspecified,
    CategoryValueSleepAnalysis.asleepCore,
    CategoryValueSleepAnalysis.asleepDeep,
    CategoryValueSleepAnalysis.asleepREM,
  ]);

  const totalMs = samples
    .filter((sample) => asleepValues.has(sample.value))
    .reduce((sum, sample) => sum + (sample.endDate.getTime() - sample.startDate.getTime()), 0);

  return Math.round((totalMs / 1000 / 60 / 60) * 10) / 10;
}

export async function getWorkoutMinutesToday(): Promise<number> {
  const workouts = await queryWorkoutSamples({
    filter: { date: { startDate: startOfToday(), endDate: new Date() } },
    limit: 0,
  });

  const totalSeconds = workouts.reduce((sum, w) => sum + w.duration.quantity, 0);
  return Math.round(totalSeconds / 60);
}
