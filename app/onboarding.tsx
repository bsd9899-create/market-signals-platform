import { useState } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import type { GoalType } from '@/src/data/database.types';
import { profileRepository } from '@/src/data/repositories/profileRepository';
import { Button, Card, Screen, Text, TextField } from '@/src/design-system';
import { colors } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useProfileStore } from '@/src/features/auth/profileStore';

const GOAL_OPTIONS: { value: GoalType; label: string; emoji: string }[] = [
  { value: 'lose_weight', label: 'التنحيف', emoji: '🔥' },
  { value: 'gain_muscle', label: 'زيادة العضلات', emoji: '💪' },
  { value: 'increase_activity', label: 'زيادة النشاط', emoji: '🏃' },
  { value: 'general_health', label: 'صحة عامة', emoji: '🌿' },
];

export default function OnboardingScreen() {
  const router = useRouter();
  const fetchProfile = useProfileStore((s) => s.fetch);

  const [displayName, setDisplayName] = useState('');
  const [goalType, setGoalType] = useState<GoalType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    if (!displayName.trim()) {
      setError('أدخل اسمك أولًا');
      return;
    }
    if (!goalType) {
      setError('اختر هدفك الأساسي');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await profileRepository.updateCurrent({
        display_name: displayName.trim(),
        goal_type: goalType,
        onboarding_completed_at: new Date().toISOString(),
      });
      await fetchProfile();
      router.replace('/(tabs)');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'تعذّر الحفظ، حاول مرة أخرى');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ gap: spacing.xl, paddingVertical: spacing.xl }}>
        <View style={{ gap: spacing.xs }}>
          <Text variant="displayMd">هلا فيك في هِمّة 🌿</Text>
          <Text variant="body" color="textSecondary">
            خلنا نتعرف عليك بسرعة قبل ما نبدأ
          </Text>
        </View>

        <TextField label="وش نناديك؟" placeholder="اسمك" value={displayName} onChangeText={setDisplayName} />

        <View style={{ gap: spacing.sm }}>
          <Text variant="captionStrong" color="textSecondary">
            وش هدفك الأساسي؟
          </Text>
          <View style={{ gap: spacing.sm }}>
            {GOAL_OPTIONS.map((option) => {
              const selected = goalType === option.value;
              return (
                <Pressable key={option.value} onPress={() => setGoalType(option.value)}>
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
        </View>

        {error ? (
          <Text variant="caption" color="danger">
            {error}
          </Text>
        ) : null}

        <Button label={isSubmitting ? 'جارِ الحفظ...' : 'ابدأ رحلتك'} onPress={handleSubmit} disabled={isSubmitting} />
      </ScrollView>
    </Screen>
  );
}
