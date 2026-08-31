import { dailyLogsRepository } from '@/src/data/repositories/dailyLogsRepository';
import { useAuthStore } from '@/src/features/auth/store';
import { NumericLogForm } from '@/src/features/quick-add/NumericLogForm';

export default function LogWaterScreen() {
  const userId = useAuthStore((s) => s.session?.user.id);

  return (
    <NumericLogForm
      title="الماء"
      emoji="💧"
      unitLabel="مل"
      placeholder="مثلاً 300"
      presets={[250, 500, 750]}
      onSubmit={async (amountMl) => {
        if (!userId) throw new Error('لا يوجد مستخدم مسجّل الدخول');
        await dailyLogsRepository.addWater(userId, amountMl);
      }}
    />
  );
}
