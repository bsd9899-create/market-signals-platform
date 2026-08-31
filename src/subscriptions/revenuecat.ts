import Purchases, { LOG_LEVEL, type CustomerInfo, type PurchasesPackage } from 'react-native-purchases';
import { Platform } from 'react-native';
import { env } from '@/src/lib/env';

/**
 * معرّف الاستحقاق (Entitlement) في لوحة تحكم RevenueCat — يُضبط هناك
 * وقت إنشاء المنتجات، وليس اختراعًا من الكود. لو غُيّر الاسم في
 * RevenueCat يجب تحديثه هنا أيضًا.
 */
export const PREMIUM_ENTITLEMENT_ID = 'premium';

let isConfigured = false;

/** لا شيء يحدث بدون مفتاح RevenueCat حقيقي — يمنع محاولة إعداد SDK بمفتاح وهمي. */
export const isRevenueCatConfigured = Boolean(env.EXPO_PUBLIC_REVENUECAT_IOS_API_KEY);

export function initPurchases(appUserID: string) {
  if (isConfigured || !isRevenueCatConfigured || Platform.OS !== 'ios') return;

  Purchases.setLogLevel(LOG_LEVEL.WARN);
  Purchases.configure({ apiKey: env.EXPO_PUBLIC_REVENUECAT_IOS_API_KEY!, appUserID });
  isConfigured = true;
}

export function hasPremiumEntitlement(customerInfo: CustomerInfo): boolean {
  return customerInfo.entitlements.active[PREMIUM_ENTITLEMENT_ID] !== undefined;
}

export async function getCurrentOfferingPackages(): Promise<PurchasesPackage[]> {
  if (!isConfigured) return [];
  const offerings = await Purchases.getOfferings();
  return offerings.current?.availablePackages ?? [];
}

export async function purchasePackage(pkg: PurchasesPackage): Promise<CustomerInfo> {
  const { customerInfo } = await Purchases.purchasePackage(pkg);
  return customerInfo;
}

export async function restorePurchases(): Promise<CustomerInfo> {
  return Purchases.restorePurchases();
}

export async function getCustomerInfo(): Promise<CustomerInfo | null> {
  if (!isConfigured) return null;
  return Purchases.getCustomerInfo();
}
