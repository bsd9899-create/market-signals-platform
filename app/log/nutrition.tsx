import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import { Button, Screen, Text, TextField, colors } from '@/src/design-system';
import { radius, spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

const MEAL_TYPES: { value: 'breakfast' | 'lunch' | 'dinner' | 'snack'; label: string }[] = [
  { value: 'breakfast', label: 'فطور' },
  { value: 'lunch', label: 'غداء' },
  { value: 'dinner', label: 'عشاء' },
  { value: 'snack', label: 'وجبة خفيفة' },
];

export default function LogNutritionScreen() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.session?.user.id);

  const [mealType, setMealType] = useState<(typeof MEAL_TYPES)[number]['value']>('lunch');
  const [description, setDescription] = useState('');
  const [calories, setCalories] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    if (!userId) return;
    if (!description.trim()) {
      setError('صف الوجبة باختصار');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await dailyLogsRepository.addNutritionLog(userId, {
        mealType,
        description: description.trim(),
        calories: calories ? Number(calories) : undefined,
      });
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
        <Text variant="displayMd">🍽️ التغذية</Text>

        <View style={{ flexDirection: 'row-reverse', flexWrap: 'wrap', gap: spacing.sm }}>
          {MEAL_TYPES.map((meal) => {
            const selected = mealType === meal.value;
            return (
              <Pressable
                key={meal.value}
                onPress={() => setMealType(meal.value)}
                style={{
                  paddingVertical: spacing.xs,
                  paddingHorizontal: spacing.md,
                  borderRadius: radius.pill,
                  backgroundColor: selected ? colors.primary : colors.surfaceAlt,
                }}
              >
                <Text variant="captionStrong" color={selected ? 'onPrimary' : 'textPrimary'}>
                  {meal.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <TextField
          label="وش أكلت؟"
          placeholder="مثلاً: صدر دجاج مع أرز"
          value={description}
          onChangeText={setDescription}
          editable={!isSubmitting}
        />

        <TextField
          label="السعرات (اختياري)"
          placeholder="مثلاً 450"
          value={calories}
          onChangeText={setCalories}
          keyboardType="number-pad"
          error={error ?? undefined}
          editable={!isSubmitting}
        />

        <Button label={isSubmitting ? 'جارِ الحفظ...' : 'حفظ'} disabled={isSubmitting} onPress={handleSubmit} />
      </KeyboardAvoidingView>
    </Screen>
  );
}
