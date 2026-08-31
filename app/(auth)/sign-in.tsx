import { useState } from 'react';
import { KeyboardAvoidingView, Platform, View } from 'react-native';
import { useRouter } from 'expo-router';
import { z } from 'zod';
import { Button, Screen, Text, TextField, Wordmark } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { requestEmailOtp } from '@/src/features/auth/api';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

const emailSchema = z.string().trim().email('أدخل بريدًا إلكترونيًا صحيحًا');

export default function SignInScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    const result = emailSchema.safeParse(email);
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? 'بريد إلكتروني غير صحيح');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await requestEmailOtp(result.data);
      router.push({ pathname: '/(auth)/verify', params: { email: result.data } });
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّر إرسال رمز الدخول، حاول مرة أخرى'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1, justifyContent: 'center', gap: spacing.xl }}
      >
        <Wordmark />
        <View style={{ gap: spacing.xs }}>
          <Text variant="title" style={{ textAlign: 'center' }}>
            هلا فيك 👋
          </Text>
          <Text variant="body" color="textSecondary" style={{ textAlign: 'center' }}>
            أدخل بريدك الإلكتروني وسنرسل لك رمز دخول سريع — بدون كلمة مرور
          </Text>
        </View>

        <View style={{ gap: spacing.sm }}>
          <TextField
            placeholder="بريدك الإلكتروني"
            value={email}
            onChangeText={setEmail}
            error={error ?? undefined}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
            textContentType="emailAddress"
            editable={!isSubmitting}
          />
          <Button
            label={isSubmitting ? 'جارِ الإرسال...' : 'إرسال رمز الدخول'}
            onPress={handleSubmit}
            disabled={isSubmitting}
          />
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}
