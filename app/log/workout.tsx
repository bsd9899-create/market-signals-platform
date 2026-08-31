import { useState } from 'react';
import { KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import { Button, Screen, Text, TextField } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

export default function LogWorkoutScreen() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.session?.user.id);

  const [title, setTitle] = useState('');
  const [duration, setDuration] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    if (!userId) return;
    if (!title.trim()) {
      setError('أدخل اسم التمرين');
      return;
    }
    const minutes = Number(duration);
    if (!Number.isFinite(minutes) || minutes <= 0) {
      setError('أدخل مدة صحيحة بالدقائق');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await dailyLogsRepository.addWorkout(userId, { title: title.trim(), durationMinutes: Math.round(minutes) });
      router.back();
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّر الحفظ، حاول مرة أخرى'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1, gap: spacing.lg }}>
        <Text variant="displayMd">🏋️ التمرين</Text>

        <TextField
          label="اسم التمرين"
          placeholder="مثلاً: صدر وترايسبس"
          value={title}
          onChangeText={setTitle}
          editable={!isSubmitting}
        />

        <TextField
          label="المدة (دقيقة)"
          placeholder="مثلاً 45"
          value={duration}
          onChangeText={setDuration}
          keyboardType="number-pad"
          error={error ?? undefined}
          editable={!isSubmitting}
        />

        <Button label={isSubmitting ? 'جارِ الحفظ...' : 'حفظ'} disabled={isSubmitting} onPress={handleSubmit} />
      </KeyboardAvoidingView>
    </Screen>
  );
}
