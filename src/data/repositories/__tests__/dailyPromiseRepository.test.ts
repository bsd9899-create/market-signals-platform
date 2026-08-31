import { dailyPromiseRepository } from '../dailyPromiseRepository';
import { supabase } from '../../supabase';

jest.mock('../../supabase', () => ({
  supabase: { from: jest.fn() },
}));

/** بنّاء وهمي متسلسل (chainable) يحاكي PostgrestQueryBuilder — كل دالة تعيد نفسها. */
function mockQueryBuilder(finalResult: { data: unknown; error: unknown }) {
  const builder: Record<string, jest.Mock> = {};
  const chainableMethods = ['select', 'eq', 'upsert', 'update'];
  for (const method of chainableMethods) {
    builder[method] = jest.fn(() => builder);
  }
  builder.maybeSingle = jest.fn(() => Promise.resolve(finalResult));
  // upsert/update بدون .maybeSingle() في الكود الفعلي — تُنتظَر مباشرة كـ Promise
  // لذلك نجعل الكائن نفسه "thenable" ليعمل مع await مباشرة بعد upsert()/update().
  (builder as unknown as PromiseLike<typeof finalResult>).then = (resolve) =>
    Promise.resolve(finalResult).then(resolve as never);
  return builder;
}

const mockedFrom = supabase.from as jest.Mock;

describe('dailyPromiseRepository', () => {
  afterEach(() => jest.clearAllMocks());

  it('getToday يستعلم عن جدول daily_promises بمرشّحات user_id والتاريخ الصحيحة', async () => {
    const builder = mockQueryBuilder({ data: { promise_type: 'workout', fulfilled: null }, error: null });
    mockedFrom.mockReturnValue(builder);

    const result = await dailyPromiseRepository.getToday('user-1');

    expect(mockedFrom).toHaveBeenCalledWith('daily_promises');
    expect(builder.eq).toHaveBeenCalledWith('user_id', 'user-1');
    expect(result).toEqual({ promise_type: 'workout', fulfilled: null });
  });

  it('getToday يرمي الخطأ بدل إخفائه لو فشل الاستعلام', async () => {
    const builder = mockQueryBuilder({ data: null, error: new Error('db down') });
    mockedFrom.mockReturnValue(builder);

    await expect(dailyPromiseRepository.getToday('user-1')).rejects.toThrow('db down');
  });

  it('setToday يستخدم upsert بمفتاح user_id,date (وليس insert) لمنع تكرار وعدين لنفس اليوم', async () => {
    const builder = mockQueryBuilder({ data: null, error: null });
    mockedFrom.mockReturnValue(builder);

    await dailyPromiseRepository.setToday('user-1', 'water');

    expect(builder.upsert).toHaveBeenCalledWith(
      expect.objectContaining({ user_id: 'user-1', promise_type: 'water', fulfilled: null }),
      { onConflict: 'user_id,date' }
    );
  });
});
