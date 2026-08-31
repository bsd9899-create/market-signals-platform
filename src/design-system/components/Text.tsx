import { Text as RNText, type TextProps as RNTextProps } from 'react-native';
import { colors, type ColorToken } from '../colors';
import { typography, type TypographyToken } from '../typography';

export type TextProps = RNTextProps & {
  variant?: TypographyToken;
  color?: ColorToken;
};

/**
 * مكوّن النص الأساسي في التطبيق — عربي RTL افتراضيًا، بخط Tajawal
 * وأحجام موحّدة من الـ Design System. استخدم هذا بدل <Text> من
 * react-native مباشرة في كل الشاشات.
 */
export function Text({ variant = 'body', color = 'textPrimary', style, ...rest }: TextProps) {
  return (
    <RNText
      style={[
        typography[variant],
        { color: colors[color], textAlign: 'right', writingDirection: 'rtl' },
        style,
      ]}
      {...rest}
    />
  );
}
