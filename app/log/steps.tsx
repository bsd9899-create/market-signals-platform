import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import { useAuthStore } from '@/src/features/auth/store';
import { NumericLogForm } from '@/src/features/quick-add/NumericLogForm';

export default function LogStepsScreen() {
  const userId = useAuthStore((s) => s.session?.user.id);

  return (
    <NumericLogForm
      title="الخطوات"
      emoji="👟"
      unitLabel="خطوة"
      placeholder="إجمالي خطوات اليوم"
      onSubmit={async (steps) => {
        if (!userId) throw new Error('لا يوجد مستخدم مسجّل الدخول');
        await dailyLogsRepository.setStepsToday(userId, Math.round(steps));
      }}
    />
  );
}
