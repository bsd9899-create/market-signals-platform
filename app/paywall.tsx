import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useRouter } from 'expo-router';
import type { PurchasesPackage } from 'react-native-purchases';
import { Button, Card, Screen, Text, colors } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';
import { useAuthStore } from '@/src/features/auth/store';
import { getCurrentOfferingPackages, isRevenueCatConfigured, purchasePackage, restorePurchases } from '@/src/subscriptions/revenuecat';
import { usePremiumStatus } from '@/src/subscriptions/usePremiumStatus';
import { getFriendlyErrorMessage } from '@/src/lib/errors';

export default function PaywallScreen() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.session?.user.id);
  const { refresh } = usePremiumStatus(userId);

  const [packages, setPackages] = useState<PurchasesPackage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [busyPackageId, setBusyPackageId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isRevenueCatConfigured) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- لا يوجد جلب بيانات لننتظره هنا أصلاً
      setIsLoading(false);
      return;
    }
    getCurrentOfferingPackages()
      .then(setPackages)
      .catch((e) => setError(getFriendlyErrorMessage(e, 'تعذّر تحميل الخطط')))
      .finally(() => setIsLoading(false));
  }, []);

  async function handlePurchase(pkg: PurchasesPackage) {
    setBusyPackageId(pkg.identifier);
    setError(null);
    try {
      await purchasePackage(pkg);
      await refresh();
      router.back();
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّر إتمام الشراء'));
    } finally {
      setBusyPackageId(null);
    }
  }

  async function handleRestore() {
    setError(null);
    try {
      await restorePurchases();
      await refresh();
      router.back();
    } catch (e) {
      setError(getFriendlyErrorMessage(e, 'تعذّر استعادة المشتريات'));
    }
  }

  return (
    <Screen>
      <View style={{ flex: 1, gap: spacing.lg }}>
        <View>
          <Text variant="displayMd">هِمّة+ ✨</Text>
          <Text variant="body" color="textSecondary" style={{ marginTop: spacing.xs }}>
            دعم الالتزام على المدى الطويل — مزايا إضافية قادمة تباعًا.
          </Text>
        </View>

        {!isRevenueCatConfigured ? (
          <Card variant="soft">
            <Text variant="body" color="textSecondary">
              الاشتراكات غير مفعّلة بعد في هذه النسخة — بانتظار ربط منتجات هِمّة+ من App Store Connect وRevenueCat.
            </Text>
          </Card>
        ) : isLoading ? (
          <ActivityIndicator color={colors.primary} />
        ) : packages.length === 0 ? (
          <Card variant="soft">
            <Text variant="body" color="textSecondary">
              لا توجد خطط متاحة حاليًا.
            </Text>
          </Card>
        ) : (
          <View style={{ gap: spacing.sm }}>
            {packages.map((pkg) => (
              <Card key={pkg.identifier}>
                <Text variant="bodyStrong">{pkg.product.title}</Text>
                <Text variant="title" color="primary" style={{ marginTop: spacing.xxs }}>
                  {pkg.product.priceString}
                </Text>
                <Button
                  label={busyPackageId === pkg.identifier ? 'جارِ الشراء...' : 'اشترك'}
                  style={{ marginTop: spacing.sm }}
                  disabled={busyPackageId !== null}
                  onPress={() => handlePurchase(pkg)}
                />
              </Card>
            ))}
          </View>
        )}

        {error ? (
          <Text variant="caption" color="danger">
            {error}
          </Text>
        ) : null}

        <Button label="استعادة المشتريات" variant="ghost" onPress={handleRestore} />
      </View>
    </Screen>
  );
}
