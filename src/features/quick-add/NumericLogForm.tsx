import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Button, Screen, Text, TextField, colors } from '@/src/design-system';
import { radius, spacing } from '@/src/design-system/spacing';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

type NumericLogFormProps = {
  title: string;
  emoji: string;
  unitLabel: string;
  placeholder: string;
  /** أزرار قيم جاهزة (مثل 250/500/750 للماء) — اختيارية. */
  presets?: number[];
  /** يسمح بفواصل عشرية (الوزن/النوم) أم أعداد صحيحة فقط (الخطوات). */
  allowDecimal?: boolean;
  onSubmit: (value: number) => Promise<void>;
};

/**
 * نموذج إدخال رقمي موحّد — يغطي الماء والوزن والخطوات والنوم بنفس
 * الشكل، فرقها فقط الوحدة والقيم الجاهزة والسماح بالكسور.
 */
export function NumericLogForm({
  title,
  emoji,
  unitLabel,
  placeholder,
  presets,
  allowDecimal = false,
  onSubmit,
}: NumericLogFormProps) {
  const router = useRouter();
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(raw: number) {
    if (!Number.isFinite(raw) || raw <= 0) {
      setError('أدخل رقمًا صحيحًا أكبر من صفر');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit(raw);
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
        <Text variant="displayMd">
          {emoji} {title}
        </Text>

        {presets && presets.length > 0 ? (
          <View style={{ flexDirection: 'row-reverse', gap: spacing.sm }}>
            {presets.map((preset) => (
              <Pressable
                key={preset}
                disabled={isSubmitting}
                onPress={() => submit(preset)}
                style={{
                  flex: 1,
                  paddingVertical: spacing.md,
                  borderRadius: radius.md,
                  backgroundColor: colors.surfaceAlt,
                  alignItems: 'center',
                }}
              >
                <Text variant="bodyStrong">{preset}</Text>
              </Pressable>
            ))}
          </View>
        ) : null}

        <TextField
          label={`أو أدخل قيمة مخصّصة (${unitLabel})`}
          placeholder={placeholder}
          value={value}
          onChangeText={setValue}
          error={error ?? undefined}
          keyboardType={allowDecimal ? 'decimal-pad' : 'number-pad'}
          editable={!isSubmitting}
        />

        <Button
          label={isSubmitting ? 'جارِ الحفظ...' : 'حفظ'}
          disabled={isSubmitting}
          onPress={() => submit(Number(value.replace(',', '.')))}
        />
      </KeyboardAvoidingView>
    </Screen>
  );
}
