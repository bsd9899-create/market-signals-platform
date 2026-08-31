import { View } from 'react-native';
import { colors, Text } from '@/src/design-system';
import { radius, spacing } from '@/src/design-system/spacing';
import { arabicWeekdayLetter, toDateKey } from '@/src/lib/date';

type WeeklyBarChartProps = {
  history: { date: string; completion_percent: number }[];
  days: number;
};

const BAR_MAX_HEIGHT = 96;

/**
 * رسم بياني بسيط بأعمدة (بدون مكتبة رسوم خارجية) — يملأ الأيام
 * الناقصة من history بصفر حتى لو المستخدم لم يفتح التطبيق فيها.
 */
export function WeeklyBarChart({ history, days }: WeeklyBarChartProps) {
  const byDate = new Map(history.map((h) => [h.date, h.completion_percent]));

  const series = Array.from({ length: days }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (days - 1 - i));
    const dateKey = toDateKey(d);
    return { dateKey, percent: byDate.get(dateKey) ?? 0 };
  });

  return (
    <View style={{ flexDirection: 'row-reverse', alignItems: 'flex-end', gap: spacing.sm, height: BAR_MAX_HEIGHT + 24 }}>
      {series.map((day) => (
        <View key={day.dateKey} style={{ flex: 1, alignItems: 'center', gap: spacing.xxs }}>
          <View
            style={{
              width: '70%',
              height: Math.max(4, (day.percent / 100) * BAR_MAX_HEIGHT),
              backgroundColor: day.percent > 0 ? colors.primary : colors.divider,
              borderRadius: radius.sm,
            }}
          />
          <Text variant="caption" color="textSecondary">
            {arabicWeekdayLetter(day.dateKey)}
          </Text>
        </View>
      ))}
    </View>
  );
}
