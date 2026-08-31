import { Pressable, View } from 'react-native';
import type { DailyPromise, PromiseType } from '@/src/data/repositories/dailyPromiseRepository';
import { Card, Text } from '@/src/design-system';
import { colors } from '@/src/design-system';
import { radius, spacing } from '@/src/design-system/spacing';
import { PROMISE_LABELS } from '../useDailyPromise';

const PROMISE_OPTIONS = Object.keys(PROMISE_LABELS) as PromiseType[];

type DailyPromiseCardProps = {
  promise: DailyPromise | null;
  onChoose: (type: PromiseType) => void;
  onMarkFulfilled: (fulfilled: boolean) => void;
};

export function DailyPromiseCard({ promise, onChoose, onMarkFulfilled }: DailyPromiseCardProps) {
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
              onPress={() => onChoose(type)}
              style={{
                paddingVertical: spacing.xs,
                paddingHorizontal: spacing.md,
                borderRadius: radius.pill,
                backgroundColor: colors.surface,
              }}
            >
              <Text variant="captionStrong">{PROMISE_LABELS[type]}</Text>
            </Pressable>
          ))}
        </View>
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
            onPress={() => onMarkFulfilled(true)}
            style={{ flex: 1, paddingVertical: spacing.xs, borderRadius: radius.md, backgroundColor: colors.primary, alignItems: 'center' }}
          >
            <Text variant="captionStrong" color="onPrimary">
              أيوه 👏
            </Text>
          </Pressable>
          <Pressable
            onPress={() => onMarkFulfilled(false)}
            style={{ flex: 1, paddingVertical: spacing.xs, borderRadius: radius.md, backgroundColor: colors.surface, alignItems: 'center' }}
          >
            <Text variant="captionStrong">مو بعد</Text>
          </Pressable>
        </View>
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
