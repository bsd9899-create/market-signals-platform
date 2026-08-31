import { useEffect } from 'react';
import { useRouter, useSegments } from 'expo-router';
import { startAuthListener, useAuthStore } from './store';
import { useProfileStore } from './profileStore';

/**
 * حارس التنقل الرئيسي للتطبيق: بدون جلسة → شاشات الدخول، مع جلسة لكن
 * بدون onboarding_completed_at → شاشة الترحيب، وإلا → التطبيق نفسه.
 * يعيد isReady لمنع أي وميض شاشة خاطئة قبل معرفة حالة المستخدم.
 */
export function useAuthGate() {
  const router = useRouter();
  const segments = useSegments();

  const session = useAuthStore((s) => s.session);
  const isInitializing = useAuthStore((s) => s.isInitializing);

  const profile = useProfileStore((s) => s.profile);
  const hasProfileLoaded = useProfileStore((s) => s.hasLoaded);
  const fetchProfile = useProfileStore((s) => s.fetch);
  const clearProfile = useProfileStore((s) => s.clear);

  useEffect(() => {
    startAuthListener();
  }, []);

  useEffect(() => {
    if (isInitializing) return;
    if (session) {
      fetchProfile();
    } else {
      clearProfile();
    }
    // session?.user.id بدل session نفسها — الكائن يتغيّر مرجعيًا مع كل
    // تجديد توكن تلقائي حتى لو بقي نفس المستخدم، وإضافته للاعتماديات
    // ستُعيد جلب الملف الشخصي بلا داعٍ عند كل تجديد صامت للتوكن.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isInitializing, session?.user.id, fetchProfile, clearProfile]);

  const isReady = !isInitializing && (!session || hasProfileLoaded);

  useEffect(() => {
    if (!isReady) return;

    const inAuthGroup = segments[0] === '(auth)';
    const inOnboarding = segments[0] === 'onboarding';

    if (!session && !inAuthGroup) {
      router.replace('/(auth)/sign-in');
      return;
    }

    if (session && !profile?.onboarding_completed_at && !inOnboarding) {
      router.replace('/onboarding');
      return;
    }

    if (session && profile?.onboarding_completed_at && (inAuthGroup || inOnboarding)) {
      router.replace('/(tabs)');
    }
  }, [isReady, segments, session, profile, router]);

  return { isReady };
}
