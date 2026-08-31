import { useCallback } from 'react';
import { RefreshControl, ScrollView, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Button, Card, ProgressBar, Screen, Text, TeamsSkeleton, colors } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { useTeamData } from '@/src/features/teams/useTeamData';

export default function TeamsScreen() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.session?.user.id);
  const { data, hasTeam, isLoading, error, refetch } = useTeamData(userId);

  useFocusEffect(
    useCallback(() => {
      refetch();
    }, [refetch])
  );

  if (hasTeam === null && isLoading) {
    return (
      <Screen>
        <TeamsSkeleton />
      </Screen>
    );
  }

  if (hasTeam === false) {
    return (
      <Screen>
        <View style={{ flex: 1, justifyContent: 'center', gap: spacing.lg }}>
          <View>
            <Text variant="displayMd">الفرق 🤝</Text>
            <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xs }}>
              التنافس هنا على نسبة الالتزام بهدفك الشخصي، مو على رقم واحد للجميع.
            </Text>
          </View>
          <Button label="أنشئ فريقًا" onPress={() => router.push('/teams/create')} />
          <Button label="انضم بكود دعوة" variant="secondary" onPress={() => router.push('/teams/join')} />
        </View>
      </Screen>
    );
  }

  if (!data) {
    return (
      <Screen style={{ alignItems: 'center', justifyContent: 'center', gap: spacing.sm }}>
        <Text variant="body" color="textSecondary">
          {error ?? 'تعذّر تحميل الفريق'}
        </Text>
        <Button label="إعادة المحاولة" variant="secondary" onPress={refetch} />
      </Screen>
    );
  }

  return (
    <Screen>
      <ScrollView
        contentContainerStyle={{ gap: spacing.md, paddingBottom: spacing.xxxl }}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={colors.primary} />}
      >
        <View style={{ marginTop: spacing.md }}>
          <Text variant="displayMd">{data.team.name}</Text>
          <Text variant="caption" color="textSecondary" style={{ marginTop: spacing.xxs }}>
            كود الدعوة: {data.team.invite_code} — شاركه مع أصدقائك
          </Text>
        </View>

        <Card variant="soft">
          <Text variant="overline" color="textSecondary">
            نبض الفريق اليوم
          </Text>
          <Text variant="displayLg" color="primary" style={{ marginTop: spacing.xxs }}>
            {data.pulsePercent ?? 0}%
          </Text>
          <View style={{ marginTop: spacing.sm }}>
            <ProgressBar progress={(data.pulsePercent ?? 0) / 100} />
          </View>
        </Card>

        <Card>
          <Text variant="overline" color="textSecondary">
            الترتيب
          </Text>
          <View style={{ marginTop: spacing.sm, gap: spacing.sm }}>
            {data.leaderboard.map((row, index) => (
              <View
                key={row.user_id}
                style={{ flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center' }}
              >
                <View style={{ flexDirection: 'row-reverse', alignItems: 'center', gap: spacing.sm }}>
                  <Text variant="bodyStrong" color={index === 0 ? 'accent' : 'textSecondary'}>
                    {index === 0 ? '🥇' : `#${index + 1}`}
                  </Text>
                  <Text variant="body">
                    {row.display_name}
                    {row.user_id === userId ? ' (أنت)' : ''}
                  </Text>
                </View>
                <Text variant="bodyStrong" color={index === 0 ? 'accent' : 'textPrimary'}>
                  {row.total_points}
                </Text>
              </View>
            ))}
          </View>
        </Card>

        <Card variant="soft">
          <Text variant="overline" color="textSecondary">
            الأعضاء ({data.roster.length})
          </Text>
          <View style={{ marginTop: spacing.sm, gap: spacing.xs }}>
            {data.roster.map((member) => (
              <Text key={member.user_id} variant="body">
                {member.display_name} {member.role === 'owner' ? '👑' : ''}
              </Text>
            ))}
          </View>
        </Card>

        <Card>
          <View style={{ flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text variant="overline" color="textSecondary">
              التحديات
            </Text>
            <Button
              label="تحدٍ جديد"
              variant="ghost"
              onPress={() => router.push({ pathname: '/teams/new-challenge', params: { teamId: data.team.id } })}
            />
          </View>

          {data.challenges.length === 0 ? (
            <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xs }}>
              لا توجد تحديات بعد.
            </Text>
          ) : (
            <View style={{ marginTop: spacing.sm, gap: spacing.md }}>
              {data.challenges.map((challenge) => (
                <View key={challenge.id}>
                  <Text variant="bodyStrong">{challenge.title}</Text>
                  <Text variant="caption" color="textSecondary">
                    {challenge.start_date} → {challenge.end_date}
                  </Text>
                  <View style={{ marginTop: spacing.xs }}>
                    <ProgressBar progress={challenge.myProgressPercent / 100} />
                  </View>
                  <Text variant="caption" color="textSecondary" style={{ marginTop: spacing.xxs }}>
                    التزامك: {challenge.myProgressPercent}%
                  </Text>
                </View>
              ))}
            </View>
          )}
        </Card>
      </ScrollView>
    </Screen>
  );
}
