import { Screen, Text } from '@/src/design-system';

export default function ProgressScreen() {
  return (
    <Screen>
      <Text variant="title">تقدمي</Text>
      <Text variant="body" color="textSecondary" style={{ marginTop: 8 }}>
        الإحصائيات والرسوم البيانية تُبنى في المرحلة 6.
      </Text>
    </Screen>
  );
}
