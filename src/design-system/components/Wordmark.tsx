import { Text } from './Text';

/**
 * علامة نصية مؤقتة لاسم "هِمّة" بخط Tajawal الغامق ولون العلامة، إلى
 * حين توفّر ملف الشعار الرسمي الفعلي (راجع assets/branding/README.md)
 * لاستبدالها بصورة حقيقية.
 */
export function Wordmark() {
  return (
    <Text variant="displayLg" color="primary" style={{ textAlign: 'center' }}>
      هِمّة
    </Text>
  );
}
