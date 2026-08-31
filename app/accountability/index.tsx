import { ActivityIndicator, ScrollView, View } from 'react-native';
import { Button, Card, Screen, Text, colors } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { useTeamData } from '@/src/features/teams/useTeamData';
import { useAccountability } from '@/src/features/accountability/useAccountability';
import type { PingKind } from '@/src/data/repositories/accountabilityRepository';

const PING_OPTIONS: { kind: PingKind; label: string }[] = [
  { kind: 'lets_go', label: '🔥 يلا نكمل' },
  { kind: 'almost_there', label: '💪 باقي لك شوي' },
  { kind: 'well_done', label: '👏 كفو' },
  { kind: 'with_you', label: '🤝 معك للنهاية' },
];

export default function AccountabilityScreen() {
  const userId = useAuthStore((s) => s.session?.user.id);
  const { data: team, hasTeam } = useTeamData(userId);
  const {
    pair,
    pings,
    otherUserId,
    isIncomingRequest,
    isOutgoingRequest,
    isLoading,
    isActing,
    error,
    sendRequest,
    respond,
    endPair,
    sendPing,
    refetch,
  } = useAccountability(userId);

  function nameOf(id: string | null) {
    if (!id) return 'شريكك';
    return team?.roster.find((m) => m.user_id === id)?.display_name ?? 'شريكك';
  }

  if (isLoading && !pair) {
    return (
      <Screen style={{ alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={colors.primary} />
      </Screen>
    );
  }

  // خطأ في التحميل الأولي (وليس "لا يوجد رفيق بعد") — لا نعرض شاشة
  // الاختيار في هذه الحالة، لأنها قد توهم المستخدم بأن كل شيء طبيعي.
  if (error && !pair) {
    return (
      <Screen style={{ alignItems: 'center', justifyContent: 'center', gap: spacing.sm }}>
        <Text variant="body" color="textSecondary">
          {error}
        </Text>
        <Button label="إعادة المحاولة" variant="secondary" onPress={refetch} />
      </Screen>
    );
  }

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ gap: spacing.md, paddingBottom: spacing.xxxl }} showsVerticalScrollIndicator={false}>
        <View style={{ marginTop: spacing.md }}>
          <Text variant="displayMd">رفيق هِمّة 🤝</Text>
          <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xs }}>
            شريك التزام واحد، بدون شات — بس تفاعلات سريعة تحفّزكم مع بعض.
          </Text>
        </View>

        {!pair && (
          <Card variant="soft">
            {hasTeam && team && team.roster.length > 1 ? (
              <View style={{ gap: spacing.sm }}>
                <Text variant="captionStrong" color="textSecondary">
                  اختر رفيقك من فريقك
                </Text>
                {team.roster
                  .filter((m) => m.user_id !== userId)
                  .map((member) => (
                    <View
                      key={member.user_id}
                      style={{ flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center' }}
                    >
                      <Text variant="body">{member.display_name}</Text>
                      <Button
                        label="اطلب"
                        variant="secondary"
                        disabled={isActing}
                        onPress={() => sendRequest(member.user_id)}
                      />
                    </View>
                  ))}
              </View>
            ) : (
              <Text variant="body" color="textSecondary">
                انضم لفريق فيه صديق واحد على الأقل عشان تقدر تختار رفيق هِمّة.
              </Text>
            )}
          </Card>
        )}

        {isOutgoingRequest && (
          <Card variant="soft">
            <Text variant="body">بانتظار رد {nameOf(otherUserId)}...</Text>
            <Button label="إلغاء الطلب" variant="ghost" disabled={isActing} style={{ marginTop: spacing.sm }} onPress={endPair} />
          </Card>
        )}

        {isIncomingRequest && (
          <Card variant="soft">
            <Text variant="bodyStrong">{nameOf(otherUserId)} يريد أن يكون رفيق هِمّة معك</Text>
            <View style={{ flexDirection: 'row-reverse', gap: spacing.sm, marginTop: spacing.sm }}>
              <Button label="قبول" disabled={isActing} onPress={() => respond(true)} style={{ flex: 1 }} />
              <Button label="رفض" variant="secondary" disabled={isActing} onPress={() => respond(false)} style={{ flex: 1 }} />
            </View>
          </Card>
        )}

        {pair?.status === 'active' && (
          <>
            <Card>
              <Text variant="overline" color="textSecondary">
                رفيقك
              </Text>
              <Text variant="title" style={{ marginTop: spacing.xxs }}>
                {nameOf(otherUserId)}
              </Text>
              <View style={{ flexDirection: 'row-reverse', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md }}>
                {PING_OPTIONS.map((option) => (
                  <Button
                    key={option.kind}
                    label={option.label}
                    variant="secondary"
                    disabled={isActing}
                    onPress={() => sendPing(option.kind)}
                  />
                ))}
              </View>
            </Card>

            <Card variant="soft">
              <Text variant="overline" color="textSecondary">
                آخر التفاعلات
              </Text>
              <View style={{ marginTop: spacing.sm, gap: spacing.xs }}>
                {pings.length === 0 ? (
                  <Text variant="body" color="textSecondary">
                    لا توجد تفاعلات بعد — ابدأ أنت!
                  </Text>
                ) : (
                  pings.map((ping) => (
                    <Text key={ping.id} variant="body">
                      {ping.sender_id === userId ? 'أنت' : nameOf(ping.sender_id)}:{' '}
                      {PING_OPTIONS.find((o) => o.kind === ping.kind)?.label}
                    </Text>
                  ))
                )}
              </View>
            </Card>

            <Button label="إنهاء الشراكة" variant="ghost" disabled={isActing} onPress={endPair} />
          </>
        )}

        {error && pair ? (
          <Text variant="caption" color="danger" style={{ textAlign: 'center' }}>
            {error}
          </Text>
        ) : null}
      </ScrollView>
    </Screen>
  );
}
