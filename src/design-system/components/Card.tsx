import type { PropsWithChildren } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { colors } from '../colors';
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
  },
  soft: {
    backgroundColor: colors.surfaceAlt,
    borderColor: 'transparent',
  },
});
