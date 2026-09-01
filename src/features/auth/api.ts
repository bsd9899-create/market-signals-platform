import { supabase } from '@/src/data/supabase';

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

/**
 * حذف الحساب نهائيًا — يستدعي Edge Function موثوقة (supabase/functions/
 * delete-account) لأن حذف auth.users يتطلب صلاحية admin لا تُمنح
 * للعميل مطلقًا. متطلب أساسي من Apple لأي تطبيق يسمح بإنشاء حساب.
 */
export async function deleteAccount() {
  const { error } = await supabase.functions.invoke('delete-account');
  if (error) throw error;
  await supabase.auth.signOut();
}
