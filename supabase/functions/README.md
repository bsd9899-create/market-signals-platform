# Supabase Edge Functions

هذه الدوال تعمل على Deno (بيئة تشغيل Supabase Edge Functions)، وليس
React Native — لذلك مستثناة عمدًا من `tsconfig.json` الرئيسي للتطبيق
(لا تملك أنواع Deno/`npm:` specifiers). يمكن فتحها والتحقق منها عبر
Deno مباشرة لاحقًا:

```bash
deno check supabase/functions/revenuecat-webhook/index.ts
```

## revenuecat-webhook

يستقبل RevenueCat webhook ويحدّث `public.subscriptions` بصلاحية
service role (المسار الوحيد المسموح به لتعديل هذا الجدول). غير
مُنشور بعد — يحتاج مشروع RevenueCat حقيقي. راجع التعليق أعلى الملف
لخطوات النشر.
