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
