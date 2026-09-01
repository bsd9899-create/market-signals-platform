import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';
import { AppState } from 'react-native';
import { env, isSupabaseConfigured } from '@/src/lib/env';
import type { Database } from './database.types';

if (!isSupabaseConfigured) {
  console.warn(
    '[supabase] EXPO_PUBLIC_SUPABASE_URL / EXPO_PUBLIC_SUPABASE_ANON_KEY غير معرَّفة. ' +
      'انسخ .env.example إلى .env وأضف قيم مشروع Supabase الحقيقي — كل ميزات ' +
      'الحساب والبيانات لن تعمل بدونها.'
  );
}

/**
 * عميل Supabase الوحيد في التطبيق. anon key آمن للتضمين في التطبيق —
 * الحماية الفعلية للبيانات تأتي بالكامل من سياسات RLS في قاعدة
 * البيانات (راجع supabase/migrations)، وليس من إخفاء هذا المفتاح.
 */
export const supabase = createClient<Database>(
  env.EXPO_PUBLIC_SUPABASE_URL ?? 'https://placeholder.supabase.co',
  env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? 'placeholder-anon-key',
  {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
      // PKCE إلزامي لتبادل كود OAuth (Google) داخل تطبيق React Native —
      // الطريقة الافتراضية (implicit) تعتمد على تحليل التطبيق لرابط ويب،
      // وهذا غير متاح هنا أصلًا بما أن detectSessionInUrl مُعطّلة.
      flowType: 'pkce',
    },
  }
);

// إيقاف/استئناف التجديد التلقائي للجلسة حسب حالة التطبيق (توصية Supabase
// الرسمية لـ React Native) — يمنع استهلاك طلبات شبكة وهي في الخلفية.
AppState.addEventListener('change', (state) => {
  if (state === 'active') {
    supabase.auth.startAutoRefresh();
  } else {
    supabase.auth.stopAutoRefresh();
  }
});
