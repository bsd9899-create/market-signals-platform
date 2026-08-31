import { getFriendlyErrorMessage, isOfflineError } from '../errors';

describe('isOfflineError', () => {
  it('يتعرّف على فشل fetch الشائع في React Native', () => {
    expect(isOfflineError(new Error('Network request failed'))).toBe(true);
  });

  it('يتعرّف على فشل fetch في المتصفح/Node', () => {
    expect(isOfflineError(new TypeError('Failed to fetch'))).toBe(true);
  });

  it('لا يعتبر خطأ منطق عادي انقطاع شبكة', () => {
    expect(isOfflineError(new Error('كود الدعوة غير صحيح'))).toBe(false);
  });

  it('لا يفشل مع قيم ليست Error', () => {
    expect(isOfflineError('نص عادي')).toBe(false);
    expect(isOfflineError(null)).toBe(false);
  });
});

describe('getFriendlyErrorMessage', () => {
  it('يعطي رسالة انقطاع اتصال مخصّصة عند خطأ شبكة', () => {
    expect(getFriendlyErrorMessage(new Error('Network request failed'))).toContain('غير متصل بالإنترنت');
  });

  it('يعيد رسالة الخطأ نفسها لو كان خطأ منطق عادي', () => {
    expect(getFriendlyErrorMessage(new Error('كود الدعوة غير صحيح'))).toBe('كود الدعوة غير صحيح');
  });

  it('يستخدم fallback المخصّص عند غياب رسالة واضحة', () => {
    expect(getFriendlyErrorMessage('شيء غريب', 'تعذّر الحفظ')).toBe('تعذّر الحفظ');
  });

  it('يستخدم الرسالة العامة الافتراضية لو لم يُمرَّر fallback', () => {
    expect(getFriendlyErrorMessage({})).toBe('حدث خطأ غير متوقع، حاول مرة أخرى');
  });
});
