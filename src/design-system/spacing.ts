/** مقياس تباعد موحّد (شبكة 4px) — يمنع القيم العشوائية المتفرقة في الشاشات. */
export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 20,
  xl: 24,
  xxl: 32,
  xxxl: 40,
} as const;

export type SpacingToken = keyof typeof spacing;

/** نصف قطر الحواف — دائري ودافئ بدل الزوايا الحادة. */
export const radius = {
  sm: 10,
  md: 16,
  lg: 24,
  pill: 999,
} as const;

export type RadiusToken = keyof typeof radius;
