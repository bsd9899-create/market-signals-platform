import { supabase } from '@/src/data/supabase';

/**
 * دخول بدون كلمة مرور: نرسل رمزًا مكوّنًا من 6 أرقام على البريد،
 * ونؤكده في شاشة verify. shouldCreateUser يسمح بإنشاء حساب جديد
 * تلقائيًا لو كان أول مرة — نفس الشاشة لتسجيل الدخول والتسجيل معًا،
 * تماشيًا مع مبدأ "أقل عدد ممكن من الخطوات".
 */
export async function requestEmailOtp(email: string) {
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { shouldCreateUser: true },
  });
  if (error) throw error;
}

export async function verifyEmailOtp(email: string, token: string) {
  const { data, error } = await supabase.auth.verifyOtp({ email, token, type: 'email' });
  if (error) throw error;
  return data.session;
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}
