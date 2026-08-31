import { useState } from 'react';
import { KeyboardAvoidingView, Platform } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { teamsRepository } from '@/src/data/repositories/teamsRepository';
import { Button, Screen, Text, TextField } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { toDateKey } from '@/src/lib/date';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

export default function NewChallengeScreen() {
  const router = useRouter();
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  const userId = useAuthStore((s) => s.session?.user.id);

  const [title, setTitle] = useState('');
  const [durationDays, setDurationDays] = useState('7');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    if (!userId || !teamId) return;
    if (!title.trim()) {
      setError('أدخل اسم التحدي');
      return;
    }
    const days = Number(durationDays);
    if (!Number.isFinite(days) || days <= 0) {
      setError('أدخل عدد أيام صحيح');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const start = new Date();
      const end = new Date();
      end.setDate(end.getDate() + Math.round(days) - 1);

      await teamsRepository.createChallenge({
        teamId,
        title: title.trim(),
        startDate: toDateKey(start),
        endDate: toDateKey(end),
        createdBy: userId,
      });
      router.back();
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّر إنشاء التحدي'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1, gap: spacing.lg }}>
        <Text variant="displayMd">تحدٍ جديد 🏆</Text>
        <TextField
          label="اسم التحدي"
          placeholder="مثلاً: أسبوع الالتزام"
          value={title}
          onChangeText={setTitle}
          editable={!isSubmitting}
        />
        <TextField
          label="المدة (أيام)"
          value={durationDays}
          onChangeText={setDurationDays}
          keyboardType="number-pad"
          error={error ?? undefined}
          editable={!isSubmitting}
        />
        <Button label={isSubmitting ? 'جارِ الإنشاء...' : 'إنشاء التحدي'} disabled={isSubmitting} onPress={handleSubmit} />
      </KeyboardAvoidingView>
    </Screen>
  );
}
