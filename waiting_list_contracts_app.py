# -*- coding: utf-8 -*-
"""
نظام التعاقد على الخدمات الجراحية - المشروع القومي لقوائم الانتظار
---------------------------------------------------------------
برنامج ويب احترافي لإدارة طلبات التعاقد بين المستشفيات والمشروع القومي لقوائم الانتظار.

✅ التصحيحات الجذرية لنظام رفع وحذف وإعادة رفع الملفات:

1. تبسيط نظام رفع الملفات:
   - استخدام مفاتيح بسيطة وثابتة لـ st.file_uploader: up_{request_id}_{doc_id}_{updated_at}
   - إضافة آلية منع المعالجة المتكررة باستخدام session_state
   - إزالة استخدام timestamp المتغير الذي يسبب إعادة تهيئة غير ضرورية
   - استخدام st.form لمنع إعادة التشغيل التلقائي عند رفع الملف
   - استخدام form_submit_button للتحكم في عملية الرفع
   - إعادة تحميل واحدة فقط بعد نجاح الرفع

2. تبسيط نظام حذف الملفات:
   - حذف آمن للملفات من القرص باستخدام os.remove()
   - تحديث قاعدة البيانات بشكل صحيح: SET file_name=NULL, file_path=NULL, satisfied=0
   - تنظيف session_state بشكل انتقائي (فقط المفاتيح المرتبطة بالمستند المحذوف)
   - استخدام st.rerun() مرة واحدة بعد الحذف الناجح

3. إصلاح نظام إعادة رفع الملفات:
   - المفتاح يتغير تلقائياً عند تحديث updated_at في قاعدة البيانات
   - st.file_uploader يُعيد تهيئة نفسه بعد الحذف بسبب تغيير المفتاح
   - إزالة التعارضات في session_state
   - ضمان عمل الرفع بعد الحذف مباشرة

4. تبسيط دالة render_file_downloader:
   - إزالة timestamp المتغير من مفاتيح التنزيل
   - استخدام مفتاح بسيط: {key_prefix}_{doc_id}
   - إصلاح خطأ is_satisfied غير المعرّف
   - تحسين معالجة الأخطاء

5. إزالة التعارضات:
   - عدم وجود تضارب في مفاتيح st.file_uploader (كل مستند له مفتاح فريد)
   - عدم وجود تضارب في session_state (تنظيف انتقائي)
   - عدم وجود تضارب في تحديث قاعدة البيانات (معاملات آمنة)
   - عدم وجود تضارب في معالجة الملفات (معالجة آمنة للأخطاء)

النتيجة: نظام رفع وحذف وإعادة رفع ملفات يعمل بشكل صحيح باستخدام st.form لمنع إعادة التشغيل التلقائي.
"""
import os
import re
import io
import zipfile
import hashlib
import base64
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
from contextlib import contextmanager
import sqlite3
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
import secrets
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------------------------- إعدادات أساسية ---------------------------- #
APP_TITLE = "المشروع القومي لقوائم الانتظار - التعاقد على الخدمات الجراحية"
DB_PATH = Path("data/app.db")
STORAGE_DIR = Path("storage")
EXPORTS_DIR = Path("exports")
RESOURCES_DIR = Path("static")

# نظام هاش متوافق: إنشاء جديد باستخدام salt:sha256(salt:password)، والتحقق يدعم القديم والجديد
def secure_hash(password: str, salt: str = None) -> str:
    """إنشاء تجزئة salt:sha256(salt:password) مع تطبيع Unicode وتوحيد الترميز"""
    if not password:
        return ""
    if salt is None:
        salt = secrets.token_hex(16)
    import unicodedata
    normalized = unicodedata.normalize("NFC", str(password).strip())
    combined = f"{salt}:{normalized}"
    digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return f"{salt}:{digest}"

def old_hash_pw(pw: str) -> str:
    """النظام القديم: SHA-256 بدون salt مع تطبيع Unicode وتوحيد الترميز"""
    if pw is None:
        return ""
    try:
        import unicodedata
        normalized = unicodedata.normalize("NFC", str(pw).strip())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    except Exception:
        return ""

def hash_pw(password: str) -> str:
    """يُستخدم لإنشاء/تحديث كلمات المرور الجديدة (النظام الجديد مع salt)"""
    return secure_hash(password)

def verify_password(password: str, stored_hash: str) -> bool:
    """التحقق المتوافق: يدعم القديم (SHA-256) والجديد (salt:hash) مع تنظيف المسافات المحتملة."""
    if not password or not stored_hash:
        return False
    try:
        import unicodedata
        pw_norm = unicodedata.normalize("NFC", str(password).strip())
        # تنظيف قيمة الهاش المخزنة
        sh = str(stored_hash).strip()
        # نظام قديم: بدون ':'
        if ":" not in sh:
            return sh == old_hash_pw(pw_norm)
        # نظام جديد: salt:hash مع تنظيف الأجزاء
        parts = sh.split(":", 1)
        if len(parts) != 2:
            return False
        salt, hash_part = (parts[0] or "").strip(), (parts[1] or "").strip()
        if not salt or not hash_part:
            return False
        # إعادة بناء الصيغة بعد التنظيف للمقارنة النهائية
        cleaned_stored = f"{salt}:{hash_part}"
        expected = secure_hash(pw_norm, salt)
        return expected == cleaned_stored
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

# إنشاء المجلدات
for p in [DB_PATH.parent, STORAGE_DIR, EXPORTS_DIR, RESOURCES_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# ---------------------------- أنماط CSS مخصصة ---------------------------- #
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    /* توسيع العرض الأقصى للصفحة الرئيسية */
    .main {
        background-color: #f8f9fa;
        color: #333;
        direction: rtl;
        font-family: 'Cairo', sans-serif;
        max-width: 100vw; 
        padding-left: 2rem;
        padding-right: 2rem;
        margin: 0 auto;
    }
    
    .stForm {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 100%;
    }
    
    .stDataFrame {
        width: 100% !important;
    }
    
    .stButton>button {
        background-color: #1a56db;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
        width: auto;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #1e40af;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stTextArea>div>div>textarea {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px;
        font-family: 'Cairo', sans-serif;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #1a56db;
        box-shadow: 0 0 0 2px rgba(26, 86, 219, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-size: 16px;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
    }
    
    h1, h2, h3 {
        color: #1e40af;
        font-family: 'Cairo', sans-serif;
        margin-bottom: 1rem;
    }
    
    .header {
        text-align: center;
        color: #1e40af;
        font-weight: 700;
        margin-bottom: 30px;
        font-family: 'Cairo', sans-serif;
        padding: 20px;
        background: linear-gradient(135deg, #f0f4ff 0%, #e6eeff 100%);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .subheader {
        color: #1a56db;
        font-weight: 600;
        margin-top: 25px;
        margin-bottom: 15px;
        border-bottom: 3px solid #dbeafe;
        padding-bottom: 10px;
        font-family: 'Cairo', sans-serif;
    }
    
    .info-box {
        background-color: #dbeafe;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #1e40af;
        margin: 15px 0;
        font-family: 'Cairo', sans-serif;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .logo-container {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .logo-container img {
        max-width: 180px;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .footer {
        text-align: center;
        margin-top: 40px;
        padding: 25px;
        border-top: 2px solid #e2e8f0;
        color: #64748b;
        font-size: 14px;
        width: 100%;
        background-color: #f8fafc;
    }
    
    .stats-card {
        background-color: white;
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
        width: 100%;
        transition: transform 0.3s ease;
    }
    
    .stats-card:hover {
        transform: translateY(-5px);
    }
    
    .stats-header {
        color: #1e40af;
        font-weight: 700;
        margin-bottom: 20px;
        font-size: 20px;
        text-align: center;
    }
    
    .stats-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .stats-label {
        font-weight: 600;
        color: #374151;
    }
    
    .stats-value {
        font-weight: 700;
        color: #1e40af;
        background-color: #dbeafe;
        padding: 4px 12px;
        border-radius: 20px;
        min-width: 40px;
        text-align: center;
    }
    
    section[data-testid="stSidebar"] {
        width: 320px !important; /* زيادة عرض القائمة الجانبية */
        background: linear-gradient(180deg, #87CEEB 0%, #B0E2FF 50%, #87CEFA 100%);
        color: white;
}
    
    /* تكبير الخط في القائمة الجانبية */
    section[data-testid="stSidebar"] .st-emotion-cache-16idsys p {
        font-size: 1.1rem !important;
        font-weight: 600;
    }


    .sidebar-content {
        padding: 20px;
}
    
    .sidebar-title {
        color: white;
        font-weight: 700;
        margin-bottom: 20px;
        text-align: center;
        font-size: 24px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}
    
    .sidebar-item {
       padding: 12px 15px;
       margin: 8px 0;
       border-radius: 8px;
       transition: background-color 0.3s ease;
       cursor: pointer;
       color: white;
       font-weight: 500;
       font-size: 16px;
       text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);

}
    
    .sidebar-item:hover {
       background-color: rgba(255, 255, 255, 0.2);
       color: white;
}
    
    .sidebar-item.active {
       background-color: rgba(255, 255, 255, 0.3);
       color: white;
       font-weight: 600;
       background-color: rgba(255, 255, 255, 0.4);

}
    
    /* تحسين المظهر للجداول */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .dataframe th {
        background-color: #1e40af !important;
        color: white !important;
        font-weight: 600;
        padding: 12px;
    }
    
    .dataframe td {
        padding: 10px;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .dataframe tr:hover {
        background-color: #f1f5f9 !important;
    }
    
    /* تحسين أزرار التنزيل */
    .stDownloadButton>button {
        background-color: #10b981;
        width: 100%;
    }
    
    .stDownloadButton>button:hover {
        background-color: #059669;
    }
    
    /* تحسين أزرار الحذف */
    .delete-button>button {
        background-color: #ef4444;
    }
    
    .delete-button>button:hover {
        background-color: #dc2626;
    }
    
    /* تحسين رسائل التنبيه */
    .stAlert {
        border-radius: 8px;
    }
    
    /* تحسين الأقسام القابلة للطي */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 18px;
        color: #1e40af;
    }
    
    /* تحسين أشرطة التقدم */
    .stProgress > div > div > div {
        background-color: #1e40af;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------- ثوابت وخيارات ---------------------------- #
DEFAULT_HOSPITAL_TYPES = ["حكومي", "خاص"]
DEFAULT_SECTORS = [
    "المستشفيات التعليمية", "القطاع العلاجي", "المؤسسه العلاجيه",
    "امانة المراكز الطبية المتخصصة", "التأمين الصحي", "المستشفيات الجامعية",
    "القوات المسلحه", "الشرطه", "المستشفيات الخاصه", "الهيئه العامه للرعايه الصحيه"
]
DEFAULT_GOVERNORATES = [
    "القاهره", "الجيزه", "الاسكندريه", "الدقهليه", "البحر الاحمر", "البحيره",
    "الفيوم", "الغربية", "الإسماعيلية", "المنوفية", "المنيا", "القليوبية",
    "الوادي الجديد", "سوهاج", "أسوان", "أسيوط", "الشرقية", "دمياط",
    "بورسعيد", "البحر الأحمر", "السويس", "شمال سيناء", "جنوب سيناء",
    "كفر الشيخ", "مطروح", "البحر الأحمر", "الاقصر", "قنا", "بني سويف"
]
DEFAULT_SERVICES = [
    "جراحة أورام",
    "زراعة كبد",
    "جراحة الأوعية الدموية والقسطرة الطرفية",
    "قسطرة قلبية",
    "قلب مفتوح",
    "زراعة قوقعة",
    "جراحة عيون",
    "قسطرة مخية",
    "جراحة مخ وأعصاب",
    "جراحة عظام",
    "زراعة كلى",
]
AGE_CATEGORIES = ["كبار", "أطفال", "كبار وأطفال"]
DEFAULT_REQUEST_STATUSES = [
    "جاري دراسة الطلب ومراجعة الأوراق",
    "جارِ المعاينة",
    "يجب استيفاء متطلبات التعاقد",
    "قيد الانتظار",
    "مقبول",
    "مرفوض",
    "إرجاء التعاقد",
    "لا يوجد حاجة للتعاقد",
    "مغلق",
    "إعادة تقديم",
    "طلب غير مكتمل",
]
DOC_TYPES = [
    "ترخيص العلاج الحر موضح به التخصصات",
    "ترخيص الوحدات",
    "صورة بطاقة ضريبية للمنشأة سارية",
    "صورة حديثة للسجل التجاري",
    "طلب موجه لمدير المشروع بالتخصصات المطلوب المشاركة بها (خطاب موقع ومعتمد من السيد الدكتور رئيس القطاع في حال تعاقد مستشفى حكومي)",
    "بيان معتمد بالسعة الاستيعابية الشهرية لكل تخصص (عدد العمليات/شهريًا)",
    "بيان بالأجهزة والتجهيزات الطبية (مرفق عقود الصيانة - بيان بتاريخ تصنيع الأجهزة)",
    "قائمة بالجراحين والأطباء (المؤهلات - شهادة خبرة معتمدة - سابقة أعمال بعدد الحالات)",
    "بيانات السادة الجراحين والأطباء (جهة العمل الحكومية - أرقام التليفون - صورة كارنيه النقابة)",
    "شهادة الحماية المدنية",
    "تقييم مكافحة العدوى (ذاتي)",
    "تقييم مكافحة العدوى من الجهة التابع لها المستشفى",
    "عقد تداول النفايات",
    "استيفاء نماذج اعتماد المنشأة بالمشروع الخاصة بكل تخصص",
    "فيديو لغرف العمليات والإقامة",
    "السعة السريرية الكلية - عدد أسرة الرعايات",
    "تشكيل فريق مكافحة العدوى - تشكيل فريق الجودة",
    "محاضر اجتماعات الفرق لآخر 3 أشهر",
    "السياسات الخاصة بالجراحة والتخدير معتمدة",
    "أخرى",
]
GOVERNMENT_OPTIONAL_DOCS = {
    "ترخيص العلاج الحر موضح به التخصصات",
    "صورة بطاقة ضريبية للمنشأة سارية",
    "صورة حديثة للسجل التجاري",
    "أخرى",
    "تقييم مكافحة العدوى (ذاتي)"
}
PRIVATE_OPTIONAL_DOCS = set(["أخرى","تقييم مكافحة العدوى من الجهة التابع لها المستشفى"])
RESOURCE_FILES = [
    "متطلبات التعاقد.pdf",
    "طريقة التسجيل.pdf",
    "اللائحه الاسترشاديه.pdf",
    "القلب المفتوح.pdf",
    "القسطره القلبيه.pdf",
    "الاوعيه الدمويه والقسطره الطرفيه.pdf",
    "القسطره المخيه.pdf",
    "المخ والاعصاب.pdf",
    "الرمد.pdf",
    "العظام.pdf",
    "الاورام.pdf",
    "زراعة الكبد.pdf",
    "زراعة الكلى.pdf",
    "زراعة القوقعه.pdf"
    
]

# تعريف إعدادات الحالات كثوابت لتجنب التعارض
STATUS_SETTINGS_DEFAULTS = {
    "open": {"طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "جارِ المعاينة", "يجب استيفاء متطلبات التعاقد", "قيد الانتظار", "مقبول"},
    "blocked": {"مرفوض", "إرجاء التعاقد"},
    "final": {"إعادة تقديم", "مقبول", "مرفوض", "مغلق", "إرجاء التعاقد", "لا يوجد حاجة للتعاقد"}
}

# دالة لتحديث المستندات الاختيارية في الطلبات الموجودة
def update_existing_requests_optional_docs():
    """تحديث المستندات الاختيارية في الطلبات الموجودة عند تغيير الإعدادات"""
    try:
        with get_conn() as conn:
            hospital_types = get_hospital_types()
            total_updated = 0
            
            for htype in hospital_types:
                optional_docs = get_optional_docs_for_type(htype)
                all_doc_names = [dt['name'] for dt in get_document_types()]
                
                # الحصول على جميع الطلبات لهذا النوع من المستشفيات
                requests = conn.execute(
                    "SELECT r.id FROM requests r JOIN hospitals h ON r.hospital_id = h.id WHERE h.type = ? AND r.deleted_at IS NULL", 
                    (htype,)
                ).fetchall()
                
                for req in requests:
                    # تحديث حالة المطلوب/اختياري للمستندات
                    for doc_name in all_doc_names:
                        is_required = 0 if doc_name in optional_docs else 1
                        result = conn.execute(
                            "UPDATE documents SET required = ? WHERE request_id = ? AND doc_type = ?", 
                            (is_required, req['id'], doc_name)
                        )
                        total_updated += result.rowcount
            
            conn.commit()
            print(f"تم تحديث {total_updated} مستند في الطلبات الموجودة")
            
    except Exception as e:
        print(f"خطأ في تحديث المستندات الاختيارية: {e}")






# ---------------------------- أدوات مساعدة ---------------------------- #
def generate_username(hospital_name: str) -> str:
    arabic_to_english = {
        'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'g', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's',
        'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': '3', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
        'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ى': 'a', 'ئ': '2', 'ء': '2', 'ؤ': '2'
    }
    
    hospital_name = str(hospital_name)
    english_name = ""
    for char in hospital_name:
        if char in arabic_to_english:
            english_name += arabic_to_english[char]
        elif char.isalpha() or char.isdigit():
            english_name += char
        else:
            english_name += "_"
            
    words = re.split(r"[_\s\-]+", english_name.lower())
    valid_words = [word for word in words if word]
    username = "".join(valid_words[:3]) 
    
    username = re.sub(r"[^\w]", "", username)
    username = username.strip("_")
    
    if not username or username[0].isdigit():
        username = "hospital_" + username
    
    return username[:20] or "hospital"

@contextmanager
def get_conn():
    """Context manager for database connections with proper cleanup."""
    conn = None
    try:
        conn = sqlite3.connect(
            DB_PATH, 
            check_same_thread=False, 
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=30.0
        )
        conn.row_factory = sqlite3.Row
        # تفعيل WAL mode لتحسين الأداء وتقليل القفل
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        yield conn
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            import time
            time.sleep(0.1)
            try:
                if conn:
                    conn.close()
                conn = sqlite3.connect(
                    DB_PATH, 
                    check_same_thread=False, 
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                    timeout=30.0
                )
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                yield conn
            except sqlite3.Error as db_error:
                print(f"Database connection error: {db_error}")
                raise db_error
        else:
            print(f"Database operational error: {e}")
            raise e
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        raise e
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing database connection: {e}")

# تم توحيد دوال التجزئة في hash_pw أعلاه ولا حاجة لتعريفات إضافية هنا

def check_file_type(filename: str, is_video_allowed: bool) -> bool:
    ext = Path(filename).suffix.lower()
    allowed_extensions = {'.pdf'}
    if is_video_allowed:
        allowed_extensions.update({'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'})
    return ext in allowed_extensions

def safe_filename(name: str) -> str:
    if not name:
        return "file"
    # إزالة المسارات الخطيرة
    name = name.replace("..", "").replace("/", "_").replace("\\", "_")
    name = re.sub(r"[^\w\-\.\u0621-\u064A\s]", "_", name)
    name = re.sub(r"\s+", "_", name).strip("_.")
    # تجنب الأسماء المحجوزة
    reserved_names = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
    if name.upper() in reserved_names:
        name = f"_{name}"
    return name or "file"

def is_video_only_document(doc_type_name: str) -> bool:
    VIDEO_ONLY_DOCUMENTS = {"فيديو لغرف العمليات والإقامة"}
    return doc_type_name in VIDEO_ONLY_DOCUMENTS

def cleanup_memory():
    """تنظيف الذاكرة المؤقتة وتحرير الموارد"""
    try:
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        if hasattr(st, 'cache_resource'):
            st.cache_resource.clear()
        
        keys_to_remove = [k for k in st.session_state.keys() 
                         if k.startswith(('upload_processed_', 'dl_', 'delete_', 'save_', 'sat_', 'req_admin_', 'cm_'))]
        
        for key in keys_to_remove:
            st.session_state.pop(key, None)
        
        import gc
        gc.collect()
        
        return True
    except Exception as e:
        print(f"Error in cleanup_memory: {e}")
        return False

def force_refresh_cache():
    """إجبار تحديث الذاكرة المؤقتة لضمان عرض البيانات المحدثة"""
    try:
        # مسح جميع الدوال المخزنة مؤقتاً
        functions_to_clear = [
            get_list_from_meta, get_hospital_types, get_sectors, get_governorates,
            get_request_statuses, get_preventing_statuses, get_blocking_statuses,
            get_document_types, get_optional_docs_for_type, get_active_services,
            get_all_services, get_all_hospitals, get_all_sectors, get_active_service_names
        ]
        
        for func in functions_to_clear:
            if hasattr(func, 'clear'):
                func.clear()
        
        return True
    except Exception as e:
        print(f"Error in force_refresh_cache: {e}")
        return False

def safe_file_operation(operation, *args, **kwargs):
    """تنفيذ عمليات الملفات بشكل آمن مع إدارة الأخطاء"""
    try:
        return operation(*args, **kwargs)
    except PermissionError:
        import time
        time.sleep(0.1)  # انتظار قصير ثم محاولة مرة أخرى
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            print(f"File operation failed after retry: {e}")
            return False
    except Exception as e:
        print(f"File operation failed: {e}")
        return False

def parse_date_safely(date_str: str, default_value=None):
    """محاولة تحويل نص إلى تاريخ بأمان، وإرجاع قيمة افتراضية عند الفشل."""
    if not date_str or date_str == "غير محدد":
        return default_value
    try:
        # errors='coerce' سيجعل pandas يعيد NaT (Not a Time) عند الفشل
        dt = pd.to_datetime(date_str, errors='coerce')
        return dt.date() if pd.notna(dt) else default_value
    except Exception:
        return default_value
# ---------------------------- وظائف مساعدة للإعدادات ---------------------------- #
@st.cache_data(ttl=3600)
def get_list_from_meta(key: str, default_list: list) -> list:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return (row["value"].split(",") if row and row["value"] else []) or default_list

@st.cache_data(ttl=1800)
def get_hospital_types() -> list:
    return get_list_from_meta('hospital_types', DEFAULT_HOSPITAL_TYPES)

def set_hospital_types(types: list):
    with get_conn() as conn:
        conn.execute("INSERT INTO meta(key,value) VALUES('hospital_types', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (",".join(types),))
        conn.commit()
    # مسح الذاكرة المؤقتة لضمان تحديث البيانات
    get_hospital_types.clear()
    get_list_from_meta.clear()

@st.cache_data(ttl=1800)
def get_sectors() -> list:
    return get_list_from_meta('sectors', DEFAULT_SECTORS)

def set_sectors(sectors: list):
    with get_conn() as conn:
        conn.execute("INSERT INTO meta(key,value) VALUES('sectors', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (",".join(sectors),))
        conn.commit()
    # مسح الذاكرة المؤقتة
    get_sectors.clear()
    get_list_from_meta.clear()

@st.cache_data(ttl=1800)
def get_governorates() -> list:
    return get_list_from_meta('governorates', DEFAULT_GOVERNORATES)

def set_governorates(gov: list):
    with get_conn() as conn:
        conn.execute("INSERT INTO meta(key,value) VALUES('governorates', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (",".join(gov),))
        conn.commit()
    # مسح الذاكرة المؤقتة
    get_governorates.clear()
    get_list_from_meta.clear()

@st.cache_data(ttl=600)
def get_request_statuses() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM request_statuses ORDER BY id").fetchall()
        return [row['name'] for row in rows] if rows else DEFAULT_REQUEST_STATUSES

@st.cache_data(ttl=600)
def get_preventing_statuses() -> set:
    """الحصول على الحالات التي تمنع تقديم طلب جديد."""
    with get_conn() as conn:
        rows = conn.execute("SELECT status_name FROM status_settings WHERE prevents_new_request = 1").fetchall()
        return {row['status_name'] for row in rows}

@st.cache_data(ttl=600)
def get_blocking_statuses() -> set:
    """الحصول على الحالات التي تمنع التقديم لفترة معينة."""
    with get_conn() as conn:
        rows = conn.execute("SELECT status_name FROM status_settings WHERE blocks_service_for_days > 0").fetchall()
        return {row['status_name'] for row in rows}

def is_final_status(status: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT is_final_state FROM status_settings WHERE status_name = ?", (status,)).fetchone()
        return row and row['is_final_state'] == 1

@st.cache_data(ttl=1800)
def get_document_types() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT name, display_name, is_video_allowed FROM document_types ORDER BY name").fetchall()
        return [{'name': r['name'], 'display_name': r['display_name'], 'is_video_allowed': r['is_video_allowed']} for r in rows]

@st.cache_data(ttl=1800)
def get_optional_docs_for_type(hospital_type: str) -> set:
    with get_conn() as conn:
        rows = conn.execute("SELECT doc_name FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,)).fetchall()
        return {row['doc_name'] for row in rows}

def set_optional_docs_for_type(hospital_type: str, doc_names: list):
    """تحديد المستندات الاختيارية لنوع معين من المستشفيات"""
    with get_conn() as conn:
        # حذف الإعدادات القديمة
        conn.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,))
        
        # إضافة الإعدادات الجديدة
        if doc_names:
            conn.executemany(
                "INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", 
                [(hospital_type, name) for name in doc_names if name]
            )
        
        conn.commit()
    
    # تحديث الطلبات الموجودة فوراً
    update_existing_requests_optional_docs()
    
    # مسح الذاكرة المؤقتة لضمان التحديث
    get_optional_docs_for_type.clear()
    get_document_types.clear()
    
    print(f"تم تحديث المستندات الاختيارية لـ {hospital_type}: {doc_names}")

def ensure_request_docs(request_id: int, hospital_type: str):
    """ضمان وجود جميع المستندات للطلب مع تحديث حالة المطلوب/الاختياري"""
    with get_conn() as conn:
        existing = {r["doc_type"] for r in conn.execute("SELECT doc_type FROM documents WHERE request_id=?", (request_id,)).fetchall()}
        optional_docs = get_optional_docs_for_type(hospital_type)
        all_doc_types = get_document_types()
        
        # إضافة المستندات المفقودة
        docs_to_insert = []
        for dt in all_doc_types:
            dt_name = dt['name']
            if dt_name not in existing:
                required = 0 if dt_name in optional_docs else 1
                docs_to_insert.append((request_id, dt_name, dt['display_name'], required, 0, None, dt['is_video_allowed'], datetime.now().isoformat()))
        
        if docs_to_insert:
            conn.executemany(
                "INSERT INTO documents (request_id, doc_type, display_name, required, satisfied, uploaded_at, is_video_allowed, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                docs_to_insert
            )
        
        # تحديث جميع المستندات الموجودة بناءً على الإعدادات الحالية
        for dt in all_doc_types:
            dt_name = dt['name']
            required = 0 if dt_name in optional_docs else 1
            conn.execute(
                "UPDATE documents SET required = ?, display_name = ?, is_video_allowed = ?, updated_at = ? WHERE request_id = ? AND doc_type = ?", 
                (required, dt['display_name'], dt['is_video_allowed'], datetime.now().isoformat(), request_id, dt_name)
            )
        
        conn.commit()
    
def hospital_has_open_request(hospital_id: int, service_id: int, prevented_statuses: set) -> bool:
    """التحقق من وجود طلب مفتوح (منع التقديم) لنفس الخدمة"""
    if not prevented_statuses:
        return False
    with get_conn() as conn:
        placeholders = ",".join(["?"] * len(prevented_statuses))
        query = f"""
            SELECT 1
            FROM requests
            WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL AND status IN ({placeholders})
            LIMIT 1
        """
        params = [hospital_id, service_id] + list(prevented_statuses)
        return conn.execute(query, params).fetchone() is not None

def hospital_blocked_from_request(hospital_id: int, service_id: int, blocked_statuses: set) -> bool:
    """التحقق من منع المستشفى من تقديم طلب لنفس الخدمة لمدة 3 أشهر"""
    if not blocked_statuses:
        return False
    with get_conn() as conn:
        three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
        placeholders = ",".join(["?"] * len(blocked_statuses))
        query = f"""
            SELECT 1
            FROM requests
            WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL AND status IN ({placeholders}) AND closed_at > ?
            LIMIT 1
        """
        params = [hospital_id, service_id] + list(blocked_statuses) + [three_months_ago]
        return conn.execute(query, params).fetchone() is not None

def is_hospital_profile_complete(hospital_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT manager_name, manager_phone, address FROM hospitals WHERE id=?", (hospital_id,)).fetchone()
        if not row: return False
        
        # الحقول الإلزامية فقط: مدير المستشفى، هاتف المدير، العنوان
        required_fields = [row['manager_name'], row['manager_phone'], row['address']]
        
        return all(field and str(field).strip() for field in required_fields)

# ---------------------------- نظام مراقبة التغييرات ---------------------------- #
class DatabaseChangeHandler(FileSystemEventHandler):
    """مراقب تغييرات قاعدة البيانات"""
    
    def __init__(self):
        self.last_modified = time.time()
        self.debounce_time = 1.0  # ثانية واحدة لتجنب التحديثات المتعددة
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        current_time = time.time()
        if current_time - self.last_modified > self.debounce_time:
            self.last_modified = current_time
            # تشغيل migrations عند تغيير قاعدة البيانات
            try:
                run_migrations()
                # مسح الذاكرة المؤقتة لضمان تحديث البيانات
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
            except Exception as e:
                print(f"خطأ في تحديث قاعدة البيانات: {e}")

def start_database_monitor():
    """بدء مراقبة تغييرات قاعدة البيانات"""
    # تعطيل مراقبة التغييرات مؤقتاً لتجنب مشاكل القفل
    pass

# ---------------------------- إعداد قاعدة البيانات ---------------------------- #
DB_SCHEMA_VERSION = 5

def get_current_schema_version():
    """الحصول على إصدار قاعدة البيانات الحالي"""
    try:
        with get_conn() as conn:
            result = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            return int(result['value']) if result else 0
    except:
        return 0

def set_schema_version(version):
    """تحديث إصدار قاعدة البيانات"""
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)", (str(version),))
        conn.commit()

def run_migrations():
    """تشغيل migrations لتحديث قاعدة البيانات تلقائياً"""
    try:
        current_version = get_current_schema_version()
        
        if current_version < DB_SCHEMA_VERSION:
            with get_conn() as conn:
                # إضافة جدول activity_log إذا لم يكن موجوداً
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        username TEXT,
                        user_role TEXT,
                        action TEXT NOT NULL,
                        details TEXT
                    )""")
                
                # إضافة الفهارس لتحسين الأداء
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_hospital_service ON requests(hospital_id, service_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_request_id ON documents(request_id)")
                
                conn.commit()
                set_schema_version(DB_SCHEMA_VERSION)
    except Exception as e:
        print(f"خطأ في migrations: {e}")
        # لا نرفع الخطأ لتجنب إيقاف التطبيق
        pass

def run_ddl():
    with get_conn() as conn:
        cur = conn.cursor()
        
        cur.execute("""CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'admin')""")
        cur.execute("""CREATE TABLE IF NOT EXISTS hospitals (id INTEGER PRIMARY KEY, name TEXT NOT NULL, sector TEXT, governorate TEXT, code TEXT UNIQUE, type TEXT DEFAULT 'خاص', address TEXT, other_branches TEXT, other_branches_address TEXT, license_start TEXT, license_end TEXT, manager_name TEXT, manager_phone TEXT, license_number TEXT, username TEXT UNIQUE, password_hash TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY, name TEXT UNIQUE, active INTEGER DEFAULT 1)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY, hospital_id INTEGER, service_id INTEGER, age_category TEXT, status TEXT DEFAULT 'طلب غير مكتمل', admin_note TEXT, created_at TEXT, deleted_at TEXT, closed_at TEXT, updated_at TEXT, FOREIGN KEY (hospital_id) REFERENCES hospitals(id), FOREIGN KEY (service_id) REFERENCES services(id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, request_id INTEGER, doc_type TEXT, display_name TEXT, file_name TEXT, file_path TEXT, required INTEGER DEFAULT 1, satisfied INTEGER DEFAULT 0, admin_comment TEXT, uploaded_at TEXT, is_video_allowed INTEGER DEFAULT 0, updated_at TEXT, FOREIGN KEY (request_id) REFERENCES requests(id))""")
        
        # إضافة عمود updated_at إذا لم يكن موجوداً
        try:
            cur.execute("ALTER TABLE documents ADD COLUMN updated_at TEXT")
        except sqlite3.OperationalError:
            pass  # العمود موجود مسبقاً
        cur.execute("""CREATE TABLE IF NOT EXISTS document_types (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL, description TEXT, is_video_allowed INTEGER DEFAULT 0)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS hospital_type_optional_docs (id INTEGER PRIMARY KEY, hospital_type TEXT NOT NULL, doc_name TEXT NOT NULL, UNIQUE(hospital_type, doc_name))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS meta (`key` TEXT PRIMARY KEY, value TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS request_statuses (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS status_settings (status_name TEXT PRIMARY KEY, prevents_new_request INTEGER DEFAULT 0, blocks_service_for_days INTEGER DEFAULT 0, is_final_state INTEGER DEFAULT 0, FOREIGN KEY (status_name) REFERENCES request_statuses(name) ON DELETE CASCADE)""")

        # سيتم إنشاء الجداول والأعمدة الإضافية في نظام migrations
        pass

        if cur.execute("SELECT COUNT(1) FROM admins").fetchone()[0] == 0:
            # إنشاء مستخدم إداري افتراضي بكلمة مرور ثابتة
            default_password = "admin123"
            cur.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", ("admin", hash_pw(default_password), "admin"))
            print(f"Default admin password set to: {default_password}")
        
        if cur.execute("SELECT COUNT(1) FROM services").fetchone()[0] == 0:
            cur.executemany("INSERT INTO services (name) VALUES (?)", [(s,) for s in DEFAULT_SERVICES])
        
        if cur.execute("SELECT COUNT(1) FROM document_types").fetchone()[0] == 0:
            video_allowed = {"فيديو لغرف العمليات والإقامة"}
            cur.executemany("INSERT INTO document_types (name, display_name, is_video_allowed) VALUES (?, ?, ?)", 
                            [(d, d, 1 if d in video_allowed else 0) for d in DOC_TYPES])

        if cur.execute("SELECT COUNT(1) FROM request_statuses").fetchone()[0] == 0:
            cur.executemany("INSERT INTO request_statuses (name) VALUES (?)", [(s,) for s in DEFAULT_REQUEST_STATUSES])
            
        if cur.execute("SELECT COUNT(1) FROM status_settings").fetchone()[0] == 0:
            open_statuses = STATUS_SETTINGS_DEFAULTS["open"]
            blocked_statuses = STATUS_SETTINGS_DEFAULTS["blocked"]
            final_statuses = STATUS_SETTINGS_DEFAULTS["final"]
            settings = [(s, 1 if s in open_statuses else 0, 90 if s in blocked_statuses else 0, 1 if s in final_statuses else 0) for s in DEFAULT_REQUEST_STATUSES]
            cur.executemany("INSERT INTO status_settings VALUES (?, ?, ?, ?)", settings)

        # تحديث المستندات الاختيارية فقط إذا لم تكن موجودة
        if cur.execute("SELECT COUNT(1) FROM hospital_type_optional_docs").fetchone()[0] == 0:
            cur.executemany("INSERT INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", 
                            [("حكومي", d) for d in GOVERNMENT_OPTIONAL_DOCS] + [("خاص", d) for d in PRIVATE_OPTIONAL_DOCS])
        
        # سيتم تحديث المستندات في نظام migrations
        pass
        
        conn.commit()

# --- إضافة جديدة: دالة تسجيل النشاط ---
def log_activity(action: str, details: str = ""):
    """يسجل نشاط المستخدم في قاعدة البيانات."""
    user = st.session_state.get("user")
    if not user:
        return  # لا تسجل أي شيء إذا لم يكن هناك مستخدم مسجل

    username = user.get("username")
    user_role = user.get("role")
    
    with get_conn() as conn:
        conn.execute("INSERT INTO activity_log (timestamp, username, user_role, action, details) VALUES (?, ?, ?, ?, ?)",
                     (datetime.now().isoformat(), username, user_role, action, details))
        conn.commit()

# ---------------------------- واجهة الدخول ---------------------------- #
def login_ui():
    banner_path = next((p for p in [Path("static/banner.png"), Path("static/banner.jpg")] if p.exists()), None)
    
    if banner_path:
        with open(banner_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded_string}' class='banner-image'></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='header'><h1>{APP_TITLE}</h1></div>", unsafe_allow_html=True)
    

    with st.form("login_form"):
        st.markdown("### تسجيل الدخول")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("تسجيل الدخول"):
            # تقليم وتطبيع لتوحيد السلوك بين البيئات
            import unicodedata
            uname = unicodedata.normalize("NFC", (username or "").strip())
            pw = unicodedata.normalize("NFC", (password or "").strip())
            if not uname or not pw:
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور")
            else:
                with get_conn() as conn:
                    # الاستعلام باستخدام uname بعد التطبيع
                    hospital_user = conn.execute("SELECT * FROM hospitals WHERE username=?", (uname,)).fetchone()
                    admin_user = conn.execute("SELECT * FROM admins WHERE username=?", (uname,)).fetchone()
                    user_data = hospital_user or admin_user
                    table_name = "hospitals" if hospital_user else "admins"

                    if user_data and user_data['password_hash']:
                        # التحقق باستخدام pw بعد التطبيع
                        if verify_password(pw, user_data['password_hash']):
                            # ترقية تلقائية إذا كان الهاش قديم بدون salt
                            sh = str(user_data['password_hash']).strip()
                            if ":" not in sh:
                                try:
                                    new_hash = hash_pw(pw)
                                    conn.execute(f"UPDATE {table_name} SET password_hash=? WHERE id=?", (new_hash, user_data['id']))
                                    conn.commit()
                                except Exception as e:
                                    print(f"Password upgrade failed: {e}")
                            role = "hospital" if hospital_user else user_data["role"]
                            st.session_state.user = {"role": role, **dict(user_data)}
                            log_activity("تسجيل الدخول")
                            st.success("تم تسجيل الدخول بنجاح")
                            st.rerun()
                    # فشل موحّد
                    if 'user' not in st.session_state:
                        time.sleep(0.1)
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# ---------------------------- صفحات المستشفى ---------------------------- #
def hospital_home():
    user = st.session_state.user
    logo_path = Path("static/logo.png")
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=80)
    
    st.sidebar.markdown(f"### أهلاً بكِ")
    st.sidebar.markdown(f"**{user['name']}**")
    st.sidebar.markdown("---")

    menu_items = ["🏠 الصفحة الرئيسية", "📝 تقديم طلب جديد", "📂 طلباتي", "📥 ملفات للتنزيل", "🔑 تغيير كلمة المرور", "🚪 تسجيل الخروج"]
    menu_icons = ["house-fill", "file-earmark-plus-fill", "folder-fill", "download", "key-fill", "box-arrow-right"]

    with st.sidebar:
        selection = option_menu(None, menu_items, icons=menu_icons, menu_icon="cast", default_index=0)

    # Mapping selection to functions
    menu_options = {"🏠 الصفحة الرئيسية": hospital_dashboard_ui, "📝 تقديم طلب جديد": hospital_new_request_ui, "📂 طلباتي": hospital_requests_ui, "📥 ملفات للتنزيل": lambda u: resources_download_ui(), "🔑 تغيير كلمة المرور": lambda u: change_password_ui(user_id=u["id"], user_table="hospitals")}
    
    if selection == "🚪 تسجيل الخروج":
        st.session_state.clear()
        st.rerun()
    else:
        menu_options[selection](user)

def hospital_dashboard_ui(user: dict):
    st.markdown("<div class='subheader'>ملف المستشفى</div>", unsafe_allow_html=True)

    # إظهار رسالة النجاح الثابتة إذا كانت موجودة في حالة الجلسة
    if st.session_state.get("profile_update_success"):
        st.success("تم تحديث بياناتك بنجاح. يمكنك الآن تقديم طلبك من القائمة الجانبية.")
        del st.session_state["profile_update_success"] # حذف الرسالة بعد عرضها مرة واحدة

    with get_conn() as conn:
        hospital = conn.execute("SELECT * FROM hospitals WHERE id=?", (user["id"],)).fetchone()
    
    # checkbox خارج الـ form
    if hospital['type'] != 'حكومي':
        current_no_end = hospital['license_end'] == "غير محدد" or not hospital['license_end']
        no_end_date = st.checkbox("ترخيص دائم (بدون تاريخ انتهاء)", value=current_no_end, key="no_end_date_checkbox")
    else:
        no_end_date = False
    
    with st.form("edit_hospital_profile"):
        st.info("يمكنك تحديث بيانات التواصل والترخيص من هنا. لتغيير البيانات الأساسية، يرجى التواصل مع الإدارة.")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("اسم المستشفى", value=hospital['name'], disabled=True)
            st.text_input("القطاع", value=hospital['sector'] or "", disabled=True)
            st.text_input("المحافظة", value=hospital['governorate'] or "", disabled=True)
        with col2:
            st.text_input("كود المستشفى", value=hospital['code'], disabled=True)
            st.text_input("نوع المستشفى", value=hospital['type'] or "", disabled=True)
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        with col3:
            # تواريخ الترخيص للمستشفيات الخاصة فقط - لا تظهر للحكومية
            if hospital['type'] != 'حكومي':
                license_start = st.date_input("بداية الترخيص", value=parse_date_safely(hospital['license_start']), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
                license_number = st.text_input("رقم الترخيص", value=hospital['license_number'] or "")
            else:
                license_start = None
                license_number = st.text_input("رقم الترخيص (اختياري)", value=hospital['license_number'] or "")
            manager_name = st.text_input("مدير المستشفى", value=hospital['manager_name'] or "")
        with col4:
            # تاريخ النهاية - للمستشفيات الخاصة فقط
            if hospital['type'] != 'حكومي':
                if not no_end_date:
                    license_end = st.date_input("تاريخ انتهاء الترخيص", value=parse_date_safely(hospital['license_end'], date.today()), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
                else:
                    license_end = "غير محدد"
            else:
                license_end = None
            manager_phone = st.text_input("هاتف المدير", value=hospital['manager_phone'] or "")
            address = st.text_area("عنوان المستشفى", value=hospital['address'] or "", height=100)
        
        # إضافة حقول الفروع (اختيارية)
        st.markdown("---")
        st.markdown("**معلومات الفروع (اختياري)**")
        col5, col6 = st.columns(2)
        with col5:
            other_branches = st.text_input("الفروع الأخرى", value=hospital['other_branches'] or "", help="اختياري - أسماء الفروع الأخرى")
        with col6:
            other_branches_address = st.text_area("عناوين الفروع", value=hospital['other_branches_address'] or "", height=100, help="اختياري - عناوين الفروع الأخرى")

        if st.form_submit_button("حفظ البيانات"):
            try:
                with get_conn() as conn:
                    # تحضير قيمة license_end بشكل صحيح
                    license_end_value = None
                    if hospital['type'] != 'حكومي':
                        if license_end == "غير محدد":
                            license_end_value = "غير محدد"
                        elif license_end:
                            license_end_value = str(license_end)
                    
                    conn.execute("""
                        UPDATE hospitals SET address=?, license_start=?, license_end=?, 
                        manager_name=?, manager_phone=?, license_number=?, other_branches=?, other_branches_address=? WHERE id=?
                    """, (address, str(license_start) if license_start else None, license_end_value, 
                          manager_name, manager_phone, license_number, other_branches, other_branches_address, user["id"]))
                    conn.commit()
                st.session_state["profile_update_success"] = True # تعيين علامة النجاح
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

@st.cache_data(ttl=600)
def get_active_services():
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM services WHERE active=1 ORDER BY name").fetchall()
        return [dict(row) for row in rows]



def hospital_new_request_ui(user: dict):
    """واجهة تقديم طلب تعاقد جديد للمستشفى مع إعادة التحميل الصحيحة."""
    if not is_hospital_profile_complete(user["id"]):
        st.warning("⚠️ يجب إكمال بيانات المستشفى الأساسية أولاً (مدير المستشفى، هاتف المدير، عنوان المستشفى)")
        hospital_dashboard_ui(user)
        return

    services = get_active_services()

    st.markdown("<div class='subheader'>تقديم طلب تعاقد جديد</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يرجى اختيار الخدمة والفئة العمرية، ثم رفع المستندات المطلوبة.</div>", unsafe_allow_html=True)

    with st.form("new_request"):
        service_name = st.selectbox("الخدمة المراد التعاقد عليها", [s["name"] for s in services])
        age_category = st.selectbox("الفئة", AGE_CATEGORIES)
        submitted = st.form_submit_button("إنشاء الطلب")

    if submitted:
        service_id = next((s["id"] for s in services if s["name"] == service_name), None)
        if not service_id:
             st.error("خطأ في تحديد الخدمة.")
             return

        # جلب الحالات المانعة من قاعدة البيانات بدلاً من كتابتها بشكل ثابت
        preventing_statuses = get_preventing_statuses()
        blocking_statuses = get_blocking_statuses()
        
        if hospital_has_open_request(user["id"], service_id, preventing_statuses):
            st.error("لا يمكن إنشاء طلب جديد لنفس الخدمة قبل إغلاق الطلب الحالي من قبل الإدارة.")
            return
            
        if hospital_blocked_from_request(user["id"], service_id, blocking_statuses):
            st.error("لا يمكن تقديم طلب لنفس الخدمة لمدة 3 أشهر من تاريخ رفض الطلب أو إرجاء التعاقد.")
            return
        # =========================================================

        req_id = None
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO requests (hospital_id, service_id, age_category, status, created_at)
                VALUES (?,?,?,?,?)
            """, (user["id"], service_id, age_category, "طلب غير مكتمل", datetime.now().isoformat()))
            req_id = cur.lastrowid
            conn.commit()

        ensure_request_docs(req_id, user["type"])  # تغيير hospital_type إلى type
        st.success("تم إنشاء الطلب. يمكنك الآن رفع المستندات.")
        st.session_state["active_request_id"] = req_id
        st.session_state[f"editing_request_{req_id}"] = True 
        st.rerun() 

    req_id = st.session_state.get("active_request_id")
    is_editing = st.session_state.get(f"editing_request_{req_id}", False)

    if req_id and is_editing:
        documents_upload_ui(req_id, user, is_active_edit=True)



def documents_upload_ui(request_id: int, user: dict, is_active_edit: bool = False):
    """واجهة رفع المستندات المطلوبة - بدون إعادة تحميل"""
    st.markdown("<div class='subheader'>رفع المستندات المطلوبة</div>", unsafe_allow_html=True)
    
    ensure_request_docs(request_id, user["type"])
    
    # قراءة البيانات المحدثة في كل مرة
    with get_conn() as conn:
        docs = conn.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,)).fetchall()
        docs = [dict(d) for d in docs]

    all_required_uploaded = all(doc['satisfied'] for doc in docs if doc['required'] == 1)
    
    for doc in docs:
        cols = st.columns([3, 3, 2, 2, 2])
        with cols[0]:
            st.write(f"**{doc['display_name'] or doc['doc_type']}**")
            if doc['required'] == 1:
                 st.caption("🔴 **مطلوب**")
            else:
                 st.caption("🟡 *اختياري*")
        with cols[1]:
            allowed_types = ['pdf']
            is_video_allowed_flag = doc.get('is_video_allowed', 0)
            video_only = is_video_only_document(doc['doc_type'])
            
            if video_only:
                allowed_types = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
                st.caption("فيديو فقط")
            elif is_video_allowed_flag:
                allowed_types.extend(['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])
                st.caption("PDF أو فيديو")
            else:
                st.caption("PDF فقط")

            # استخدام form لمنع إعادة التشغيل التلقائي
            with st.form(key=f"upload_form_{request_id}_{doc['id']}", clear_on_submit=True):
                uploaded_file = st.file_uploader(
                    "رفع ملف", 
                    type=allowed_types, 
                    label_visibility="collapsed",
                    help="اختر ملف للرفع"
                )
                
                upload_button = st.form_submit_button("رفع الملف", use_container_width=True)
                
                if upload_button and uploaded_file is not None:
                    # التحقق من نوع الملف
                    if video_only:
                        file_valid = check_file_type(uploaded_file.name, True)
                    elif is_video_allowed_flag:
                        file_valid = check_file_type(uploaded_file.name, True)
                    else:
                        file_valid = uploaded_file.name.lower().endswith('.pdf')
                    
                    if file_valid:
                        if save_uploaded_file(uploaded_file, user, request_id, doc):
                            st.success("✅ تم رفع الملف بنجاح")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ فشل في رفع الملف")
                    else:
                        st.error("❌ نوع الملف غير مسموح")

        with cols[2]:
            # عرض زر التنزيل بناءً على البيانات المحدثة
            if doc.get('file_path') and doc.get('satisfied'):
                try:
                    file_path_obj = Path(doc['file_path'])
                    if file_path_obj.exists() and file_path_obj.stat().st_size > 0:
                        with open(file_path_obj, "rb") as f:
                            file_data = f.read()
                        
                        file_ext = file_path_obj.suffix.lower()
                        mime_type = "application/pdf" if file_ext == '.pdf' else "video/mp4" if file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'] else "application/octet-stream"
                        
                        st.download_button(
                            "📥 تنزيل",
                            data=file_data,
                            file_name=file_path_obj.name,
                            mime=mime_type,
                            key=f"dl_{request_id}_{doc['id']}",
                            use_container_width=True
                        )
                    else:
                        st.caption("— ملف غير موجود")
                except Exception:
                    st.caption("— خطأ")
            else:
                st.caption("— لم يتم الرفع")
            

        with cols[3]:
            if doc.get("file_path") and doc.get("satisfied"):
                delete_key = f"del_{request_id}_{doc['id']}"
                if st.button("🗑️ حذف", key=delete_key, type="secondary"):
                    # حذف الملف من القرص
                    file_path = doc.get("file_path")
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"خطأ في حذف الملف: {e}")
                    
                    # تحديث قاعدة البيانات
                    now_iso = datetime.now().isoformat()
                    with get_conn() as conn:
                        conn.execute(
                            "UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0, uploaded_at=NULL, updated_at=? WHERE id=?", 
                            (now_iso, doc["id"])
                        )
                        conn.execute("UPDATE requests SET updated_at=? WHERE id=?", (now_iso, request_id))
                        conn.commit()
                    
                    # تنظيف session state
                    keys_to_clean = [k for k in st.session_state.keys() if f"up_{request_id}_{doc['id']}" in k or f"processed_" in k]
                    for k in keys_to_clean:
                        st.session_state.pop(k, None)
                    
                    st.success("✅ تم حذف الملف بنجاح")
                    # إعادة تحميل فقط بعد الحذف لتحديث المفاتيح
                    st.rerun()
            else:
                st.write("")
        with cols[4]:
            # عرض الحالة بناءً على البيانات المحدثة
            if doc["satisfied"]:
                st.success("✅ مستوفى")
            else:
                st.error("❌ غير مستوفى")
            
    if is_active_edit:
        # عرض ملخص المستندات
        required_docs = [doc for doc in docs if doc['required'] == 1]
        optional_docs = [doc for doc in docs if doc['required'] == 0]
        required_uploaded = sum(1 for doc in required_docs if doc['satisfied'])
        optional_uploaded = sum(1 for doc in optional_docs if doc['satisfied'])
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📋 **المستندات المطلوبة:** {required_uploaded}/{len(required_docs)} مرفوعة")
        with col2:
            st.info(f"📄 **المستندات الاختيارية:** {optional_uploaded}/{len(optional_docs)} مرفوعة")
        
        if st.button("حفظ الطلب", disabled=not all_required_uploaded, use_container_width=True):
            if not all_required_uploaded: 
                 st.error("❌ لا يمكن حفظ الطلب: هناك مستندات مطلوبة لم يتم رفعها.")
                 missing_docs = [doc['display_name'] or doc['doc_type'] for doc in required_docs if not doc['satisfied']]
                 st.warning(f"المستندات المطلوبة المفقودة: {', '.join(missing_docs)}")
            else:
                with get_conn() as conn:
                    statuses = get_request_statuses()
                    initial_status = statuses[0] if statuses else "جاري دراسة الطلب ومراجعة الأوراق"
                    conn.execute("UPDATE requests SET status=?, updated_at=? WHERE id=?", (initial_status, datetime.now().isoformat(), request_id))
                    conn.commit()
                
                log_activity("تقديم طلب مكتمل", f"طلب رقم: {request_id}")
                
                for key in list(st.session_state.keys()):
                    if key.startswith(("active_request_id", f"editing_request_{request_id}", "upload_done_")):
                        st.session_state.pop(key, None)
                
                st.success("✅ تم حفظ الطلب بنجاح. سيتم مراجعته من قبل الإدارة.")
                st.balloons()
                time.sleep(0.5)
                st.rerun()
        elif not all_required_uploaded:
            st.info("⚠️ يرجى رفع جميع المستندات المطلوبة (🔴) لتفعيل زر 'حفظ الطلب'. المستندات الاختيارية (🟡) غير ملزمة.")

# ... (دالة save_uploaded_file كما هي) ...
def save_uploaded_file(file, user: dict, request_id: int, doc_row):
    """حفظ ملف مرفوع من قبل المستخدم - محسّن بالكامل"""
    if file is None:
        return False
    
    try:
        doc_dict = dict(doc_row) if hasattr(doc_row, 'keys') else doc_row
        
        # استخدام ID المستشفى بدلاً من الاسم لزيادة الأمان
        hospital_id_str = str(user["id"])
        safe_request_id = str(int(request_id))
        dest_dir = STORAGE_DIR / hospital_id_str / safe_request_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # تحديد امتداد الملف
        file_ext = Path(file.name).suffix.lower() or '.pdf'
        safe_doc_type = safe_filename(doc_dict['doc_type'])[:50]
        fn = f"{safe_doc_type}{file_ext}"
        dest_path = dest_dir / fn
        
        # حذف الملف القديم إن وجد مع معالجة الأخطاء
        if dest_path.exists():
            try:
                dest_path.unlink()
                time.sleep(0.1)  # انتظار قصير لضمان الحذف
            except PermissionError:
                # إذا كان الملف مقفل، حاول مرة أخرى
                time.sleep(0.2)
                try:
                    dest_path.unlink()
                except Exception as e:
                    print(f"تحذير: لم يتم حذف الملف القديم: {e}")
            except Exception as e:
                print(f"خطأ في حذف الملف القديم: {e}")

        # حفظ الملف الجديد
        try:
            with open(dest_path, "wb") as f:
                f.write(file.getbuffer())
        except Exception as e:
            print(f"خطأ في كتابة الملف: {e}")
            return False
        
        # التحقق من الحفظ
        if not dest_path.exists():
            print("الملف غير موجود بعد الحفظ")
            return False
            
        file_size = dest_path.stat().st_size
        if file_size == 0:
            print("الملف فارغ بعد الحفظ")
            dest_path.unlink()
            return False
            
        # تحديث قاعدة البيانات
        now_iso = datetime.now().isoformat()
        with get_conn() as conn:
            conn.execute(
                "UPDATE documents SET file_name=?, file_path=?, uploaded_at=?, satisfied=1, updated_at=? WHERE id=?",
                (fn, str(dest_path), now_iso, now_iso, doc_dict["id"])
            )
            conn.execute("UPDATE requests SET updated_at=? WHERE id=?", (now_iso, request_id))
            conn.commit()
        
        print(f"تم رفع الملف بنجاح: {fn} ({file_size} bytes)")
        return True
        
    except Exception as e:
        print(f"خطأ في رفع الملف: {e}")
        import traceback
        traceback.print_exc()
        return False

def render_file_downloader(doc: sqlite3.Row, key_prefix: str = "dl"):
    """دالة موحدة لعرض زر تنزيل الملف - مبسطة ومحسّنة"""
    if doc["file_path"] and doc["satisfied"]:
        try:
            file_path_obj = Path(doc["file_path"])
            if file_path_obj.exists() and file_path_obj.is_file():
                file_size = file_path_obj.stat().st_size
                if file_size > 0:
                    # مفتاح بسيط وفريد
                    download_key = f"{key_prefix}_{doc['id']}"
                    
                    try:
                        with open(file_path_obj, "rb") as f:
                            file_data = f.read()
                        
                        if file_data:
                            # تحديد MIME type
                            file_ext = file_path_obj.suffix.lower()
                            if file_ext == '.pdf':
                                mime_type = "application/pdf"
                            elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
                                mime_type = "video/mp4"
                            else:
                                mime_type = "application/octet-stream"
                            
                            st.download_button(
                                "📥 تنزيل",
                                data=file_data, 
                                file_name=file_path_obj.name, 
                                key=download_key,
                                mime=mime_type,
                                use_container_width=True
                            )
                        else:
                            st.caption("— ملف فارغ")
                    except PermissionError:
                        st.caption("— الملف مقفل")
                    except Exception as e:
                        st.caption(f"— خطأ: {str(e)[:20]}")
                else:
                    st.caption("— ملف فارغ")
            else:
                st.caption("— ملف غير موجود")
        except Exception as e:
            st.caption(f"— خطأ في المسار: {str(e)[:15]}")
    else:
        st.caption("— لم يتم الرفع")

def hospital_requests_ui(user: dict):
    st.markdown("<div class='subheader'>طلباتي</div>", unsafe_allow_html=True)
    try:
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT r.id, s.name AS service_name, r.age_category, r.status, r.created_at
                FROM requests r 
                JOIN services s ON s.id=r.service_id
                WHERE r.hospital_id=? AND r.deleted_at IS NULL 
                ORDER BY r.created_at DESC
            """, (user["id"],)).fetchall()

        if not rows:
            st.info("لا يوجد لديك طلبات حالية.")
            return

        df = pd.DataFrame([{
            'id': r['id'],
            'service_name': r['service_name'],
            'age_category': r['age_category'],
            'status': r['status'],
            'created_at': r['created_at']
        } for r in rows])
        
        st.dataframe(df, use_container_width=True, height=400)
        
        req_ids = [str(r["id"]) for r in rows]
        pick = st.selectbox("اختر طلبًا لعرض تفاصيله", ["—"] + req_ids, key="select_request_hospital")
        if pick != "—":
            request_details_ui(int(pick))
    except Exception as e:
        st.error(f"حدث خطأ في تحميل الطلبات: {e}")
        import traceback
        traceback.print_exc()

# في ملف waiting_list_contracts_app.py

def request_details_ui(request_id: int, role: str = "hospital"):
    """واجهة تفاصيل الطلب للمستخدم (المستشفى) مع السماح بالحذف في تبويب طلباتي."""
    with get_conn() as conn:
        r = conn.execute("""
            SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
                   h.type AS hospital_type, s.name AS service_name
            FROM requests r
            JOIN hospitals h ON h.id=r.hospital_id
            JOIN services s ON s.id=r.service_id
            WHERE r.id=?
        """, (request_id,)).fetchone()
        docs = conn.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,)).fetchall()



    if not r:
        st.error("الطلب غير موجود.")
        return

    st.markdown(f"<div class='subheader'>تفاصيل الطلب #{request_id}</div>", unsafe_allow_html=True)
    st.write(f"**المستشفى:** {r['hospital_name']} — ({r['hospital_code']}) — **النوع:** {r['hospital_type']} — **الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']}")

    # === إضافة عرض تواريخ الطلب ===
    try:
        created_at_dt = datetime.fromisoformat(r['created_at'])
        info_text = f"**تاريخ التقديم:** {created_at_dt.strftime('%Y-%m-%d %H:%M:%S')}"

        if r['updated_at']:
            updated_at_dt = datetime.fromisoformat(r['updated_at'])
            # عرض تاريخ التعديل فقط إذا كان مختلفًا عن تاريخ التقديم
            # نستخدم total_seconds للتحقق من الفرق الزمني
            if (updated_at_dt - created_at_dt).total_seconds() > 1: # فرق ثانية أو أكثر
                updated_at_str = updated_at_dt.strftime('%Y-%m-%d %H:%M:%S')
                info_text += f"  \n**آخر تعديل:** {updated_at_str}"
            else:
                info_text += "  \n*(لم يتم التعديل بعد)*"
        else:
            info_text += "  \n*(لم يتم التعديل بعد)*"
            
        st.info(info_text)
    except Exception as e:
        # في حالة وجود خطأ في تحويل التاريخ، عرض النصوص كما هي
        st.info(f"**تاريخ التقديم:** {r['created_at']}  \n**آخر تعديل:** {r['updated_at'] or '(لم يتم التعديل بعد)'}")
    # ===============================

    can_edit = r['status'] in ["طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "يجب استيفاء متطلبات التعاقد"]
    can_delete = r['status'] in ["طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "يجب استيفاء متطلبات التعاقد"]

    if can_delete and role == "hospital":
        if st.button("🗑️ حذف الطلب"):
            # حذف محسن مع معاملات قاعدة البيانات
            files_deleted = 0
            files_failed = 0
            
            # حذف الملفات من النظام
            for d in docs:
                if d['file_path'] and os.path.exists(d['file_path']):
                    try:
                        os.remove(d['file_path'])
                        files_deleted += 1
                    except Exception:
                        files_failed += 1
            
            # حذف من قاعدة البيانات في معاملة واحدة
            with get_conn() as conn:
                conn.execute("BEGIN TRANSACTION")
                try:
                    conn.execute("DELETE FROM documents WHERE request_id=?", (request_id,))
                    conn.execute("DELETE FROM requests WHERE id=?", (request_id,))
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
            
            log_activity("حذف طلب", f"طلب رقم: {request_id}")
            
            # تنظيف متغيرات الجلسة
            keys_to_remove = ["active_request_id", f"editing_request_{request_id}"]
            for key in keys_to_remove:
                st.session_state.pop(key, None)
            
            success_msg = "تم حذف الطلب بنجاح"
            if files_deleted > 0:
                success_msg += f" (تم حذف {files_deleted} ملف)"
            if files_failed > 0:
                success_msg += f" (فشل حذف {files_failed} ملف من القرص)"
            
            st.success(success_msg)
            st.rerun()

    if can_edit and role == "hospital":
        if st.button("✏️ تعديل الطلب"):
            st.session_state[f"editing_request_{request_id}"] = True

    is_editing = st.session_state.get(f"editing_request_{request_id}", False)
    if is_editing:
        documents_upload_ui(request_id, st.session_state.user, is_active_edit=True)
    else:
        display_request_documents_readonly(docs)

def display_request_documents_readonly(docs: list):
    """دالة لعرض المستندات في وضع القراءة فقط."""
    st.markdown("##### المستندات")
    
    # تجميع المستندات حسب النوع
    required_docs = [d for d in docs if d['required'] == 1]
    optional_docs = [d for d in docs if d['required'] == 0]
    
    if required_docs:
        st.markdown("**🔴 المستندات المطلوبة:**")
        for d in required_docs:
            c1, c2, c3, c4, c5 = st.columns([3,2,2,2,3])
            with c1:
                display_name = d['display_name'] or d['doc_type']
                st.write(display_name)
                st.caption("🔴 مطلوب")
            with c2:
                render_file_downloader(d, key_prefix=f"readonly_req_{d['id']}")
            with c3:
                st.write("✅ مستوفى" if d["satisfied"] else "❌ غير مستوفى")
            with c4:
                st.write(datetime.fromisoformat(d['uploaded_at']).strftime('%Y-%m-%d %H:%M:%S') if d['uploaded_at'] else "—")
            with c5:
                st.write(d['admin_comment'] or "")
    
    if optional_docs:
        st.markdown("**🟡 المستندات الاختيارية:**")
        for d in optional_docs:
            c1, c2, c3, c4, c5 = st.columns([3,2,2,2,3])
            with c1:
                display_name = d['display_name'] or d['doc_type']
                st.write(display_name)
                st.caption("🟡 اختياري")
            with c2:
                render_file_downloader(d, key_prefix=f"readonly_opt_{d['id']}")
            with c3:
                st.write("✅ مستوفى" if d["satisfied"] else "❌ غير مستوفى")
            with c4:
                st.write(datetime.fromisoformat(d['uploaded_at']).strftime('%Y-%m-%d %H:%M:%S') if d['uploaded_at'] else "—")
            with c5:
                st.write(d['admin_comment'] or "")

    # ... (إجراءات الطلب: حذف نهائي، استرجاع، إغلاق) ...


def resources_download_ui():
    st.markdown("<div class='subheader'>ملفات متوفرة للتنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك تنزيل النماذج والمتطلبات التالية لمساعدتك في عملية التقديم.</div>", unsafe_allow_html=True)
    for filename in RESOURCE_FILES:
        filepath = RESOURCES_DIR / filename
        if filepath.exists():
            with open(filepath, "rb") as f:
                st.download_button(label=f"📥 {filename}", data=f, file_name=filename, mime="application/pdf", use_container_width=True)
        else:
            st.warning(f"الملف غير متوفر حاليًا: {filename}")

# ---------------------------- صفحات الإدارة ---------------------------- #
def admin_home():
    user = st.session_state.user
    logo_path = Path("static/logo.png")
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=80)
    st.markdown("<div class='header'><h2>لوحة التحكم الإدارية</h2></div>", unsafe_allow_html=True)
    
    admin_menu = {
        "items": ["🏥 إدارة المستشفيات", "🧾 إدارة الطلبات", "📊 الإحصائيات", "📜 سجل النشاط", "🧩 إدارة الإعدادات", "👥 إدارة المستخدمين", "📥 إدارة ملفات التنزيل", "🔑 تغيير كلمة المرور"],
        "icons": ["hospital", "card-list", "bar-chart-line", "clock-history", "gear", "people", "download", "key-fill"],
        "functions": [admin_hospitals_ui, admin_requests_ui, admin_statistics_ui, admin_activity_log_ui, admin_lists_ui, admin_users_ui, admin_resources_ui, lambda: change_password_ui(user_id=user["id"], user_table="admins")]
    }
    reviewer_menu = {
        "items": ["🧾 مراجعة الطلبات", "📊 الإحصائيات"],
        "icons": ["card-list", "bar-chart-line"],
        "functions": [admin_requests_ui, admin_statistics_ui]
    }
    
    menu = admin_menu if user["role"] == "admin" else reviewer_menu
    
    with st.sidebar:
        selection = option_menu("القائمة", menu["items"] + ["🚪 تسجيل الخروج"], 
                                icons=menu["icons"] + ["box-arrow-right"], 
                                menu_icon="person-workspace", default_index=0)

    if selection == "🚪 تسجيل الخروج":
        st.session_state.pop("user", None)
        st.rerun()
    else:
        selected_index = (menu["items"] + ["🚪 تسجيل الخروج"]).index(selection)
        menu["functions"][selected_index]()

def admin_hospitals_ui():
    st.markdown("<div class='subheader'>إدارة المستشفيات</div>", unsafe_allow_html=True)
    
    st.markdown("#### 🔽 استيراد من ملف Excel")
    excel = st.file_uploader("اختر ملف Excel Sheet يحتوي: اسم المستشفى، القطاع، المحافظة، الكود، النوع", type=["xlsx", "xls"])
    if excel is not None:
        try:
            df = pd.read_excel(excel, sheet_name=0)
            required_cols = ["اسم المستشفى", "القطاع", "المحافظه", "كود المستشفى"]
            for c in required_cols:
                if c not in df.columns:
                    st.error(f"العمود المطلوب مفقود: {c}")
                    return
            if "نوع المستشفى" not in df.columns:
                df["نوع المستشفى"] = "خاص"
            
            df["username"] = df["اسم المستشفى"].apply(lambda name: generate_username(name) or "hospital")
            # كلمة مرور افتراضية ثابتة
            df["password"] = "1234"
            
            added, skipped = 0, 0
            with get_conn() as conn:
                cur = conn.cursor()
                for _, row in df.iterrows():
                    try:
                        username = row["username"]
                        base_username = username
                        counter = 1
                        while True:
                            cur.execute("SELECT id FROM hospitals WHERE username=?", (username,))
                            if not cur.fetchone():
                                break
                            username = f"{base_username}{counter}"
                            counter += 1
                        cur.execute("""
                            INSERT OR IGNORE INTO hospitals 
                            (name, sector, governorate, code, type, username, password_hash)
                            VALUES (?,?,?,?,?,?,?)
                        """, (
                            str(row["اسم المستشفى"]).strip(),
                            str(row["القطاع"]).strip(),
                            str(row["المحافظه"]).strip(),
                            str(row["كود المستشفى"]).strip(),
                            str(row["نوع المستشفى"]).strip() if row["نوع المستشفى"] in get_hospital_types() else get_hospital_types()[0],
                            username,
                            hash_pw(str(row["password"]).strip()), # استخدام التشفير الآمن
                        ))
                        if cur.rowcount:
                            added += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        st.warning(f"تخطي صف: {e}")
                conn.commit()
            st.success(f"تمت إضافة: {added} — تم التخطي (موجود): {skipped}")
            
            out_path = EXPORTS_DIR / f"credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(out_path, index=False)
            st.download_button("📥 تنزيل ملف الاعتمادات (username/password)", 
                             data=open(out_path, 'rb').read(), 
                             file_name=out_path.name)
        except Exception as e:
            st.error(f"فشل الاستيراد: {e}")
    
    st.markdown("#### ➕ إضافة مستشفى يدويًا")
    with st.expander("إضافة مستشفى جديد"):
        with st.form("add_hospital"):
            name = st.text_input("اسم المستشفى")
            sector = st.text_input("القطاع", help="اختر من القائمة أو أدخل يدويًا")
            gov = st.text_input("المحافظة", help="اختر من القائمة أو أدخل يدويًا")
            code = st.text_input("كود المستشفى")
            htype = st.text_input("نوع المستشفى", help="اختر من القائمة أو أدخل يدويًا")
            username = st.text_input("اسم المستخدم (سيتم توليد تلقائيًا من الاسم إن فارغ)", value="")
            password = st.text_input("كلمة المرور", type="password", value="")
            submitted = st.form_submit_button("إضافة")
            if submitted:
                if not all([name, sector, gov, code, password]):
                    st.error("يرجى ملء الحقول المطلوبة")
                else:
                    if not username:
                        username = generate_username(name) or "hospital"
                    try:
                        with get_conn() as conn:
                            # التحقق من أن اسم المستخدم فريد
                            base_username = username
                            counter = 1
                            while conn.execute("SELECT id FROM hospitals WHERE username=?", (username,)).fetchone():
                                username = f"{base_username}{counter}"
                                counter += 1

                            conn.execute("""
                                INSERT INTO hospitals (name, sector, governorate, code, type, username, password_hash)
                                VALUES (?,?,?,?,?,?,?)
                            """, (name, sector, gov, code, htype, username, hash_pw(password))) # استخدام التشفير الآمن
                            conn.commit()
                        st.success(f"تمت الإضافة. اسم المستخدم: {username}")
                    except sqlite3.IntegrityError:
                        st.error("كود المستشفى أو اسم المستخدم موجود مسبقًا")
    
    st.markdown("#### 📋 قائمة المستشفيات")
    
    # حقول البحث والتصفية
    with get_conn() as conn:
        all_hospitals = conn.execute("SELECT * FROM hospitals ORDER BY name").fetchall()
        sectors = list(set(h['sector'] for h in all_hospitals if h['sector']))
        governorates = list(set(h['governorate'] for h in all_hospitals if h['governorate']))
        types = list(set(h['type'] for h in all_hospitals if h['type']))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_text = st.text_input("🔍 بحث (الاسم، الكود، القطاع، المحافظة)")
    with col2:
        selected_sector = st.selectbox("القطاع", ["الكل"] + sorted(sectors))
    with col3:
        selected_gov = st.selectbox("المحافظة", ["الكل"] + sorted(governorates))
    with col4:
        selected_type = st.selectbox("النوع", ["الكل"] + sorted(types))
    
    # تطبيق الفلاتر
    filtered_hospitals = []
    for h in all_hospitals:
        # فلتر البحث النصي
        if search_text:
            search_fields = [str(h['name'] or ''), str(h['code'] or ''), str(h['sector'] or ''), str(h['governorate'] or '')]
            if not any(search_text.lower() in field.lower() for field in search_fields):
                continue
        
        # فلتر القطاع
        if selected_sector != "الكل" and h['sector'] != selected_sector:
            continue
            
        # فلتر المحافظة
        if selected_gov != "الكل" and h['governorate'] != selected_gov:
            continue
            
        # فلتر النوع
        if selected_type != "الكل" and h['type'] != selected_type:
            continue
            
        filtered_hospitals.append(h)
    
    if filtered_hospitals:
        df = pd.DataFrame([dict(h) for h in filtered_hospitals])
        st.dataframe(
            df[["id", "name", "sector", "governorate", "code", "type", "username"]],
            use_container_width=True,
            height=400
        )
        
        hospitals = filtered_hospitals  # للاستخدام في باقي الكود
        
        # قسم حذف المستشفى داخل قائمة مخفية
        with st.expander("🗑️ إدارة حذف المستشفى", expanded=False):
            st.warning("⚠️ تنبيه: الحذف نهائي ولا يمكن التراجع عنه")
            
            hospital_options = ["—"] + [f"{h['id']} — {h['name']} ({h['code']})" for h in hospitals]
            selected_hospital = st.selectbox("اختر مستشفى للحذف", hospital_options, key="delete_hospital_select")
            
            if selected_hospital != "—":
                hospital_id = int(selected_hospital.split(" — ")[0])
                hospital_name = selected_hospital.split(" — ")[1]
                
                # التحقق من وجود طلبات مرتبطة
                with get_conn() as conn:
                    request_count = conn.execute("SELECT COUNT(*) as request_count FROM requests WHERE hospital_id = ? AND deleted_at IS NULL", (hospital_id,)).fetchone()['request_count']
                
                if request_count > 0:
                    st.error(f"❌ لا يمكن حذف المستشفى '{hospital_name}' لأنه لديه {request_count} طلب(طلبات) نشطة.")
                    st.info("يرجى حذف أو معالجة الطلبات المرتبطة أولاً قبل حذف المستشفى.")
                else:
                    st.info(f"المستشفى المحدد: {hospital_name}")
                    
                    # زر الحذف مع تأكيد
                    if st.button("🗑️ حذف المستشفى", type="secondary", key="delete_hospital_btn"):
                        st.session_state['delete_hospital_id'] = hospital_id
                        st.session_state['delete_hospital_name'] = hospital_name
                    
                    # عرض تأكيد الحذف إذا تم الضغط على الزر
                    if 'delete_hospital_id' in st.session_state and st.session_state['delete_hospital_id'] == hospital_id:
                        st.error(f"⚠️ تأكيد الحذف النهائي للمستشفى: {st.session_state['delete_hospital_name']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ نعم، تأكيد الحذف", type="primary", key="confirm_delete"):
                                try:
                                    with get_conn() as conn:
                                        conn.execute("DELETE FROM hospitals WHERE id = ?", (st.session_state['delete_hospital_id'],))
                                        conn.commit()
                                    
                                    st.success(f"✅ تم حذف المستشفى '{st.session_state['delete_hospital_name']}' بنجاح")
                                    # مسح بيانات الحذف من session state
                                    del st.session_state['delete_hospital_id']
                                    del st.session_state['delete_hospital_name']
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ حدث خطأ أثناء الحذف: {e}")
                        
                        with col2:
                            if st.button("❌ إلغاء الحذف", key="cancel_delete"):
                                # مسح بيانات الحذف من session state
                                del st.session_state['delete_hospital_id']
                                del st.session_state['delete_hospital_name']
                                st.success("تم إلغاء عملية الحذف")
                                st.rerun()
        
        hid = st.selectbox("اختر مستشفى للتعديل", ["—"] + [f"{h['id']} — {h['name']}" for h in hospitals], key="edit_hospital_select")
        if hid != "—":
            hid_int = int(hid.split(" — ")[0])
            edit_hospital_ui(hid_int)
    
    else:
        if search_text or selected_sector != "الكل" or selected_gov != "الكل" or selected_type != "الكل":
            st.info("لا توجد مستشفيات تطابق معايير البحث")
        else:
            st.info("لا توجد مستشفيات مسجلة")


# --- دوال Callback لواجهة الأدمن ---

def _callback_update_request_status(request_id: int, new_status: str, note: str, current_status_is_final: bool):
    """Callback لتحديث حالة الطلب وملاحظة الأدمن."""
    try:
        with get_conn() as conn:
            updated_at = datetime.now().isoformat()
            
            # تحديد ما إذا كانت الحالة الجديدة نهائية
            new_status_is_final = is_final_status(new_status)
            
            if new_status_is_final:
                # إذا كانت الحالة الجديدة نهائية، قم بتعيين closed_at
                closed_at = datetime.now().isoformat()
                conn.execute("UPDATE requests SET status=?, admin_note=?, closed_at=?, updated_at=? WHERE id=?", 
                             (new_status, note, closed_at, updated_at, request_id))
            else:
                # إذا لم تكن الحالة الجديدة نهائية
                if current_status_is_final:
                    # إذا كانت الحالة الحالية نهائية، قم بإزالة closed_at
                    conn.execute("UPDATE requests SET status=?, admin_note=?, closed_at=NULL, updated_at=? WHERE id=?", 
                                 (new_status, note, updated_at, request_id))
                else:
                    # إذا لم تكن أي من الحالتين نهائية
                    conn.execute("UPDATE requests SET status=?, admin_note=?, updated_at=? WHERE id=?", 
                                 (new_status, note, updated_at, request_id))
            conn.commit()
        
        log_activity("تحديث حالة طلب", f"طلب رقم: {request_id}، الحالة الجديدة: {new_status}")
        st.success("تم حفظ الحالة بنجاح")
    except Exception as e:
        st.error(f"فشل تحديث الحالة: {e}")

def _callback_delete_document_admin(doc_id: int, file_path: str):
    """Callback لحذف مستند من قبل الأدمن."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            st.warning(f"تعذر حذف الملف من القرص: {e}")
    
    try:
        with get_conn() as conn:
            now_iso = datetime.now().isoformat()
            conn.execute("UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0, uploaded_at=NULL, updated_at=? WHERE id=?", (now_iso, doc_id))
            conn.commit()
        st.success("✅ تم حذف الملف")
    except Exception as e:
        st.error(f"فشل تحديث قاعدة البيانات: {e}")

def _callback_soft_delete_request(request_id: int, docs: list):
    """Callback للحذف النهائي (soft delete) للطلب."""
    files_deleted, files_failed = 0, 0
    for d in docs:
        if d['file_path'] and os.path.exists(d['file_path']):
            try:
                os.remove(d['file_path'])
                files_deleted += 1
            except Exception:
                files_failed += 1
    
    try:
        with get_conn() as conn:
            now_iso = datetime.now().isoformat()
            conn.execute("UPDATE requests SET deleted_at=?, updated_at=? WHERE id=?", (now_iso, now_iso, request_id))
            conn.commit()
        
        log_activity("حذف طلب نهائي", f"طلب رقم: {request_id}")
        msg = "تم الحذف النهائي."
        if files_deleted > 0: msg += f" (تم حذف {files_deleted} ملف)"
        if files_failed > 0: msg += f" (فشل حذف {files_failed} ملف)"
        st.success(msg)
    except Exception as e:
        st.error(f"فشل حذف الطلب: {e}")

def edit_hospital_ui(hospital_id: int):
    with get_conn() as conn:
        h = conn.execute("SELECT * FROM hospitals WHERE id=?", (hospital_id,)).fetchone()

    if not h:
        st.error("المستشفى غير موجود.")
        return

    st.markdown(f"<div class='subheader'>تعديل: {h['name']}</div>", unsafe_allow_html=True)
    
    # checkbox خارج الـ form للمستشفيات الخاصة
    if h["type"] != 'حكومي':
        current_no_end_admin = h["license_end"] == "غير محدد" or not h["license_end"]
        no_end_date = st.checkbox("ترخيص دائم (بدون تاريخ انتهاء)", value=current_no_end_admin, key=f"admin_no_end_{hospital_id}")
    else:
        no_end_date = False
    
    with st.form("edit_h"):
        name = st.text_input("اسم المستشفى", h["name"])
        sector = st.text_input("القطاع", h["sector"], help="اختر من القائمة أو أدخل يدويًا")
        gov = st.text_input("المحافظة", h["governorate"], help="اختر من القائمة أو أدخل يدويًا")
        code = st.text_input("كود المستشفى", h["code"])
        htype = st.text_input("نوع المستشفى", h["type"], help="اختر من القائمة أو أدخل يدويًا")
        address = st.text_area("العنوان بالكامل", h["address"] or "")
        other_br = st.text_input("الفروع الأخرى", h["other_branches"] or "")
        other_br_addr = st.text_area("عناوين الفروع الأخرى", h["other_branches_address"] or "")
        # تواريخ الترخيص - للمستشفيات الخاصة فقط
        if htype != 'حكومي':
            lic_start = st.date_input("بداية الترخيص", value=parse_date_safely(h["license_start"], default_value=date.today()), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
            
            if not no_end_date:
                lic_end = st.date_input("تاريخ انتهاء الترخيص", value=parse_date_safely(h["license_end"], default_value=date.today()), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
            else:
                lic_end = "غير محدد"
        else:
            lic_start = None
            lic_end = None
            st.info("المستشفيات الحكومية غير مطالبة بتواريخ الترخيص")
        manager = st.text_input("اسم مدير المستشفى", h["manager_name"] or "")
        manager_phone = st.text_input("رقم هاتف المدير", h["manager_phone"] or "")
        license_no = st.text_input("رقم الترخيص", h["license_number"] or "")
        username = st.text_input("اسم المستخدم", h["username"]) 
        new_pw = st.text_input("كلمة مرور جديدة (اختياري)", type="password")
        submitted = st.form_submit_button("حفظ التعديل")
        if submitted:
            try:
                q = ("UPDATE hospitals SET name=?, sector=?, governorate=?, code=?, type=?, "
                     "address=?, other_branches=?, other_branches_address=?, license_start=?, "
                     "license_end=?, manager_name=?, manager_phone=?, license_number=?, username=?")
                # تحضير قيمة lic_end بشكل صحيح
                lic_end_value = None
                if htype != 'حكومي':
                    if lic_end == "غير محدد":
                        lic_end_value = "غير محدد"
                    elif lic_end:
                        lic_end_value = str(lic_end)
                
                params = [name, sector, gov, code, htype, address, other_br, other_br_addr, 
                         str(lic_start) if lic_start else None,
                         lic_end_value,
                         manager, manager_phone, license_no, username]
                if new_pw:
                    q += ", password_hash=?"
                    params.append(hash_pw(new_pw))
                q += " WHERE id=?"
                params.append(hospital_id)
                with get_conn() as conn:
                    conn.execute(q, tuple(params))
                    conn.commit()
                st.success("تم التعديل بنجاح")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("كود المستشفى أو اسم المستخدم مستخدم مسبقًا")

@st.cache_data(ttl=600)
def get_all_services():
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM services ORDER BY name").fetchall()
        return [dict(row) for row in rows]

@st.cache_data(ttl=1800)
def get_all_hospitals():
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM hospitals ORDER BY name").fetchall()
        return [dict(row) for row in rows]

@st.cache_data(ttl=1800)
def get_all_sectors():
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT sector FROM hospitals ORDER BY sector").fetchall()
        return [dict(row) for row in rows]

def admin_requests_ui():
    st.markdown("<div class='subheader'>إدارة الطلبات</div>", unsafe_allow_html=True)
    st.markdown("#### تصفية الطلبات")
    
    services = get_all_services()
    hospitals = get_all_hospitals()
    sectors = get_all_sectors()

    service_options = ["الكل"] + [s["name"] for s in services]
    hospital_options = ["الكل"] + [h["name"] for h in hospitals]
    sector_filter_options = ["الكل"] + [s["sector"] for s in sectors]
    
    col1, col2, col3, col4, col5, col6 = st.columns(6) 
    with col1:
        selected_service = st.selectbox("الخدمة", service_options)
    with col2:
        selected_hospital = st.selectbox("المستشفى", hospital_options)
    with col3:
        request_id_input = st.text_input("ID الطلب (رقم)")
    with col4:
        selected_hospital_sector = st.selectbox("القطاع", sector_filter_options) 
    with col5:
        start_date = st.date_input("تاريخ البدء", value=None, format="YYYY/MM/DD")
    with col6:
        end_date = st.date_input("تاريخ الانتهاء", value=None, format="YYYY/MM/DD")

    status_col, deleted_col = st.columns(2)
    with status_col:
        status_options = ["الكل"] + [s for s in get_request_statuses() if s != "طلب غير مكتمل"] + ["طلب غير مكتمل"]
        status = st.selectbox("الحالة", status_options)
    with deleted_col:
        show_deleted = st.checkbox("عرض المحذوفات؟")

    # بناء الاستعلام بشكل آمن
    base_query = """SELECT r.id, h.name AS hospital, h.code AS code, h.type AS hospital_type,
                  s.name AS service, r.age_category, r.status, r.created_at, r.deleted_at
           FROM requests r
           JOIN hospitals h ON h.id=r.hospital_id
           JOIN services s ON s.id=r.service_id
           WHERE 1=1"""
    
    conditions = []
    params = []
    
    if not show_deleted:
        conditions.append("r.deleted_at IS NULL")
    if status != "الكل":
        conditions.append("r.status = ?")
        params.append(status)
    if selected_service != "الكل":
        conditions.append("s.name = ?")
        params.append(selected_service)
    if selected_hospital != "الكل":
        conditions.append("h.name = ?")
        params.append(selected_hospital)
    if request_id_input and request_id_input.isdigit():
        conditions.append("r.id = ?")
        params.append(int(request_id_input))
    if selected_hospital_sector != "الكل":
        conditions.append("h.sector = ?")
        params.append(selected_hospital_sector)
    if start_date:
        conditions.append("DATE(r.created_at) >= ?")
        params.append(start_date.isoformat())
    if end_date:
        conditions.append("DATE(r.created_at) <= ?")
        params.append(end_date.isoformat())
    
    if conditions:
        q = base_query + " AND " + " AND ".join(conditions)
    else:
        q = base_query
    
    q += " ORDER BY r.created_at DESC"

    with get_conn() as conn:
        rows = conn.execute(q, tuple(params)).fetchall()
    
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)
    
    if rows:
        pick = st.selectbox("اختر طلبًا لإدارته", ["—"] + [str(r["id"]) for r in rows])
        if pick != "—":
            admin_request_detail_ui(int(pick))

def admin_request_detail_ui(request_id: int):
    with get_conn() as conn:
        r = conn.execute("""
            SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
                   h.type AS hospital_type, s.name AS service_name,
                   h.manager_name, h.manager_phone, h.license_start, h.license_end
            FROM requests r
            JOIN hospitals h ON h.id=r.hospital_id
            JOIN services s ON s.id=r.service_id
            WHERE r.id=?
        """, (request_id,)).fetchone()
        docs = conn.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,)).fetchall()

    if not r:
        st.error("الطلب غير موجود.")
        return

    st.markdown(f"<div class='subheader'>إدارة الطلب #{request_id}</div>", unsafe_allow_html=True)
    
    # عرض بيانات المستشفى الأساسية في الأعلى
    st.markdown("#### بيانات المستشفى")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**اسم المستشفى:** {r['hospital_name']}")
        st.write(f"**كود المستشفى:** {r['hospital_code']}")
        st.write(f"**نوع المستشفى:** {r['hospital_type']}")
    with col2:
        st.write(f"**مدير المستشفى:** {r['manager_name'] or 'غير محدد'}")
        st.write(f"**هاتف المدير:** {r['manager_phone'] or 'غير محدد'}")
        if r['hospital_type'] != 'حكومي' and r['license_start']:
            st.write(f"**بداية الترخيص:** {r['license_start']}")
    
    st.markdown("---")
    st.write(f"**الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']} — **الحالة الحالية:** {r['status']}")

    colA, colB = st.columns([2,3])
    with colA:
        current_statuses = get_request_statuses()
        new_status = st.selectbox("الحالة", current_statuses, index=current_statuses.index(r['status']) if r['status'] in current_statuses else 0)
        note = st.text_area("ملاحظة إدارية", r['admin_note'] or "")
        
        current_is_final = is_final_status(r['status'])
        st.button("حفظ الحالة", 
                  on_click=_callback_update_request_status, 
                  args=(request_id, new_status, note, current_is_final)
                 )

    with colB:
        if st.button("تنزيل كل الملفات (ZIP)"):
            buf = None
            zf = None
            try:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                    files_added = 0
                    for d in docs:
                        if d['file_path'] and os.path.exists(d['file_path']):
                            try:
                                safe_name = safe_filename(d['doc_type'])[:50]
                                file_ext = Path(d['file_path']).suffix
                                arcname = f"{safe_name}{file_ext}"
                                zf.write(d['file_path'], arcname=arcname)
                                files_added += 1
                            except Exception as e:
                                print(f"Error adding file to ZIP: {e}")
                    
                    if files_added == 0:
                        st.warning("لا توجد ملفات صالحة للتنزيل")
                        return
                
                buf.seek(0)
                zip_data = buf.getvalue()
                
                if zip_data:
                    st.download_button(
                        "📥 تحميل الملفات", 
                        data=zip_data, 
                        file_name=f"request_{request_id}_files.zip",
                        mime="application/zip"
                    )
                    st.success(f"تم إنشاء ملف ZIP يحتوي على {files_added} ملف")
                else:
                    st.error("فشل في إنشاء ملف ZIP")
                    
            except Exception as e:
                st.error(f"خطأ في إنشاء ملف ZIP: {e}")
            finally:
                # تحرير الذاكرة
                if buf:
                    buf.close()
                del buf, zf
                import gc
                gc.collect()

    st.markdown("##### المستندات")
    for d in docs:
        c1, c2, c3, c4, c5, c6 = st.columns([3,2,2,2,3,3])
        with c1:
            display_name = d['display_name'] or d['doc_type']
            st.write(display_name)
            if d['required'] == 1:
                st.caption("🔴 مطلوب")
            else:
                st.caption("🟡 اختياري")
            req_toggle_admin = st.checkbox("مطلوب؟", value=bool(d['required']), key=f"req_admin_{d['id']}")
        with c2:
            sat_toggle = st.checkbox("مستوفى؟", value=bool(d['satisfied']), key=f"sat_{d['id']}")
        with c3:
            # إصلاح جذري: استخدام دالة render_file_downloader الموحدة والمحسنة
            render_file_downloader(d, key_prefix=f"admin_dl_{d['id']}")
        with c4:
            if d["file_path"]:
                delete_key = f"admin_del_{d['id']}"
                st.button("حذف", 
                          key=delete_key, 
                          on_click=_callback_delete_document_admin, 
                          args=(d['id'], d['file_path'])
                         )
        with c5:
            comment = st.text_input("تعليق", value=d['admin_comment'] or "", key=f"cm_{d['id']}")
        with c6:
            if st.button("حفظ", key=f"save_{d['id']}"):
                with get_conn() as conn:
                    new_required_value = 1 if req_toggle_admin else 0
                    now_iso = datetime.now().isoformat()
                    conn.execute("UPDATE documents SET required=?, satisfied=?, admin_comment=?, updated_at=? WHERE id=?", (new_required_value, 1 if sat_toggle else 0, comment, now_iso, d['id']))
                    conn.commit()
                st.success("تم التحديث")

    st.markdown("##### الإجراءات")
    cols = st.columns(3)
    with cols[0]:
        st.button("❌ حذف الطلب نهائيًا", 
                  on_click=_callback_soft_delete_request, 
                  args=(request_id, docs)
                 )
    with cols[1]:
        def _callback_restore_request():
            try:
                with get_conn() as conn:
                    conn.execute("UPDATE requests SET status='إعادة تقديم', deleted_at=NULL, updated_at=? WHERE id=?", (datetime.now().isoformat(), request_id))
                    conn.commit()
                log_activity("استرجاع طلب", f"طلب رقم: {request_id}")
                st.success("تم الاسترجاع")
            except Exception as e:
                st.error(f"فشل الاسترجاع: {e}")
        
        st.button("🔄 استرجاع كـ 'إعادة تقديم'", on_click=_callback_restore_request)

    with cols[2]:
        def _callback_close_request():
            _callback_update_request_status(request_id, "مغلق", r['admin_note'], is_final_status(r['status']))
        
        st.button("🔒 إغلاق الطلب", on_click=_callback_close_request)

def admin_activity_log_ui():
    """واجهة عرض سجل نشاط المستخدمين للمدير."""
    st.markdown("<div class='subheader'>📜 سجل نشاط المستخدمين</div>", unsafe_allow_html=True)

    # --- فلاتر البحث ---
    st.markdown("#### تصفية السجلات")
    col1, col2, col3 = st.columns(3)
    with col1:
        search_user = st.text_input("اسم المستخدم")
    with col2:
        with get_conn() as conn:
            actions = [r['action'] for r in conn.execute("SELECT DISTINCT action FROM activity_log ORDER BY action").fetchall()]
        selected_action = st.selectbox("نوع الإجراء", ["الكل"] + actions)
    with col3:
        date_filter = st.date_input("تاريخ محدد", value=None)

    # --- بناء الاستعلام ---
    query = "SELECT timestamp, username, user_role, action, details FROM activity_log WHERE 1=1"
    params = []

    if search_user:
        query += " AND username LIKE ?"
        params.append(f"%{search_user}%")
    if selected_action != "الكل":
        query += " AND action = ?"
        params.append(selected_action)
    if date_filter:
        query += " AND DATE(timestamp) = ?"
        params.append(date_filter.isoformat())

    query += " ORDER BY timestamp DESC LIMIT 500" # حد أقصى 500 سجل لتجنب التحميل الزائد

    # --- عرض النتائج ---
    with get_conn() as conn:
        logs = conn.execute(query, params).fetchall()

    if logs:
        df = pd.DataFrame([dict(log) for log in logs])
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.info("لا توجد سجلات تطابق معايير البحث.")

@st.cache_data(ttl=600)
def get_active_service_names():
    with get_conn() as conn:
        return [s['name'] for s in conn.execute("SELECT name FROM services WHERE active=1").fetchall()]

def admin_statistics_ui():
    st.markdown("<div class='subheader'>الإحصائيات</div>", unsafe_allow_html=True)
    
    st.markdown("#### تصفية الإحصائيات")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sectors = get_sectors()
        selected_sector = st.selectbox("القطاع", ["الكل"] + sectors)
    
    with col2:
        services = get_active_service_names()
        selected_service = st.selectbox("الخدمة", ["الكل"] + services)
    
    with col3:
        hospital_types = get_hospital_types()
        selected_type = st.selectbox("نوع المستشفى", ["الكل"] + hospital_types)
    
    with col4:
        statuses = get_request_statuses()
        selected_status = st.selectbox("حالة الطلب", ["الكل"] + statuses)
    
    col5, col6 = st.columns(2)
    with col5:
        start_date = st.date_input("من تاريخ", value=None)
    with col6:
        end_date = st.date_input("إلى تاريخ", value=None)
    
    where_conditions = ["r.deleted_at IS NULL"]
    params = []
    
    if selected_sector != "الكل":
        where_conditions.append("h.sector = ?")
        params.append(selected_sector)
    if selected_service != "الكل":
        where_conditions.append("s.name = ?")
        params.append(selected_service)
    if selected_type != "الكل":
        where_conditions.append("h.type = ?")
        params.append(selected_type)
    if selected_status != "الكل":
        where_conditions.append("r.status = ?")
        params.append(selected_status)
    if start_date:
        where_conditions.append("DATE(r.created_at) >= ?")
        params.append(start_date.isoformat())
    if end_date:
        where_conditions.append("DATE(r.created_at) <= ?")
        params.append(end_date.isoformat())

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    with get_conn() as conn:
        query_status = f"""
            SELECT r.status, COUNT(*) as count
            FROM requests r
            JOIN hospitals h ON r.hospital_id = h.id
            JOIN services s ON r.service_id = s.id
            WHERE {where_clause}
            GROUP BY r.status
            ORDER BY count DESC
        """
        status_stats = conn.execute(query_status, params).fetchall()
        
        query_service = f"""
            SELECT s.name, COUNT(*) as count
            FROM requests r
            JOIN hospitals h ON r.hospital_id = h.id
            JOIN services s ON r.service_id = s.id
            WHERE {where_clause}
            GROUP BY s.name
            ORDER BY count DESC
        """
        service_stats = conn.execute(query_service, params).fetchall()
        
        query_type = f"""
            SELECT h.type, COUNT(*) as count
            FROM requests r
            JOIN hospitals h ON r.hospital_id = h.id
            JOIN services s ON r.service_id = s.id
            WHERE {where_clause}
            GROUP BY h.type
            ORDER BY count DESC
        """
        type_stats = conn.execute(query_type, params).fetchall()
        
        query_sector = f"""
            SELECT h.sector, COUNT(*) as count
            FROM requests r
            JOIN hospitals h ON r.hospital_id = h.id
            JOIN services s ON r.service_id = s.id
            WHERE {where_clause}
            GROUP BY h.sector
            ORDER BY count DESC
        """
        sector_stats = conn.execute(query_sector, params).fetchall()

    st.markdown("#### إحصائيات مفصلة")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب الحالة</div>", unsafe_allow_html=True)
        for stat in status_stats:
            st.markdown(f"<div class='stats-item'><span class='stats-label'>{stat['status']}</span><span class='stats-value'>{stat['count']}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب نوع المستشفى</div>", unsafe_allow_html=True)
        for stat in type_stats:
            st.markdown(f"<div class='stats-item'><span class='stats-label'>{stat['type']}</span><span class='stats-value'>{stat['count']}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب الخدمة</div>", unsafe_allow_html=True)
        for stat in service_stats:
            st.markdown(f"<div class='stats-item'><span class='stats-label'>{stat['name']}</span><span class='stats-value'>{stat['count']}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب القطاع</div>", unsafe_allow_html=True)
        for stat in sector_stats:
            st.markdown(f"<div class='stats-item'><span class='stats-label'>{stat['sector']}</span><span class='stats-value'>{stat['count']}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    try:
        import plotly.express as px
        plotly_available = True
    except ImportError:
        plotly_available = False
        st.info("لم يتم تثبيت مكتبة 'plotly'. سيتم عرض الإحصائيات بشكل نصي فقط.")

    if plotly_available:
        st.markdown("---")
        st.markdown("#### 📊 الإحصائيات البيانية")
        try:
            status_data = [dict(row) for row in status_stats]
            type_data = [dict(row) for row in type_stats]
            service_data = [dict(row) for row in service_stats]
            sector_data = [dict(row) for row in sector_stats]

            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
                st.markdown("<div class='stats-header'>حسب الحالة</div>", unsafe_allow_html=True)
                if len(status_data) > 0:
                    try:
                        status_df = pd.DataFrame(status_data)
                        fig_status = px.pie(status_df, values='count', names='status', title='توزيع الطلبات حسب الحالة', color_discrete_sequence=px.colors.sequential.Blues_r)
                        fig_status.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_status, use_container_width=True)
                    except Exception as e:
                        st.warning(f"خطأ في إنشاء الرسم البياني: {e}")
                else:
                    st.info("لا توجد بيانات")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with chart_col2:
                st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
                st.markdown("<div class='stats-header'>حسب نوع المستشفى</div>", unsafe_allow_html=True)
                if len(type_data) > 0:
                    try:
                        type_df = pd.DataFrame(type_data)
                        fig_type = px.bar(type_df, x='type', y='count', title='عدد الطلبات حسب نوع المستشفى', color='type', color_discrete_sequence=['#1f77b4', '#ff7f0e'])
                        fig_type.update_layout(xaxis_title="نوع المستشفى", yaxis_title="العدد")
                        st.plotly_chart(fig_type, use_container_width=True)
                    except Exception as e:
                        st.warning(f"خطأ في إنشاء الرسم البياني: {e}")
                else:
                    st.info("لا توجد بيانات")
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"حدث خطأ أثناء إنشاء الرسوم البيانية: {e}")

def admin_lists_ui():
    st.markdown("<div class='subheader'>إدارة الخدمات وأنواع المستشفيات</div>", unsafe_allow_html=True)

    st.markdown("#### 🧩 الخدمات")
    with get_conn() as conn:
        services = conn.execute("SELECT * FROM services ORDER BY active DESC, name").fetchall()
    
    for service in services:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(service['name'])
        with col2:
            status = "مفعلة" if service['active'] else "معطلة"
            st.write(status)
        with col3:
            if st.button("تغيير الحالة" if service['active'] else "تفعيل", key=f"toggle_{service['id']}"):
                with get_conn() as conn:
                    new_status = 0 if service['active'] else 1
                    conn.execute("UPDATE services SET active=? WHERE id=?", (new_status, service['id']))
                    conn.commit()
                st.success("تم تغيير الحالة")
                # مسح الذاكرة المؤقتة
                get_active_services.clear()
                get_all_services.clear()
                get_active_service_names.clear()
                time.sleep(0.5)
                st.rerun()

    with st.form("add_service"):
        sname = st.text_input("إضافة خدمة جديدة")
        s_active = st.checkbox("مفعلة؟", value=True)
        sub = st.form_submit_button("إضافة الخدمة")
        if sub and sname:
            try:
                with get_conn() as conn:
                    conn.execute("INSERT INTO services (name, active) VALUES (?,?)", (sname.strip(), 1 if s_active else 0))
                    conn.commit()
                st.success("تمت الإضافة")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("الخدمة موجودة مسبقًا")
        # مسح الذاكرة المؤقتة عند إضافة خدمة جديدة
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()

    st.markdown("#### 🏥 أنواع المستشفيات")
    types = get_hospital_types()
    editable = st.text_input("أنواع المستشفيات (مفصولة بفواصل)", ",".join(types))
    if st.button("حفظ الأنواع"):
        new_types = [t.strip() for t in editable.split(",") if t.strip()]
        if new_types:
            set_hospital_types(new_types)
            st.success("تم الحفظ")
            time.sleep(0.5)
            st.rerun()

    st.markdown("#### 🏢 القطاعات")
    sectors = get_sectors()
    editable_sectors = st.text_input("القطاعات (مفصولة بفواصل)", ",".join(sectors))
    if st.button("حفظ القطاعات"):
        new_sectors = [s.strip() for s in editable_sectors.split(",") if s.strip()]
        if new_sectors:
            set_sectors(new_sectors)
            st.success("تم الحفظ")
            time.sleep(0.5)
            st.rerun()

    st.markdown("#### 🗺️ المحافظات")
    gov = get_governorates()
    editable_gov = st.text_input("المحافظات (مفصولة بفواصل)", ",".join(gov))
    if st.button("حفظ المحافظات"):
        new_gov = [g.strip() for g in editable_gov.split(",") if g.strip()]
        if new_gov:
            set_governorates(new_gov)
            st.success("تم الحفظ")
            time.sleep(0.5)
            st.rerun()

    st.markdown("#### 📋 حالات الطلبات (للأدمن فقط)")
    current_statuses = get_request_statuses()
    st.write("الحالات الحالية: " + ", ".join(current_statuses))

    with st.form("add_edit_status"):
        new_status_name = st.text_input("اسم الحالة الجديدة أو تعديل الحالية")
        selected_status_for_edit = st.selectbox("اختر حالة لتعديل إعداداتها", [""] + current_statuses)
        prevents_new = st.checkbox("يمنع تقديم طلب جديد لنفس الخدمة", value=False)
        blocks_days = st.number_input("يمنع تقديم طلب لنفس الخدمة لمدة (أيام) - 0 للتعطيل", min_value=0, value=0)
        is_final = st.checkbox("حالة نهائية (تغلق الطلب)", value=False)

        if st.form_submit_button("إضافة/تعديل الحالة"):
             if new_status_name:
                 try:
                     with get_conn() as conn:
                         conn.execute("INSERT OR IGNORE INTO request_statuses (name) VALUES (?)", (new_status_name,))
                         conn.execute("""
                             INSERT INTO status_settings (status_name, prevents_new_request, blocks_service_for_days, is_final_state)
                             VALUES (?, ?, ?, ?)
                             ON CONFLICT(status_name) DO UPDATE SET
                             prevents_new_request=excluded.prevents_new_request,
                             blocks_service_for_days=excluded.blocks_service_for_days,
                             is_final_state=excluded.is_final_state
                         """, (new_status_name, 1 if prevents_new else 0, blocks_days, 1 if is_final else 0))
                         conn.commit()
                     st.success(f"تمت إضافة أو تعديل الحالة: {new_status_name}")
                     # مسح الذاكرة المؤقتة وإعادة تحميل الصفحة
                     get_request_statuses.clear()
                     get_preventing_statuses.clear()
                     get_blocking_statuses.clear()
                     time.sleep(0.5)
                     st.rerun()
                 except Exception as e:
                     st.error(f"خطأ: {e}")
             else:
                 st.warning("يرجى إدخال اسم الحالة.")

    with st.form("delete_status"):
         status_to_delete = st.selectbox("اختر حالة لحذفها", [""] + [s for s in current_statuses if s != "طلب غير مكتمل"])
         if st.form_submit_button("حذف الحالة"):
             if status_to_delete:
                 try:
                     with get_conn() as conn:
                         count = conn.execute("SELECT COUNT(*) as c FROM requests WHERE status = ?", (status_to_delete,)).fetchone()['c']
                         if count > 0:
                             st.warning(f"لا يمكن حذف الحالة '{status_to_delete}' لأنها مستخدمة في {count} طلب(طلبات).")
                         else:
                             conn.execute("DELETE FROM status_settings WHERE status_name = ?", (status_to_delete,))
                             conn.execute("DELETE FROM request_statuses WHERE name = ?", (status_to_delete,))
                             conn.commit()
                             st.success(f"تم حذف الحالة: {status_to_delete}")
                             # مسح الذاكرة المؤقتة
                             get_request_statuses.clear()
                             get_preventing_statuses.clear()
                             get_blocking_statuses.clear()
                             time.sleep(0.5)
                             st.rerun()
                 except Exception as e:
                     st.error(f"خطأ: {e}")
             else:
                 st.warning("يرجى اختيار حالة للحذف.")

    st.markdown("#### 📄 أنواع المستندات المطلوبة (للأدمن فقط)")
    doc_types = get_document_types()
    
    for doc in doc_types:
        with st.expander(f"تعديل: {doc['display_name']} ({doc['name']})"):
            new_display_name = st.text_input("الاسم المعروض", value=doc['display_name'], key=f"display_{doc['name']}")
            new_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟", value=bool(doc['is_video_allowed']), key=f"video_{doc['name']}")
            
            if st.button("حفظ التعديل", key=f"save_doc_{doc['name']}"):
                with get_conn() as conn:
                    # تحديث نوع المستند
                    conn.execute("UPDATE document_types SET display_name = ?, is_video_allowed = ? WHERE name = ?", (new_display_name, 1 if new_is_video_allowed else 0, doc['name']))
                    
                    # تحديث المستندات الموجودة في الطلبات
                    conn.execute("UPDATE documents SET display_name = ?, is_video_allowed = ? WHERE doc_type = ?", (new_display_name, 1 if new_is_video_allowed else 0, doc['name']))
                    
                    conn.commit()
                st.success("تم حفظ التعديل وتطبيقه على جميع الطلبات")
                # إعادة تحميل الصفحة
                time.sleep(0.5)
                st.rerun()

    with st.form("add_doc_type"):
        st.markdown("##### إضافة نوع مستند جديد")
        new_doc_name = st.text_input("الاسم الداخلي (لا يمكن تغييره لاحقًا)")
        new_doc_display_name = st.text_input("الاسم المعروض")
        new_doc_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟")
        
        if st.form_submit_button("إضافة نوع مستند"):
            if new_doc_name and new_doc_display_name:
                try:
                    with get_conn() as conn:
                        # إضافة نوع المستند الجديد
                        conn.execute("INSERT INTO document_types (name, display_name, is_video_allowed) VALUES (?, ?, ?)", (new_doc_name, new_doc_display_name, 1 if new_doc_is_video_allowed else 0))
                        
                        # إضافة المستند للطلبات الموجودة مع تحديث is_video_allowed
                        existing_requests = conn.execute("SELECT DISTINCT r.id, h.type FROM requests r JOIN hospitals h ON r.hospital_id = h.id WHERE r.deleted_at IS NULL").fetchall()
                        for req in existing_requests:
                            hospital_type = req['type']
                            optional_docs = get_optional_docs_for_type(hospital_type)
                            is_required = 0 if new_doc_name in optional_docs else 1
                            conn.execute("INSERT OR IGNORE INTO documents (request_id, doc_type, display_name, required, satisfied, uploaded_at, is_video_allowed, updated_at) VALUES (?, ?, ?, ?, 0, NULL, ?, ?)", 
                                       (req['id'], new_doc_name, new_doc_display_name, is_required, 1 if new_doc_is_video_allowed else 0, datetime.now().isoformat()))
                        
                        conn.commit()
                    st.success("تمت إضافة نوع المستند وتطبيقه على الطلبات الموجودة")
                    # إعادة تحميل الصفحة لعرض التغييرات
                    time.sleep(0.5)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("الاسم الداخلي موجود مسبقًا")
                except Exception as e:
                    st.error(f"خطأ: {e}")
            else:
                st.warning("يرجى ملء الحقول المطلوبة.")

    st.markdown("#### 📄 إدارة المستندات الاختيارية لأنواع المستشفيات")
    hospital_types = get_hospital_types()
    all_doc_names = [dt['name'] for dt in get_document_types()]

    if hospital_types:
        for htype in hospital_types:
            with st.expander(f"تعديل المستندات لـ {htype}", expanded=False):
                st.markdown(f"### {htype}")
                current_optional_docs = get_optional_docs_for_type(htype)
                selected_optional_docs = st.multiselect(
                    f"اختر المستندات الاختيارية لـ {htype}",
                    options=all_doc_names,
                    default=list(current_optional_docs),
                    key=f"multiselect_optional_docs_{htype}"
                )
                
                if st.button(f"💾 حفظ التغييرات لـ {htype}", key=f"save_button_{htype}"):
                    try:
                        set_optional_docs_for_type(htype, selected_optional_docs)
                        
                        # تطبيق التغييرات على الطلبات الموجودة فوراً
                        with get_conn() as conn:
                            # الحصول على جميع الطلبات لهذا النوع من المستشفيات
                            requests = conn.execute("SELECT r.id FROM requests r JOIN hospitals h ON r.hospital_id = h.id WHERE h.type = ? AND r.deleted_at IS NULL", (htype,)).fetchall()
                            
                            updated_requests = 0
                            for req in requests:
                                # تحديث حالة المطلوب/اختياري للمستندات
                                for doc_name in all_doc_names:
                                    is_required = 0 if doc_name in selected_optional_docs else 1
                                    result = conn.execute("UPDATE documents SET required = ? WHERE request_id = ? AND doc_type = ?", (is_required, req['id'], doc_name))
                                    if result.rowcount > 0:
                                        updated_requests += 1
                            
                            conn.commit()
                            
                        # مسح الذاكرة المؤقتة لضمان التحديث
                        get_optional_docs_for_type.clear()
                        get_document_types.clear()
                        
                        st.success(f"✅ تم حفظ المستندات الاختيارية لـ {htype} وتطبيقها على {len(requests)} طلب موجود")
                        st.info(f"📋 المستندات الاختيارية الحالية لـ {htype}: {', '.join(selected_optional_docs) if selected_optional_docs else 'لا توجد'}")
                        # إعادة تحميل الصفحة لعرض التغييرات
                        time.sleep(0.5)  # انتظار قصير لضمان حفظ البيانات
                        st.rerun() 
                    except Exception as e:
                        st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")

def admin_users_ui():
    st.markdown("<div class='subheader'>إدارة المستخدمين</div>", unsafe_allow_html=True)
    
    st.markdown("#### 👤 المستخدمون الإداريون")
    with get_conn() as conn:
        admins = conn.execute("SELECT id, username, role FROM admins ORDER BY id").fetchall()
    
    for admin in admins:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"<div style='padding: 10px;'><b>{admin['username']}</b> ({admin['role']})</div>", unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ حذف", key=f"del_admin_{admin['id']}") and admin['username'] != 'admin':
                with get_conn() as conn:
                    conn.execute("DELETE FROM admins WHERE id=?", (admin['id'],))
                    conn.commit()
                st.success("تم الحذف")
                st.rerun()
        with col3:
            if st.button("إعادة تعيين كلمة المرور", key=f"reset_admin_{admin['id']}"):
                with get_conn() as conn:
                    import secrets
                    new_password = secrets.token_urlsafe(8)
                    conn.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new_password), admin['id']))
                    conn.commit()
                st.success(f"تمت إعادة تعيين كلمة المرور إلى: {new_password}")
        with col4:
            st.write("")
    
    st.markdown("#### ➕ إضافة مستخدم")
    with st.form("add_admin"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة مرور قوية")
        role = st.selectbox("الدور", ["admin", "reviewer"])
        sub = st.form_submit_button("إضافة")
        if sub:
            try:
                with get_conn() as conn:
                    conn.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", (u, hash_pw(p), role))
                    conn.commit()
                st.success("تمت الإضافة")
            except sqlite3.IntegrityError:
                st.error("اسم المستخدم موجود مسبقًا")
    
    st.markdown("#### 🔁 إعادة تعيين كلمة المرور")
    with st.form("reset_password"):
        user_type = st.radio("نوع المستخدم", ["مستشفى", "إداري"])
        
        if user_type == "مستشفى":
            with get_conn() as conn:
                hospitals = conn.execute("SELECT id, name, username FROM hospitals ORDER BY name").fetchall()
            
            hospital_options = [f"{h['id']} - {h['name']} ({h['username']})" for h in hospitals]
            selected_hospital = st.selectbox("اختر المستشفى", hospital_options)
            new_password = st.text_input("كلمة المرور الجديدة", type="password", value="")
            
            if st.form_submit_button("إعادة تعيين"):
                if selected_hospital:
                    hospital_id = int(selected_hospital.split(" - ")[0])
                    with get_conn() as conn:
                        conn.execute("UPDATE hospitals SET password_hash=? WHERE id=?", (hash_pw(new_password), hospital_id))
                        conn.commit()
                    st.success(f"تمت إعادة تعيين كلمة المرور للمستشفى: {selected_hospital}")
        
        else:
            with get_conn() as conn:
                admins = conn.execute("SELECT id, username FROM admins ORDER BY username").fetchall()
            
            if admins:
                admin_options = [f"{a['id']} - {a['username']}" for a in admins]
                selected_admin = st.selectbox("اختر المستخدم الإداري", admin_options)
                new_password = st.text_input("كلمة المرور الجديدة", type="password")
                
                if st.form_submit_button("إعادة تعيين"):
                    if selected_admin:
                        admin_id = int(selected_admin.split(" - ")[0])
                        with get_conn() as conn:
                            conn.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new_password), admin_id))
                            conn.commit()
                        st.success(f"تمت إعادة تعيين كلمة المرور للمستخدم: {selected_admin}")
            else:
                st.info("لا يوجد مستخدمين إداريين لإعادة تعيين كلمات مرورهم")

def admin_resources_ui():
    st.markdown("<div class='subheader'>إدارة ملفات التنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك رفع الملفات التالية لجعلها متوفرة للمستخدمين</div>", unsafe_allow_html=True)
    
    RESOURCES_DIR.mkdir(exist_ok=True)
    
    # الحصول على قائمة الملفات من الثابت RESOURCE_FILES
    resource_files_list = RESOURCE_FILES

    for filename in resource_files_list:
        filepath = RESOURCES_DIR / filename
        st.markdown(f"#### {filename}")
        col1, col2 = st.columns([3, 1])
        with col1:
            if filepath.exists():
                st.success("✅ الملف متوفر")
                with open(filepath, "rb") as f:
                    st.download_button(
                        label="📥 تنزيل الملف الحالي",
                        data=f,
                        file_name=filename,
                        mime="application/pdf",
                        key=f"download_{filename}"
                    )
            else:
                st.warning("⚠️ الملف غير متوفر")
        with col2:
            uploaded_file = st.file_uploader("رفع ملف جديد", type=["pdf"], key=f"upload_{filename}")
            if uploaded_file is not None:
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("تم رفع الملف بنجاح")

# ---------------------------- وظائف عامة ---------------------------- #
def change_password_ui(user_id: int, user_table: str):
    st.markdown("<div class='subheader'>تغيير كلمة المرور</div>", unsafe_allow_html=True)
    
    with st.form("change_pw"):
        old_pw = st.text_input("كلمة المرور الحالية", type="password")
        new_pw1 = st.text_input("كلمة المرور الجديدة", type="password")
        new_pw2 = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
        
        if st.form_submit_button("تغيير كلمة المرور", use_container_width=True):
            if not all([old_pw, new_pw1, new_pw2]):
                st.warning("يرجى ملء جميع الحقول.")
                return
            if new_pw1 != new_pw2:
                st.error("كلمتا المرور الجديدتان غير متطابقتين.")
                return

            with get_conn() as conn:
                user = conn.execute(f"SELECT password_hash FROM {user_table} WHERE id=?", (user_id,)).fetchone()
                if not user:
                    st.error("لم يتم العثور على المستخدم.")
                    return
                if verify_password(old_pw, user['password_hash']):
                    conn.execute(f"UPDATE {user_table} SET password_hash=? WHERE id=?", (hash_pw(new_pw1), user_id))
                    conn.commit()
                    st.success("تم تغيير كلمة المرور بنجاح.")
                    log_activity("تغيير كلمة المرور")
                    st.info("يرجى تسجيل الدخول مرة أخرى باستخدام كلمة المرور الجديدة.")
                    st.session_state.clear()
                    st.rerun()
                else:
                    time.sleep(0.1)
                    st.error("كلمة المرور الحالية غير صحيحة.")

# ---------------------------- تشغيل التطبيق ---------------------------- #
def main():
    # إعدادات الصفحة الأساسية
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # --- إضافة البنر في الأعلى ---
    banner_path = next((p for p in [Path("static/banner.png"), Path("static/banner.jpg")] if p.exists()), None)
    if "user" in st.session_state and banner_path: # عرض البنر فقط بعد تسجيل الدخول
        with open(banner_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded_string}' class='banner-image'></div>", unsafe_allow_html=True)


    # تهيئة قاعدة البيانات وتشغيل migrations (مرة واحدة فقط)
    @st.cache_resource
    def initialize_database():
        try:
            run_ddl()
            run_migrations()
            # تنظيف الذاكرة المؤقتة بعد التهيئة لضمان البيانات المحدثة
            force_refresh_cache()
            return True
        except Exception as e:
            st.error(f"❌ خطأ في تهيئة النظام: {e}")
            return False
    
    if not initialize_database():
        st.error("يرجى إعادة تحميل الصفحة أو التواصل مع الدعم الفني")
        return
    
    # التحقق من حالة تسجيل الدخول
    if "user" not in st.session_state:
        # عرض واجهة الدخول
        login_ui()
    else:
        # توجيه المستخدم بناءً على الدور
        role = st.session_state.user.get("role")
        
        # إضافة رسالة ترحيبية بسيطة وتنظيف الذاكرة المؤقتة
        if "welcome_shown" not in st.session_state:
            user_name = st.session_state.user.get("name", st.session_state.user.get("username", "المستخدم"))
            st.toast(f"مرحباً بعودتك {user_name}! 👋", icon="🏨")
            st.session_state.welcome_shown = True
            # تنظيف دوري للذاكرة المؤقتة لضمان عرض البيانات المحدثة
            cleanup_memory()
        
        if role == "hospital":
            hospital_home()
        elif role in ["admin", "reviewer"]:
            admin_home()
        else:
            st.error("❌ دور المستخدم غير معروف")
            st.session_state.pop("user", None)
    
    # تذييل الصفحة البسيط والأنيق
    st.markdown("""
        <div class='footer'>
            <div style="text-align: center; padding: 20px;">
                <p style="margin: 0; font-weight: 600; color: #1e40af; font-size: 16px;">
                    © 2025 المشروع القومي لقوائم الانتظار
                </p>
                <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">
                    تصميم وتطوير: الغرفة المركزية لقوائم الانتظار
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("""
        **❌ حدث خطأ غير متوقع في النظام**
        
        يرجى:
        1. تحديث الصفحة
        2. التأكد من اتصال الإنترنت
        3. التواصل مع الدعم الفني إذا استمرت المشكلة
        """)
        # لإظهار الخطأ الفعلي في الطرفية أثناء التطوير
        import traceback
        traceback.print_exc()

