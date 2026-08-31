import { Link } from 'expo-router';
import { View } from 'react-native';
import { Screen, Text } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';

export default function NotFoundScreen() {
  return (
    <Screen>
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.sm }}>
        <Text variant="title">الصفحة غير موجودة</Text>
        <Link href="/">
          <Text variant="bodyStrong" color="primary">
            الرجوع إلى اليوم
          </Text>
        </Link>
      </View>
    </Screen>
  );
}
