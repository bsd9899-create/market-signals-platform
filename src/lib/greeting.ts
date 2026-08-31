/** تحية مناسبة لوقت اليوم — تفاصيل صغيرة تجعل الشاشة تشعر أنها حيّة. */
export function getTimeGreeting(date: Date = new Date()): string {
  const hour = date.getHours();
  if (hour < 5) return 'الوقت متأخر 🌙';
  if (hour < 12) return 'صباح الخير';
  if (hour < 17) return 'هلا';
  if (hour < 21) return 'مساء الخير';
  return 'مساء النشاط';
}
