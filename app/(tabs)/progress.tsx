import { useCallback } from 'react';
import { RefreshControl, ScrollView, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { Button, Card, ProgressSkeleton, Screen, Text, colors } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { useProgressData } from '@/src/features/progress/useProgressData';
import { WeeklyBarChart } from '@/src/features/progress/components/WeeklyBarChart';

export default function ProgressScreen() {
  const userId = useAuthStore((s) => s.session?.user.id);
  const { summary, isLoading, error, refetch } = useProgressData(userId);

  useFocusEffect(
    useCallback(() => {
      refetch();
    }, [refetch])
  );

  if (!summary && isLoading) {
    return (
      <Screen>
        <ProgressSkeleton />
      </Screen>
    );
  }

  if (!summary) {
    return (
      <Screen style={{ alignItems: 'center', justifyContent: 'center', gap: spacing.sm }}>
        <Text variant="body" color="textSecondary">
          {error ?? 'تعذّر تحميل التقدم'}
        </Text>
        <Button label="إعادة المحاولة" variant="secondary" onPress={refetch} />
      </Screen>
    );
  }

  const hasAnyActivity =
    summary.workoutsThisWeek > 0 || summary.weightNowKg !== null || summary.history.some((h) => h.completion_percent > 0);

  return (
    <Screen>
      <ScrollView
        contentContainerStyle={{ gap: spacing.md, paddingBottom: spacing.xxxl }}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={colors.primary} />}
      >
        <Text variant="displayMd" style={{ marginTop: spacing.md }}>
          تقدمي
        </Text>

        {!hasAnyActivity ? (
          <Card variant="soft">
            <Text variant="body" color="textSecondary">
              ما سجّلت شيئًا بعد هالأسبوع — أول إدخال (ماء، خطوات، تمرين...) بيبدأ يبني تقدمك هنا.
            </Text>
          </Card>
        ) : null}

        <Card>
          <Text variant="overline" color="textSecondary">
            آخر 7 أيام
          </Text>
          <View style={{ marginTop: spacing.md }}>
            <WeeklyBarChart history={summary.history} days={7} />
          </View>
        </Card>

        <View style={{ flexDirection: 'row-reverse', gap: spacing.sm }}>
          <Card variant="soft" style={{ flex: 1 }}>
            <Text variant="caption" color="textSecondary">
              الوزن الحالي
            </Text>
            <Text variant="title" style={{ marginTop: spacing.xxs }}>
              {summary.weightNowKg !== null ? `${summary.weightNowKg} كجم` : '—'}
            </Text>
            {summary.weightDeltaKg !== null ? (
              <Text
                variant="caption"
                color={summary.weightDeltaKg <= 0 ? 'success' : 'textSecondary'}
                style={{ marginTop: spacing.xxs }}
              >
                {summary.weightDeltaKg > 0 ? '+' : ''}
                {summary.weightDeltaKg} كجم آخر 30 يوم
              </Text>
            ) : null}
          </Card>

          <Card variant="soft" style={{ flex: 1 }}>
            <Text variant="caption" color="textSecondary">
              متوسط الخطوات
            </Text>
            <Text variant="title" style={{ marginTop: spacing.xxs }}>
              {summary.averageSteps.toLocaleString('ar')}
            </Text>
            <Text variant="caption" color="textSecondary" style={{ marginTop: spacing.xxs }}>
              آخر 7 أيام
            </Text>
          </Card>
        </View>

        <Card variant="soft">
          <Text variant="caption" color="textSecondary">
            التمارين هذا الأسبوع
          </Text>
          <Text variant="title" style={{ marginTop: spacing.xxs }}>
            {summary.workoutsThisWeek}
          </Text>
        </Card>

        <Card>
          <Text variant="overline" color="textSecondary">
            تقييم هِمّة الأسبوعي
          </Text>
          <Text variant="displayLg" color="primary" style={{ marginTop: spacing.xxs }}>
            {summary.weeklyReview.score} / 10
          </Text>
          <View style={{ marginTop: spacing.sm, gap: spacing.xxs }}>
            <Text variant="body">
              أقوى نقطة: <Text variant="bodyStrong">{summary.weeklyReview.strongestLabel}</Text>
            </Text>
            <Text variant="body">
              تحتاج اهتمامًا: <Text variant="bodyStrong">{summary.weeklyReview.weakestLabel}</Text>
            </Text>
          </View>
          <Text variant="caption" color="textSecondary" style={{ marginTop: spacing.sm }}>
            تركيزك للأسبوع القادم: {summary.weeklyReview.focusNextWeekLabel}
          </Text>
        </Card>
      </ScrollView>
    </Screen>
  );
}
