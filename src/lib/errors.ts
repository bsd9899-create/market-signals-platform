/**
 * يحوّل أخطاء الشبكة/Supabase الخام إلى رسالة عربية مفهومة للمستخدم.
 * نستخدمها في كل مكان بدل عرض `error.message` الخام (غالبًا إنجليزي
 * وتقني)، وتكتشف تحديدًا حالة "لا يوجد اتصال إنترنت" لتعطي رسالة
 * مختلفة قابلة للتصرف (أعد المحاولة) بدل رسالة عامة.
 */
export function getFriendlyErrorMessage(error: unknown, fallback = 'حدث خطأ غير متوقع، حاول مرة أخرى'): string {
  if (isOfflineError(error)) {
    return 'يبدو أنك غير متصل بالإنترنت — تحقق من اتصالك وحاول مرة أخرى';
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

/** يكتشف فشل fetch الناتج عن انقطاع الشبكة (وليس خطأ خادم/منطق). */
export function isOfflineError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const message = error.message.toLowerCase();
  return (
    message.includes('network request failed') ||
    message.includes('failed to fetch') ||
    message.includes('networkerror') ||
    message.includes('the internet connection appears to be offline')
  );
}
