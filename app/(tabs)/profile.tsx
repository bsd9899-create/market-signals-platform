import { useState } from 'react';
import { Alert, Linking, View } from 'react-native';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
import { Button, Card, Screen, Text } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { deleteAccount, signOut } from '@/src/features/auth/api';
import { useAuthStore } from '@/src/features/auth/store';
import { useProfileStore } from '@/src/features/auth/profileStore';
import { useHealthSync } from '@/src/integrations/health/useHealthSync';
import { getFriendlyErrorMessage } from '@/src/lib/errors';
import { GOAL_OPTIONS } from '@/src/features/profile/GoalPicker';

const PRIVACY_POLICY_URL = 'https://github.com/bsd9899-create/market-signals-platform/blob/main/docs/PRIVACY_POLICY.md';

export default function ProfileScreen() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.session?.user.id);
  const profile = useProfileStore((s) => s.profile);
  const { isAvailable, isSyncing, error, syncToday } = useHealthSync(userId);
  const [isDeleting, setIsDeleting] = useState(false);

  function confirmDeleteAccount() {
    Alert.alert(
      'حذف الحساب نهائيًا',
      'سيُحذف حسابك وكل بياناتك (السجلات، الفرق، الاشتراك) نهائيًا ولا يمكن التراجع. متأكد؟',
      [
        { text: 'إلغاء', style: 'cancel' },
        {
          text: 'حذف نهائي',
          style: 'destructive',
          onPress: async () => {
            setIsDeleting(true);
            try {
              await deleteAccount();
            } catch (e) {
              Alert.alert('تعذّر حذف الحساب', getFriendlyErrorMessage(e, 'حاول مرة أخرى لاحقًا'));
            } finally {
              setIsDeleting(false);
            }
          },
        },
      ]
    );
  }

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <View>
          <Text variant="title">{profile?.display_name ?? 'حسابي'}</Text>
          <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xxs }}>
            {profile?.goal_type
              ? `هدفك: ${GOAL_OPTIONS.find((g) => g.value === profile.goal_type)?.label ?? ''}`
              : 'أكمل هدفك من تعديل ملفي'}
          </Text>
        </View>

        <Button label="تعديل ملفي" variant="secondary" onPress={() => router.push('/profile-edit')} />
        <Button label="رفيق هِمّة 🤝" variant="secondary" onPress={() => router.push('/accountability')} />
        <Button label="هِمّة+ ✨" variant="secondary" onPress={() => router.push('/paywall')} />

        <Card variant="soft">
          <Text variant="overline" color="textSecondary">
            Apple Health
          </Text>
          {isAvailable ? (
            <>
              <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xs }}>
                مزامنة الخطوات والوزن والنوم والتمارين من تطبيق الصحة.
              </Text>
              <Button
                label={isSyncing ? 'جارِ المزامنة...' : 'مزامنة الآن'}
                variant="secondary"
                style={{ marginTop: spacing.sm }}
                disabled={isSyncing}
                onPress={syncToday}
              />
              {error ? (
                <Text variant="caption" color="danger" style={{ marginTop: spacing.xs }}>
                  {error}
                </Text>
              ) : null}
            </>
          ) : (
            <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xs }}>
              غير متاح على هذا الجهاز (يحتاج iPhone حقيقيًا ونسخة Dev Client مبنية بصلاحية HealthKit).
            </Text>
          )}
        </Card>

        <Button
          label="سياسة الخصوصية"
          variant="ghost"
          onPress={() => Linking.openURL(PRIVACY_POLICY_URL).catch(() => {})}
        />
        <Button label="تسجيل الخروج" variant="ghost" onPress={() => signOut()} />
        <Button
          label={isDeleting ? 'جارِ الحذف...' : 'حذف حسابي نهائيًا'}
          variant="ghost"
          disabled={isDeleting}
          onPress={confirmDeleteAccount}
        />

        <Text variant="caption" color="textSecondary" style={{ textAlign: 'center' }}>
          هِمّة — الإصدار {Constants.expoConfig?.version ?? '1.0.0'}
        </Text>
      </View>
    </Screen>
  );
}
