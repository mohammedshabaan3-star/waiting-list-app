# دليل المطور - نظام التعاقد المحسن

## 🔧 البنية التقنية

### نظام Migrations
النظام يستخدم migrations لتطبيق التغييرات على قاعدة البيانات تلقائياً:

```python
# إضافة migration جديد
def run_migrations():
    current_version = get_current_schema_version()
    
    if current_version < NEW_VERSION:
        # كود التحديث هنا
        with get_conn() as conn:
            # تطبيق التغييرات
            conn.execute("ALTER TABLE ...")
            conn.commit()
    
    # تحديث الإصدار
    if current_version < DB_SCHEMA_VERSION:
        set_schema_version(DB_SCHEMA_VERSION)
```

### مراقبة التغييرات
النظام يراقب ملف قاعدة البيانات ويطبق التحديثات تلقائياً:

```python
class DatabaseChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # تطبيق migrations عند تغيير قاعدة البيانات
        run_migrations()
        # مسح الذاكرة المؤقتة
        st.cache_data.clear()
```

## 📊 تحسينات الأداء

### الفهارس المضافة:
- `idx_requests_hospital_service`: تسريع البحث بالمستشفى والخدمة
- `idx_requests_status`: تسريع البحث بالحالة
- `idx_requests_created_at`: تسريع ترتيب التواريخ
- `idx_documents_request_id`: تسريع جلب المستندات
- `idx_activity_log_timestamp`: تسريع سجل النشاط

### إدارة الذاكرة المؤقتة:
```python
# مسح الذاكرة عند التحديث
if hasattr(st, 'cache_data'):
    st.cache_data.clear()
```

## 🔄 التحديث التلقائي

### عند تغيير الإعدادات:
```python
def set_hospital_types(types: list):
    # حفظ البيانات
    with get_conn() as conn:
        conn.execute("...")
        conn.commit()
    
    # مسح الذاكرة المؤقتة
    if hasattr(st, 'cache_data'):
        st.cache_data.clear()
```

### عند تغيير المستندات الاختيارية:
```python
def set_optional_docs_for_type(hospital_type: str, doc_names: list):
    # حفظ الإعدادات
    # ...
    
    # تحديث الطلبات الموجودة
    update_existing_requests_optional_docs()
    
    # مسح الذاكرة المؤقتة
    if hasattr(st, 'cache_data'):
        st.cache_data.clear()
```

## 🛠️ إضافة مميزات جديدة

### إضافة migration جديد:
1. زيادة `DB_SCHEMA_VERSION`
2. إضافة الكود في `run_migrations()`
3. اختبار التحديث

### إضافة نوع مستند جديد:
1. إضافة النوع في `document_types`
2. تحديث `update_existing_requests_optional_docs()`
3. إضافة للطلبات الموجودة

### إضافة حالة طلب جديدة:
1. إضافة في `request_statuses`
2. تحديث `status_settings`
3. تحديث منطق التحقق

## 🔒 الأمان

### تشفير كلمات المرور:
```python
# النظام الجديد - bcrypt
def secure_hash(password: str, salt: str = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    combined = f"{salt}:{password}"
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return f"{salt}:{hash_obj.hexdigest()}"

# التحقق من كلمة المرور
def verify_password(password: str, stored_hash: str) -> bool:
    # يدعم النظام القديم والجديد
    if ':' not in stored_hash:
        return stored_hash == old_hash_pw(password)
    
    salt, hash_part = stored_hash.split(':', 1)
    expected_hash = secure_hash(password, salt)
    return expected_hash == stored_hash
```

## 📝 سجل النشاط

### تسجيل الأنشطة:
```python
def log_activity(action: str, details: str = ""):
    user = st.session_state.get("user")
    if not user:
        return
    
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO activity_log (timestamp, username, user_role, action, details) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), user["username"], user["role"], action, details)
        )
        conn.commit()
```

## 🚀 التشغيل والنشر

### التشغيل المحلي:
```bash
python run_app.py
```

### التشغيل السريع:
```bash
./start.sh
```

### إعدادات Streamlit:
الملف `.streamlit/config.toml` يحتوي على إعدادات محسنة للأداء.

## 🐛 استكشاف الأخطاء

### مشاكل قاعدة البيانات:
- النظام يطبق migrations تلقائياً
- لا حاجة لحذف قاعدة البيانات

### مشاكل الأداء:
- الفهارس تحسن الاستعلامات
- مسح الذاكرة المؤقتة يحدث تلقائياً

### مشاكل التحديث:
- مراقب الملفات يطبق التغييرات تلقائياً
- البيانات تتحدث فوراً

## 📋 قائمة المراجعة للتطوير

- [ ] زيادة `DB_SCHEMA_VERSION` عند إضافة migration
- [ ] إضافة الكود في `run_migrations()`
- [ ] مسح الذاكرة المؤقتة بعد التحديثات
- [ ] تسجيل الأنشطة المهمة
- [ ] اختبار التحديث على بيانات موجودة
- [ ] توثيق التغييرات في README

## 🔗 الملفات المهمة

- `waiting_list_contracts_app.py`: الملف الرئيسي
- `run_app.py`: ملف التشغيل المحسن
- `requirements.txt`: المتطلبات
- `.streamlit/config.toml`: إعدادات Streamlit
- `README.md`: دليل المستخدم
- `DEVELOPER_GUIDE.md`: دليل المطور (هذا الملف)

---
© 2025 المشروع القومي لقوائم الانتظار - دليل المطور