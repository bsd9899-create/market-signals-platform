import { Pressable, View } from 'react-native';
import type { GoalType } from '@/src/data/database.types';
import { Card, Text, colors } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';

export const GOAL_OPTIONS: { value: GoalType; label: string; emoji: string }[] = [
  { value: 'lose_weight', label: 'التنحيف', emoji: '🔥' },
  { value: 'gain_muscle', label: 'زيادة العضلات', emoji: '💪' },
  { value: 'increase_activity', label: 'زيادة النشاط', emoji: '🏃' },
  { value: 'general_health', label: 'صحة عامة', emoji: '🌿' },
];

type GoalPickerProps = {
  value: GoalType | null;
  onChange: (goal: GoalType) => void;
};

/** اختيار الهدف الأساسي — مكوّن مشترك بين onboarding وتعديل الملف الشخصي. */
export function GoalPicker({ value, onChange }: GoalPickerProps) {
  return (
    <View style={{ gap: spacing.sm }}>
      {GOAL_OPTIONS.map((option) => {
        const selected = value === option.value;
        return (
          <Pressable key={option.value} onPress={() => onChange(option.value)}>
            <Card
              variant={selected ? 'surface' : 'soft'}
              style={selected ? { borderColor: colors.primary, borderWidth: 2 } : undefined}
            >
              <View style={{ flexDirection: 'row-reverse', alignItems: 'center', gap: spacing.sm }}>
                <Text variant="title">{option.emoji}</Text>
                <Text variant="bodyStrong">{option.label}</Text>
              </View>
            </Card>
          </Pressable>
        );
      })}
    </View>
  );
}
