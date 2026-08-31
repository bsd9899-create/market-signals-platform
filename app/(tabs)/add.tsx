import { Redirect } from 'expo-router';

/**
 * لا يُعرض هذا التبويب أبدًا — الضغط عليه يُفتح كـ Modal عبر
 * quick-add بدل التنقل الطبيعي (راجع listeners.tabPress في _layout).
 * هذا الملف موجود فقط لأن Expo Router يتطلب ملف مسار لكل Tabs.Screen.
 */
export default function AddTabPlaceholder() {
  return <Redirect href="/" />;
}
