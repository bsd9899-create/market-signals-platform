import { useEffect, useState } from 'react';
import { KeyboardAvoidingView, Platform, View } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { Button, Screen, Text, TextField } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { requestEmailOtp, verifyEmailOtp } from '@/src/features/auth/api';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

const RESEND_COOLDOWN_SECONDS = 30;

export default function VerifyScreen() {
  const { email } = useLocalSearchParams<{ email: string }>();
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  async function handleVerify() {
    if (!email) return;
    if (code.trim().length < 6) {
      setError('رمز الدخول مكوّن من 6 أرقام');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      // نجاح التحقق يحدّث الجلسة تلقائيًا عبر onAuthStateChange في
      // src/features/auth/store.ts، وحارس التنقل في app/_layout.tsx
      // يتولى الانتقال للمكان الصحيح (Onboarding أو الرئيسية).
      await verifyEmailOtp(email, code.trim());
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'رمز غير صحيح، حاول مرة أخرى'));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResend() {
    if (!email || cooldown > 0) return;
    setIsResending(true);
    setError(null);
    try {
      await requestEmailOtp(email);
      setCooldown(RESEND_COOLDOWN_SECONDS);
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّر إعادة الإرسال'));
    } finally {
      setIsResending(false);
    }
  }

  return (
    <Screen>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1, justifyContent: 'center', gap: spacing.xl }}
      >
        <View style={{ gap: spacing.xs }}>
          <Text variant="title" style={{ textAlign: 'center' }}>
            تحقق من بريدك
          </Text>
          <Text variant="body" color="textSecondary" style={{ textAlign: 'center' }}>
            أرسلنا رمز دخول إلى {email}
          </Text>
        </View>

        <View style={{ gap: spacing.sm }}>
          <TextField
            placeholder="رمز الدخول"
            value={code}
            onChangeText={setCode}
            error={error ?? undefined}
            keyboardType="number-pad"
            maxLength={6}
            editable={!isSubmitting}
            style={{ textAlign: 'center', letterSpacing: 8 }}
          />
          <Button
            label={isSubmitting ? 'جارِ التحقق...' : 'تأكيد'}
            onPress={handleVerify}
            disabled={isSubmitting}
          />
          <Button
            label={isResending ? 'جارِ الإرسال...' : cooldown > 0 ? `أعد الإرسال بعد ${cooldown} ثانية` : 'إعادة إرسال الرمز'}
            variant="ghost"
            onPress={handleResend}
            disabled={isResending || cooldown > 0}
          />
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}
