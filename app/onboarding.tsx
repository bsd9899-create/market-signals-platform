import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import type { GoalType } from '@/src/data/database.types';
import { profileRepository } from '@/src/data/repositories/profileRepository';
import { Button, Screen, Text, TextField } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useProfileStore } from '@/src/features/auth/profileStore';
import { GoalPicker } from '@/src/features/profile/GoalPicker';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

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
      setError(getFriendlyErrorMessage(e, 'تعذّر الحفظ، حاول مرة أخرى'));
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
          <GoalPicker value={goalType} onChange={setGoalType} />
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
