import { Screen, Text } from '@/src/design-system';

export default function ProfileScreen() {
  return (
    <Screen>
      <Text variant="title">حسابي</Text>
      <Text variant="body" color="textSecondary" style={{ marginTop: 8 }}>
        الحساب، الاشتراك، وإعدادات الخصوصية تُبنى في المراحل القادمة.
      </Text>
    </Screen>
  );
}
