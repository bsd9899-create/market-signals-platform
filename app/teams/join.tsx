import { useState } from 'react';
import { KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { teamsRepository } from '@/src/data/repositories/teamsRepository';
import { Button, Screen, Text, TextField } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

export default function JoinTeamScreen() {
  const router = useRouter();

  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    if (!code.trim()) {
      setError('أدخل كود الدعوة');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await teamsRepository.joinByCode(code.trim());
      router.back();
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'كود الدعوة غير صحيح'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1, gap: spacing.lg }}>
        <Text variant="displayMd">انضم لفريق 🔑</Text>
        <TextField
          label="كود الدعوة"
          placeholder="مثلاً: a1b2c3d4"
          value={code}
          onChangeText={setCode}
          autoCapitalize="none"
          error={error ?? undefined}
          editable={!isSubmitting}
        />
        <Button label={isSubmitting ? 'جارِ الانضمام...' : 'انضمام'} disabled={isSubmitting} onPress={handleSubmit} />
      </KeyboardAvoidingView>
    </Screen>
  );
}
