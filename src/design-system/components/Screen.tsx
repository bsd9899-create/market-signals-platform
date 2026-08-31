import type { PropsWithChildren } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { SafeAreaView, type Edge } from 'react-native-safe-area-context';
import { colors } from '../colors';
import { spacing } from '../spacing';

type ScreenProps = PropsWithChildren<{
  edges?: Edge[];
  padded?: boolean;
  style?: ViewStyle;
}>;

/** حاوية موحّدة لكل الشاشات: خلفية كريمية + احترام مناطق الجهاز الآمنة. */
export function Screen({ children, edges = ['top', 'bottom'], padded = true, style }: ScreenProps) {
  return (
    <SafeAreaView edges={edges} style={styles.safeArea}>
      <View style={[padded && styles.padded, style]}>{children}</View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  padded: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
});
