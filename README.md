# هِمّة (Hemma)

تطبيق جوال للصحة واللياقة والالتزام اليومي — الهدف الأساسي مساعدة
المستخدم على **الاستمرار**، لا مجرد تسجيل الأرقام.

## Stack

- **Mobile**: React Native + Expo (EAS Dev Client) + TypeScript + Expo Router
- **Backend/DB**: Supabase (PostgreSQL + Auth + Row Level Security + Storage + Realtime)
- **Subscriptions**: RevenueCat فوق Apple StoreKit (هِمّة+، شهري/سنوي)
- **Health**: طبقة تكامل معزولة مع Apple HealthKit
- **اللغة**: عربية، RTL بالكامل

## البنية

```
app/                        # الشاشات والتنقل (Expo Router)
src/
├── design-system/          # ألوان، خط، تباعد، مكونات أساسية (من هوية الشعار)
├── features/                # منطق كل ميزة (اليوم، الفرق، ...)
├── domain/                  # منطق أعمال صافٍ (قرار اليوم، وضع الإنقاذ)
├── data/                    # Supabase client + repositories
├── subscriptions/           # RevenueCat + Paywall + حالة Premium
└── integrations/health/     # HealthKit adapter
supabase/
├── migrations/               # مخطط قاعدة البيانات + RLS
└── functions/                 # Edge Functions
assets/branding/              # هوية هِمّة البصرية (راجع README فيه)
```

## التشغيل محليًا

يتطلب المشروع **EAS Dev Client** (ليس Expo Go) لأن HealthKit وRevenueCat
مكتبات Native لا تعمل داخل Expo Go.

```bash
npm install
npx expo start --dev-client
```

## متغيرات البيئة

انسخ `.env.example` إلى `.env` واملأ القيم المطلوبة (Supabase, RevenueCat).
لا تضع أي سر مباشرة في الكود أو Git.

## حالة المشروع

يُبنى على مراحل متسلسلة (راجع سجل الـ commits). كل مرحلة تُختبر وتُتحقق
منها (TypeScript + Metro bundling) قبل الانتقال للتالية.
