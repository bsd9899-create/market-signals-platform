import { useEffect, useState } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import {
  useFonts,
  Tajawal_400Regular,
  Tajawal_500Medium,
  Tajawal_700Bold,
  Tajawal_800ExtraBold,
} from '@expo-google-fonts/tajawal';
import { colors } from '@/src/design-system';
import { ensureRTL } from '@/src/lib/rtl';
import { useAuthGate } from '@/src/features/auth/useAuthGate';

SplashScreen.preventAutoHideAsync().catch(() => {
  // لا شيء نفعله لو فشل — بعض بيئات التشغيل (Web) لا تدعمه.
});

export default function RootLayout() {
  const [isRestarting, setIsRestarting] = useState(false);
  const [fontsLoaded, fontsError] = useFonts({
    Tajawal_400Regular,
    Tajawal_500Medium,
    Tajawal_700Bold,
    Tajawal_800ExtraBold,
  });

  useEffect(() => {
    // فحص لمرة واحدة فقط عند الإقلاع لحالة نظام خارجية (I18nManager)
    // وليس اشتقاق حالة من props/state — إعادة الهيكلة لتفادي هذا التحذير
    // ستضيف تعقيدًا (microtask وهمي) بلا أي فائدة فعلية هنا.
    if (ensureRTL()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsRestarting(true);
    }
  }, []);

  const { isReady: isAuthReady } = useAuthGate();

  useEffect(() => {
    if ((fontsLoaded || fontsError) && !isRestarting && isAuthReady) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [fontsLoaded, fontsError, isRestarting, isAuthReady]);

  if (isRestarting || (!fontsLoaded && !fontsError) || !isAuthReady) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }}>
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="onboarding" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="quick-add" options={{ presentation: 'modal' }} />
          <Stack.Screen name="log/water" options={{ presentation: 'modal' }} />
          <Stack.Screen name="log/weight" options={{ presentation: 'modal' }} />
          <Stack.Screen name="log/steps" options={{ presentation: 'modal' }} />
          <Stack.Screen name="log/nutrition" options={{ presentation: 'modal' }} />
          <Stack.Screen name="log/workout" options={{ presentation: 'modal' }} />
          <Stack.Screen name="log/sleep" options={{ presentation: 'modal' }} />
          <Stack.Screen name="teams/create" options={{ presentation: 'modal' }} />
          <Stack.Screen name="teams/join" options={{ presentation: 'modal' }} />
          <Stack.Screen name="teams/new-challenge" options={{ presentation: 'modal' }} />
          <Stack.Screen name="accountability/index" />
          <Stack.Screen name="paywall" options={{ presentation: 'modal' }} />
          <Stack.Screen name="profile-edit" options={{ presentation: 'modal' }} />
        </Stack>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
