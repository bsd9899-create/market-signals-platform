import { z } from 'zod';

/**
 * قراءة والتحقق من متغيرات البيئة العامة (EXPO_PUBLIC_*) في مكان واحد
 * بدل الاعتماد على process.env مباشرة في كل ملف. راجع .env.example.
 */
const envSchema = z.object({
  EXPO_PUBLIC_SUPABASE_URL: z.string().url().optional(),
  EXPO_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1).optional(),
  EXPO_PUBLIC_REVENUECAT_IOS_API_KEY: z.string().min(1).optional(),
});

const parsed = envSchema.safeParse({
  EXPO_PUBLIC_SUPABASE_URL: process.env.EXPO_PUBLIC_SUPABASE_URL,
  EXPO_PUBLIC_SUPABASE_ANON_KEY: process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY,
  EXPO_PUBLIC_REVENUECAT_IOS_API_KEY: process.env.EXPO_PUBLIC_REVENUECAT_IOS_API_KEY,
});

export const env = parsed.success
  ? parsed.data
  : ({} as z.infer<typeof envSchema>);

export const isSupabaseConfigured = Boolean(
  env.EXPO_PUBLIC_SUPABASE_URL && env.EXPO_PUBLIC_SUPABASE_ANON_KEY
);
