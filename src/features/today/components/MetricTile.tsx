import { View } from 'react-native';
import { Card, ProgressBar, Text } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';

type MetricTileProps = {
  emoji: string;
  label: string;
  valueText: string;
  progress?: number;
};

/** بطاقة صغيرة لعنصر واحد في صف (تمرين/تغذية/ماء/خطوات) في شاشة اليوم. */
export function MetricTile({ emoji, label, valueText, progress }: MetricTileProps) {
  return (
    <Card variant="soft" style={{ flex: 1, gap: spacing.xs }}>
      <Text variant="title">{emoji}</Text>
      <Text variant="captionStrong" color="textSecondary">
        {label}
      </Text>
      <Text variant="bodyStrong">{valueText}</Text>
      {progress !== undefined ? (
        <View style={{ marginTop: spacing.xxs }}>
          <ProgressBar progress={progress} height={5} />
        </View>
      ) : null}
    </Card>
  );
}
