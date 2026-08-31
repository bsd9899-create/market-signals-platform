import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Button, Screen, Text } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';

/**
 * الإضافة السريعة (ماء/وزن/خطوات/تغذية/تمرين/نوم) — هيكل المرحلة 1 فقط،
 * النماذج الفعلية المرتبطة بقاعدة البيانات تُبنى في المرحلة 5.
 */
export default function QuickAddModal() {
  const router = useRouter();
  return (
    <Screen>
      <View style={{ gap: spacing.md }}>
        <Text variant="title">إضافة سريعة</Text>
        <Text variant="body" color="textSecondary">
          خيارات الإضافة (ماء، وزن، خطوات، تغذية، تمرين، نوم) تُبنى في المرحلة 5.
        </Text>
        <Button label="إغلاق" variant="secondary" onPress={() => router.back()} />
      </View>
    </Screen>
  );
}
