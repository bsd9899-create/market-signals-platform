import type { Href } from 'expo-router';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Screen, Text, colors } from '@/src/design-system';
import { radius, spacing } from '@/src/design-system/spacing';

const QUICK_ADD_OPTIONS: { emoji: string; label: string; href: Href }[] = [
  { emoji: '💧', label: 'ماء', href: '/log/water' },
  { emoji: '⚖️', label: 'وزن', href: '/log/weight' },
  { emoji: '👟', label: 'خطوات', href: '/log/steps' },
  { emoji: '🍽️', label: 'تغذية', href: '/log/nutrition' },
  { emoji: '🏋️', label: 'تمرين', href: '/log/workout' },
  { emoji: '💤', label: 'نوم', href: '/log/sleep' },
];

export default function QuickAddModal() {
  const router = useRouter();

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <Text variant="title">إضافة سريعة</Text>

        <View style={{ flexDirection: 'row-reverse', flexWrap: 'wrap', gap: spacing.sm }}>
          {QUICK_ADD_OPTIONS.map((option) => (
            <Pressable
              key={option.label}
              onPress={() => router.push(option.href)}
              style={{
                width: '30%',
                aspectRatio: 1,
                borderRadius: radius.lg,
                backgroundColor: colors.surfaceAlt,
                alignItems: 'center',
                justifyContent: 'center',
                gap: spacing.xxs,
              }}
            >
              <Text variant="displayMd">{option.emoji}</Text>
              <Text variant="captionStrong">{option.label}</Text>
            </Pressable>
          ))}
        </View>
      </View>
    </Screen>
  );
}
