import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import { useAuthStore } from '@/src/features/auth/store';
import { NumericLogForm } from '@/src/features/quick-add/NumericLogForm';

export default function LogWeightScreen() {
  const userId = useAuthStore((s) => s.session?.user.id);

  return (
    <NumericLogForm
      title="الوزن"
      emoji="⚖️"
      unitLabel="كجم"
      placeholder="مثلاً 75.5"
      allowDecimal
      onSubmit={async (weightKg) => {
        if (!userId) throw new Error('لا يوجد مستخدم مسجّل الدخول');
        await dailyLogsRepository.addWeight(userId, weightKg);
      }}
    />
  );
}
