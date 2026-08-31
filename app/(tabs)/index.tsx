import { ScrollView, View } from 'react-native';
import { Card, Screen, Text } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';

/**
 * شاشة "اليوم" — أهم شاشة في التطبيق. هذا هيكل المرحلة 1 فقط (تخطيط +
 * تصميم)، منطق قرار اليوم/الإنجاز الفعلي والربط بقاعدة البيانات يُبنى
 * في المرحلة 4.
 */
export default function TodayScreen() {
  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={{ gap: spacing.md, paddingBottom: spacing.xxxl }} showsVerticalScrollIndicator={false}>
        <View style={{ marginTop: spacing.md }}>
          <Text variant="displayMd">هلا بدر 👋</Text>
        </View>

        <Card variant="soft">
          <Text variant="overline" color="textSecondary">
            قرار اليوم
          </Text>
          <Text variant="title" style={{ marginTop: spacing.xxs }}>
            اليوم ركز على التمرين 🔥
          </Text>
        </Card>

        <Card>
          <Text variant="caption" color="textSecondary">
            إنجاز اليوم
          </Text>
          <Text variant="displayLg" color="primary" style={{ marginTop: spacing.xxs }}>
            —
          </Text>
        </Card>
      </ScrollView>
    </Screen>
  );
}
