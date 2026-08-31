import { colors } from './colors';
import { radius, spacing } from './spacing';
import { typography } from './typography';

export const theme = {
  colors,
  spacing,
  radius,
  typography,
} as const;

export type Theme = typeof theme;

export { colors, spacing, radius, typography };
export { fontFamily } from './typography';
export { palette } from './colors';
