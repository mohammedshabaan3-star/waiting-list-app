# خطة تنفيذ نظام الإشعارات

**تاريخ الخطة:** 15 يناير 2026  
**المشروع:** تطبيق قوائم الانتظار للعقود  
**الهدف:** إكمال تفعيل نظام الإشعارات في واجهة المستخدم

---

## 📋 الوضع الحالي

✅ **ما هو موجود:**
- جدول `notifications` في قاعدة البيانات
- وظائف النظام الأساسية (`create_notification`, `get_user_notifications`, إلخ)
- هيكل قاعدة البيانات مكتمل

❌ **ما هو مفقود:**
- واجهة المستخدم لعرض الإشعارات
- التكامل مع أحداث التطبيق
- الإشعارات التلقائية

---

## 🎯 المرحلة الأولى: واجهة الإشعارات الأساسية

### 1. إضافة مؤشر الإشعارات في الشريط العلوي

```python
# في دالة main() أو في الشريط العلوي
def show_notifications_indicator(user):
    """عرض مؤشر الإشعارات غير المقروءة"""
    unread_count = get_unread_count(user["id"], user["role"])
    
    if unread_count > 0:
        st.markdown(f"""
        <div style="position: fixed; top: 10px; right: 10px; z-index: 999;">
            <span style="background: red; color: white; border-radius: 50%; 
                         padding: 5px 10px; font-size: 12px;">
                🔔 {unread_count}
            </span>
        </div>
        """, unsafe_allow_html=True)
```

### 2. إنشاء صفحة الإشعارات

```python
def notifications_page_ui(user):
    """صفحة عرض الإشعارات"""
    st.markdown("<div class='subheader'>الإشعارات</div>", unsafe_allow_html=True)
    
    # الحصول على الإشعارات
    notifications = get_user_notifications(user["id"], user["role"])
    
    if not notifications:
        st.info("لا توجد إشعارات")
        return
    
    # عرض الإشعارات
    for notif in notifications:
        with st.container():
            col1, col2, col3 = st.columns([6, 2, 2])
            
            with col1:
                # تمييز الإشعارات غير المقروءة
                style = "font-weight: bold;" if not notif['is_read'] else ""
                st.markdown(f"<div style='{style}'>{notif['title']}</div>", 
                           unsafe_allow_html=True)
                st.write(notif['message'])
                st.caption(f"📅 {notif['created_at']}")
            
            with col2:
                # نوع الإشعار
                type_emoji = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
                st.write(f"{type_emoji.get(notif['type'], 'ℹ️')} {notif['type']}")
            
            with col3:
                # زر تعليم كمقروء
                if not notif['is_read']:
                    if st.button("تعليم كمقروء", key=f"mark_{notif['id']}"):
                        mark_notification_read(notif['id'])
                        st.rerun()
                else:
                    st.write("✅ مقروء")
            
            st.divider()
```

### 3. إضافة الإشعارات للقائمة الجانبية

```python
# في دالة إنشاء القائمة الجانبية
def create_sidebar_menu(user):
    # ... الكود الموجود ...
    
    # إضافة خيار الإشعارات
    unread_count = get_unread_count(user["id"], user["role"])
    notif_label = f"🔔 الإشعارات ({unread_count})" if unread_count > 0 else "🔔 الإشعارات"
    
    menu_options.append(notif_label)
    
    # ... باقي الكود ...
```

---

## 🔄 المرحلة الثانية: الإشعارات التلقائية

### 1. إشعارات تغيير حالة الطلب

```python
def _callback_update_request_status(request_id: int, new_status: str, note: str, is_final: bool):
    """تحديث حالة الطلب مع إرسال إشعار"""
    # ... الكود الموجود لتحديث الحالة ...
    
    # إرسال إشعار للمستشفى
    with get_conn() as conn:
        request_data = conn.execute("""
            SELECT r.*, h.name as hospital_name 
            FROM requests r 
            JOIN hospitals h ON r.hospital_id = h.id 
            WHERE r.id = ?
        """, (request_id,)).fetchone()
        
        if request_data:
            create_notification(
                user_id=request_data['hospital_id'],
                user_role="hospital",
                title="تحديث حالة الطلب",
                message=f"تم تحديث حالة طلبكم رقم {request_id} إلى: {new_status}",
                notification_type="info",
                related_id=request_id
            )
```

### 2. إشعارات الطلبات الجديدة

```python
def create_new_request(user, service_id, age_category):
    """إنشاء طلب جديد مع إرسال إشعار للإدارة"""
    # ... الكود الموجود لإنشاء الطلب ...
    
    # إرسال إشعار للإدارة
    create_notification(
        user_id=None,  # للجميع
        user_role="admin",
        title="طلب جديد",
        message=f"تم تقديم طلب جديد من {user['name']} للخدمة: {service_name}",
        notification_type="info",
        related_id=req_id
    )
    
    # إرسال إشعار لمراجع القطاع إذا وُجد
    hospital_sector = get_hospital_sector(user["id"])
    if hospital_sector:
        create_notification(
            user_id=None,
            user_role="reviewer_sector",
            title="طلب جديد في قطاعكم",
            message=f"طلب جديد في قطاع {hospital_sector} من {user['name']}",
            notification_type="info",
            related_id=req_id
        )
```

### 3. إشعارات رفع المستندات

```python
def save_uploaded_file(uploaded_file, user, request_id, doc):
    """حفظ ملف مرفوع مع إرسال إشعار"""
    # ... الكود الموجود لحفظ الملف ...
    
    # إرسال إشعار للإدارة عند اكتمال المستندات
    if all_documents_uploaded(request_id):
        create_notification(
            user_id=None,
            user_role="admin",
            title="طلب مكتمل جاهز للمراجعة",
            message=f"الطلب رقم {request_id} مكتمل ويحتاج للمراجعة",
            notification_type="success",
            related_id=request_id
        )
```

---

## 📧 المرحلة الثالثة: الإشعارات الخارجية (اختيارية)

### 1. إعداد نظام البريد الإلكتروني

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_notification(to_email: str, subject: str, message: str):
    """إرسال إشعار بالبريد الإلكتروني"""
    try:
        # إعدادات البريد الإلكتروني
        smtp_server = "smtp.gmail.com"  # أو خادم البريد المناسب
        smtp_port = 587
        sender_email = "your-email@domain.com"
        sender_password = "your-password"
        
        # إنشاء الرسالة
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain', 'utf-8'))
        
        # إرسال الرسالة
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
```

### 2. تحديث دالة إنشاء الإشعار

```python
def create_notification(user_id: int, user_role: str, title: str, message: str, 
                       notification_type: str = "info", related_id: int = None,
                       send_email: bool = False):
    """إنشاء إشعار مع إمكانية الإرسال بالبريد الإلكتروني"""
    # إنشاء الإشعار في قاعدة البيانات
    success = create_notification_db(user_id, user_role, title, message, 
                                   notification_type, related_id)
    
    # إرسال بريد إلكتروني إذا طُلب ذلك
    if success and send_email and user_id:
        user_email = get_user_email(user_id, user_role)
        if user_email:
            send_email_notification(user_email, title, message)
    
    return success
```

---

## 🛠️ خطوات التنفيذ التفصيلية

### الأسبوع الأول:
1. **اليوم 1-2**: إضافة مؤشر الإشعارات في الشريط العلوي
2. **اليوم 3-4**: إنشاء صفحة عرض الإشعارات
3. **اليوم 5**: إضافة الإشعارات للقائمة الجانبية واختبار الواجهة

### الأسبوع الثاني:
1. **اليوم 1-2**: إضافة إشعارات تغيير حالة الطلب
2. **اليوم 3-4**: إضافة إشعارات الطلبات الجديدة
3. **اليوم 5**: إضافة إشعارات رفع المستندات واختبار شامل

### الأسبوع الثالث (اختياري):
1. **اليوم 1-3**: إعداد نظام البريد الإلكتروني
2. **اليوم 4-5**: اختبار الإشعارات الخارجية وتحسينات

---

## 🧪 اختبار النظام

### اختبارات الواجهة:
- [ ] عرض مؤشر الإشعارات غير المقروءة
- [ ] عرض قائمة الإشعارات
- [ ] تعليم الإشعارات كمقروءة
- [ ] تحديث العداد تلقائياً

### اختبارات الإشعارات التلقائية:
- [ ] إشعار عند تغيير حالة الطلب
- [ ] إشعار عند تقديم طلب جديد
- [ ] إشعار عند اكتمال المستندات
- [ ] إشعارات مخصصة حسب دور المستخدم

### اختبارات الأداء:
- [ ] سرعة تحميل الإشعارات
- [ ] عدم تأثير الإشعارات على أداء التطبيق
- [ ] إدارة الذاكرة بكفاءة

---

## 📝 ملاحظات التنفيذ

### أولويات:
1. **عالية**: واجهة الإشعارات الأساسية
2. **متوسطة**: الإشعارات التلقائية للأحداث المهمة
3. **منخفضة**: الإشعارات الخارجية

### اعتبارات الأمان:
- التحقق من صلاحيات المستخدم قبل عرض الإشعارات
- تشفير البيانات الحساسة في الإشعارات
- تنظيف الإشعارات القديمة دورياً

### اعتبارات الأداء:
- تحديد عدد الإشعارات المعروضة (مثلاً 50 إشعار)
- استخدام التخزين المؤقت للإشعارات المتكررة
- تحسين استعلامات قاعدة البيانات

---

**تم إعداد هذه الخطة بواسطة:** نظام التحليل التلقائي  
**آخر تحديث:** 15 يناير 2026