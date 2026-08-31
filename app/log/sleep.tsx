import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import { useAuthStore } from '@/src/features/auth/store';
import { NumericLogForm } from '@/src/features/quick-add/NumericLogForm';

export default function LogSleepScreen() {
  const userId = useAuthStore((s) => s.session?.user.id);

  return (
    <NumericLogForm
      title="النوم"
      emoji="💤"
      unitLabel="ساعة"
      placeholder="مثلاً 7.5"
      allowDecimal
      onSubmit={async (hours) => {
        if (!userId) throw new Error('لا يوجد مستخدم مسجّل الدخول');
        await dailyLogsRepository.setSleepToday(userId, hours);
      }}
    />
  );
}
