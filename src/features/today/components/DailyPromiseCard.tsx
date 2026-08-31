import { Pressable, View } from 'react-native';
import type { DailyPromise, PromiseType } from '@/src/data/repositories/dailyPromiseRepository';
import { Card, Text, colors } from '@/src/design-system';
import { radius, spacing } from '@/src/design-system/spacing';
import { PROMISE_LABELS } from '../useDailyPromise';

const PROMISE_OPTIONS = Object.keys(PROMISE_LABELS) as PromiseType[];

type DailyPromiseCardProps = {
  promise: DailyPromise | null;
  isSaving?: boolean;
  error?: string | null;
  onChoose: (type: PromiseType) => void;
  onMarkFulfilled: (fulfilled: boolean) => void;
};

export function DailyPromiseCard({ promise, isSaving, error, onChoose, onMarkFulfilled }: DailyPromiseCardProps) {
  const errorText = error ? (
    <Text variant="caption" color="danger" style={{ marginTop: spacing.xs }}>
      {error}
    </Text>
  ) : null;

  if (!promise) {
    return (
      <Card variant="soft">
        <Text variant="overline" color="textSecondary">
          وش وعدك اليوم؟
        </Text>
        <View style={{ flexDirection: 'row-reverse', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.sm }}>
          {PROMISE_OPTIONS.map((type) => (
            <Pressable
              key={type}
              disabled={isSaving}
              onPress={() => onChoose(type)}
              style={{
                paddingVertical: spacing.xs,
                paddingHorizontal: spacing.md,
                borderRadius: radius.pill,
                backgroundColor: colors.surface,
                opacity: isSaving ? 0.6 : 1,
              }}
            >
              <Text variant="captionStrong">{PROMISE_LABELS[type]}</Text>
            </Pressable>
          ))}
        </View>
        {errorText}
      </Card>
    );
  }

  if (promise.fulfilled === null) {
    return (
      <Card variant="soft">
        <Text variant="overline" color="textSecondary">
          وعدك اليوم
        </Text>
        <Text variant="bodyStrong" style={{ marginTop: spacing.xxs }}>
          {PROMISE_LABELS[promise.promise_type]}
        </Text>
        <Text variant="caption" color="textSecondary" style={{ marginTop: spacing.sm }}>
          وفيت بوعدك؟
        </Text>
        <View style={{ flexDirection: 'row-reverse', gap: spacing.sm, marginTop: spacing.xs }}>
          <Pressable
            disabled={isSaving}
            onPress={() => onMarkFulfilled(true)}
            style={{
              flex: 1,
              paddingVertical: spacing.xs,
              borderRadius: radius.md,
              backgroundColor: colors.primary,
              alignItems: 'center',
              opacity: isSaving ? 0.6 : 1,
            }}
          >
            <Text variant="captionStrong" color="onPrimary">
              أيوه 👏
            </Text>
          </Pressable>
          <Pressable
            disabled={isSaving}
            onPress={() => onMarkFulfilled(false)}
            style={{
              flex: 1,
              paddingVertical: spacing.xs,
              borderRadius: radius.md,
              backgroundColor: colors.surface,
              alignItems: 'center',
              opacity: isSaving ? 0.6 : 1,
            }}
          >
            <Text variant="captionStrong">مو بعد</Text>
          </Pressable>
        </View>
        {errorText}
      </Card>
    );
  }

  return (
    <Card variant="soft">
      <Text variant="overline" color="textSecondary">
        وعدك اليوم
      </Text>
      <Text variant="bodyStrong" style={{ marginTop: spacing.xxs }}>
        {PROMISE_LABELS[promise.promise_type]} {promise.fulfilled ? '✅' : '↻ نكمل بكرة'}
      </Text>
    </Card>
  );
}
