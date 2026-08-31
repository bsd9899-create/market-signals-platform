import { TextInput, View, type TextInputProps } from 'react-native';
import { colors } from '../colors';
import { radius, spacing } from '../spacing';
import { fontFamily } from '../typography';
import { Text } from './Text';

type TextFieldProps = TextInputProps & {
  label?: string;
  error?: string;
};

/** حقل إدخال نصي موحّد — RTL افتراضيًا، مع تسمية ورسالة خطأ اختياريتين. */
export function TextField({ label, error, style, ...rest }: TextFieldProps) {
  return (
    <View style={{ gap: spacing.xxs }}>
      {label ? (
        <Text variant="captionStrong" color="textSecondary">
          {label}
        </Text>
      ) : null}
      <TextInput
        placeholderTextColor={colors.textSecondary}
        textAlign="right"
        style={[
          {
            fontFamily: fontFamily.regular,
            fontSize: 15,
            color: colors.textPrimary,
            backgroundColor: colors.surfaceAlt,
            borderRadius: radius.md,
            paddingHorizontal: spacing.md,
            paddingVertical: spacing.sm,
            borderWidth: 1,
            borderColor: error ? colors.danger : 'transparent',
            writingDirection: 'rtl',
          },
          style,
        ]}
        {...rest}
      />
      {error ? (
        <Text variant="caption" color="danger">
          {error}
        </Text>
      ) : null}
    </View>
  );
}
