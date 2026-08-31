import type { PropsWithChildren } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { colors, palette } from '../colors';
import { radius, spacing } from '../spacing';

type CardProps = PropsWithChildren<{
  variant?: 'surface' | 'soft';
  style?: ViewStyle;
}>;

/** بطاقة أساسية بزوايا دائرية دافئة — تُستخدم لكل الأقسام في شاشة "اليوم" وغيرها. */
export function Card({ children, variant = 'surface', style }: CardProps) {
  return <View style={[styles.base, variant === 'soft' && styles.soft, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.divider,
    // ظل خفيف جدًا — إحساس "مرفوعة قليلاً" دافئ بدل البطاقات المسطّحة تمامًا.
    shadowColor: palette.teal900,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 1,
  },
  soft: {
    backgroundColor: colors.surfaceAlt,
    borderColor: 'transparent',
    shadowOpacity: 0,
    elevation: 0,
  },
});
