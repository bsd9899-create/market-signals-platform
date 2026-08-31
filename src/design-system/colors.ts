/**
 * ألوان هِمّة — مستخرجة من الهوية البصرية للشعار الرسمي.
 *
 * القاعدة: التيل الداكن هو اللون الأساسي (نص، أيقونات، عناصر تفاعلية)،
 * والذهبي Accent محدود الاستخدام (تمييز/إنجاز/CTA رئيسي فقط) تمامًا
 * كما يظهر في الشعار (الذهبي فقط في أيقونة الدمبل، وليس كخلفية كبيرة).
 */
export const palette = {
  teal900: '#0F2E2A',
  teal700: '#173F39',
  teal600: '#1F4D45',
  teal500: '#2F6259',
  teal100: '#DCE9E5',

  gold500: '#C79A56',
  gold300: '#E3C793',
  gold100: '#F3E7CE',

  cream50: '#FBF3EA',
  cream100: '#F5E9D8',
  white: '#FFFFFF',

  neutral700: '#4A4E4B',
  neutral500: '#6B6F6D',
  neutral300: '#DAD2C4',
  neutral200: '#EDE5D8',

  success: '#3F8F6B',
  warning: '#D98C3D',
  danger: '#C1503F',
} as const;

export const colors = {
  background: palette.cream50,
  surface: palette.white,
  surfaceAlt: palette.cream100,

  primary: palette.teal700,
  primaryPressed: palette.teal900,
  onPrimary: palette.cream50,

  accent: palette.gold500,
  accentSoft: palette.gold100,
  onAccent: palette.teal900,

  textPrimary: palette.teal900,
  textSecondary: palette.neutral500,
  textOnDark: palette.cream50,

  border: palette.neutral300,
  divider: palette.neutral200,

  success: palette.success,
  warning: palette.warning,
  danger: palette.danger,
} as const;

export type ColorToken = keyof typeof colors;
