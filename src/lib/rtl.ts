import { I18nManager } from 'react-native';
import RNRestart from 'react-native-restart';

/**
 * هِمّة تطبيق عربي RTL فقط. نفرض RTL على مستوى النظام مرة واحدة عند أول
 * تشغيل، ثم نعيد تشغيل الجافاسكريبت ليطبّق React Native التخطيط الصحيح
 * (تبديل الاتجاه يتطلب إعادة تشغيل، وهذا سلوك موثّق في React Native).
 *
 * @returns true إذا أعاد التشغيل (يجب على الشاشة المستدعية عدم عرض شيء بعدها)
 */
export function ensureRTL(): boolean {
  if (I18nManager.isRTL) {
    return false;
  }
  I18nManager.allowRTL(true);
  I18nManager.forceRTL(true);
  RNRestart.restart();
  return true;
}
