# تفعيل تسجيل الدخول عبر Google وApple — خطوات لوحات التحكم

الكود جاهز بالكامل (`src/features/auth/oauth.ts`، `app/(auth)/sign-in.tsx`)
ولا يحتاج أي تعديل إضافي. المتبقي كله إعداد خارجي في لوحات تحكم
Google/Apple/Supabase — لا يمكن تنفيذه من الكود ولا من هذه الجلسة.

## 0) رابط العودة إلى التطبيق (يُستخدم في كل الخطوات التالية)

```
hemma://auth/callback
```

## 1) Google

1. **Google Cloud Console** → APIs & Services → Credentials →
   **Create Credentials → OAuth client ID**.
2. نوع التطبيق: **Web application** (وليس iOS) — Supabase نفسه هو من
   يتحدث مع Google، وليس تطبيق الجوال مباشرة.
3. **Authorized redirect URI**:
   `https://<project-ref>.supabase.co/auth/v1/callback`
   (استبدل `<project-ref>` بمعرّف مشروع Supabase الحقيقي).
4. احفظ **Client ID** و**Client Secret** الناتجين.
5. **Supabase Dashboard** → Authentication → Providers → **Google** →
   فعّله → الصق Client ID/Secret → Save.

## 2) Apple

1. **Apple Developer Portal** → Certificates, Identifiers & Profiles →
   Identifiers → تأكد أن App ID الحالي (`com.hemma.app`) مفعّل عليه
   قابلية **Sign In with Apple**.
2. أنشئ **Services ID** جديد (مثلًا `com.hemma.app.signin`) —
   هذا مختلف عن Bundle ID التطبيق، ويمثّل "عميل الويب" الذي يتحدث معه
   Supabase. أضف:
   - Domain: `<project-ref>.supabase.co`
   - Return URL: `https://<project-ref>.supabase.co/auth/v1/callback`
3. أنشئ **مفتاح Sign In with Apple** جديد (Keys)، نزّل ملف `.p8`
   (يُنزَّل مرة واحدة فقط — احفظه).
4. **Supabase Dashboard** → Authentication → Providers → **Apple** →
   فعّله، وامْلأ:
   - Services ID (كـ Client ID)
   - Team ID
   - Key ID
   - محتوى ملف `.p8`
   - **مهم:** في حقل "Authorized Client IDs" أضف أيضًا `com.hemma.app`
     (Bundle ID نفسه) — لأن تسجيل الدخول من داخل التطبيق (الطريقة
     الأصلية عبر `expo-apple-authentication` المستخدمة في الكود) يصدر
     رمزًا يحمل `aud = com.hemma.app`، وليس الـ Services ID. بدون هذا
     السطر سيرفض Supabase الرمز حتى لو كانت كل الإعدادات الأخرى صحيحة.

## 3) رابط العودة داخل Supabase (خطوة مشتركة لكل من Google وApple)

**Supabase Dashboard** → Authentication → URL Configuration →
**Redirect URLs** → أضف:

```
hemma://auth/callback
```

بدون هذا السطر تحديدًا سيرفض Supabase إعادة توجيه Google (وليس Apple —
Apple لا يمر عبر هذا المسار لأنه تدفق أصلي مباشر لا يفتح متصفحًا إطلاقًا).

## 4) لا تغييرات مطلوبة في قاعدة البيانات

Trigger إنشاء الملف الشخصي (`handle_new_user`) يعمل تلقائيًا على أي
إدخال في `auth.users` بغض النظر عن طريقة الدخول (بريد، Google، Apple) —
لا حاجة لأي migration جديدة.

## 5) الاختبار الفعلي يحتاج Development Build

`expo-apple-authentication` وGoogle OAuth (عبر `expo-web-browser`) وحدات
أصلية — **لن تعمل داخل Expo Go**، تمامًا كما هو الحال مع HealthKit
والاشتراكات. اختبرها فقط عبر Development Build حقيقي على جهاز
(راجع `docs/EAS_BUILD_GUIDE.md`).
