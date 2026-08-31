import { useCallback, useEffect, useState } from 'react';
import Purchases, { type CustomerInfo } from 'react-native-purchases';
import { subscriptionsRepository } from '@/src/data/repositories/subscriptionsRepository';
import { getCustomerInfo, hasPremiumEntitlement, initPurchases, isRevenueCatConfigured } from './revenuecat';

export function usePremiumStatus(userId: string | undefined) {
  const [isPremium, setIsPremium] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      if (isRevenueCatConfigured) {
        initPurchases(userId);
        const customerInfo = await getCustomerInfo();
        if (customerInfo) {
          setIsPremium(hasPremiumEntitlement(customerInfo));
          return;
        }
      }
      // احتياطي: لا يوجد RevenueCat مُهيّأ بعد — نعتمد على آخر حالة
      // متزامنة في قاعدة البيانات (تُحدَّث فقط عبر webhook من الخادم).
      const row = await subscriptionsRepository.getCurrent(userId);
      setIsPremium(row?.is_premium ?? false);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    // جلب أولي عند التركيب (يستدعي setIsLoading داخل refresh) — نمط
    // قياسي ومختبَر في هذا المشروع، وليس اشتقاق حالة من props.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    if (!isRevenueCatConfigured) return;

    const listener = (customerInfo: CustomerInfo) => setIsPremium(hasPremiumEntitlement(customerInfo));
    Purchases.addCustomerInfoUpdateListener(listener);
    return () => {
      Purchases.removeCustomerInfoUpdateListener(listener);
    };
  }, [refresh]);

  return { isPremium, isLoading, refresh };
}
