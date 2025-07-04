# نظام إدارة المشاريع والمهام

مشروع تطوير ويب باستخدام Flask لإنشاء نظام إدارة مشاريع ومهام.

## متطلبات النظام
- Python 3.10+
- pip

## كيفية تشغيل المشروع

### 1. تفعيل البيئة الافتراضية
```powershell
.\env\Scripts\Activate.ps1
```

### 2. تثبيت المكتبات المطلوبة
```bash
pip install -r requirements.txt
```

### 3. تشغيل الخادم
```bash
python app.py
```

### 4. الوصول للتطبيق
افتح المتصفح واذهب إلى: http://127.0.0.1:5000

## شرح النظام

النظام يتكون من نوعين من المستخدمين:

**المدير (Admin):**
- إضافة مشاريع جديدة
- توزيع المهام على الأعضاء
- إدارة جميع المشاريع

**العضو العادي:**
- عرض المهام الموكلة إليه
- تحديث حالة المهام
- رؤية المشاريع التي ينتمي إليها

## ملاحظات مهمة
- أول مستخدم يسجل في النظام يصبح مدير تلقائياً
- قاعدة البيانات محلية (SQLite)
- جميع الملفات موجودة في المجلدات المخصصة 