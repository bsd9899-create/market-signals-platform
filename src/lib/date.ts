/** تنسيق تاريخ محلي YYYY-MM-DD لأعمدة `date` (بدون منطقة زمنية) في قاعدة البيانات. */
export function toDateKey(d: Date = new Date()): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** بداية اليوم المحلي كـ ISO — لتصفية السجلات ذات timestamptz (ماء/تمرين/نوم...). */
export function startOfTodayISO(): string {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d.toISOString();
}

/** الحرف الأول من اسم اليوم بالعربي (ح ن ث ر خ ج س) — لتسميات الرسوم الصغيرة. */
const ARABIC_WEEKDAY_LETTERS = ['ح', 'ن', 'ث', 'ر', 'خ', 'ج', 'س'];

export function arabicWeekdayLetter(dateKey: string): string {
  const [year, month, day] = dateKey.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  return ARABIC_WEEKDAY_LETTERS[date.getDay()];
}
