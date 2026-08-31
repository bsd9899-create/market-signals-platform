import { useCallback } from 'react';
import { RefreshControl, ScrollView, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Button, Card, ProgressRing, Screen, Text, TodaySkeleton, colors, palette } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { useProfileStore } from '@/src/features/auth/profileStore';
import { useTodayData } from '@/src/features/today/useTodayData';
import { getNextTask } from '@/src/features/today/nextTask';
import { MetricTile } from '@/src/features/today/components/MetricTile';
import { DailyPromiseCard } from '@/src/features/today/components/DailyPromiseCard';
import { useDailyPromise } from '@/src/features/today/useDailyPromise';
import { useTeamData } from '@/src/features/teams/useTeamData';
import { getTimeGreeting } from '@/src/lib/greeting';

export default function TodayScreen() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.session?.user.id);
  const displayName = useProfileStore((s) => s.profile?.display_name);
  const { summary, isLoading, error, refetch } = useTodayData(userId);
  const { data: team, hasTeam, refetch: refetchTeam } = useTeamData(userId);
  const {
    promise,
    isSaving: isPromiseSaving,
    error: promiseError,
    choose: choosePromise,
    markFulfilled,
    refetch: refetchPromise,
  } = useDailyPromise(userId);

  // إعادة الجلب عند الرجوع من الإضافة السريعة أو أي شاشة أخرى — التبويبات
  // في Expo Router تبقى مثبّتة (لا تُعاد بالكامل) عند التنقل بينها.
  useFocusEffect(
    useCallback(() => {
      refetch();
      refetchTeam();
      refetchPromise();
    }, [refetch, refetchTeam, refetchPromise])
  );

  if (!summary && isLoading) {
    return (
      <Screen edges={['top']}>
        <TodaySkeleton />
      </Screen>
    );
  }

  if (!summary) {
    return (
      <Screen edges={['top']} style={{ alignItems: 'center', justifyContent: 'center', gap: spacing.sm }}>
        <Text variant="body" color="textSecondary">
          {error ?? 'تعذّر تحميل بيانات اليوم'}
        </Text>
        <Button label="إعادة المحاولة" variant="secondary" onPress={refetch} />
      </Screen>
    );
  }

  const nextTask = getNextTask(summary);

  return (
    <Screen edges={['top']}>
      <ScrollView
        contentContainerStyle={{ gap: spacing.md, paddingBottom: spacing.xxxl }}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={colors.primary} />}
      >
        <View style={{ marginTop: spacing.md }}>
          <Text variant="displayMd">
            {getTimeGreeting()} {displayName ?? ''} 👋
          </Text>
        </View>

        <DailyPromiseCard
          promise={promise}
          isSaving={isPromiseSaving}
          error={promiseError}
          onChoose={choosePromise}
          onMarkFulfilled={markFulfilled}
        />

        {/* البطاقة الرئيسية — قرار اليوم وإنجاز اليوم معًا، تجيب فورًا على
            "كيف وضعي؟" بدون تفريق بصري بين رقمين مرتبطين بنفس الفكرة. */}
        <Card variant={summary.recoveryMode ? 'soft' : 'surface'}>
          <View style={{ flexDirection: 'row-reverse', alignItems: 'center', gap: spacing.md }}>
            <View style={{ flex: 1, gap: spacing.xxs }}>
              <Text variant="overline" color="textSecondary">
                {summary.recoveryMode ? 'وضع الإنقاذ 🌱' : 'قرار اليوم'}
              </Text>
              <Text variant="title">{summary.decisionText}</Text>
            </View>
            <ProgressRing
              progress={summary.completionPercent / 100}
              size={92}
              strokeWidth={9}
              fillColor={summary.completionPercent >= 90 ? palette.gold500 : colors.primary}
            >
              <Text variant="title" color={summary.completionPercent >= 90 ? 'accent' : 'primary'}>
                {summary.completionPercent}%
              </Text>
            </ProgressRing>
          </View>
        </Card>

        <Text variant="overline" color="textSecondary" style={{ marginTop: spacing.xs }}>
          أساسيات اليوم
        </Text>

        <View style={{ flexDirection: 'row-reverse', gap: spacing.sm }}>
          <MetricTile
            emoji="🏋️"
            label="التمرين"
            valueText={`${summary.workoutMinutes} د`}
            progress={summary.workoutMinutes / 30}
          />
          <MetricTile emoji="🍽️" label="التغذية" valueText={`${summary.mealsLogged} وجبات`} />
        </View>
        <View style={{ flexDirection: 'row-reverse', gap: spacing.sm }}>
          <MetricTile
            emoji="💧"
            label="الماء"
            valueText={`${summary.waterMl}/${summary.waterTargetMl} مل`}
            progress={summary.waterMl / summary.waterTargetMl}
          />
          <MetricTile
            emoji="👟"
            label="الخطوات"
            valueText={`${summary.steps}/${summary.stepsTarget}`}
            progress={summary.steps / summary.stepsTarget}
          />
        </View>

        <Card>
          <Text variant="overline" color="textSecondary">
            مهمتك القادمة
          </Text>
          <View style={{ flexDirection: 'row-reverse', alignItems: 'center', gap: spacing.sm, marginTop: spacing.xs }}>
            <Text variant="displayMd">{nextTask.emoji}</Text>
            <View>
              <Text variant="bodyStrong">{nextTask.title}</Text>
              <Text variant="caption" color="textSecondary">
                {nextTask.subtitle}
              </Text>
            </View>
          </View>
          {nextTask.ctaLabel ? (
            <Button
              label={nextTask.ctaLabel}
              style={{ marginTop: spacing.md }}
              onPress={() => router.push('/quick-add')}
            />
          ) : null}
        </Card>

        <Card variant="soft">
          <Text variant="overline" color="textSecondary">
            مع فريقك
          </Text>
          {hasTeam && team ? (
            <>
              <Text variant="bodyStrong" style={{ marginTop: spacing.xs }}>
                نبض الفريق: {team.pulsePercent ?? 0}%
              </Text>
              {team.myRank ? (
                <Text variant="caption" color="textSecondary" style={{ marginTop: spacing.xxs }}>
                  أنت المركز #{team.myRank}
                </Text>
              ) : null}
            </>
          ) : (
            <>
              <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xs }}>
                ما انضممت لفريق بعد — أنشئ فريقك أو انضم لصديق لتتحفزوا مع بعض.
              </Text>
              <Button
                label="اذهب إلى الفرق"
                variant="secondary"
                style={{ marginTop: spacing.sm }}
                onPress={() => router.push('/(tabs)/teams')}
              />
            </>
          )}
        </Card>
      </ScrollView>
    </Screen>
  );
}
