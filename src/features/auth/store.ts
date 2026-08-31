import type { Session } from '@supabase/supabase-js';
import { create } from 'zustand';
import { supabase } from '@/src/data/supabase';

type AuthState = {
  session: Session | null;
  /** true فقط أثناء أول تحميل للجلسة عند فتح التطبيق. */
  isInitializing: boolean;
};

export const useAuthStore = create<AuthState>(() => ({
  session: null,
  isInitializing: true,
}));

let listenerStarted = false;

/**
 * يبدأ الاستماع لتغيّرات جلسة Supabase مرة واحدة فقط لعمر التطبيق.
 * يُستدعى من app/_layout.tsx.
 */
export function startAuthListener() {
  if (listenerStarted) return;
  listenerStarted = true;

  supabase.auth.getSession().then(({ data }) => {
    useAuthStore.setState({ session: data.session, isInitializing: false });
  });

  supabase.auth.onAuthStateChange((_event, session) => {
    useAuthStore.setState({ session, isInitializing: false });
  });
}
