# دليل الاستخدام

---

## ١. نظام العمولات (pos_sales_commission)

### الإعداد

**١. تفعيل العمولات على نقطة البيع**
- اذهب إلى: `Point of Sale → Configuration → Settings`
- فعّل خيار **Commission**
- احفظ بـ `Save`

**٢. إضافة قواعد العمولة**
- اذهب إلى: `Point of Sale → Configuration → Commission Rules`
- أنشئ قاعدة جديدة بـ `New`
- حدد نوع الحساب: نسبة مئوية أو مبلغ ثابت
- اربطها بمنتج أو فئة منتج إن أردت

**٣. ربط العمولة بالموظف**
- اذهب إلى: `Employees → [اسم الموظف] → Commission`
- حدد حساب العمولة الخاص بالموظف

### الاستخدام اليومي

عند الضغط على **Validate** في شاشة الدفع، تظهر نافذة لتحديد الموظف المسؤول عن كل سطر من الطلب.
- اختر الموظف من القائمة المنسدلة لكل منتج
- أو اتركه فارغاً ليُحسب للكاشير الافتراضي
- اضغط **Confirm** للمتابعة أو **Cancel** للإلغاء

### متابعة العمولات

- `Point of Sale → Reporting → Commission Lines` — لعرض جميع العمولات
- `Point of Sale → Reporting → Pay Commission` — لصرف العمولات المستحقة

---

## ٢. برنامج الولاء — اشترِ X واحصل على Y

### الإعداد

**١. فتح برامج الولاء**
- اذهب إلى: `Point of Sale → Products → Gift cards & eWallet`
- أو من: `Point of Sale → Configuration → Settings` → قسم **Pricing** → `Promotions, Coupons, Gift Card & Loyalty`

**٢. إنشاء برنامج جديد**
- اضغط `New`
- في حقل **Program Type** اختر: `Loyalty Card`
- أدخل اسم البرنامج

**٣. إعداد شرط الشراء (Trigger)**
- في قسم **Conditions** اضغط `Add a line`
- **Minimum Quantity**: الكمية الواجب شراؤها (مثلاً `2`)
- **Products**: حدد المنتج المطلوب أو اتركه فارغاً لأي منتج

**٤. إعداد المكافأة (Reward)**
- في قسم **Rewards** اضغط `Add a line`
- **Reward Type** اختر: `Free Product`
- **Quantity Rewarded**: عدد المنتجات المجانية (مثلاً `1`)
- **Reward Product**: المنتج الذي يحصل عليه العميل مجاناً

**٥. ربط البرنامج بنقطة البيع**
- اذهب إلى: `Point of Sale → Configuration → Settings`
- في قسم **Pricing** تأكد أن البرنامج مفعّل

### الاستخدام

- عند إضافة المنتجات في POS، يُطبَّق البرنامج تلقائياً عند استيفاء الشرط
- يظهر سطر مجاني تلقائي بسعر `0.00` في الطلب
- إن كان البرنامج يتطلب بطاقة ولاء: اضغط زر **Loyalty** في شاشة المنتجات لإدخال رقم بطاقة العميل

---

> للدعم الفني راجع ملفات السجلات في: `Point of Sale → Reporting`
