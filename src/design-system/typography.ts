/**
 * الخط الأساسي لهِمّة: Tajawal — خط عربي عصري دافئ ومريح للقراءة،
 * يناسب إحساس الشعار (بساطة + دفء) دون تقليد شكل الكاليغرافي الخاص
 * بالعلامة نفسها (المحفوظ للشعار فقط).
 */
export const fontFamily = {
  regular: 'Tajawal_400Regular',
  medium: 'Tajawal_500Medium',
  bold: 'Tajawal_700Bold',
  extraBold: 'Tajawal_800ExtraBold',
} as const;

type TypeStyle = {
  fontFamily: string;
  fontSize: number;
  lineHeight: number;
};

export const typography = {
  displayLg: { fontFamily: fontFamily.extraBold, fontSize: 32, lineHeight: 40 },
  displayMd: { fontFamily: fontFamily.bold, fontSize: 26, lineHeight: 34 },
  title: { fontFamily: fontFamily.bold, fontSize: 20, lineHeight: 28 },
  subtitle: { fontFamily: fontFamily.medium, fontSize: 17, lineHeight: 24 },
  body: { fontFamily: fontFamily.regular, fontSize: 15, lineHeight: 22 },
  bodyStrong: { fontFamily: fontFamily.medium, fontSize: 15, lineHeight: 22 },
  caption: { fontFamily: fontFamily.regular, fontSize: 13, lineHeight: 18 },
  captionStrong: { fontFamily: fontFamily.medium, fontSize: 13, lineHeight: 18 },
  overline: { fontFamily: fontFamily.bold, fontSize: 12, lineHeight: 16 },
} satisfies Record<string, TypeStyle>;

export type TypographyToken = keyof typeof typography;
