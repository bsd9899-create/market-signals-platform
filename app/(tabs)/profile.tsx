import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Button, Screen, Text } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { signOut } from '@/src/features/auth/api';
import { useProfileStore } from '@/src/features/auth/profileStore';

export default function ProfileScreen() {
  const router = useRouter();
  const profile = useProfileStore((s) => s.profile);

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <View>
          <Text variant="title">{profile?.display_name ?? 'حسابي'}</Text>
          <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xxs }}>
            الاشتراك، وإعدادات الخصوصية تُبنى في المراحل القادمة.
          </Text>
        </View>
        <Button label="رفيق هِمّة 🤝" variant="secondary" onPress={() => router.push('/accountability')} />
        <Button label="هِمّة+ ✨" variant="secondary" onPress={() => router.push('/paywall')} />
        <Button label="تسجيل الخروج" variant="ghost" onPress={() => signOut()} />
      </View>
    </Screen>
  );
}
