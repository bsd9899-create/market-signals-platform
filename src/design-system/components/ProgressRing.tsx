import { View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { colors } from '../colors';

type ProgressRingProps = {
  /** نسبة من 0 إلى 1 */
  progress: number;
  size?: number;
  strokeWidth?: number;
  trackColor?: string;
  fillColor?: string;
  children?: React.ReactNode;
};

/** حلقة تقدّم دائرية — تُستخدم في "إنجاز اليوم" كعنصر بصري مركزي مميّز. */
export function ProgressRing({
  progress,
  size = 120,
  strokeWidth = 10,
  trackColor = colors.divider,
  fillColor = colors.primary,
  children,
}: ProgressRingProps) {
  const clamped = Math.max(0, Math.min(1, progress));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - clamped);

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={{ position: 'absolute' }}>
        <Circle cx={size / 2} cy={size / 2} r={radius} stroke={trackColor} strokeWidth={strokeWidth} fill="none" />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={fillColor}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          // تدوير -90° عشان تبدأ الحلقة من الأعلى بدل اليمين — نفس
          // الاتجاه بصريًا في RTL وLTR لأن الدائرة متناظرة.
          rotation={-90}
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      {children}
    </View>
  );
}
