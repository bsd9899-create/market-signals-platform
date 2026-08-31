import { useEffect, useState } from 'react';
import { Animated, StyleSheet, View, type ViewStyle } from 'react-native';
import { palette } from '../colors';
import { radius } from '../spacing';

type SkeletonProps = {
  width?: number | `${number}%`;
  height?: number;
  style?: ViewStyle;
};

/** كتلة نابضة مكان محتوى قيد التحميل — أهدأ من دوّارة تحميل في شاشات فيها بنية بطاقات واضحة. */
export function Skeleton({ width = '100%', height = 16, style }: SkeletonProps) {
  // useState بدل useRef.current — قراءة .current أثناء الرندر تحديدًا
  // ما يحذّر منه react-hooks/refs الجديد، رغم أن Animated.Value نفسه
  // كائن قابل للتحوّل (mutable) بطبعه.
  const [opacity] = useState(() => new Animated.Value(0.5));

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 1, duration: 700, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.5, duration: 700, useNativeDriver: true }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={[styles.base, { width, height, opacity }, style]}
      accessible={false}
      importantForAccessibility="no"
    />
  );
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: palette.neutral200,
    borderRadius: radius.sm,
  },
});

/** هيكل جاهز لبطاقة شاشة اليوم أثناء التحميل الأول — يطابق تخطيطها الفعلي. */
export function TodaySkeleton() {
  return (
    <View style={{ gap: 16, paddingTop: 16 }}>
      <Skeleton width={180} height={30} />
      <Skeleton height={90} />
      <Skeleton height={150} />
      <View style={{ flexDirection: 'row-reverse', gap: 12 }}>
        <Skeleton height={90} style={{ flex: 1 }} />
        <Skeleton height={90} style={{ flex: 1 }} />
      </View>
      <View style={{ flexDirection: 'row-reverse', gap: 12 }}>
        <Skeleton height={90} style={{ flex: 1 }} />
        <Skeleton height={90} style={{ flex: 1 }} />
      </View>
      <Skeleton height={110} />
    </View>
  );
}

/** هيكل جاهز لشاشة تقدمي أثناء التحميل الأول. */
export function ProgressSkeleton() {
  return (
    <View style={{ gap: 16, paddingTop: 16 }}>
      <Skeleton width={140} height={30} />
      <Skeleton height={160} />
      <View style={{ flexDirection: 'row-reverse', gap: 12 }}>
        <Skeleton height={80} style={{ flex: 1 }} />
        <Skeleton height={80} style={{ flex: 1 }} />
      </View>
      <Skeleton height={80} />
      <Skeleton height={140} />
    </View>
  );
}

/** هيكل جاهز لشاشة الفرق أثناء التحميل الأول. */
export function TeamsSkeleton() {
  return (
    <View style={{ gap: 16, paddingTop: 16 }}>
      <Skeleton width={160} height={30} />
      <Skeleton height={130} />
      <Skeleton height={160} />
      <Skeleton height={100} />
    </View>
  );
}
