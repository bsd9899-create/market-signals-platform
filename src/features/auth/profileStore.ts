import { create } from 'zustand';
import { profileRepository, type Profile } from '@/src/data/repositories/profileRepository';

type ProfileState = {
  profile: Profile | null;
  isLoading: boolean;
  /** true بعد أول محاولة جلب (نجحت أو فشلت) — يميّز "لم نجلب بعد" عن "لا يوجد ملف". */
  hasLoaded: boolean;
  /** يُعاد جلبه من root layout عند تغيّر الجلسة، ومن onboarding بعد الحفظ. */
  fetch: () => Promise<void>;
  clear: () => void;
};

/**
 * حالة عامة لملف المستخدم الحالي (وليست hook محلي) — لأن أكثر من
 * مكان يحتاج قراءتها (حارس التنقل في app/_layout) وتحديثها (شاشة
 * onboarding) وكلاهما يجب أن يريا نفس النسخة الحديثة فورًا.
 */
export const useProfileStore = create<ProfileState>((set) => ({
  profile: null,
  isLoading: false,
  hasLoaded: false,
  fetch: async () => {
    set({ isLoading: true });
    try {
      const profile = await profileRepository.getCurrent();
      set({ profile, isLoading: false, hasLoaded: true });
    } catch {
      set({ isLoading: false, hasLoaded: true });
    }
  },
  clear: () => set({ profile: null, isLoading: false, hasLoaded: false }),
}));
