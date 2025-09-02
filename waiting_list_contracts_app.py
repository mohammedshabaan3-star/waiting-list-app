<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""
نظام التعاقد على الخدمات الجراحية - المشروع القومي لقوائم الانتظار
---------------------------------------------------------------
برنامج ويب احترافي لإدارة طلبات التعاقد بين المستشفيات والمشروع القومي لقوائم الانتظار.
الميزات:
✅ واجهة مستخدم عربية جذابة ومتميزة.
✅ واجهة دخول واحدة مع تحديد تلقائي للدور (مستشفى / أدمن).
✅ توليد أسماء مستخدمين من اسم المستشفى (أول 3 كلمات بالإنجليزية).
✅ توليد كلمة مرور افتراضية (1234).
✅ إدارة كاملة للبيانات الأساسية لكل مستشفى.
✅ تقديم طلبات التعاقد على الخدمات الجراحية.
✅ رفع ملفات PDF/Video مطلوبة مع تسمية منظمة.
✅ وضع علامة "مستوفى / غير مستوفى" على كل ملف من قبل الأدمن.
✅ يمكن تقديم طلب جديد لنفس الخدمة فقط بعد "حذف نهائي" أو "إعادة تقديم".
✅ إمكانية حذف الطلب نهائياً (ينتقل إلى المحذوفات) مع إتاحة تقديم طلب جديد فوراً.
✅ دعم التمييز بين المستشفيات الحكومية والخاصة (تفعيل/تعطيل متطلبات).
✅ إضافة وتعديل الخدمات من قبل الأدمن.
✅ تعديل بيانات المستشفى بالكامل.
✅ بحث متقدم في الطلبات (بالاسم، الخدمة، نص حر).
✅ تصميم ألوان جذاب وأنيق (أزرق داكن، أبيض، أزرق فاتح).
✅ دعم استيراد/تصدير ملفات Excel.
✅ إجبارية إدخال بيانات المستشفى الأساسية قبل حفظ الطلب.
✅ السماح بالتعديل/الحذف/إعادة الرفع في حالة "جارى دراسة الطلب".
✅ إمكانية حذف أو إلغاء تفعيل خدمة.
✅ تبويب لاستعادة كلمات المرور (إعادة تعيينها).
✅ صلاحيات المستخدم المراجع.
✅ تحليل إحصائي متقدم مع تصفية حسب القطاع والخدمة والنوع والحالة.
✅ إضافة شعار للواجهة وحقوق الملكية.
✅ ملفات للتنزيل: نماذج الاعتماد ومتطلبات التعاقد وطريقة التسجيل وتعليمات هامة.
✅ منع التقديم لنفس الخدمة لمدة 3 أشهر في حالة (مرفوض) أو (إرجاء التعاقد).
✅ إتاحة تعديل وإعادة تعيين بيانات المستشفى من قبل الأدمن.
✅ في شاشة الأدمن والمراجع إتاحة التعامل مع الطلبات باختيار الخدمة والمستشفى وID الطلب.
✅ تعديل وحذف وإضافة الحالات (حالة الطلب) من قبل الأدمن فقط.
✅ دعم القوائم المنسدلة والدخول الحر في البحث والحقول.
✅ تعديل: طلب غير مكتمل حتى رفع المستندات المطلوبة.
✅ تعديل: إمكانية إدارة أنواع المستندات المطلوبة.
✅ تعديل: دعم رفع فيديو لغرف العمليات.
✅ تعديل: التحكم في حالات الطلب التي تمنع التقديم.
✅ تعديل: توسيع الشاشة.
"""
import os
import re
import io
import zipfile
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import sqlite3
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
# ---------------------------- إعدادات أساسية ---------------------------- #
APP_TITLE = "المشروع القومي لقوائم الانتظار - التعاقد على الخدمات الجراحية"
DB_PATH = Path("data/app.db")
STORAGE_DIR = Path("storage")
EXPORTS_DIR = Path("exports")
RESOURCES_DIR = Path("static")

# إنشاء المجلدات
for p in [DB_PATH.parent, STORAGE_DIR, EXPORTS_DIR, RESOURCES_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# ... (الأجزاء الأخرى من الكود كما هي) ...

# - أنماط CSS مخصصة - #
st.markdown("""
<style>
    /* توسيع العرض الأقصى للصفحة الرئيسية */
    .main {
        background-color: #f8f9fa;
        color: #333;
        direction: rtl;
        font-family: 'Cairo', sans-serif;
        /* تغيير العرض الأقصى ليغطي الشاشة بالكامل */
        max-width: 100vw; /* عرض الشاشة بالكامل */
        padding-left: 2rem;
        padding-right: 2rem;
        margin: 0 auto; /* توسيط المحتوى */
    }
    
    /* تحسين عرض الحاويات داخل النماذج */
    .stForm {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        /* زيادة العرض داخل النماذج */
        max-width: 100%;
    }
    
    /* تحسين عرض الجداول */
    .stDataFrame {
        width: 100% !important;
    }
    
    /* تحسين عرض أعمدة النص */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        width: 100%;
        min-width: 200px; /* الحد الأدنى للعرض */
    }
    
    /* تحسين عرض الأزرار */
    .stButton>button {
        background-color: #1a56db;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
        width: auto; /* السماح للأزرار بالتكيف مع المحتوى */
    }
    
    .stButton>button:hover {
        background-color: #1e40af;
    }
    
    /* تحسين عرض عناصر الإدخال */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stTextArea>div>div>textarea {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض علامات التبويب */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-size: 16px;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض التنبيهات */
    .stAlert {
        border-radius: 8px;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض العناوين */
    h1, h2, h3 {
        color: #1e40af;
        font-family: 'Cairo', sans-serif;
    }
    
    .header {
        text-align: center;
        color: #1e40af;
        font-weight: 200;
        margin-bottom: 20px;
        font-family: 'Cairo', sans-serif;
    }
    
    .subheader {
        color: #1a56db;
        font-weight: 200;
        margin-top: 20px;
        margin-bottom: 10px;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض مربعات المعلومات */
    .info-box {
        background-color: #dbeafe;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1e40af;
        margin: 10px 0;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض النصوص المطلوبة */
    .required::after {
        content: " *";
        color: red;
    }
    
    /* تحسين عرض شعار التطبيق */
    .logo-container {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .logo-container img {
        max-width: 150px;
        height: auto;
    }
    
    /* تحسين عرض التذييل */
    .footer {
        text-align: center;
        margin-top: 30px;
        padding: 20px;
        border-top: 1px solid #e2e8f0;
        color: #64748b;
        font-size: 14px;
        /* جعل التذييل يغطي العرض الكامل */
        width: 100%;
    }
    
    /* تحسين عرض بطاقات الإحصائيات */
    .stats-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        width: 100%;
    }
    
    /* تحسين عرض عناصر الإحصائيات */
    .stats-header {
        color: #1e40af;
        font-weight: 600;
        margin-bottom: 15px;
        font-size: 18px;
    }
    
    .stats-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .stats-item:last-child {
        border-bottom: none;
    }
    
    .stats-label {
        font-weight: 500;
    }
    
    .stats-value {
        font-weight: 600;
        color: #1a56db;
    }
    
    /* تحسين عرض أعمدة البيانات */
    [data-testid="column"] {
        padding: 0 10px;
    }
    
    /* تحسين عرض محددات الصفحات */
    .css-18ni7ap { /* محدد الصفحة */
        max-width: 100%;
    }
    
    /* تحسين عرض محتوى التطبيق بشكل عام */
    section[data-testid="stSidebar"] {
        width: 250px !important; /* تحديد عرض الشريط الجانبي */
    }
    
    /* تحسين عرض العناصر داخل الأعمدة */
    .st-bf { /* معرف CSS لأعمدة Streamlit */
        gap: 1rem; /* المسافة بين الأعمدة */
    }
</style>
""", unsafe_allow_html=True)

# ... (باقي الكود كما هو) ...

# ---------------------------- ثوابت وخيارات ---------------------------- #
# سيتم تحميلها من قاعدة البيانات أو استخدام الافتراضية لاحقاً
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
# أنواع الفئات
AGE_CATEGORIES = ["كبار", "أطفال", "كبار وأطفال"]
# حالة الطلب الافتراضية - سيتم تحميلها من قاعدة البيانات
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
    "طلب غير مكتمل", # حالة جديدة
]
# أنواع المستندات المطلوبة الافتراضية - سيتم تحميلها من قاعدة البيانات
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
    "فيديو لغرف العمليات والإقامة", # نوع ملف مرن
    "السعة السريرية الكلية - عدد أسرة الرعايات",
    "تشكيل فريق مكافحة العدوى - تشكيل فريق الجودة",
    "محاضر اجتماعات الفرق لآخر 3 أشهر",
    "السياسات الخاصة بالجراحة والتخدير معتمدة",
    "أخرى",
]
GOVERNMENT_OPTIONAL_DOCS = {
    "ترخيص العلاج الحر موضح به التخصصات", # <-- تمت تصحيحه
    "صورة بطاقة ضريبية للمنشأة سارية",
    "صورة حديثة للسجل التجاري",
    "أخرى","تقييم مكافحة العدوى (ذاتي)"
}
# المستندات التي لا تُطلب للمستشفيات الخاصة (افتراضياً) - يمكن أن تكون فارغة
PRIVATE_OPTIONAL_DOCS = set(["أخرى","تقييم مكافحة العدوى من الجهة التابع لها المستشفى"])
# ... (باقي الثوابت كما هي: DEFAULT_SERVICES, DEFAULT_HOSPITAL_TYPES, إلخ) ...
# -----------

# ملفات الموارد المتاحة للتنزيل
RESOURCE_FILES = [
    "القلب المفتوح.pdf",
    "القسطره القلبيه.pdf",
    "الاوعيه الدمويه والقسطره الطرفيه.pdf",
    "القسطره المخيه.pdf",
    "المخ والاعصاب.pdf",
    "الرمد.pdf",
    "العظام.pdf",
    "زراعة الكبد.pdf",
    "زراعة الكلى.pdf",
    "الاورام.pdf",
      "زراعة القوقعه.pdf",
    "متطلبات التعاقد.pdf",
    "طريقة التسجيل.pdf",
    "تعليمات هامة.pdf"
]

# ---------------------------- أدوات مساعدة ---------------------------- #
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def check_file_type(filename: str, is_video_allowed: bool) -> bool:
    """التحقق من نوع الملف المسموح برفعه"""
    ext = Path(filename).suffix.lower()
    allowed_extensions = {'.pdf'}
    if is_video_allowed:
        allowed_extensions.update({'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'})
    return ext in allowed_extensions

def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\-\.\u0621-\u064A\s]", "_", name)
    name = re.sub(r"\s+", "_", name).strip("_.")
    return name or "file"

def is_video_only_document(doc_type_name: str) -> bool:
    """
    التحقق مما إذا كان نوع المستند يجب أن يقبل فقط ملفات الفيديو.
    Args:
        doc_type_name (str): اسم نوع المستند كما هو في قاعدة البيانات.
    Returns:
        bool: True إذا كان يجب أن يكون فيديو فقط، False إذا كان يقبل PDF أيضًا.
    """
    # قائمة بأسماء المستندات التي يجب أن تقبل فقط ملفات الفيديو
    VIDEO_ONLY_DOCUMENTS = {
        "فيديو لغرف العمليات والإقامة"
        # يمكن إضافة أسماء أخرى هنا في المستقبل إذا لزم الأمر
    }
    return doc_type_name in VIDEO_ONLY_DOCUMENTS

# ---------------------------- وظائف مساعدة للإعدادات ---------------------------- #

def get_hospital_types() -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='hospital_types'")
    row = cur.fetchone()
    conn.close()
    types = row["value"].split(",") if row and row["value"] else []
    return types or DEFAULT_HOSPITAL_TYPES

def set_hospital_types(types: list):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO meta(key,value) VALUES('hospital_types', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(types),))
    conn.commit()
    conn.close()

def get_sectors() -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='sectors'")
    row = cur.fetchone()
    conn.close()
    sectors = row["value"].split(",") if row and row["value"] else []
    return sectors or DEFAULT_SECTORS

def set_sectors(sectors: list):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO meta(key,value) VALUES('sectors', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(sectors),))
    conn.commit()
    conn.close()

def get_governorates() -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='governorates'")
    row = cur.fetchone()
    conn.close()
    gov = row["value"].split(",") if row and row["value"] else []
    return gov or DEFAULT_GOVERNORATES

def set_governorates(gov: list):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO meta(key,value) VALUES('governorates', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(gov),))
    conn.commit()
    conn.close()

def get_request_statuses() -> list:
    """الحصول على قائمة الحالات من قاعدة البيانات أو استخدام الافتراضية"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM request_statuses ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    if rows:
        return [row['name'] for row in rows]
    else:
        # في حالة عدم وجود حالات مخصصة، نستخدم الافتراضية
        return DEFAULT_REQUEST_STATUSES

def get_open_statuses() -> set:
    """الحصول على الحالات التي تمنع تقديم طلب جديد لنفس الخدمة"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status_name FROM status_settings WHERE prevents_new_request = 1")
    rows = cur.fetchall()
    conn.close()
    return {row['status_name'] for row in rows}

def get_blocked_statuses(days: int = 90) -> set:
    """الحصول على الحالات التي تمنع التقديم لنفس الخدمة لمدة X أيام"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status_name FROM status_settings WHERE blocks_service_for_days >= ?", (days,))
    rows = cur.fetchall()
    conn.close()
    return {row['status_name'] for row in rows}

def is_final_status(status: str) -> bool:
    """التحقق مما إذا كانت الحالة نهائية (تتطلب تسجيل closed_at)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT is_final_state FROM status_settings WHERE status_name = ?", (status,))
    row = cur.fetchone()
    conn.close()
    return row and row['is_final_state'] == 1

def get_document_types() -> list:
    """الحصول على قائمة أنواع المستندات"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, display_name, is_video_allowed FROM document_types ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [{'name': row['name'], 'display_name': row['display_name'], 'is_video_allowed': row['is_video_allowed']} for row in rows]

def get_optional_docs_for_type(hospital_type: str) -> set:
    """جلب المستندات الاختيارية لنوع مستشفى معين من قاعدة البيانات."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT doc_name FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,))
    rows = cur.fetchall()
    conn.close()
    return {row['doc_name'] for row in rows}

def set_optional_docs_for_type(hospital_type: str, doc_names: list):
    """تحديث المستندات الاختيارية لنوع مستشفى معين في قاعدة البيانات."""
    conn = get_conn()
    cur = conn.cursor()
    # حذف الإدخالات الحالية لهذا النوع
    cur.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,))
    # إدخال الإدخالات الجديدة
    for doc_name in doc_names:
        if doc_name: # تجنب إدخال أسماء فارغة
            cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", (hospital_type, doc_name))
    conn.commit()
    conn.close()

def ensure_request_docs(request_id: int, hospital_type: str):
    """إنشاء سجلات المستندات الافتراضية للطلب وفق نوع المستشفى."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT doc_type FROM documents WHERE request_id=?", (request_id,))
    existing = {r["doc_type"] for r in cur.fetchall()}
    
    # ***تحديث هنا: استخدام القواعد الجديدة***
    # الحصول على المستندات الاختيارية لهذا النوع من قاعدة البيانات
    optional_docs_for_this_type = get_optional_docs_for_type(hospital_type)

    for dt in DOC_TYPES:
        # ***تحديث هنا: تحديد ما إذا كان المستند مطلوبًا أم لا***
        # إذا كان المستند في قائمة المستندات الاختيارية لهذا النوع، فهو غير مطلوب (required=0)
        # وإلا، فهو مطلوب (required=1)
        required = 0 if dt in optional_docs_for_this_type else 1
        
        if dt not in existing:
            cur.execute(
                "INSERT INTO documents (request_id, doc_type, required, satisfied, uploaded_at) VALUES (?,?,?,?,?)",
                (request_id, dt, required, 0, None),
            )
    conn.commit()
    conn.close()

def hospital_has_open_request(hospital_id: int, service_id: int) -> bool:
    """التحقق من وجود طلب مفتوح (منع التقديم) لنفس الخدمة"""
    open_statuses = get_open_statuses()
    if not open_statuses:
         return False # إذا لم تكن هناك حالات مفتوحة محددة، لا تمنع

    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(open_statuses))
    query = f"""
        SELECT COUNT(1) c
        FROM requests
        WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL AND status IN ({placeholders})
    """
    params = [hospital_id, service_id] + list(open_statuses)
    cur.execute(query, params)
    c = cur.fetchone()["c"]
    conn.close()
    return c > 0

def hospital_blocked_from_request(hospital_id: int, service_id: int) -> bool:
    """التحقق من منع المستشفى من تقديم طلب لنفس الخدمة لمدة 3 أشهر"""
    blocked_statuses = get_blocked_statuses(90) # افتراضيًا 90 يوم
    if not blocked_statuses:
        return False # إذا لم تكن هناك حالات محظورة محددة، لا تمنع

    conn = get_conn()
    cur = conn.cursor()
    three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
    placeholders = ",".join(["?"] * len(blocked_statuses))
    query = f"""
        SELECT COUNT(1) c
        FROM requests
        WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL AND status IN ({placeholders}) AND closed_at > ?
    """
    params = [hospital_id, service_id] + list(blocked_statuses) + [three_months_ago]
    cur.execute(query, params)
    c = cur.fetchone()["c"]
    conn.close()
    return c > 0

def generate_username(hospital_name: str) -> str:
    """توليد اسم مستخدم من اسم المستشفى (أول 3 كلمات بالإنجليزية)"""
    arabic_to_english = {
        'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'g', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's',
        'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': '3', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
        'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ى': 'a', 'ئ': '2', 'ء': '2', 'ؤ': '2'
    }
    english_name = ""
    for char in hospital_name:
        if char in arabic_to_english:
            english_name += arabic_to_english[char]
        elif char.isalpha() or char.isdigit():
            english_name += char
        else:
            english_name += "_"
    words = english_name.split("_")[:3]
    username = "".join(words).replace(" ", "").replace("-", "").replace("_", "")
    username = re.sub(r"[^\w]", "", username)
    return username.lower()[:20] or "hospital"

def is_hospital_profile_complete(hospital_id: int) -> bool:
    """التحقق من إكمال بيانات المستشفى الأساسية"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT license_start, license_end, license_number, manager_name, manager_phone, address
        FROM hospitals WHERE id=?
    """, (hospital_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    required_fields = [
        row['license_start'], row['license_end'], row['license_number'],
        row['manager_name'], row['manager_phone'], row['address']
    ]
    return all(field and str(field).strip() for field in required_fields)

# ---------------------------- واجهة الدخول ---------------------------- #
def login_ui():
    # البحث عن البانر (يدعم PNG و JPG)
    banner_path_png = Path("static/banner.png")
    banner_path_jpg = Path("static/banner.jpg")
    banner_path = None
    if banner_path_png.exists():
        banner_path = banner_path_png
    elif banner_path_jpg.exists():
        banner_path = banner_path_jpg
    
    if banner_path:
        st.image(str(banner_path), use_container_width=True, caption="")
    else:
        # رسالة اختيارية للمستخدم الإداري
        # st.warning("لم يتم العثور على ملف البانر (banner.png أو banner.jpg) في مجلد static/")
        pass # أو اتركه فارغًا إذا كنت لا تريد إظهار أي شيء

    st.markdown(f"<div class='header'><h1>{APP_TITLE}</h1></div>", unsafe_allow_html=True)
    
    # البحث عن الشعار (يدعم PNG و JPG)
    logo_path_png = Path("static/logo.png")
    logo_path_jpg = Path("static/logo.jpg")
    logo_path = None
    if logo_path_png.exists():
        logo_path = logo_path_png
    elif logo_path_jpg.exists():
        logo_path = logo_path_jpg
    
    if logo_path:
        st.image(str(logo_path), width=50)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    # ... (باقي الكود كما هو)
    with st.form("login_form"):
        st.markdown("### تسجيل دخول")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("تسجيل الدخول")
        if submitted:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM hospitals WHERE username=? AND password_hash=?", (username, hash_pw(password)))
            hospital_user = cur.fetchone()
            if hospital_user:
                st.session_state.user = {
                    "role": "hospital",
                    "hospital_id": hospital_user["id"],
                    "hospital_name": hospital_user["name"],
                    "hospital_code": hospital_user["code"],
                    "hospital_type": hospital_user["type"],
                }
                st.success("تم تسجيل الدخول بنجاح")
                st.rerun()
            cur.execute("SELECT * FROM admins WHERE username=? AND password_hash=?", (username, hash_pw(password)))
            admin_user = cur.fetchone()
            conn.close()
            if admin_user:
                st.session_state.user = {
                    "role": admin_user["role"],
                    "username": admin_user["username"],
                    "admin_id": admin_user["id"],
                }
                st.success("تم تسجيل الدخول بنجاح")
                st.rerun()
            if not hospital_user and not admin_user:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# ... (تستمر في القسم التالي)
# ... (متابعة من القسم 2)

# تعريف الإصدار الحالي لهيكل قاعدة البيانات
# قم بزيادة هذا الرقم في كل مرة تضيف فيها تغييرًا جديدًا على هيكل قاعدة البيانات
DB_SCHEMA_VERSION = 4  # مثال: تم إضافة عمود is_video_allowed وجدول hospital_type_optional_docs

# تعريف الإصدار الحالي لهيكل قاعدة البيانات
DB_SCHEMA_VERSION = 4

@st.cache_resource
def get_db_initial_version():
    """الحصول على إصدار قاعدة البيانات عند بدء التشغيل"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
        row = cur.fetchone()
        version = row['version'] if row else 0
        conn.close()
        return version
    except:
        return 0

# تعريف الإصدار الحالي لهيكل قاعدة البيانات
# قم بزيادة هذا الرقم في كل مرة تضيف فيها تغييرًا جديدًا على هيكل قاعدة البيانات
DB_SCHEMA_VERSION = 4 # مثال: تم إضافة عمود is_video_allowed وجدول hospital_type_optional_docs

def run_ddl():
    """إنشاء جداول قاعدة البيانات وتحديثها إذا لزم الأمر لـ SQLite."""
    conn = get_conn()
    with conn:
        cur = conn.cursor()
        
        # --- إنشاء الجداول ---
        # جدول الأدمن
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT DEFAULT 'admin' -- admin, reviewer
            )
        """)
        
        # جدول المستشفيات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sector TEXT,
                governorate TEXT,
                code TEXT UNIQUE,
                type TEXT DEFAULT 'خاص',
                address TEXT,
                other_branches TEXT,
                other_branches_address TEXT,
                license_start TEXT,
                license_end TEXT,
                manager_name TEXT,
                manager_phone TEXT,
                license_number TEXT,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        """)
        
        # جدول الخدمات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                active INTEGER DEFAULT 1
            )
        """)
        
        # جدول الطلبات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_id INTEGER,
                service_id INTEGER,
                age_category TEXT,
                status TEXT DEFAULT 'طلب غير مكتمل',
                admin_note TEXT,
                created_at TEXT,
                deleted_at TEXT,
                closed_at TEXT, -- تاريخ إغلاق الطلب (مرفوض/مقبول/مغلق/...)
                updated_at TEXT, -- تاريخ آخر تعديل
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        """)

        # ترقية جدول الطلبات: إضافة عمود updated_at إذا لم يكن موجوداً
        try:
            cur.execute("SELECT updated_at FROM requests LIMIT 1")
        except sqlite3.OperationalError as e:
            if "no such column: updated_at" in str(e):
                cur.execute("ALTER TABLE requests ADD COLUMN updated_at TEXT")
                conn.commit()
                print("تمت إضافة عمود 'updated_at' إلى جدول 'requests'.")
            else:
                raise e

        # ترقية جدول الطلبات: إضافة عمود closed_at إذا لم يكن موجوداً
        try:
            cur.execute("SELECT closed_at FROM requests LIMIT 1")
        except sqlite3.OperationalError as e:
            if "no such column: closed_at" in str(e):
                cur.execute("ALTER TABLE requests ADD COLUMN closed_at TEXT")
                conn.commit()
                print("تمت إضافة عمود 'closed_at' إلى جدول 'requests'.")
            else:
                raise e

        # جدول المستندات (الذي تم تحديثه)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                doc_type TEXT, -- الاسم الأصلي من قائمة المستندات
                display_name TEXT, -- الاسم المعروض (يمكن تعديله)
                file_name TEXT,
                file_path TEXT,
                required INTEGER DEFAULT 1,
                satisfied INTEGER DEFAULT 0,
                admin_comment TEXT,
                uploaded_at TEXT,
                is_video_allowed INTEGER DEFAULT 0, -- إضافة العمود الجديد للسماح بالفيديو
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
        """)

        # ترقية جدول المستندات: إضافة عمود is_video_allowed إذا لم يكن موجوداً
        try:
            cur.execute("SELECT is_video_allowed FROM documents LIMIT 1")
        except sqlite3.OperationalError as e:
            if "no such column: is_video_allowed" in str(e):
                cur.execute("ALTER TABLE documents ADD COLUMN is_video_allowed INTEGER DEFAULT 0")
                conn.commit()
                print("تمت إضافة عمود 'is_video_allowed' إلى جدول 'documents'.")
            else:
                raise e

        # جدول أنواع المستندات (لإدارة أسماء المستندات وتفاصيلها)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL, -- الاسم الأصلي
                display_name TEXT NOT NULL, -- الاسم المعروض
                description TEXT, -- وصف اختياري
                is_video_allowed INTEGER DEFAULT 0 -- هل يسمح برفع فيديو لهذا النوع؟
            )
        """)

        # جدول إعدادات المستندات الاختيارية للatypes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS optional_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_type TEXT NOT NULL, -- 'حكومي' أو 'خاص'
                doc_type_name TEXT NOT NULL, -- الاسم الأصلي للمستند
                FOREIGN KEY (doc_type_name) REFERENCES document_types(name)
            )
        """)

        # === تحديث مهم: جدول لربط أنواع المستشفيات بالمستندات الاختيارية ===
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hospital_type_optional_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_type TEXT NOT NULL,
                doc_name TEXT NOT NULL,
                UNIQUE(hospital_type, doc_name)
            )
        """)
        # ================================================================

        # جدول الميتا (لتخزين الإعدادات المتغيرة)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                `key` TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # جدول حالات الطلبات القابلة للتخصيص
        cur.execute("""
            CREATE TABLE IF NOT EXISTS request_statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # جدول إعدادات الحالات (لتحديد السلوك)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS status_settings (
                status_name TEXT PRIMARY KEY,
                prevents_new_request INTEGER DEFAULT 0, -- يمنع تقديم طلب جديد لنفس الخدمة
                blocks_service_for_days INTEGER DEFAULT 0, -- يمنع تقديم طلب لنفس الخدمة لمدة X أيام
                is_final_state INTEGER DEFAULT 0, -- حالة نهائية (تغلق الطلب)
                FOREIGN KEY (status_name) REFERENCES request_statuses(name)
            )
        """)

        conn.commit()

        # --- التهيئة الأولية للبيانات (seeding/updating) ---
        # seed default admin
        cur.execute("SELECT COUNT(1) c FROM admins")
        if cur.fetchone()["c"] == 0:
            cur.execute("INSERT OR IGNORE INTO admins (username, password_hash, role) VALUES (?,?,?)",
                       ("admin", hash_pw("admin123"), "admin"))
            conn.commit()

        # seed services
        cur.execute("SELECT COUNT(1) c FROM services")
        if cur.fetchone()["c"] == 0:
            cur.executemany("INSERT OR IGNORE INTO services (name, active) VALUES (?,1)", [(s,) for s in DEFAULT_SERVICES])
            conn.commit()

        # seed hospital types
        cur.execute("SELECT value FROM meta WHERE `key`='hospital_types'")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO meta (`key`, value) VALUES ('hospital_types', ?)", (",".join(DEFAULT_HOSPITAL_TYPES),))
            conn.commit()

        # seed sectors
        cur.execute("SELECT value FROM meta WHERE `key`='sectors'")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO meta (`key`, value) VALUES ('sectors', ?)", (",".join(DEFAULT_SECTORS),))
            conn.commit()

        # seed governorates
        cur.execute("SELECT value FROM meta WHERE `key`='governorates'")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO meta (`key`, value) VALUES ('governorates', ?)", (",".join(DEFAULT_GOVERNORATES),))
            conn.commit()

        # seed default request statuses if not exists
        cur.execute("SELECT COUNT(1) c FROM request_statuses")
        if cur.fetchone()["c"] == 0:
            for status in DEFAULT_REQUEST_STATUSES:
                 cur.execute("INSERT OR IGNORE INTO request_statuses (name) VALUES (?)", (status,))
            conn.commit()

        # seed default status settings if not exists
        cur.execute("SELECT COUNT(1) c FROM status_settings")
        if cur.fetchone()["c"] == 0:
            # الحالات التي تمنع تقديم طلب جديد (مفتوحة)
            open_statuses = {"جاري دراسة الطلب ومراجعة الأوراق", "جارِ المعاينة", "يجب استيفاء متطلبات التعاقد", "قيد الانتظار", "مقبول", "إعادة تقديم"}
            # الحالات التي تمنع التقديم لمدة 3 أشهر
            blocked_statuses = {"مرفوض", "إرجاء التعاقد"}
            # الحالات النهائية
            final_statuses = {"مقبول", "مرفوض", "مغلق", "إرجاء التعاقد", "لا يوجد حاجة للتعاقد"}

            for status in DEFAULT_REQUEST_STATUSES:
                prevents_new = 1 if status in open_statuses else 0
                blocks_days = 90 if status in blocked_statuses else 0
                is_final = 1 if status in final_statuses else 0
                cur.execute("""
                    INSERT OR IGNORE INTO status_settings (status_name, prevents_new_request, blocks_service_for_days, is_final_state)
                    VALUES (?, ?, ?, ?)
                """, (status, prevents_new, blocks_days, is_final))
            conn.commit()

        # seed default document types if not exists
        cur.execute("SELECT COUNT(1) c FROM document_types")
        if cur.fetchone()["c"] == 0:
            video_allowed_docs = {"فيديو لغرف العمليات والإقامة"}
            for doc in DOC_TYPES:
                display_name = doc
                is_video = 1 if doc in video_allowed_docs else 0
                cur.execute("""
                    INSERT OR IGNORE INTO document_types (name, display_name, is_video_allowed)
                    VALUES (?, ?, ?)
                """, (doc, display_name, is_video))
            conn.commit()

        # === تحديث مهم: seed/update default optional docs for hospital types ===
        # الآن نقوم بتحديث أو إدخال المستندات الاختيارية لأنواع المستشفيات بناءً على الثوابت
        # 1. تحديث المستندات الاختيارية للمستشفيات الحكومية
        cur.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", ("حكومي",))
        for doc_name in GOVERNMENT_OPTIONAL_DOCS:
             if doc_name: # تجنب إدخال أسماء فارغة
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("حكومي", doc_name))
        conn.commit()
        
        # 2. تحديث المستندات الاختيارية للمستشفيات الخاصة
        cur.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", ("خاص",))
        for doc_name in PRIVATE_OPTIONAL_DOCS:
             if doc_name: # تجنب إدخال أسماء فارغة
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("خاص", doc_name))
        conn.commit()
        # =====================================================================

        # seed default optional docs if not exists (للحظات الانتقال)
        cur.execute("SELECT COUNT(1) c FROM optional_docs")
        if cur.fetchone()["c"] == 0:
            for doc in GOVERNMENT_OPTIONAL_DOCS:
                cur.execute("INSERT OR IGNORE INTO optional_docs (hospital_type, doc_type_name) VALUES (?, ?)", ("حكومي", doc))
            # يمكن إضافة مستندات اختيارية للخاص هنا إذا لزم الأمر
            for doc in PRIVATE_OPTIONAL_DOCS:
                cur.execute("INSERT OR IGNORE INTO optional_docs (hospital_type, doc_type_name) VALUES (?, ?)", ("خاص", doc))
            conn.commit()

        # === تحديث مهم: تهيئة القيم الافتراضية للمستندات الاختيارية ===
        # نتحقق مما إذا كانت هناك قيم موجودة بالفعل لتجنب الإدخال المكرر
        cur.execute("SELECT COUNT(*) AS count FROM hospital_type_optional_docs")
        if cur.fetchone()['count'] == 0:
            # إدخال المستندات الاختيارية الافتراضية للمستشفيات الحكومية
            for doc_name in GOVERNMENT_OPTIONAL_DOCS:
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("حكومي", doc_name))
            # إدخال المستندات الاختيارية الافتراضية للمستشفيات الخاصة
            for doc_name in PRIVATE_OPTIONAL_DOCS:
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("خاص", doc_name))
        conn.commit()
        # ===============================================================

    # الاتصال يُغلق تلقائيًا عند الخروج من `with`
# ---------------------------- صفحات المستشفى ---------------------------- #
def hospital_home():
    user = st.session_state.user
    # البحث عن الشعار للشريط الجانبي (يدعم PNG و JPG)
    logo_path_sidebar_png = Path("static/logo.png")
    logo_path_sidebar_jpg = Path("static/logo.jpg")
    logo_path_sidebar = None
    if logo_path_sidebar_png.exists():
        logo_path_sidebar = logo_path_sidebar_png
    elif logo_path_sidebar_jpg.exists():
        logo_path_sidebar = logo_path_sidebar_jpg

    if logo_path_sidebar:
        st.sidebar.image(str(logo_path_sidebar), width=80)
    st.markdown(f"<div class='header'><h2>مرحباً {user['hospital_name']}</h2></div>", unsafe_allow_html=True)
    st.caption(f"نوع المستشفى: {user['hospital_type']}")
    menu = st.sidebar.radio("القائمة", [
        "🏠 الصفحة الرئيسية",
        "📝 تقديم طلب جديد",
        "📂 طلباتي",
        "📥 ملفات متوفرة للتنزيل",
        "🔑 تغيير كلمة المرور",
        "🚪 تسجيل الخروج",
    ])
    if menu == "🏠 الصفحة الرئيسية":
        hospital_dashboard_ui(user)
    elif menu == "📝 تقديم طلب جديد":
        hospital_new_request_ui(user)
    elif menu == "📂 طلباتي":
        hospital_requests_ui(user)
    elif menu == "📥 ملفات متوفرة للتنزيل":
        resources_download_ui()
    elif menu == "🔑 تغيير كلمة المرور":
        change_password_ui(role="hospital", hospital_id=user["hospital_id"])
    elif menu == "🚪 تسجيل الخروج":
        st.session_state.pop("user", None)
        st.rerun()

def hospital_dashboard_ui(user: dict):
    st.markdown("<div class='subheader'>ملف المستشفى</div>", unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals WHERE id=?", (user["hospital_id"],))
    hospital = cur.fetchone()
    conn.close()
    if hospital:
        with st.form("edit_hospital_profile"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("**اسم المستشفى**", value=hospital['name'], disabled=True)
                sector = st.text_input("**القطاع**", value=hospital['sector'] or "", disabled=True)
                governorate = st.text_input("**المحافظة**", value=hospital['governorate'] or "", disabled=True)
                st.text_input("**كود المستشفى**", value=hospital['code'], disabled=True)
                htype = st.text_input("**نوع المستشفى**", value=hospital['type'] or "", disabled=True)
            with col2:
                license_start = st.date_input("**بداية الترخيص**",
                                            value=pd.to_datetime(hospital['license_start']).date() if hospital['license_start'] else None)
                license_end = st.date_input("**نهاية الترخيص",
                                          value=pd.to_datetime(hospital['license_end']).date() if hospital['license_end'] else None)
                license_number = st.text_input("**رقم الترخيص**", value=hospital['license_number'] or "")
                manager_name = st.text_input("**مدير المستشفى**", value=hospital['manager_name'] or "")
                manager_phone = st.text_input("**هاتف المدير**", value=hospital['manager_phone'] or "")
            address = st.text_area("**عنوان المستشفى**", value=hospital['address'] or "", height=100)
            other_branches = st.text_input("الفروع الأخرى", value=hospital['other_branches'] or "")
            other_branches_address = st.text_area("عناوين الفروع الأخرى", value=hospital['other_branches_address'] or "", height=100)
            submitted = st.form_submit_button("حفظ البيانات")
            if submitted:
                try:
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE hospitals SET address=?,
                        other_branches=?, other_branches_address=?, license_start=?,
                        license_end=?, manager_name=?, manager_phone=?, license_number=?
                        WHERE id=?
                    """, (
                        address, other_branches, other_branches_address,
                        str(license_start) if license_start else None,
                        str(license_end) if license_end else None,
                        manager_name, manager_phone, license_number, user["hospital_id"]
                    ))
                    conn.commit()
                    conn.close()
                    st.success("تم حفظ البيانات بنجاح")
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ: {str(e)}")

def hospital_new_request_ui(user: dict):
    if not is_hospital_profile_complete(user["hospital_id"]):
        st.warning("⚠️ يجب إكمال بيانات المستشفى الأساسية أولاً (بداية الترخيص، نهاية الترخيص، رقم الترخيص، مدير المستشفى، هاتف المدير، عنوان المستشفى)")
        hospital_dashboard_ui(user)
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM services WHERE active=1 ORDER BY name")
    services = cur.fetchall()
    conn.close()

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

        if hospital_has_open_request(user["hospital_id"], service_id):
            st.error("لا يمكن إنشاء طلب جديد لنفس الخدمة قبل إغلاق الطلب الحالي من قبل الإدارة.")
            return

        if hospital_blocked_from_request(user["hospital_id"], service_id):
            st.error("لا يمكن تقديم طلب لنفس الخدمة لمدة 3 أشهر من تاريخ رفض الطلب أو إرجاء التعاقد.")
            return

        conn = get_conn()
        cur = conn.cursor()
        # إنشاء طلب بحالة "طلب غير مكتمل" افتراضيًا
        cur.execute("""
            INSERT INTO requests (hospital_id, service_id, age_category, status, created_at)
            VALUES (?,?,?,?,?)
        """, (user["hospital_id"], service_id, age_category, "طلب غير مكتمل", datetime.now().isoformat()))
        req_id = cur.lastrowid
        conn.commit()
        conn.close()

        ensure_request_docs(req_id, user["hospital_type"])
        st.success("تم إنشاء الطلب. يمكنك الآن رفع المستندات.")
        st.session_state["active_request_id"] = req_id
        st.rerun() # إعادة التحميل لعرض واجهة رفع المستندات

    req_id = st.session_state.get("active_request_id")
    if req_id:
        documents_upload_ui(req_id, user)

# ... (الجزء الأول من الدالة كما هو) ...

# استبدل الدالة القديمة في ملفك بـ:

@st.cache_data(ttl=180, show_spinner=False)
def _get_documents_cached(request_id):
    """جلب المستندات مع التخزين المؤقت"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    # التحويل إلى قائمة من القواميس لجعلها قابلة للتسلسل
    docs = [dict(row) for row in cur.fetchall()] 
    conn.close()
    return docs # الآن docs قائمة من القواميس، وهي قابلة للتسلسل

# ... (imports and other functions) ...

# في ملف waiting_list_contracts_app.py

def documents_upload_ui(request_id: int, user: dict, is_active_edit: bool = False):
    """واجهة رفع المستندات المطلوبة مع التحقق من رفع المستندات الإلزامية فقط."""
    st.markdown("<div class='subheader'>رفع المستندات المطلوبة</div>", unsafe_allow_html=True)
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    docs = cur.fetchall()
    conn.close()

    # ***تحديث مهم: متغير لتتبع ما إذا تم رفع كل المستندات المطلوبة فقط***
    # الآن يعتمد على القيمة الفعلية من قاعدة البيانات وليس على حالة مخزنة في الجلسة
    all_required_uploaded = True 
    
    for doc in docs:
        cols = st.columns([3, 3, 2, 2, 2])
        with cols[0]:
            st.write(f"**{doc['display_name'] or doc['doc_type']}**")
            # ***تحديث هنا: عرض الحالة الحالية من قاعدة البيانات***
            if doc['required']:
                 st.caption("مطلوب")
            else:
                 st.caption("اختياري")
        with cols[1]:
            # تحديد أنواع الملفات المسموحة بناءً على إعدادات المستند
            allowed_types = ['pdf']
            # التحقق من وجود العمود 'is_video_allowed' وقيمته بشكل آمن
            is_video_allowed_flag = doc['is_video_allowed'] if 'is_video_allowed' in doc.keys() else 0
            
            # ***تحديث مهم: التحقق مما إذا كان المستند مخصصًا فقط للفيديو***
            video_only = is_video_only_document(doc['doc_type'])
            
            if video_only:
                allowed_types = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
                st.caption("أنواع الملفات المسموحة: فيديو فقط (MP4, AVI, MOV, WMV, FLV, WEBM)")
            elif is_video_allowed_flag:
                allowed_types.extend(['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])
                st.caption("أنواع الملفات المسموحة: PDF ومقاطع فيديو (MP4, AVI, MOV, WMV, FLV, WEBM)")
            else:
                allowed_types = ['pdf']
                st.caption("أنواع الملفات المسموحة: PDF فقط")

            uploaded = st.file_uploader("رفع ملف", type=allowed_types, key=f"up_{doc['id']}")

            if uploaded is not None:
                # ***تحديث مهم: التحقق من نوع الملف المرفوع***
                if video_only:
                    if not check_file_type(uploaded.name, True): # يجب أن يكون فيديو
                        st.error("الرجاء رفع ملف فيديو فقط (MP4, AVI, MOV, WMV, FLV, WEBM)")
                    else:
                        save_uploaded_file(uploaded, user, request_id, doc)
                elif is_video_allowed_flag:
                    if not check_file_type(uploaded.name, True): # يمكن أن يكون PDF أو فيديو
                        st.error(f"الرجاء رفع ملف بصيغة {' أو '.join(allowed_types).upper()}")
                    else:
                        save_uploaded_file(uploaded, user, request_id, doc)
                else:
                    if not uploaded.name.lower().endswith('.pdf'): # يجب أن يكون PDF فقط
                        st.error("الرجاء رفع ملف PDF فقط")
                    else:
                        save_uploaded_file(uploaded, user, request_id, doc)

        with cols[2]:
            # === تحديث مهم: التحقق من وجود الملف قبل محاولة تنزيله ===
            # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
            if doc["file_path"]:
                try:
                    # التحقق من أن الملف موجود فعليًا على القرص
                    if os.path.exists(doc["file_path"]):
                        # إذا كان موجودًا، عرض زر التنزيل
                        with open(doc["file_path"], "rb") as f:
                            st.download_button("تنزيل", data=f.read(), file_name=os.path.basename(doc["file_path"]), key=f"dl_{doc['id']}")
                    else:
                        # إذا لم يكن موجودًا، عرض رسالة للمستخدم
                        st.warning("⚠️ الملف غير متوفر على القرص. يرجى رفع ملف جديد.")
                        # ***تحديث مهم: مسح مسار الملف من قاعدة البيانات***
                        # لأن الملف غير موجود فعليًا، من الأفضل مسح المسار المخزن في قاعدة البيانات
                        # لتجنب محاولة الوصول إليه مرة أخرى في المستقبل
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (doc["id"],))
                        conn.commit()
                        conn.close()
                        # إعادة تحميل الصفحة لتحديث العرض
                        st.rerun()
                except Exception as e:
                    # في حالة حدوث أي خطأ آخر أثناء محاولة الوصول إلى الملف
                    st.error(f"❌ خطأ في الوصول إلى الملف: {e}")
                    # مسح المسار المخزن في قاعدة البيانات
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (doc["id"],))
                    conn.commit()
                    conn.close()
                    # إعادة تحميل الصفحة لتحديث العرض
                    st.rerun()
            # =========================================================
        with cols[3]:
            if doc["file_path"]:
                if st.button("حذف", key=f"del_{doc['id']}"):
                    try:
                        os.remove(doc["file_path"]) if os.path.exists(doc["file_path"]) else None
                    except Exception:
                        pass
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (doc["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
        with cols[4]:
            st.write("✅ مستوفى" if doc["satisfied"] else "❌ غير مستوفى")
            
            # ***تحديث مهم: التحقق من المستندات المطلوبة فقط***
            # فقط المستندات المطلوبة (required = 1) تؤثر على تمكين زر الحفظ
            # هذه القيمة تأتي الآن من قاعدة البيانات بعد التحديث بواسطة الأدمن
            if doc["required"] and not doc["file_path"]:
                all_required_uploaded = False # إذا كان مستند مطلوب غير مرفوع، قم بتعيين العلامة على False

    # ***تحديث مهم: عرض زر الحفظ فقط إذا كان في وضع التحرير النشط***
    if is_active_edit:
        # زر حفظ الطلب يصبح نشطًا فقط بعد رفع كل المستندات المطلوبة (التي required = 1)
        # المستندات الاختيارية (required = 0) لم تعد تمنع الحفظ
        if st.button("حفظ الطلب", disabled=not all_required_uploaded):
            # التحقق من المستندات المطلوبة لا يزال ضروريًا للحماية
            if not all_required_uploaded: 
                 st.error("لا يمكن حفظ الطلب: هناك مستندات مطلوبة لم يتم رفعها.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                # تحديث حالة الطلب إلى الحالة الافتراضية الأولى بعد الإنشاء
                # ***تحديث مهم: استخدام get_request_statuses() للحصول على القائمة الحالية***
                statuses = get_request_statuses()
                initial_status = statuses[0] if statuses else "جاري دراسة الطلب ومراجعة الأوراق"
                # تحديث الحالة و updated_at
                cur.execute("UPDATE requests SET status=?, updated_at=? WHERE id=?", (initial_status, datetime.now().isoformat(), request_id))
                conn.commit()
                conn.close()
                st.success("تم حفظ الطلب بنجاح. سيتم مراجعته من قبل الإدارة.")
                st.session_state.pop("active_request_id", None)
                # ***تحديث مهم: تنظيف علامة التحرير النشط***
                if f"editing_request_{request_id}" in st.session_state:
                    st.session_state.pop(f"editing_request_{request_id}", None)
                st.rerun() # إعادة التحميل لتحديث الواجهة
        elif not all_required_uploaded:
            # عرض رسالة فقط إذا كانت هناك مستندات مطلوبة ناقصة
            st.info("يرجى رفع جميع المستندات المطلوبة لتفعيل زر 'حفظ الطلب'.")
    # else:
    #     # إذا لم يكن في وضع التحرير النشط، لا تظهر زر الحفظ
    #     pass

# ... (دالة save_uploaded_file كما هي) ...


def save_uploaded_file(file, user: dict, request_id: int, doc_row):
    """حفظ ملف مرفوع من قبل المستخدم."""
    hospital_name = user["hospital_name"]
    # ***تحديث مهم: قصر أسماء الملفات لتجنب مشاكل المسار***
    dest_dir = STORAGE_DIR / safe_filename(hospital_name)[:50] / str(request_id) # قصر اسم المستشفى
    dest_dir.mkdir(parents=True, exist_ok=True)
    # ***تحديث مهم: الحفاظ على امتداد الملف الأصلي***
    fn = f"{safe_filename(doc_row['doc_type'])[:50]}{Path(file.name).suffix}" # قصر اسم نوع المستند واحتفاظ بالامتداد
    dest_path = dest_dir / fn
    try:
        with open(dest_path, "wb") as f:
            f.write(file.getbuffer())
        conn = get_conn()
        cur = conn.cursor()
        # تحديث updated_at في جدول documents
        cur.execute("""
            UPDATE documents
            SET file_name=?, file_path=?, uploaded_at=?
            WHERE id=?
        """, (fn, str(dest_path), datetime.now().isoformat(), doc_row["id"]))
        # تحديث updated_at في جدول requests أيضًا
        cur.execute("UPDATE requests SET updated_at=? WHERE id=?", (datetime.now().isoformat(), request_id))
        conn.commit()
        conn.close()
        st.success(f"تم رفع الملف: {fn}")
    except OSError as e:
        st.error(f"❌ فشل رفع الملف '{fn}': {e}")
        # محاولة حذف الملف الجزئي إن وجد
        if dest_path.exists():
            try:
                dest_path.unlink()
            except:
                pass


        
def save_uploaded_file(file, user: dict, request_id: int, doc_row):
    hospital_name = user["hospital_name"]
    dest_dir = STORAGE_DIR / safe_filename(hospital_name) / str(request_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    fn = f"{safe_filename(doc_row['doc_type'])}{Path(file.name).suffix}" # الحفاظ على امتداد الملف الأصلي
    dest_path = dest_dir / fn
    with open(dest_path, "wb") as f:
        f.write(file.getbuffer())
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE documents
        SET file_name=?, file_path=?, uploaded_at=?
        WHERE id=?
    """, (fn, str(dest_path), datetime.now().isoformat(), doc_row["id"]))
    conn.commit()
    conn.close()
    st.success(f"تم رفع الملف: {fn}")

def hospital_requests_ui(user: dict):
    st.markdown("<div class='subheader'>طلباتي</div>", unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    # عرض الطلبات بما في ذلك "طلب غير مكتمل"
    cur.execute("""
        SELECT r.id, s.name AS service_name, r.age_category, r.status, r.created_at, r.deleted_at
        FROM requests r
        JOIN services s ON s.id=r.service_id
        WHERE r.hospital_id=?
        ORDER BY r.created_at DESC
    """, (user["hospital_id"],))
    rows = cur.fetchall()
    conn.close()
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)
    if rows:
        req_ids = [r["id"] for r in rows]
        pick = st.selectbox("اختر طلبًا لإدارته", ["—"] + [str(i) for i in req_ids])
        if pick != "—":
            request_details_ui(int(pick), role="hospital")

# ... (الجزء العلوي من الدالة كما هو: استيراد البيانات وعرض معلومات الطلب) ...

# في ملف waiting_list_contracts_app.py

# في ملف waiting_list_contracts_app.py

def request_details_ui(request_id: int, role: str = "hospital"):
    """واجهة تفاصيل الطلب للمستخدم (المستشفى) مع التحكم في عرض زر الحفظ."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
               h.type AS hospital_type, s.name AS service_name
        FROM requests r
        JOIN hospitals h ON h.id=r.hospital_id
        JOIN services s ON s.id=r.service_id
        WHERE r.id=?
    """, (request_id,))
    r = cur.fetchone()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    docs = cur.fetchall()
    conn.close()

    if not r:
        st.error("الطلب غير موجود.")
        return

    st.markdown(f"<div class='subheader'>تفاصيل الطلب #{request_id}</div>", unsafe_allow_html=True)
    st.write(f"**المستشفى:** {r['hospital_name']} — ({r['hospital_code']}) — **النوع:** {r['hospital_type']} — **الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']}")

    # === إضافة عرض تواريخ الطلب ===
    try:
        # التأكد من أن created_at و updated_at كائنات datetime
        created_at_dt = r['created_at']
        if isinstance(created_at_dt, str):
            created_at_dt = datetime.fromisoformat(created_at_dt)
            
        info_text = f"**تاريخ التقديم:** {created_at_dt.strftime('%Y-%m-%d %H:%M:%S')}"

        if r['updated_at']:
            updated_at_dt = r['updated_at']
            # التأكد من أنه كائن datetime
            if isinstance(updated_at_dt, str):
                updated_at_dt = datetime.fromisoformat(updated_at_dt)
                
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

    # السماح بالتعديل/الحذف فقط إذا كانت الحالة "طلب غير مكتمل" أو حالات محددة أخرى
    can_edit = r['status'] in ["طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "يجب استيفاء متطلبات التعاقد"]

    if can_edit and role == "hospital":
        st.info("يمكنك تعديل أو حذف هذا الطلب لأن حالته 'طلب غير مكتمل' أو 'جارى دراسة الطلب ومراجعة الأوراق' أو 'يجب استيفاء متطلبات التعاقد'")
        col_del_edit, col_save_cancel = st.columns([1, 1])
        with col_del_edit:
            if st.button("🗑️ حذف الطلب"):
                for d in docs:
                    if d['file_path'] and os.path.exists(d['file_path']):
                        try:
                            os.remove(d['file_path'])
                        except Exception:
                            pass
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("DELETE FROM documents WHERE request_id=?", (request_id,))
                cur.execute("DELETE FROM requests WHERE id=?", (request_id,))
                conn.commit()
                conn.close()
                st.success("تم حذف الطلب بنجاح")
                # تنظيف متغيرات الجلسة
                st.session_state.pop("active_request_id", None)
                if f"editing_request_{request_id}" in st.session_state:
                    st.session_state.pop(f"editing_request_{request_id}", None)
                st.rerun()
            if st.button("✏️ تعديل الطلب"):
                # ***تحديث مهم: تعيين علامة التحرير النشط***
                st.session_state[f"editing_request_{request_id}"] = True
                st.session_state["active_request_id"] = request_id
                st.rerun()
        
        # ***تحديث مهم: التحقق مما إذا كان المستخدم في وضع التحرير النشط***
        is_currently_editing = st.session_state.get(f"editing_request_{request_id}", False)
        
        # عرض واجهة رفع المستندات فقط إذا كان في وضع التحرير النشط
        if st.session_state.get("active_request_id") == request_id and is_currently_editing:
            # ***تحديث مهم: استدعاء documents_upload_ui مع تمرير علم is_active_edit=True***
            documents_upload_ui(request_id, st.session_state.user, is_active_edit=True)
        elif st.session_state.get("active_request_id") == request_id and not is_currently_editing:
            # إذا كان الطلب نشطًا ولكن ليس في وضع التحرير، أظهر رسالة
            st.info("لقد دخلت إلى واجهة تحرير الطلب. يرجى رفع المستندات المطلوبة ثم النقر على 'حفظ الطلب'.")
            # عرض واجهة رفع المستندات بدون زر الحفظ النشط
            documents_upload_ui(request_id, st.session_state.user, is_active_edit=False)
    else:
        st.markdown("##### المستندات")
        for d in docs:
            c1, c2, c3, c4, c5 = st.columns([3,2,2,2,3])
            with c1:
                display_name = d['display_name'] or d['doc_type']
                st.write(display_name)
                st.caption("مطلوب" if d['required'] else "اختياري")
            with c2:
                # === تحديث مهم: التحقق من وجود الملف قبل محاولة تنزيله ===
                # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
                if d["file_path"]:
                    try:
                        # التحقق من أن الملف موجود فعليًا على القرص
                        if os.path.exists(d["file_path"]):
                            # إذا كان موجودًا، عرض زر التنزيل
                            with open(d["file_path"], "rb") as f:
                                st.download_button("تنزيل", data=f.read(), file_name=os.path.basename(d["file_path"]), key=f"dl_req_{d['id']}")
                        else:
                            # إذا لم يكن موجودًا، عرض رسالة للمستخدم
                            st.warning("⚠️ الملف غير متوفر على القرص.")
                            # ***تحديث مهم: مسح مسار الملف من قاعدة البيانات***
                            # لأن الملف غير موجود فعليًا، من الأفضل مسح المسار المخزن في قاعدة البيانات
                            # لتجنب محاولة الوصول إليه مرة أخرى في المستقبل
                            conn = get_conn()
                            cur = conn.cursor()
                            cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                            conn.commit()
                            conn.close()
                            # إعادة تحميل الصفحة لتحديث العرض
                            st.rerun()
                    except Exception as e:
                        # في حالة حدوث أي خطأ آخر أثناء محاولة الوصول إلى الملف
                        st.error(f"❌ خطأ في الوصول إلى الملف: {e}")
                        # مسح المسار المخزن في قاعدة البيانات
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                        conn.commit()
                        conn.close()
                        # إعادة تحميل الصفحة لتحديث العرض
                        st.rerun()
                # =========================================================
            with c3:
                st.write("✅ مستوفى" if d["satisfied"] else "❌ غير مستوفى")
            with c4:
                # === تحديث مهم: التحقق من تواريخ المستندات ===
                try:
                    uploaded_at_dt = d['uploaded_at']
                    if isinstance(uploaded_at_dt, str):
                        uploaded_at_dt = datetime.fromisoformat(uploaded_at_dt)
                    st.write(uploaded_at_dt.strftime('%Y-%m-%d %H:%M:%S') if uploaded_at_dt else "—")
                except Exception:
                    st.write(d['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S') if d['uploaded_at'] else "—")
                # =========================================================
            with c5:
                st.write(d['admin_comment'] or "")

    # ... (إجراءات الطلب: حذف نهائي، استرجاع، إغلاق) ...





def resources_download_ui():
    st.markdown("<div class='subheader'>ملفات متوفرة للتنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك تنزيل الملفات التالية لمساعدتك في عملية التقديم</div>", unsafe_allow_html=True)
    RESOURCES_DIR.mkdir(exist_ok=True)
    for filename in RESOURCE_FILES:
        filepath = RESOURCES_DIR / filename
        if filepath.exists():
            with open(filepath, "rb") as f:
                st.download_button(
                    label=f"📥 {filename}",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
        else:
            st.warning(f"الملف غير متوفر: {filename}")

# ... (تستمر في القسم التالي)
# ... (متابعة من القسم 4)

@st.cache_data(ttl=300, show_spinner=False)
def get_requests_data(hospital_id=None, filters=None):
    """جلب بيانات الطلبات مع التخزين المؤقت"""
    conn = get_conn()
    cur = conn.cursor()
    
    if hospital_id:  # للطلبات الخاصة بالمستشفى
        cur.execute("""
            SELECT r.id, s.name AS service_name, r.age_category, r.status, r.created_at, r.deleted_at
            FROM requests r
            JOIN services s ON s.id=r.service_id
            WHERE r.hospital_id=?
            ORDER BY r.created_at DESC
            LIMIT 100
        """, (hospital_id,))
    else:  # لجميع الطلبات (للأدمن)
        q = """SELECT r.id, h.name AS hospital, h.code AS code, h.type AS hospital_type,
                      s.name AS service, r.age_category, r.status, r.created_at, r.deleted_at
               FROM requests r
               JOIN hospitals h ON h.id=r.hospital_id
               JOIN services s ON s.id=r.service_id
               WHERE 1=1"""
        params = []
        
        if filters:
            if filters.get('show_deleted') == False:
                q += " AND r.deleted_at IS NULL"
            if filters.get('status') and filters['status'] != "الكل":
                q += " AND r.status=?"
                params.append(filters['status'])
        
        q += " ORDER BY r.created_at DESC LIMIT 200"
        cur.execute(q, tuple(params))
    
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
@st.cache_data(ttl=600, show_spinner=False)
def get_statistics_data(filters=None):
    """جلب بيانات الإحصائيات مع التخزين المؤقت"""
    conn = get_conn()
    cur = conn.cursor()
    
    where_conditions = ["r.deleted_at IS NULL"]
    params = []
    
    if filters:
        if filters.get('sector') and filters['sector'] != "الكل":
            where_conditions.append("h.sector = ?")
            params.append(filters['sector'])
    
    where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
    
    query_status = f"""
        SELECT r.status, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        WHERE {where_clause}
        GROUP BY r.status
        ORDER BY count DESC
        LIMIT 20
    """
    
    cur.execute(query_status, params)
    status_stats = cur.fetchall()
    
    conn.close()
    return {
        'status_stats': [dict(row) for row in status_stats],
    }
def admin_home():
    user = st.session_state.user
    logo_path_sidebar_admin = Path("static/logo.png")
    if logo_path_sidebar_admin.exists():
        st.sidebar.image(str(logo_path_sidebar_admin), width=80)
    st.markdown("<div class='header'><h2>لوحة التحكم - الأدمن/المراجع</h2></div>", unsafe_allow_html=True)
    if user["role"] == "admin":
        menu = st.sidebar.radio("القائمة", [
            "🏥 إدارة المستشفيات",
            "🧾 إدارة الطلبات",
            "📊 الإحصائيات",
            "🗂️ الطلبات المحذوفة",
            "🧩 إدارة الخدمات والأنواع",
            "👥 إدارة المستخدمين",
            "📥 ملفات متوفرة للتنزيل",
            "🚪 تسجيل الخروج",
        ])
    else: # reviewer
        menu = st.sidebar.radio("القائمة", [
            "🧾 مراجعة الطلبات",
            "📊 الإحصائيات",
            "🗂️ الطلبات المحذوفة",
            "📥 ملفات متوفرة للتنزيل",
            "🚪 تسجيل الخروج",
        ])
    if menu == "🏥 إدارة المستشفيات":
        admin_hospitals_ui()
    elif menu == "🧾 إدارة الطلبات" or menu == "🧾 مراجعة الطلبات":
        admin_requests_ui()
    elif menu == "📊 الإحصائيات":
        admin_statistics_ui()
    elif menu == "🗂️ الطلبات المحذوفة":
        admin_deleted_ui()
    elif menu == "🧩 إدارة الخدمات والأنواع":
        admin_lists_ui()
    elif menu == "👥 إدارة المستخدمين":
        admin_users_ui()
    elif menu == "📥 ملفات متوفرة للتنزيل":
        admin_resources_ui()
    elif menu == "🚪 تسجيل الخروج":
        st.session_state.pop("user", None)
        st.rerun()

def admin_hospitals_ui():
    st.markdown("<div class='subheader'>إدارة المستشفيات</div>", unsafe_allow_html=True)
    # استيراد من Excel
    st.markdown("#### 🔽 استيراد من ملف Excel")
    excel = st.file_uploader("اختر ملف Excel Sheet يحتوي: اسم المستشفى، القطاع، المحافظة، الكود، النوع", type=["xlsx", "xls"])
    if excel is not None:
        try:
            df = pd.read_excel(excel, sheet_name=0) # 0 تعني الورقة الأولى
            required_cols = ["اسم المستشفى", "القطاع", "المحافظه", "كود المستشفى"]
            for c in required_cols:
                if c not in df.columns:
                    st.error(f"العمود المطلوب مفقود: {c}")
                    return
            if "نوع المستشفى" not in df.columns:
                df["نوع المستشفى"] = "خاص"
            # توليد أسماء مستخدمين وكلمات مرور
            df["username"] = df["اسم المستشفى"].apply(generate_username)
            df["password"] = "1234"  # كلمة مرور افتراضية
            conn = get_conn()
            cur = conn.cursor()
            added, skipped = 0, 0
            for _, row in df.iterrows():
                try:
                    username = row["username"]
                    # تأكد من تفرّد اسم المستخدم
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
                        hash_pw(str(row["password"]).strip()),
                    ))
                    if cur.rowcount:
                        added += 1
                    else:
                        skipped += 1
                except Exception as e:
                    st.warning(f"تخطي صف: {e}")
            conn.commit()
            conn.close()
            st.success(f"تمت إضافة: {added} — تم التخطي (موجود): {skipped}")
            # تصدير ملف الاعتمادات
            out_path = EXPORTS_DIR / f"credentials_{datetime.now().strftime('%Y%m%d_%H%M?')}.xlsx"
            df.to_excel(out_path, index=False)
            st.download_button("📥 تنزيل ملف الاعتمادات (username/password)", 
                             data=open(out_path, 'rb').read(), 
                             file_name=out_path.name)
        except Exception as e:
            st.error(f"فشل الاستيراد: {e}")
    # إضافة يدوية
    st.markdown("#### ➕ إضافة مستشفى يدويًا")
    with st.expander("إضافة مستشفى جديد"):
        with st.form("add_hospital"):
            name = st.text_input("اسم المستشفى")
            sector = st.text_input("القطاع", help="اختر من القائمة أو أدخل يدويًا")
            gov = st.text_input("المحافظة", help="اختر من القائمة أو أدخل يدويًا")
            code = st.text_input("كود المستشفى")
            htype = st.text_input("نوع المستشفى", help="اختر من القائمة أو أدخل يدويًا")
            username = st.text_input("اسم المستخدم (سيتم توليد تلقائيًا من الاسم إن فارغ)", value="")
            password = st.text_input("كلمة المرور", type="password", value="1234")
            submitted = st.form_submit_button("إضافة")
            if submitted:
                if not all([name, sector, gov, code, password]):
                    st.error("يرجى ملء الحقول المطلوبة")
                else:
                    if not username:
                        username = generate_username(name)
                        # تأكد من التفرّد
                        base_username = username
                        conn = get_conn()
                        counter = 1
                        while conn.execute("SELECT id FROM hospitals WHERE username=?", (username,)).fetchone():
                            username = f"{base_username}{counter}"
                            counter += 1
                        conn.close()
                    try:
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO hospitals (name, sector, governorate, code, type, username, password_hash)
                            VALUES (?,?,?,?,?,?,?)
                        """, (name, sector, gov, code, htype, username, hash_pw(password)))
                        conn.commit()
                        conn.close()
                        st.success(f"تمت الإضافة. اسم المستخدم: {username}")
                    except sqlite3.IntegrityError:
                        st.error("كود المستشفى أو اسم المستخدم موجود مسبقًا")
    # عرض القائمة
    st.markdown("#### 📋 قائمة المستشفيات")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals ORDER BY name")
    hospitals = cur.fetchall()
    conn.close()
    if hospitals:
        df = pd.DataFrame([dict(h) for h in hospitals])
        st.dataframe(
        df[["id", "name", "sector", "governorate", "code", "type", "username"]].style.set_properties(**{
            'background-color': '#f8f9fa',
            'color': 'black',
            'border': '1px solid #dee2e6',
            'font-family': 'Cairo, sans-serif'
        }).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#1e40af'), ('color', 'white'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('padding', '12px')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#e2e8f0')]}
        ]),
        use_container_width=True,
        height=400  # ارتفاع ثابت مع شريط تمرير
    )
        # إنشاء قائمة منسدلة للمستشفيات
        hospital_options = ["—"] + [f"{h['id']} — {h['name']}" for h in hospitals]
        hid = st.selectbox("اختر مستشفى للتعديل", hospital_options)
        if hid != "—":
            hid_int = int(hid.split(" — ")[0])
            
            # إيجاد المستشفى المختار من القائمة المحملة باستخدام المعرف
            selected_hospital_record = None
            for h in hospitals:
                if h['id'] == hid_int:
                    selected_hospital_record = h
                    break
            
            if selected_hospital_record:
                # --- إضافة زر حذف المستشفى ---
                st.markdown("---") # خط فاصل
                st.markdown(f"### إجراءات على المستشفى المحدد: {selected_hospital_record['name']}") # عرض اسم المستشفى الصحيح
                
                # استخدام expander لتجميع خيارات التعديل والحذف
                with st.expander("عرض خيارات التعديل والحذف", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ تعديل بيانات المستشفى", key=f"edit_hospital_{hid_int}"):
                            edit_hospital_ui(hid_int)
                    
                    with col2:
                        # استخدام متغير جلسة لحالة تأكيد الحذف
                        confirm_key = f"confirm_delete_hospital_{hid_int}"
                        if st.button("🗑️ حذف هذا المستشفى", key=f"delete_hospital_button_{hid_int}"):
                            # عند الضغط على زر الحذف، نعرض رسالة تأكيد
                            st.session_state[confirm_key] = True
                            st.warning(f"هل أنت متأكد أنك تريد حذف المستشفى '{selected_hospital_record['name']}' وجميع طلباته؟ هذا الإجراء لا يمكن التراجع عنه.")
                        
                        # التحقق مما إذا كان المستخدم قد أكد الحذف
                        if st.session_state.get(confirm_key, False):
                            # عرض أزرار التأكيد وإلغاء الأمر
                            st.markdown("---")
                            st.markdown("### ⚠️ تأكيد الحذف")
                            confirm_col1, confirm_col2 = st.columns(2)
                            with confirm_col1:
                                if st.button("✅ نعم، قم بالحذف", key=f"confirm_yes_{hid_int}"):
                                    # تنفيذ عملية الحذف
                                    hospital_name = selected_hospital_record['name'] # الحصول على اسم المستشفى للرسالة
                                    try:
                                        conn = get_conn()
                                        cur = conn.cursor()
                                        # 1. حذف الطلبات المرتبطة بالمستشفى أولاً لتجنب مشاكل الـ Foreign Key
                                        cur.execute("DELETE FROM requests WHERE hospital_id = ?", (hid_int,))
                                        # 2. حذف المستشفى نفسه
                                        cur.execute("DELETE FROM hospitals WHERE id = ?", (hid_int,))
                                        conn.commit()
                                        conn.close()
                                        st.success(f"✅ تم حذف المستشفى '{hospital_name}' وجميع طلباته بنجاح.")
                                        # حذف مفتاح التأكيد من الجلسة
                                        if confirm_key in st.session_state:
                                            del st.session_state[confirm_key]
                                        # إعادة تحميل الصفحة لتحديث القائمة
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ حدث خطأ أثناء حذف المستشفى '{hospital_name}': {e}")
                                        if 'conn' in locals():
                                            conn.close()
                            with confirm_col2:
                                if st.button("❌ إلغاء", key=f"confirm_no_{hid_int}"):
                                    # إلغاء عملية الحذف
                                    if confirm_key in st.session_state:
                                        del st.session_state[confirm_key]
                                    st.info("تم إلغاء عملية الحذف.")
                                    # إعادة تحميل الصفحة لإزالة رسالة التحذير
                                    st.rerun()
            else:
                st.error("لم يتم العثور على المستشفى المحدد.")


def edit_hospital_ui(hospital_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals WHERE id=?", (hospital_id,))
    h = cur.fetchone()
    st.markdown(f"<div class='subheader'>تعديل: {h['name']}</div>", unsafe_allow_html=True)
    with st.form("edit_h"):
        name = st.text_input("اسم المستشفى", h["name"])
        sector = st.text_input("القطاع", h["sector"], help="اختر من القائمة أو أدخل يدويًا")
        gov = st.text_input("المحافظة", h["governorate"], help="اختر من القائمة أو أدخل يدويًا")
        code = st.text_input("كود المستشفى", h["code"])
        htype = st.text_input("نوع المستشفى", h["type"], help="اختر من القائمة أو أدخل يدويًا")
        address = st.text_area("العنوان بالكامل", h["address"] or "")
        other_br = st.text_input("الفروع الأخرى", h["other_branches"] or "")
        other_br_addr = st.text_area("عناوين الفروع الأخرى", h["other_branches_address"] or "")
        lic_start = st.date_input("بداية الترخيص", 
                                value=pd.to_datetime(h["license_start"]).date() if h["license_start"] else date.today())
        lic_end = st.date_input("نهاية الترخيص", 
                              value=pd.to_datetime(h["license_end"]).date() if h["license_end"] else date.today())
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
                params = [name, sector, gov, code, htype, address, other_br, other_br_addr, 
                         str(lic_start), str(lic_end), manager, manager_phone, license_no, username]
                if new_pw:
                    q += ", password_hash=?"
                    params.append(hash_pw(new_pw))
                q += " WHERE id=?"
                params.append(hospital_id)
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(q, tuple(params))
                conn.commit()
                conn.close()
                st.success("تم التعديل بنجاح")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("كود المستشفى أو اسم المستخدم مستخدم مسبقًا")

def admin_requests_ui():
    st.markdown("<div class='subheader'>إدارة الطلبات</div>", unsafe_allow_html=True)
    st.markdown("#### تصفية الطلبات")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM services ORDER BY name")
    services = cur.fetchall()
    service_options = ["الكل"] + [s["name"] for s in services]
    cur.execute("SELECT id, name FROM hospitals ORDER BY name")
    hospitals = cur.fetchall()
    hospital_options = ["الكل"] + [h["name"] for h in hospitals]
    
    # 获取所有唯一的部门 (sector) 用于筛选
    cur.execute("SELECT DISTINCT sector FROM hospitals ORDER BY sector")
    sectors = cur.fetchall()
    sector_filter_options = ["الكل"] + [s["sector"] for s in sectors]
    
    conn.close()

    # 创建筛选控件的列布局
    # 增加一列用于部门筛选，另一列用于日期范围
    col1, col2, col3, col4, col5, col6 = st.columns(6) 
    with col1:
        selected_service = st.selectbox("الخدمة", service_options)
    with col2:
        selected_hospital = st.selectbox("المستشفى", hospital_options)
    with col3:
        request_id_input = st.text_input("ID الطلب (رقم)")
    with col4:
        # 新增：按部门筛选
        selected_hospital_sector = st.selectbox("القطاع", sector_filter_options) 
    with col5:
        # 新增：开始日期
        start_date = st.date_input("تاريخ البدء", value=None, format="YYYY/MM/DD")
    with col6:
        # 新增：结束日期
        end_date = st.date_input("تاريخ الانتهاء", value=None, format="YYYY/MM/DD")

    # 现有的状态筛选和显示删除项选项
    # 为了布局清晰，可以将它们放在新的一行
    status_col, deleted_col = st.columns(2)
    with status_col:
        # استبعاد "طلب غير مكتمل" من عرض الطلبات للمراجعة إلا إذا تم طلبها صراحة
        status_options = ["الكل"] + [s for s in get_request_statuses() if s != "طلب غير مكتمل"] + ["طلب غير مكتمل"]
        status = st.selectbox("الحالة", status_options)
    with deleted_col:
        show_deleted = st.checkbox("عرض المحذوفات؟")

    # 构建 SQL 查询语句和参数
    q = """SELECT r.id, h.name AS hospital, h.code AS code, h.type AS hospital_type,
                  s.name AS service, r.age_category, r.status, r.created_at, r.deleted_at
           FROM requests r
           JOIN hospitals h ON h.id=r.hospital_id
           JOIN services s ON s.id=r.service_id
           WHERE 1=1""" # 使用 WHERE 1=1 作为基础，方便动态添加条件
    params = []
    
    # 应用现有筛选条件
    if not show_deleted:
        q += " AND r.deleted_at IS NULL"
    if status != "الكل":
        q += " AND r.status=?"
        params.append(status)
    if selected_service != "الكل":
        q += " AND s.name=?"
        params.append(selected_service)
    if selected_hospital != "الكل":
        q += " AND h.name=?"
        params.append(selected_hospital)
    if request_id_input and request_id_input.isdigit():
        q += " AND r.id=?"
        params.append(int(request_id_input))
        
    # 应用新增的筛选条件
    # 1. 按医院部门筛选
    if selected_hospital_sector != "الكل":
        q += " AND h.sector=?"
        params.append(selected_hospital_sector)
    # 2. 按提交日期范围筛选
    # 注意：数据库中 created_at 是 TEXT 类型，存储 ISO 格式字符串 (e.g., '2023-10-27T10:30:00.123456')
    # 我们可以使用 DATE() 函数提取日期部分进行比较
    if start_date:
        q += " AND DATE(r.created_at) >= ?"
        params.append(start_date.isoformat()) # 转换为 'YYYY-MM-DD' 字符串
    if end_date:
        q += " AND DATE(r.created_at) <= ?"
        params.append(end_date.isoformat()) # 转换为 'YYYY-MM-DD' 字符串

    # 添加排序
    q += " ORDER BY r.created_at DESC"

    # 执行查询
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    # 显示结果
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)
    
    if rows:
        pick = st.selectbox("اختر طلبًا لإدارته", ["—"] + [str(r["id"]) for r in rows])
        if pick != "—":
            admin_request_detail_ui(int(pick))


# ... (الجزء العلوي من الدالة كما هو: استيراد البيانات وعرض معلومات الطلب) ...

# ... (الجزء العلوي من الدالة كما هو: استيراد البيانات وعرض معلومات الطلب) ...

def admin_request_detail_ui(request_id: int):
    """واجهة تفاصيل الطلب للمراجع/الأدمن مع تحديث تاريخ التعديل."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
               h.type AS hospital_type, s.name AS service_name
        FROM requests r
        JOIN hospitals h ON h.id=r.hospital_id
        JOIN services s ON s.id=r.service_id
        WHERE r.id=?
    """, (request_id,))
    r = cur.fetchone()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    docs = cur.fetchall()
    conn.close()

    if not r:
        st.error("الطلب غير موجود.")
        return

    st.markdown(f"<div class='subheader'>إدارة الطلب #{request_id}</div>", unsafe_allow_html=True)
    st.write(f"**المستشفى:** {r['hospital_name']} — ({r['hospital_code']}) — **النوع:** {r['hospital_type']} — **الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']} — **الحالة الحالية:** {r['status']}")

    colA, colB = st.columns([2,3])
    with colA:
        current_statuses = get_request_statuses()
        new_status = st.selectbox("الحالة", current_statuses,
                                index=current_statuses.index(r['status']) if r['status'] in current_statuses else 0)
        note = st.text_area("ملاحظة إدارية", r['admin_note'] or "")
        if st.button("حفظ الحالة"):
            conn = get_conn()
            cur = conn.cursor()
            closed_at = None
            # تحديث updated_at مع كل تغيير
            updated_at = datetime.now().isoformat()
            
            # إذا كانت الحالة الجديدة نهائية، قم بتحديث closed_at
            if is_final_status(new_status):
                closed_at = datetime.now().isoformat()
                cur.execute("UPDATE requests SET status=?, admin_note=?, closed_at=?, updated_at=? WHERE id=?",
                           (new_status, note, closed_at, updated_at, request_id))
            else:
                # إذا تم تغيير الحالة من نهائية إلى غير نهائية، قم بمسح closed_at
                if r['closed_at'] and not is_final_status(new_status):
                     cur.execute("UPDATE requests SET status=?, admin_note=?, closed_at=NULL, updated_at=? WHERE id=?",
                                (new_status, note, updated_at, request_id))
                else:
                     cur.execute("UPDATE requests SET status=?, admin_note=?, updated_at=? WHERE id=?",
                                (new_status, note, updated_at, request_id))
            conn.commit()
            conn.close()
            st.success("تم الحفظ")
            st.rerun()
    with colB:
        if st.button("تنزيل كل الملفات (ZIP)"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for d in docs:
                    # === تحديث مهم: التحقق من وجود الملف قبل محاولة إضافته إلى ZIP ===
                    # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
                    if d['file_path'] and os.path.exists(d['file_path']):
                        try:
                            zf.write(d['file_path'], arcname=f"{safe_filename(d['doc_type'])}{Path(d['file_path']).suffix}")
                        except Exception as e:
                            # في حالة حدوث خطأ، تجاهل الملف وتابع
                            pass
                    # =========================================================
            buf.seek(0)
            st.download_button("📥 تحميل الملفات", data=buf,
                             file_name=f"request_{request_id}_files.zip")

    st.markdown("##### المستندات")
    for d in docs:
        c1, c2, c3, c4, c5, c6 = st.columns([3,2,2,2,3,3])
        with c1:
            display_name = d['display_name'] or d['doc_type']
            st.write(display_name)
            st.caption("مطلوب" if d['required'] else "اختياري")
            # ***تحديث مهم: إضافة checkbox لتعديل required من واجهة الأدمن***
            # هذا يتيح للأدمن تغيير حالة المستند من مطلوب إلى اختياري والعكس
            req_toggle_admin = st.checkbox("مطلوب؟", value=bool(d['required']), key=f"req_admin_{d['id']}")
        with c2:
            sat_toggle = st.checkbox("مستوفى؟", value=bool(d['satisfied']), key=f"sat_{d['id']}")
        with c3:
            # === تحديث مهم: التحقق من وجود الملف قبل محاولة تنزيله ===
            # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
            if d["file_path"]:
                try:
                    # التحقق من أن الملف موجود فعليًا على القرص
                    if os.path.exists(d["file_path"]):
                        # إذا كان موجودًا، عرض زر التنزيل
                        with open(d["file_path"], "rb") as f:
                            st.download_button("تنزيل", data=f.read(), file_name=os.path.basename(d["file_path"]), key=f"dl_admin_{d['id']}")
                    else:
                        # إذا لم يكن موجودًا، عرض رسالة للمستخدم
                        st.warning("⚠️ الملف غير متوفر على القرص.")
                        # ***تحديث مهم: مسح مسار الملف من قاعدة البيانات***
                        # لأن الملف غير موجود فعليًا، من الأفضل مسح المسار المخزن في قاعدة البيانات
                        # لتجنب محاولة الوصول إليه مرة أخرى في المستقبل
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                        conn.commit()
                        conn.close()
                        # إعادة تحميل الصفحة لتحديث العرض
                        st.rerun()
                except Exception as e:
                    # في حالة حدوث أي خطأ آخر أثناء محاولة الوصول إلى الملف
                    st.error(f"❌ خطأ في الوصول إلى الملف: {e}")
                    # مسح المسار المخزن في قاعدة البيانات
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                    conn.commit()
                    conn.close()
                    # إعادة تحميل الصفحة لتحديث العرض
                    st.rerun()
            # =========================================================
        with c4:
            if d["file_path"]:
                if st.button("حذف", key=f"del_{d['id']}"):
                    try:
                        os.remove(d["file_path"]) if os.path.exists(d["file_path"]) else None
                    except Exception:
                        pass
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
        with c5:
            comment = st.text_input("تعليق", value=d['admin_comment'] or "", key=f"cm_{d['id']}")
        with c6:
            if st.button("حفظ", key=f"save_{d['id']}"):
                conn = get_conn()
                cur = conn.cursor()
                # ***تحديث مهم: حفظ القيمة الجديدة لـ required من checkbox ***
                new_required_value = 1 if req_toggle_admin else 0
                cur.execute("""
                    UPDATE documents SET required=?, satisfied=?, admin_comment=? WHERE id=?
                """, (new_required_value, 1 if sat_toggle else 0, comment, d['id']))
                conn.commit()
                conn.close()
                st.success("تم التحديث")

    st.markdown("##### الإجراءات")
    cols = st.columns(3)
    with cols[0]:
        if st.button("❌ حذف الطلب نهائيًا"):
            for d in docs:
                if d['file_path'] and os.path.exists(d['file_path']):
                    try:
                        os.remove(d['file_path'])
                    except Exception:
                        pass
            conn = get_conn()
            cur = conn.cursor()
            # استخدام updated_at هنا أيضًا
            cur.execute("UPDATE requests SET deleted_at=?, updated_at=? WHERE id=?", (datetime.now().isoformat(), datetime.now().isoformat(), request_id))
            conn.commit()
            conn.close()
            st.success("تم الحذف النهائي. يمكن للمستشفى تقديم طلب جديد لنفس الخدمة الآن.")
            st.rerun()
    with cols[1]:
        if st.button("🔄 استرجاع كـ 'إعادة تقديم'"):
            conn = get_conn()
            cur = conn.cursor()
            # استخدام updated_at هنا أيضًا
            cur.execute("UPDATE requests SET status='إعادة تقديم', deleted_at=NULL, updated_at=? WHERE id=?", (datetime.now().isoformat(), request_id))
            conn.commit()
            conn.close()
            st.success("تم الاسترجاع")
            st.rerun()
    with cols[2]:
        if st.button("🔒 إغلاق الطلب"):
            conn = get_conn()
            cur = conn.cursor()
            final_status = "مغلق"
            # استخدام updated_at هنا أيضًا
            cur.execute("UPDATE requests SET status=?, closed_at=?, updated_at=? WHERE id=?", (final_status, datetime.now().isoformat(), datetime.now().isoformat(), request_id))
            conn.commit()
            conn.close()
            st.success("تم الإغلاق — يمكن تقديم طلب جديد")

# ... (الجزء السفلي من الدالة كما هو) ...


# ... (تستمر في القسم التالي)
# ... (متابعة من القسم 5)

def admin_deleted_ui():
    st.markdown("<div class='subheader'>الطلبات المحذوفة</div>", unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, h.name AS hospital, s.name AS service, r.age_category,
               r.status, r.created_at, r.deleted_at
        FROM requests r
        JOIN hospitals h ON h.id=r.hospital_id
        JOIN services s ON s.id=r.service_id
        WHERE r.deleted_at IS NOT NULL
        ORDER BY r.deleted_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    df = pd.DataFrame([dict(x) for x in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)

def admin_lists_ui():
    st.markdown("<div class='subheader'>إدارة الخدمات وأنواع المستشفيات</div>", unsafe_allow_html=True)

    # إدارة الخدمات
    st.markdown("#### 🧩 الخدمات")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM services ORDER BY active DESC, name")
    services = cur.fetchall()
    conn.close()
    for service in services:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(service['name'])
        with col2:
            status = "مفعلة" if service['active'] else "معطلة"
            st.write(status)
        with col3:
            if st.button("تغيير الحالة" if service['active'] else "تفعيل", key=f"toggle_{service['id']}"):
                conn = get_conn()
                cur = conn.cursor()
                new_status = 0 if service['active'] else 1
                cur.execute("UPDATE services SET active=? WHERE id=?", (new_status, service['id']))
                conn.commit()
                conn.close()
                st.success("تم تغيير الحالة")
                st.rerun()

    with st.form("add_service"):
        sname = st.text_input("إضافة خدمة جديدة")
        s_active = st.checkbox("مفعلة؟", value=True)
        sub = st.form_submit_button("إضافة الخدمة")
        if sub and sname:
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO services (name, active) VALUES (?,?)", (sname.strip(), 1 if s_active else 0))
                conn.commit()
                conn.close()
                st.success("تمت الإضافة")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("الخدمة موجودة مسبقًا")

    # إدارة أنواع المستشفيات
    st.markdown("#### 🏥 أنواع المستشفيات")
    types = get_hospital_types()
    editable = st.text_input("أنواع المستشفيات (مفصولة بفواصل)", ",".join(types))
    if st.button("حفظ الأنواع"):
        new_types = [t.strip() for t in editable.split(",") if t.strip()]
        if new_types:
            set_hospital_types(new_types)
            st.success("تم الحفظ")

    # إدارة القطاعات
    st.markdown("#### 🏢 القطاعات")
    sectors = get_sectors()
    editable_sectors = st.text_input("القطاعات (مفصولة بفواصل)", ",".join(sectors))
    if st.button("حفظ القطاعات"):
        new_sectors = [s.strip() for s in editable_sectors.split(",") if s.strip()]
        if new_sectors:
            set_sectors(new_sectors)
            st.success("تم الحفظ")

    # إدارة المحافظات
    st.markdown("#### 🗺️ المحافظات")
    gov = get_governorates()
    editable_gov = st.text_input("المحافظات (مفصولة بفواصل)", ",".join(gov))
    if st.button("حفظ المحافظات"):
        new_gov = [g.strip() for g in editable_gov.split(",") if g.strip()]
        if new_gov:
            set_governorates(new_gov)
            st.success("تم الحفظ")

    # إدارة حالات الطلبات (للأدمن فقط)
    st.markdown("#### 📋 حالات الطلبات (للأدمن فقط)")
    current_statuses = get_request_statuses()
    st.write("الحالات الحالية:")
    st.write(", ".join(current_statuses))

    # إضافة/تعديل حالة جديدة
    with st.form("add_edit_status"):
        new_status_name = st.text_input("اسم الحالة الجديدة أو تعديل الحالية")
        # تحميل الإعدادات الحالية للحالة المحددة (إن وجدت)
        selected_status_for_edit = st.selectbox("اختر حالة لتعديل إعداداتها", [""] + current_statuses)
        prevents_new = st.checkbox("يمنع تقديم طلب جديد لنفس الخدمة", value=False)
        blocks_days = st.number_input("يمنع تقديم طلب لنفس الخدمة لمدة (أيام) - 0 للتعطيل", min_value=0, value=0)
        is_final = st.checkbox("حالة نهائية (تغلق الطلب)", value=False)

        if st.form_submit_button("إضافة/تعديل الحالة"):
             if new_status_name:
                 conn = get_conn()
                 cur = conn.cursor()
                 try:
                     # إضافة أو تحديث اسم الحالة
                     cur.execute("INSERT OR IGNORE INTO request_statuses (name) VALUES (?)", (new_status_name,))
                     # تحديث الإعدادات
                     cur.execute("""
                         INSERT INTO status_settings (status_name, prevents_new_request, blocks_service_for_days, is_final_state)
                         VALUES (?, ?, ?, ?)
                         ON CONFLICT(status_name) DO UPDATE SET
                         prevents_new_request=excluded.prevents_new_request,
                         blocks_service_for_days=excluded.blocks_service_for_days,
                         is_final_state=excluded.is_final_state
                     """, (new_status_name, 1 if prevents_new else 0, blocks_days, 1 if is_final else 0))
                     conn.commit()
                     st.success(f"تمت إضافة أو تعديل الحالة: {new_status_name}")
                     st.rerun()
                 except Exception as e:
                     st.error(f"خطأ: {e}")
                 finally:
                     conn.close()
             else:
                 st.warning("يرجى إدخال اسم الحالة.")

    # حذف حالة
    with st.form("delete_status"):
         status_to_delete = st.selectbox("اختر حالة لحذفها", [""] + [s for s in current_statuses if s != "طلب غير مكتمل"]) # منع حذف الحالة الافتراضية المؤقتة
         if st.form_submit_button("حذف الحالة"):
             if status_to_delete:
                 conn = get_conn()
                 cur = conn.cursor()
                 try:
                     # التحقق مما إذا كانت الحالة مستخدمة في أي طلب
                     cur.execute("SELECT COUNT(*) as c FROM requests WHERE status = ?", (status_to_delete,))
                     count = cur.fetchone()['c']
                     if count > 0:
                         st.warning(f"لا يمكن حذف الحالة '{status_to_delete}' لأنها مستخدمة في {count} طلب(طلبات).")
                     else:
                         cur.execute("DELETE FROM status_settings WHERE status_name = ?", (status_to_delete,))
                         cur.execute("DELETE FROM request_statuses WHERE name = ?", (status_to_delete,))
                         conn.commit()
                         st.success(f"تم حذف الحالة: {status_to_delete}")
                         st.rerun()
                 except Exception as e:
                     st.error(f"خطأ: {e}")
                 finally:
                     conn.close()
             else:
                 st.warning("يرجى اختيار حالة للحذف.")

    # إدارة أنواع المستندات
    st.markdown("#### 📄 أنواع المستندات المطلوبة (للأدمن فقط)")
    doc_types = get_document_types()
    st.write("الأنواع الحالية:")
    # عرض المستندات مع إمكانية التعديل
    edited_docs = []
    for doc in doc_types:
        with st.expander(f"تعديل: {doc['display_name']} ({doc['name']})"):
            new_display_name = st.text_input("الاسم المعروض", value=doc['display_name'], key=f"display_{doc['name']}")
            new_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟", value=bool(doc['is_video_allowed']), key=f"video_{doc['name']}")
            edited_docs.append({
                'name': doc['name'],
                'display_name': new_display_name,
                'is_video_allowed': new_is_video_allowed
            })
            if st.button("حفظ التعديل", key=f"save_doc_{doc['name']}"):
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE document_types
                    SET display_name = ?, is_video_allowed = ?
                    WHERE name = ?
                """, (new_display_name, 1 if new_is_video_allowed else 0, doc['name']))
                conn.commit()
                conn.close()
                st.success("تم حفظ التعديل")
                st.rerun()

    # إضافة نوع مستند جديد
    with st.form("add_doc_type"):
        st.markdown("##### إضافة نوع مستند جديد")
        new_doc_name = st.text_input("الاسم الداخلي (لا يمكن تغييره لاحقًا)")
        new_doc_display_name = st.text_input("الاسم المعروض")
        new_doc_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟")
        if st.form_submit_button("إضافة نوع مستند"):
            if new_doc_name and new_doc_display_name:
                conn = get_conn()
                cur = conn.cursor()
                try:
                    cur.execute("""
                        INSERT INTO document_types (name, display_name, is_video_allowed)
                        VALUES (?, ?, ?)
                    """, (new_doc_name, new_doc_display_name, 1 if new_doc_is_video_allowed else 0))
                    conn.commit()
                    st.success("تمت إضافة نوع المستند")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("الاسم الداخلي موجود مسبقًا")
                except Exception as e:
                    st.error(f"خطأ: {e}")
                finally:
                    conn.close()
            else:
                st.warning("يرجى ملء الحقول المطلوبة.")

        # === إدارة المستندات الاختيارية لأنواع المستشفيات ===
    st.markdown("#### 📄 إدارة المستندات الاختيارية لأنواع المستشفيات")
    
    # الحصول على أنواع المستشفيات
    hospital_types = get_hospital_types()
    # الحصول على جميع المستندات المتاحة
    all_doc_names = DOC_TYPES 

    if not hospital_types:
        st.info("لا توجد أنواع مستشفيات معرفة. يرجى التأكد من تهيئتها أولاً.")
    else:
        # عرض واجهة لكل نوع مستشفى
        for htype in hospital_types:
            with st.expander(f"تعديل المستندات لـ {htype}", expanded=False):
                st.markdown(f"### {htype}")
                
                # جلب المستندات الاختيارية الحالية لهذا النوع من قاعدة البيانات
                current_optional_docs = get_optional_docs_for_type(htype)
                
                # استخدام multiselect لاختيار المستندات الاختيارية
                selected_optional_docs = st.multiselect(
                    f"اختر المستندات الاختيارية لـ {htype}",
                    options=all_doc_names,
                    default=list(current_optional_docs),
                    key=f"multiselect_optional_docs_{htype}" # مفتاح فريد
                )
                
                # زر حفظ التغييرات
                if st.button(f"💾 حفظ التغييرات لـ {htype}", key=f"save_button_{htype}"):
                    try:
                        # استدعاء الدالة المساعدة لتحديث قاعدة البيانات
                        set_optional_docs_for_type(htype, selected_optional_docs)
                        st.success(f"✅ تم حفظ المستندات الاختيارية لـ {htype}")
                        # إعادة تحميل الصفحة لعرض التغييرات فورًا
                        st.rerun() 
                    except Exception as e:
                        st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")
def admin_users_ui():
    st.markdown("<div class='subheader'>إدارة المستخدمين</div>", unsafe_allow_html=True)
    st.markdown("#### 👤 المستخدمون الإداريون")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM admins ORDER BY id")
    admins = cur.fetchall()
    conn.close()
    for admin in admins:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
             st.markdown(f"<div style='padding: 10px; font-family: Cairo, sans-serif;'><b>{admin['username']}</b> ({admin['role']})</div>", unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ حذف", key=f"del_admin_{admin['id']}", help="حذف المستخدم"):
                if admin['username'] != 'admin':
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM admins WHERE id=?", (admin['id'],))
                    conn.commit()
                    conn.close()
                    st.success("تم الحذف")
                    st.rerun()
                else:
                    st.warning("لا يمكن حذف المستخدم الافتراضي")
        with col3:
            if st.button("إعادة تعيين كلمة المرور", key=f"reset_admin_{admin['id']}"):
                conn = get_conn()
                cur = conn.cursor()
                new_password = "1234"
                cur.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new_password), admin['id']))
                conn.commit()
                conn.close()
                st.success(f"تمت إعادة تعيين كلمة المرور إلى: {new_password}")
        with col4:
            st.write("")
    st.markdown("#### ➕ إضافة مستخدم")
    with st.form("add_admin"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        role = st.selectbox("الدور", ["admin", "reviewer"])
        sub = st.form_submit_button("إضافة")
        if sub:
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", (u, hash_pw(p), role))
                conn.commit()
                conn.close()
                st.success("تمت الإضافة")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("اسم المستخدم موجود مسبقًا")
    st.markdown("#### 🔁 إعادة تعيين كلمة المرور")
    with st.form("reset_password"):
        user_type = st.radio("نوع المستخدم", ["مستشفى", "إداري"])
        if user_type == "مستشفى":
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, name, username FROM hospitals ORDER BY name")
            hospitals = cur.fetchall()
            conn.close()
            selected_hospital = st.selectbox("اختر المستشفى", [f"{h['id']} - {h['name']} ({h['username']})" for h in hospitals])
            new_password = st.text_input("كلمة المرور الجديدة", type="password", value="1234")
        else:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, username FROM admins WHERE username != 'admin' ORDER BY username")
            admins = cur.fetchall()
            conn.close()
            if admins:
                selected_admin = st.selectbox("اختر المستخدم الإداري", [f"{a['id']} - {a['username']}" for a in admins])
                new_password = st.text_input("كلمة المرور الجديدة", type="password")
            else:
                st.info("لا يوجد مستخدمين إداريين لإعادة تعيين كلمات مرورهم")
                selected_admin = None
                new_password = ""
        reset_sub = st.form_submit_button("إعادة تعيين")
        if reset_sub:
            try:
                conn = get_conn()
                cur = conn.cursor()
                if user_type == "مستشفى":
                    if selected_hospital:
                        hospital_id = int(selected_hospital.split(" - ")[0])
                        cur.execute("UPDATE hospitals SET password_hash=? WHERE id=?", (hash_pw(new_password), hospital_id))
                        conn.commit()
                        st.success(f"تمت إعادة تعيين كلمة المرور للمستشفى: {selected_hospital}")
                else:
                    if selected_admin:
                        admin_id = int(selected_admin.split(" - ")[0])
                        cur.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new_password), admin_id))
                        conn.commit()
                        st.success(f"تمت إعادة تعيين كلمة المرور للمستخدم: {selected_admin}")
                conn.close()
            except Exception as e:
                st.error(f"حدث خطأ: {str(e)}")

def admin_statistics_ui():
    st.markdown("<div class='subheader'>الإحصائيات</div>", unsafe_allow_html=True)
    st.markdown("#### تصفية الإحصائيات")
    
    # التصفيه حسب الخصائص الأساسية
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_sector = st.selectbox("القطاع", ["الكل"] + get_sectors())
    with col2:
        selected_service = st.selectbox("الخدمة", ["الكل"] + DEFAULT_SERVICES)
    with col3:
        selected_type = st.selectbox("نوع المستشفى", ["الكل"] + DEFAULT_HOSPITAL_TYPES)
    with col4:
        selected_status = st.selectbox("الحالة", ["الكل"] + get_request_statuses())

    # التصفيه حسب التاريخ
    st.markdown("#### تصفية حسب التاريخ")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("من تاريخ", value=None)
    with date_col2:
        end_date = st.date_input("إلى تاريخ", value=None)

    # بناء شروط الاستعلام
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
    
    # إضافة التصفيه حسب التاريخ
    if start_date:
        where_conditions.append("DATE(r.created_at) >= ?")
        params.append(start_date.isoformat())
    if end_date:
        where_conditions.append("DATE(r.created_at) <= ?")
        params.append(end_date.isoformat())

    # بناء جملة WHERE بشكل صحيح
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    conn = get_conn()
    cur = conn.cursor()
    
    # استعلامات الإحصائيات
    query_status = f"""
        SELECT r.status, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY r.status
        ORDER BY count DESC
    """
    cur.execute(query_status, params)
    status_stats = cur.fetchall()
    
    query_service = f"""
        SELECT s.name, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY s.name
        ORDER BY count DESC
    """
    cur.execute(query_service, params)
    service_stats = cur.fetchall()
    
    query_type = f"""
        SELECT h.type, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY h.type
        ORDER BY count DESC
    """
    cur.execute(query_type, params)
    type_stats = cur.fetchall()
    
    query_sector = f"""
        SELECT h.sector, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY h.sector
        ORDER BY count DESC
    """
    cur.execute(query_sector, params)
    sector_stats = cur.fetchall()
    conn.close()

    # عرض الإحصائيات النصية
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
    
    # محاولة عرض الإحصائيات البيانية
    plotly_available = False
    try:
        import plotly.express as px
        plotly_available = True
    except ImportError:
        st.info("لم يتم تثبيت مكتبة 'plotly'. سيتم عرض الإحصائيات بشكل نصي فقط. لتثبيتها، قم بتشغيل الأمر: `pip install plotly`")

    if plotly_available:
        st.markdown("---")
        st.markdown("#### 📊 الإحصائيات البيانية")
        try:
            # تحويل النتائج إلى قوائم من القواميس
            status_data = [dict(row) for row in status_stats]
            type_data = [dict(row) for row in type_stats]
            service_data = [dict(row) for row in service_stats]
            sector_data = [dict(row) for row in sector_stats]

            # عرض الرسوم البيانية
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
                st.markdown("<div class='stats-header'>حسب الحالة</div>", unsafe_allow_html=True)
                if len(status_data) > 0:
                    try:
                        status_df = pd.DataFrame(status_data)
                        fig_status = px.pie(status_df, values='count', names='status', 
                                           title='توزيع الطلبات حسب الحالة',
                                           color_discrete_sequence=px.colors.sequential.Blues_r)
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
                        fig_type = px.bar(type_df, x='type', y='count', 
                                         title='عدد الطلبات حسب نوع المستشفى',
                                         color='type',
                                         color_discrete_sequence=['#1f77b4', '#ff7f0e'])
                        fig_type.update_layout(xaxis_title="نوع المستشفى", yaxis_title="العدد")
                        st.plotly_chart(fig_type, use_container_width=True)
                    except Exception as e:
                        st.warning(f"خطأ في إنشاء الرسم البياني: {e}")
                else:
                    st.info("لا توجد بيانات")
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"حدث خطأ أثناء إنشاء الرسوم البيانية: {e}")

def admin_resources_ui():
    st.markdown("<div class='subheader'>إدارة ملفات التنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك رفع الملفات التالية لجعلها متوفرة للمستخدمين</div>", unsafe_allow_html=True)
    RESOURCES_DIR.mkdir(exist_ok=True)
    for filename in RESOURCE_FILES:
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
                st.rerun()

# ---------------------------- وظائف عامة ---------------------------- #
def change_password_ui(role: str, hospital_id: int = None):
    with st.form(f"change_pw_{role}"):
        old = st.text_input("كلمة المرور الحالية", type="password")
        new1 = st.text_input("كلمة المرور الجديدة", type="password")
        new2 = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
        sub = st.form_submit_button("تغيير")
        if sub:
            if new1 != new2:
                st.error("كلمتا المرور غير متطابقتين")
                return
            if role == "admin" or role == "reviewer":
                u = st.session_state.user
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT * FROM admins WHERE id=? AND password_hash=?", (u["admin_id"], hash_pw(old)))
                row = cur.fetchone()
                if not row:
                    st.error("كلمة المرور الحالية غير صحيحة")
                else:
                    cur.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new1), u["admin_id"]))
                    conn.commit()
                    conn.close()
                    st.success("تم التغيير")
            else: # hospital
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT * FROM hospitals WHERE id=? AND password_hash=?", (hospital_id, hash_pw(old)))
                row = cur.fetchone()
                if not row:
                    st.error("كلمة المرور الحالية غير صحيحة")
                else:
                    cur.execute("UPDATE hospitals SET password_hash=? WHERE id=?", (hash_pw(new1), hospital_id))
                    conn.commit()
                    conn.close()
                    st.success("تم التغيير")

# ---------------------------- تشغيل التطبيق ---------------------------- #
def main():
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True
    )
    if 'db_version_checked' not in st.session_state:
        run_ddl()
        st.session_state.db_version_checked = True
    
    if "user" not in st.session_state:
        login_ui()
    else:
        if st.session_state.user.get("role") == "hospital":
            hospital_home()
        else:
            admin_home()
    
    # عرض التذييل
    st.markdown("""
    <div class='footer'>
        <p>© 2025 المشروع القومي لقوائم الانتظار - التعاقد على الخدمات الجراحية</p>
        <p>تم التصميم بواسطة الغرفه المركزيه لقوائم الانتظار</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
=======

import os
import re
import io
import zipfile
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import sqlite3
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
# ---------------------------- إعدادات أساسية ---------------------------- #
APP_TITLE = "المشروع القومي لقوائم الانتظار-التعاقد على الخدمات الجراحية"
DB_PATH = Path("data/app.db")
STORAGE_DIR = Path("storage")
EXPORTS_DIR = Path("exports")
RESOURCES_DIR = Path("static")

# إنشاء المجلدات
for p in [DB_PATH.parent, STORAGE_DIR, EXPORTS_DIR, RESOURCES_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# - أنماط CSS مخصصة - #
st.markdown("""
<style>
    /* توسيع العرض الأقصى للصفحة الرئيسية */
    .main {
        background-color: #f8f9fa;
        color: #333;
        direction: rtl;
        font-family: 'Cairo', sans-serif;
        /* تغيير العرض الأقصى ليغطي الشاشة بالكامل */
        max-width: 100vw; /* عرض الشاشة بالكامل */
        padding-left: 2rem;
        padding-right: 2rem;
        margin: 0 auto; /* توسيط المحتوى */
    }
    
    /* تحسين عرض الحاويات داخل النماذج */
    .stForm {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        /* زيادة العرض داخل النماذج */
        max-width: 100%;
    }
    
    /* تحسين عرض الجداول */
    .stDataFrame {
        width: 100% !important;
    }
    
    /* تحسين عرض أعمدة النص */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        width: 100%;
        min-width: 200px; /* الحد الأدنى للعرض */
    }
    
    /* تحسين عرض الأزرار */
    .stButton>button {
        background-color: #1a56db;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
        width: auto; /* السماح للأزرار بالتكيف مع المحتوى */
    }
    
    .stButton>button:hover {
        background-color: #1e40af;
    }
    
    /* تحسين عرض عناصر الإدخال */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stTextArea>div>div>textarea {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض علامات التبويب */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-size: 16px;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض التنبيهات */
    .stAlert {
        border-radius: 8px;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض العناوين */
    h1, h2, h3 {
        color: #1e40af;
        font-family: 'Cairo', sans-serif;
    }
    
    .header {
        text-align: center;
        color: #1e40af;
        font-weight: 200;
        margin-bottom: 10px;
        font-family: 'Cairo', sans-serif;
    }
    
    .subheader {
        color: #1a56db;
        font-weight: 200;
        margin-top: 10px;
        margin-bottom: 10px;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض مربعات المعلومات */
    .info-box {
        background-color: #dbeafe;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1e40af;
        margin: 10px 0;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تحسين عرض النصوص المطلوبة */
    .required::after {
        content: " *";
        color: red;
    }
    
    /* تحسين عرض شعار التطبيق */
    .logo-container {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .logo-container img {
        max-width: 150px;
        height: auto;
    }
    
    /* تحسين عرض التذييل */
    .footer {
        text-align: center;
        margin-top: 30px;
        padding: 20px;
        border-top: 1px solid #e2e8f0;
        color: #64748b;
        font-size: 14px;
        /* جعل التذييل يغطي العرض الكامل */
        width: 100%;
    }
    
    /* تحسين عرض بطاقات الإحصائيات */
    .stats-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        width: 100%;
    }
    
    /* تحسين عرض عناصر الإحصائيات */
    .stats-header {
        color: #1e40af;
        font-weight: 600;
        margin-bottom: 15px;
        font-size: 18px;
    }
    
    .stats-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .stats-item:last-child {
        border-bottom: none;
    }
    
    .stats-label {
        font-weight: 500;
    }
    
    .stats-value {
        font-weight: 600;
        color: #1a56db;
    }
    
    /* تحسين عرض أعمدة البيانات */
    [data-testid="column"] {
        padding: 0 10px;
    }
    
    /* تحسين عرض محددات الصفحات */
    .css-18ni7ap { /* محدد الصفحة */
        max-width: 100%;
    }
    
    /* تحسين عرض محتوى التطبيق بشكل عام */
    section[data-testid="stSidebar"] {
        width: 250px !important; /* تحديد عرض الشريط الجانبي */
    }
    
    /* تحسين عرض العناصر داخل الأعمدة */
    .st-bf { /* معرف CSS لأعمدة Streamlit */
        gap: 1rem; /* المسافة بين الأعمدة */
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
# أنواع الفئات
AGE_CATEGORIES = ["كبار", "أطفال", "كبار وأطفال"]
# حالة الطلب الافتراضية - سيتم تحميلها من قاعدة البيانات
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
    "طلب غير مكتمل", # حالة جديدة
]
# أنواع المستندات المطلوبة الافتراضية - سيتم تحميلها من قاعدة البيانات
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
    "فيديو لغرف العمليات والإقامة", # نوع ملف مرن
    "السعة السريرية الكلية - عدد أسرة الرعايات",
    "تشكيل فريق مكافحة العدوى - تشكيل فريق الجودة",
    "محاضر اجتماعات الفرق لآخر 3 أشهر",
    "السياسات الخاصة بالجراحة والتخدير معتمدة",
    "أخرى",
]
GOVERNMENT_OPTIONAL_DOCS = {
    "ترخيص العلاج الحر موضح به التخصصات", # <-- تمت تصحيحه
    "صورة بطاقة ضريبية للمنشأة سارية",
    "صورة حديثة للسجل التجاري",
    "أخرى","تقييم مكافحة العدوى (ذاتي)"
}
# المستندات التي لا تُطلب للمستشفيات الخاصة (افتراضياً) - يمكن أن تكون فارغة
PRIVATE_OPTIONAL_DOCS = set(["أخرى","تقييم مكافحة العدوى من الجهة التابع لها المستشفى"])
# ... (باقي الثوابت كما هي: DEFAULT_SERVICES, DEFAULT_HOSPITAL_TYPES, إلخ) ...
# -----------

# ملفات الموارد المتاحة للتنزيل
RESOURCE_FILES = [
    "القلب المفتوح.pdf",
    "القسطره القلبيه.pdf",
    "الاوعيه الدمويه والقسطره الطرفيه.pdf",
    "القسطره المخيه.pdf",
    "المخ والاعصاب.pdf",
    "الرمد.pdf",
    "العظام.pdf",
    "زراعة الكبد.pdf",
    "زراعة الكلى.pdf",
    "الاورام.pdf",
      "زراعة القوقعه.pdf",
    "متطلبات التعاقد.pdf",
    "طريقة التسجيل.pdf",
    "تعليمات هامة.pdf"
]

# ---------------------------- أدوات مساعدة ---------------------------- #
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def check_file_type(filename: str, is_video_allowed: bool) -> bool:
    """التحقق من نوع الملف المسموح برفعه"""
    ext = Path(filename).suffix.lower()
    allowed_extensions = {'.pdf'}
    if is_video_allowed:
        allowed_extensions.update({'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'})
    return ext in allowed_extensions

def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\-\.\u0621-\u064A\s]", "_", name)
    name = re.sub(r"\s+", "_", name).strip("_.")
    return name or "file"

def is_video_only_document(doc_type_name: str) -> bool:
    """
    التحقق مما إذا كان نوع المستند يجب أن يقبل فقط ملفات الفيديو.
    Args:
        doc_type_name (str): اسم نوع المستند كما هو في قاعدة البيانات.
    Returns:
        bool: True إذا كان يجب أن يكون فيديو فقط، False إذا كان يقبل PDF أيضًا.
    """
    # قائمة بأسماء المستندات التي يجب أن تقبل فقط ملفات الفيديو
    VIDEO_ONLY_DOCUMENTS = {
        "فيديو لغرف العمليات والإقامة"
        # يمكن إضافة أسماء أخرى هنا في المستقبل إذا لزم الأمر
    }
    return doc_type_name in VIDEO_ONLY_DOCUMENTS

# ---------------------------- وظائف مساعدة للإعدادات ---------------------------- #

def get_hospital_types() -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='hospital_types'")
    row = cur.fetchone()
    conn.close()
    types = row["value"].split(",") if row and row["value"] else []
    return types or DEFAULT_HOSPITAL_TYPES

def set_hospital_types(types: list):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO meta(key,value) VALUES('hospital_types', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(types),))
    conn.commit()
    conn.close()

def get_sectors() -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='sectors'")
    row = cur.fetchone()
    conn.close()
    sectors = row["value"].split(",") if row and row["value"] else []
    return sectors or DEFAULT_SECTORS

def set_sectors(sectors: list):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO meta(key,value) VALUES('sectors', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(sectors),))
    conn.commit()
    conn.close()

def get_governorates() -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='governorates'")
    row = cur.fetchone()
    conn.close()
    gov = row["value"].split(",") if row and row["value"] else []
    return gov or DEFAULT_GOVERNORATES

def set_governorates(gov: list):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO meta(key,value) VALUES('governorates', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(gov),))
    conn.commit()
    conn.close()

def get_request_statuses() -> list:
    """الحصول على قائمة الحالات من قاعدة البيانات أو استخدام الافتراضية"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM request_statuses ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    if rows:
        return [row['name'] for row in rows]
    else:
        # في حالة عدم وجود حالات مخصصة، نستخدم الافتراضية
        return DEFAULT_REQUEST_STATUSES

def get_open_statuses() -> set:
    """الحصول على الحالات التي تمنع تقديم طلب جديد لنفس الخدمة"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status_name FROM status_settings WHERE prevents_new_request = 1")
    rows = cur.fetchall()
    conn.close()
    return {row['status_name'] for row in rows}

def get_blocked_statuses(days: int = 90) -> set:
    """الحصول على الحالات التي تمنع التقديم لنفس الخدمة لمدة X أيام"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status_name FROM status_settings WHERE blocks_service_for_days >= ?", (days,))
    rows = cur.fetchall()
    conn.close()
    return {row['status_name'] for row in rows}

def is_final_status(status: str) -> bool:
    """التحقق مما إذا كانت الحالة نهائية (تتطلب تسجيل closed_at)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT is_final_state FROM status_settings WHERE status_name = ?", (status,))
    row = cur.fetchone()
    conn.close()
    return row and row['is_final_state'] == 1

def get_document_types() -> list:
    """الحصول على قائمة أنواع المستندات"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, display_name, is_video_allowed FROM document_types ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [{'name': row['name'], 'display_name': row['display_name'], 'is_video_allowed': row['is_video_allowed']} for row in rows]

def get_optional_docs_for_type(hospital_type: str) -> set:
    """جلب المستندات الاختيارية لنوع مستشفى معين من قاعدة البيانات."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT doc_name FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,))
    rows = cur.fetchall()
    conn.close()
    return {row['doc_name'] for row in rows}

def set_optional_docs_for_type(hospital_type: str, doc_names: list):
    """تحديث المستندات الاختيارية لنوع مستشفى معين في قاعدة البيانات."""
    conn = get_conn()
    cur = conn.cursor()
    # حذف الإدخالات الحالية لهذا النوع
    cur.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,))
    # إدخال الإدخالات الجديدة
    for doc_name in doc_names:
        if doc_name: # تجنب إدخال أسماء فارغة
            cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", (hospital_type, doc_name))
    conn.commit()
    conn.close()

def ensure_request_docs(request_id: int, hospital_type: str):
    """إنشاء سجلات المستندات الافتراضية للطلب وفق نوع المستشفى."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT doc_type FROM documents WHERE request_id=?", (request_id,))
    existing = {r["doc_type"] for r in cur.fetchall()}
    
    # ***تحديث هنا: استخدام القواعد الجديدة***
    # الحصول على المستندات الاختيارية لهذا النوع من قاعدة البيانات
    optional_docs_for_this_type = get_optional_docs_for_type(hospital_type)

    for dt in DOC_TYPES:
        # ***تحديث هنا: تحديد ما إذا كان المستند مطلوبًا أم لا***
        # إذا كان المستند في قائمة المستندات الاختيارية لهذا النوع، فهو غير مطلوب (required=0)
        # وإلا، فهو مطلوب (required=1)
        required = 0 if dt in optional_docs_for_this_type else 1
        
        if dt not in existing:
            cur.execute(
                "INSERT INTO documents (request_id, doc_type, required, satisfied, uploaded_at) VALUES (?,?,?,?,?)",
                (request_id, dt, required, 0, None),
            )
    conn.commit()
    conn.close()

def hospital_has_open_request(hospital_id: int, service_id: int) -> bool:
    """التحقق من وجود طلب مفتوح (منع التقديم) لنفس الخدمة"""
    open_statuses = get_open_statuses()
    if not open_statuses:
         return False # إذا لم تكن هناك حالات مفتوحة محددة، لا تمنع

    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(open_statuses))
    query = f"""
        SELECT COUNT(1) c
        FROM requests
        WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL AND status IN ({placeholders})
    """
    params = [hospital_id, service_id] + list(open_statuses)
    cur.execute(query, params)
    c = cur.fetchone()["c"]
    conn.close()
    return c > 0

def hospital_blocked_from_request(hospital_id: int, service_id: int) -> bool:
    """التحقق من منع المستشفى من تقديم طلب لنفس الخدمة لمدة 3 أشهر"""
    blocked_statuses = get_blocked_statuses(90) # افتراضيًا 90 يوم
    if not blocked_statuses:
        return False # إذا لم تكن هناك حالات محظورة محددة، لا تمنع

    conn = get_conn()
    cur = conn.cursor()
    three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
    placeholders = ",".join(["?"] * len(blocked_statuses))
    query = f"""
        SELECT COUNT(1) c
        FROM requests
        WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL AND status IN ({placeholders}) AND closed_at > ?
    """
    params = [hospital_id, service_id] + list(blocked_statuses) + [three_months_ago]
    cur.execute(query, params)
    c = cur.fetchone()["c"]
    conn.close()
    return c > 0

def generate_username(hospital_name: str) -> str:
    """توليد اسم مستخدم من اسم المستشفى (أول 3 كلمات بالإنجليزية)"""
    arabic_to_english = {
        'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'g', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's',
        'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': '3', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
        'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ى': 'a', 'ئ': '2', 'ء': '2', 'ؤ': '2'
    }
    english_name = ""
    for char in hospital_name:
        if char in arabic_to_english:
            english_name += arabic_to_english[char]
        elif char.isalpha() or char.isdigit():
            english_name += char
        else:
            english_name += "_"
    words = english_name.split("_")[:3]
    username = "".join(words).replace(" ", "").replace("-", "").replace("_", "")
    username = re.sub(r"[^\w]", "", username)
    return username.lower()[:20] or "hospital"

def is_hospital_profile_complete(hospital_id: int) -> bool:
    """التحقق من إكمال بيانات المستشفى الأساسية"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT license_start, license_end, license_number, manager_name, manager_phone, address
        FROM hospitals WHERE id=?
    """, (hospital_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    required_fields = [
        row['license_start'], row['license_end'], row['license_number'],
        row['manager_name'], row['manager_phone'], row['address']
    ]
    return all(field and str(field).strip() for field in required_fields)

# ---------------------------- واجهة الدخول ---------------------------- #
def login_ui():
    # البحث عن البانر (يدعم PNG و JPG)
    banner_path_png = Path("static/banner.png")
    banner_path_jpg = Path("static/banner.jpg")
    banner_path = None
    if banner_path_png.exists():
        banner_path = banner_path_png
    elif banner_path_jpg.exists():
        banner_path = banner_path_jpg
    
    if banner_path:
        st.image(str(banner_path), use_container_width=True, caption="")
    else:
        # رسالة اختيارية للمستخدم الإداري
        # st.warning("لم يتم العثور على ملف البانر (banner.png أو banner.jpg) في مجلد static/")
        pass # أو اتركه فارغًا إذا كنت لا تريد إظهار أي شيء

    st.markdown(f"<div class='header'><h1>{APP_TITLE}</h1></div>", unsafe_allow_html=True)
    
    # البحث عن الشعار (يدعم PNG و JPG)
    logo_path_png = Path("static/logo.png")
    logo_path_jpg = Path("static/logo.jpg")
    logo_path = None
    if logo_path_png.exists():
        logo_path = logo_path_png
    elif logo_path_jpg.exists():
        logo_path = logo_path_jpg
    
    if logo_path:
        st.image(str(logo_path), width=50)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    # ... (باقي الكود كما هو)
    with st.form("login_form"):
        st.markdown("### تسجيل دخول")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("تسجيل الدخول")
        if submitted:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM hospitals WHERE username=? AND password_hash=?", (username, hash_pw(password)))
            hospital_user = cur.fetchone()
            if hospital_user:
                st.session_state.user = {
                    "role": "hospital",
                    "hospital_id": hospital_user["id"],
                    "hospital_name": hospital_user["name"],
                    "hospital_code": hospital_user["code"],
                    "hospital_type": hospital_user["type"],
                }
                st.success("تم تسجيل الدخول بنجاح")
                st.rerun()
            cur.execute("SELECT * FROM admins WHERE username=? AND password_hash=?", (username, hash_pw(password)))
            admin_user = cur.fetchone()
            conn.close()
            if admin_user:
                st.session_state.user = {
                    "role": admin_user["role"],
                    "username": admin_user["username"],
                    "admin_id": admin_user["id"],
                }
                st.success("تم تسجيل الدخول بنجاح")
                st.rerun()
            if not hospital_user and not admin_user:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# قم بزيادة هذا الرقم في كل مرة تضيف فيها تغييرًا جديدًا على هيكل قاعدة البيانات
DB_SCHEMA_VERSION = 4  # مثال: تم إضافة عمود is_video_allowed وجدول hospital_type_optional_docs

# تعريف الإصدار الحالي لهيكل قاعدة البيانات
DB_SCHEMA_VERSION = 4

@st.cache_resource
def get_db_initial_version():
    """الحصول على إصدار قاعدة البيانات عند بدء التشغيل"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
        row = cur.fetchone()
        version = row['version'] if row else 0
        conn.close()
        return version
    except:
        return 0

# تعريف الإصدار الحالي لهيكل قاعدة البيانات
# قم بزيادة هذا الرقم في كل مرة تضيف فيها تغييرًا جديدًا على هيكل قاعدة البيانات
DB_SCHEMA_VERSION = 4 # مثال: تم إضافة عمود is_video_allowed وجدول hospital_type_optional_docs

def run_ddl():
    """إنشاء جداول قاعدة البيانات وتحديثها إذا لزم الأمر لـ SQLite."""
    conn = get_conn()
    with conn:
        cur = conn.cursor()
        
        # --- إنشاء الجداول ---
        # جدول الأدمن
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT DEFAULT 'admin' -- admin, reviewer
            )
        """)
        
        # جدول المستشفيات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sector TEXT,
                governorate TEXT,
                code TEXT UNIQUE,
                type TEXT DEFAULT 'خاص',
                address TEXT,
                other_branches TEXT,
                other_branches_address TEXT,
                license_start TEXT,
                license_end TEXT,
                manager_name TEXT,
                manager_phone TEXT,
                license_number TEXT,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        """)
        
        # جدول الخدمات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                active INTEGER DEFAULT 1
            )
        """)
        
        # جدول الطلبات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_id INTEGER,
                service_id INTEGER,
                age_category TEXT,
                status TEXT DEFAULT 'طلب غير مكتمل',
                admin_note TEXT,
                created_at TEXT,
                deleted_at TEXT,
                closed_at TEXT, -- تاريخ إغلاق الطلب (مرفوض/مقبول/مغلق/...)
                updated_at TEXT, -- تاريخ آخر تعديل
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        """)

        # ترقية جدول الطلبات: إضافة عمود updated_at إذا لم يكن موجوداً
        try:
            cur.execute("SELECT updated_at FROM requests LIMIT 1")
        except sqlite3.OperationalError as e:
            if "no such column: updated_at" in str(e):
                cur.execute("ALTER TABLE requests ADD COLUMN updated_at TEXT")
                conn.commit()
                print("تمت إضافة عمود 'updated_at' إلى جدول 'requests'.")
            else:
                raise e

        # ترقية جدول الطلبات: إضافة عمود closed_at إذا لم يكن موجوداً
        try:
            cur.execute("SELECT closed_at FROM requests LIMIT 1")
        except sqlite3.OperationalError as e:
            if "no such column: closed_at" in str(e):
                cur.execute("ALTER TABLE requests ADD COLUMN closed_at TEXT")
                conn.commit()
                print("تمت إضافة عمود 'closed_at' إلى جدول 'requests'.")
            else:
                raise e

        # جدول المستندات (الذي تم تحديثه)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                doc_type TEXT, -- الاسم الأصلي من قائمة المستندات
                display_name TEXT, -- الاسم المعروض (يمكن تعديله)
                file_name TEXT,
                file_path TEXT,
                required INTEGER DEFAULT 1,
                satisfied INTEGER DEFAULT 0,
                admin_comment TEXT,
                uploaded_at TEXT,
                is_video_allowed INTEGER DEFAULT 0, -- إضافة العمود الجديد للسماح بالفيديو
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
        """)

        # ترقية جدول المستندات: إضافة عمود is_video_allowed إذا لم يكن موجوداً
        try:
            cur.execute("SELECT is_video_allowed FROM documents LIMIT 1")
        except sqlite3.OperationalError as e:
            if "no such column: is_video_allowed" in str(e):
                cur.execute("ALTER TABLE documents ADD COLUMN is_video_allowed INTEGER DEFAULT 0")
                conn.commit()
                print("تمت إضافة عمود 'is_video_allowed' إلى جدول 'documents'.")
            else:
                raise e

        # جدول أنواع المستندات (لإدارة أسماء المستندات وتفاصيلها)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL, -- الاسم الأصلي
                display_name TEXT NOT NULL, -- الاسم المعروض
                description TEXT, -- وصف اختياري
                is_video_allowed INTEGER DEFAULT 0 -- هل يسمح برفع فيديو لهذا النوع؟
            )
        """)

        # جدول إعدادات المستندات الاختيارية للatypes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS optional_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_type TEXT NOT NULL, -- 'حكومي' أو 'خاص'
                doc_type_name TEXT NOT NULL, -- الاسم الأصلي للمستند
                FOREIGN KEY (doc_type_name) REFERENCES document_types(name)
            )
        """)

        # === تحديث مهم: جدول لربط أنواع المستشفيات بالمستندات الاختيارية ===
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hospital_type_optional_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_type TEXT NOT NULL,
                doc_name TEXT NOT NULL,
                UNIQUE(hospital_type, doc_name)
            )
        """)
        # ================================================================

        # جدول الميتا (لتخزين الإعدادات المتغيرة)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                `key` TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # جدول حالات الطلبات القابلة للتخصيص
        cur.execute("""
            CREATE TABLE IF NOT EXISTS request_statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # جدول إعدادات الحالات (لتحديد السلوك)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS status_settings (
                status_name TEXT PRIMARY KEY,
                prevents_new_request INTEGER DEFAULT 0, -- يمنع تقديم طلب جديد لنفس الخدمة
                blocks_service_for_days INTEGER DEFAULT 0, -- يمنع تقديم طلب لنفس الخدمة لمدة X أيام
                is_final_state INTEGER DEFAULT 0, -- حالة نهائية (تغلق الطلب)
                FOREIGN KEY (status_name) REFERENCES request_statuses(name)
            )
        """)

        conn.commit()

        # --- التهيئة الأولية للبيانات (seeding/updating) ---
        # seed default admin
        cur.execute("SELECT COUNT(1) c FROM admins")
        if cur.fetchone()["c"] == 0:
            cur.execute("INSERT OR IGNORE INTO admins (username, password_hash, role) VALUES (?,?,?)",
                       ("admin", hash_pw("admin123"), "admin"))
            conn.commit()

        # seed services
        cur.execute("SELECT COUNT(1) c FROM services")
        if cur.fetchone()["c"] == 0:
            cur.executemany("INSERT OR IGNORE INTO services (name, active) VALUES (?,1)", [(s,) for s in DEFAULT_SERVICES])
            conn.commit()

        # seed hospital types
        cur.execute("SELECT value FROM meta WHERE `key`='hospital_types'")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO meta (`key`, value) VALUES ('hospital_types', ?)", (",".join(DEFAULT_HOSPITAL_TYPES),))
            conn.commit()

        # seed sectors
        cur.execute("SELECT value FROM meta WHERE `key`='sectors'")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO meta (`key`, value) VALUES ('sectors', ?)", (",".join(DEFAULT_SECTORS),))
            conn.commit()

        # seed governorates
        cur.execute("SELECT value FROM meta WHERE `key`='governorates'")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO meta (`key`, value) VALUES ('governorates', ?)", (",".join(DEFAULT_GOVERNORATES),))
            conn.commit()

        # seed default request statuses if not exists
        cur.execute("SELECT COUNT(1) c FROM request_statuses")
        if cur.fetchone()["c"] == 0:
            for status in DEFAULT_REQUEST_STATUSES:
                 cur.execute("INSERT OR IGNORE INTO request_statuses (name) VALUES (?)", (status,))
            conn.commit()

        # seed default status settings if not exists
        cur.execute("SELECT COUNT(1) c FROM status_settings")
        if cur.fetchone()["c"] == 0:
            # الحالات التي تمنع تقديم طلب جديد (مفتوحة)
            open_statuses = {"جاري دراسة الطلب ومراجعة الأوراق", "جارِ المعاينة", "يجب استيفاء متطلبات التعاقد", "قيد الانتظار", "مقبول" }
            # الحالات التي تمنع التقديم لمدة 3 أشهر
            blocked_statuses = {"مرفوض", "إرجاء التعاقد"}
            # الحالات النهائية
            final_statuses = {"مقبول", "مرفوض", "مغلق", "إرجاء التعاقد", "لا يوجد حاجة للتعاقد"}

            for status in DEFAULT_REQUEST_STATUSES:
                prevents_new = 1 if status in open_statuses else 0
                blocks_days = 90 if status in blocked_statuses else 0
                is_final = 1 if status in final_statuses else 0
                cur.execute("""
                    INSERT OR IGNORE INTO status_settings (status_name, prevents_new_request, blocks_service_for_days, is_final_state)
                    VALUES (?, ?, ?, ?)
                """, (status, prevents_new, blocks_days, is_final))
            conn.commit()

        # seed default document types if not exists
        cur.execute("SELECT COUNT(1) c FROM document_types")
        if cur.fetchone()["c"] == 0:
            video_allowed_docs = {"فيديو لغرف العمليات والإقامة"}
            for doc in DOC_TYPES:
                display_name = doc
                is_video = 1 if doc in video_allowed_docs else 0
                cur.execute("""
                    INSERT OR IGNORE INTO document_types (name, display_name, is_video_allowed)
                    VALUES (?, ?, ?)
                """, (doc, display_name, is_video))
            conn.commit()

        # === تحديث مهم: seed/update default optional docs for hospital types ===
        # الآن نقوم بتحديث أو إدخال المستندات الاختيارية لأنواع المستشفيات بناءً على الثوابت
        # 1. تحديث المستندات الاختيارية للمستشفيات الحكومية
        cur.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", ("حكومي",))
        for doc_name in GOVERNMENT_OPTIONAL_DOCS:
             if doc_name: # تجنب إدخال أسماء فارغة
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("حكومي", doc_name))
        conn.commit()
        
        # 2. تحديث المستندات الاختيارية للمستشفيات الخاصة
        cur.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", ("خاص",))
        for doc_name in PRIVATE_OPTIONAL_DOCS:
             if doc_name: # تجنب إدخال أسماء فارغة
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("خاص", doc_name))
        conn.commit()
        # =====================================================================

        # seed default optional docs if not exists (للحظات الانتقال)
        cur.execute("SELECT COUNT(1) c FROM optional_docs")
        if cur.fetchone()["c"] == 0:
            for doc in GOVERNMENT_OPTIONAL_DOCS:
                cur.execute("INSERT OR IGNORE INTO optional_docs (hospital_type, doc_type_name) VALUES (?, ?)", ("حكومي", doc))
            # يمكن إضافة مستندات اختيارية للخاص هنا إذا لزم الأمر
            for doc in PRIVATE_OPTIONAL_DOCS:
                cur.execute("INSERT OR IGNORE INTO optional_docs (hospital_type, doc_type_name) VALUES (?, ?)", ("خاص", doc))
            conn.commit()

        # === تحديث مهم: تهيئة القيم الافتراضية للمستندات الاختيارية ===
        # نتحقق مما إذا كانت هناك قيم موجودة بالفعل لتجنب الإدخال المكرر
        cur.execute("SELECT COUNT(*) AS count FROM hospital_type_optional_docs")
        if cur.fetchone()['count'] == 0:
            # إدخال المستندات الاختيارية الافتراضية للمستشفيات الحكومية
            for doc_name in GOVERNMENT_OPTIONAL_DOCS:
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("حكومي", doc_name))
            # إدخال المستندات الاختيارية الافتراضية للمستشفيات الخاصة
            for doc_name in PRIVATE_OPTIONAL_DOCS:
                 cur.execute("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", ("خاص", doc_name))
        conn.commit()
        # ===============================================================

    # الاتصال يُغلق تلقائيًا عند الخروج من `with`
# ---------------------------- صفحات المستشفى ---------------------------- #
def hospital_home():
    user = st.session_state.user
    # البحث عن الشعار للشريط الجانبي (يدعم PNG و JPG)
    logo_path_sidebar_png = Path("static/logo.png")
    logo_path_sidebar_jpg = Path("static/logo.jpg")
    logo_path_sidebar = None
    if logo_path_sidebar_png.exists():
        logo_path_sidebar = logo_path_sidebar_png
    elif logo_path_sidebar_jpg.exists():
        logo_path_sidebar = logo_path_sidebar_jpg

    if logo_path_sidebar:
        st.sidebar.image(str(logo_path_sidebar), width=80)
    st.markdown(f"<div class='header'><h2>مرحباً {user['hospital_name']}</h2></div>", unsafe_allow_html=True)
    st.caption(f"نوع المستشفى: {user['hospital_type']}")
    menu = st.sidebar.radio("القائمة", [
        "🏠 الصفحة الرئيسية",
        "📝 تقديم طلب جديد",
        "📂 طلباتي",
        "📥 ملفات متوفرة للتنزيل",
        "🔑 تغيير كلمة المرور",
        "🚪 تسجيل الخروج",
    ])
    if menu == "🏠 الصفحة الرئيسية":
        hospital_dashboard_ui(user)
    elif menu == "📝 تقديم طلب جديد":
        hospital_new_request_ui(user)
    elif menu == "📂 طلباتي":
        hospital_requests_ui(user)
    elif menu == "📥 ملفات متوفرة للتنزيل":
        resources_download_ui()
    elif menu == "🔑 تغيير كلمة المرور":
        change_password_ui(role="hospital", hospital_id=user["hospital_id"])
    elif menu == "🚪 تسجيل الخروج":
        st.session_state.pop("user", None)
        st.rerun()

def hospital_dashboard_ui(user: dict):
    st.markdown("<div class='subheader'>ملف المستشفى</div>", unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals WHERE id=?", (user["hospital_id"],))
    hospital = cur.fetchone()
    conn.close()
    if hospital:
        with st.form("edit_hospital_profile"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("**اسم المستشفى**", value=hospital['name'], disabled=True)
                sector = st.text_input("**القطاع**", value=hospital['sector'] or "", disabled=True)
                governorate = st.text_input("**المحافظة**", value=hospital['governorate'] or "", disabled=True)
                st.text_input("**كود المستشفى**", value=hospital['code'], disabled=True)
                htype = st.text_input("**نوع المستشفى**", value=hospital['type'] or "", disabled=True)
            with col2:
                license_start = st.date_input("**بداية الترخيص**",
                                            value=pd.to_datetime(hospital['license_start']).date() if hospital['license_start'] else None)
                license_end = st.date_input("**نهاية الترخيص",
                                          value=pd.to_datetime(hospital['license_end']).date() if hospital['license_end'] else None)
                license_number = st.text_input("**رقم الترخيص**", value=hospital['license_number'] or "")
                manager_name = st.text_input("**مدير المستشفى**", value=hospital['manager_name'] or "")
                manager_phone = st.text_input("**هاتف المدير**", value=hospital['manager_phone'] or "")
            address = st.text_area("**عنوان المستشفى**", value=hospital['address'] or "", height=100)
            other_branches = st.text_input("الفروع الأخرى", value=hospital['other_branches'] or "")
            other_branches_address = st.text_area("عناوين الفروع الأخرى", value=hospital['other_branches_address'] or "", height=100)
            submitted = st.form_submit_button("حفظ البيانات")
            if submitted:
                try:
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE hospitals SET address=?,
                        other_branches=?, other_branches_address=?, license_start=?,
                        license_end=?, manager_name=?, manager_phone=?, license_number=?
                        WHERE id=?
                    """, (
                        address, other_branches, other_branches_address,
                        str(license_start) if license_start else None,
                        str(license_end) if license_end else None,
                        manager_name, manager_phone, license_number, user["hospital_id"]
                    ))
                    conn.commit()
                    conn.close()
                    st.success("تم حفظ البيانات بنجاح")
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ: {str(e)}")

def hospital_new_request_ui(user: dict):
    if not is_hospital_profile_complete(user["hospital_id"]):
        st.warning("⚠️ يجب إكمال بيانات المستشفى الأساسية أولاً (بداية الترخيص، نهاية الترخيص، رقم الترخيص، مدير المستشفى، هاتف المدير، عنوان المستشفى)")
        hospital_dashboard_ui(user)
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM services WHERE active=1 ORDER BY name")
    services = cur.fetchall()
    conn.close()

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

        if hospital_has_open_request(user["hospital_id"], service_id):
            st.error("لا يمكن إنشاء طلب جديد لنفس الخدمة قبل إغلاق الطلب الحالي من قبل الإدارة.")
            return

        if hospital_blocked_from_request(user["hospital_id"], service_id):
            st.error("لا يمكن تقديم طلب لنفس الخدمة لمدة 3 أشهر من تاريخ رفض الطلب أو إرجاء التعاقد.")
            return

        conn = get_conn()
        cur = conn.cursor()
        # إنشاء طلب بحالة "طلب غير مكتمل" افتراضيًا
        cur.execute("""
            INSERT INTO requests (hospital_id, service_id, age_category, status, created_at)
            VALUES (?,?,?,?,?)
        """, (user["hospital_id"], service_id, age_category, "طلب غير مكتمل", datetime.now().isoformat()))
        req_id = cur.lastrowid
        conn.commit()
        conn.close()

        ensure_request_docs(req_id, user["hospital_type"])
        st.success("تم إنشاء الطلب. يمكنك الآن رفع المستندات.")
        st.session_state["active_request_id"] = req_id
        st.rerun() # إعادة التحميل لعرض واجهة رفع المستندات

    req_id = st.session_state.get("active_request_id")
    if req_id:
        documents_upload_ui(req_id, user)

# ... (الجزء الأول من الدالة كما هو) ...

# استبدل الدالة القديمة في ملفك بـ:

@st.cache_data(ttl=180, show_spinner=False)
def _get_documents_cached(request_id):
    """جلب المستندات مع التخزين المؤقت"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    # التحويل إلى قائمة من القواميس لجعلها قابلة للتسلسل
    docs = [dict(row) for row in cur.fetchall()] 
    conn.close()
    return docs # الآن docs قائمة من القواميس، وهي قابلة للتسلسل

# ... (imports and other functions) ...

# في ملف waiting_list_contracts_app.py

def documents_upload_ui(request_id: int, user: dict, is_active_edit: bool = False):
    """واجهة رفع المستندات المطلوبة مع التحقق من رفع المستندات الإلزامية فقط."""
    st.markdown("<div class='subheader'>رفع المستندات المطلوبة</div>", unsafe_allow_html=True)
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    docs = cur.fetchall()
    conn.close()

    # ***تحديث مهم: متغير لتتبع ما إذا تم رفع كل المستندات المطلوبة فقط***
    # الآن يعتمد على القيمة الفعلية من قاعدة البيانات وليس على حالة مخزنة في الجلسة
    all_required_uploaded = True 
    
    for doc in docs:
        cols = st.columns([3, 3, 2, 2, 2])
        with cols[0]:
            st.write(f"**{doc['display_name'] or doc['doc_type']}**")
            # ***تحديث هنا: عرض الحالة الحالية من قاعدة البيانات***
            if doc['required']:
                 st.caption("مطلوب")
            else:
                 st.caption("اختياري")
        with cols[1]:
            # تحديد أنواع الملفات المسموحة بناءً على إعدادات المستند
            allowed_types = ['pdf']
            # التحقق من وجود العمود 'is_video_allowed' وقيمته بشكل آمن
            is_video_allowed_flag = doc['is_video_allowed'] if 'is_video_allowed' in doc.keys() else 0
            
            # ***تحديث مهم: التحقق مما إذا كان المستند مخصصًا فقط للفيديو***
            video_only = is_video_only_document(doc['doc_type'])
            
            if video_only:
                allowed_types = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
                st.caption("أنواع الملفات المسموحة: فيديو فقط (MP4, AVI, MOV, WMV, FLV, WEBM)")
            elif is_video_allowed_flag:
                allowed_types.extend(['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])
                st.caption("أنواع الملفات المسموحة: PDF ومقاطع فيديو (MP4, AVI, MOV, WMV, FLV, WEBM)")
            else:
                allowed_types = ['pdf']
                st.caption("أنواع الملفات المسموحة: PDF فقط")

            uploaded = st.file_uploader("رفع ملف", type=allowed_types, key=f"up_{doc['id']}")

            if uploaded is not None:
                # ***تحديث مهم: التحقق من نوع الملف المرفوع***
                if video_only:
                    if not check_file_type(uploaded.name, True): # يجب أن يكون فيديو
                        st.error("الرجاء رفع ملف فيديو فقط (MP4, AVI, MOV, WMV, FLV, WEBM)")
                    else:
                        save_uploaded_file(uploaded, user, request_id, doc)
                elif is_video_allowed_flag:
                    if not check_file_type(uploaded.name, True): # يمكن أن يكون PDF أو فيديو
                        st.error(f"الرجاء رفع ملف بصيغة {' أو '.join(allowed_types).upper()}")
                    else:
                        save_uploaded_file(uploaded, user, request_id, doc)
                else:
                    if not uploaded.name.lower().endswith('.pdf'): # يجب أن يكون PDF فقط
                        st.error("الرجاء رفع ملف PDF فقط")
                    else:
                        save_uploaded_file(uploaded, user, request_id, doc)

        with cols[2]:
            # === تحديث مهم: التحقق من وجود الملف قبل محاولة تنزيله ===
            # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
            if doc["file_path"]:
                try:
                    # التحقق من أن الملف موجود فعليًا على القرص
                    if os.path.exists(doc["file_path"]):
                        # إذا كان موجودًا، عرض زر التنزيل
                        with open(doc["file_path"], "rb") as f:
                            st.download_button("تنزيل", data=f.read(), file_name=os.path.basename(doc["file_path"]), key=f"dl_{doc['id']}")
                    else:
                        # إذا لم يكن موجودًا، عرض رسالة للمستخدم
                        st.warning("⚠️ الملف غير متوفر على القرص. يرجى رفع ملف جديد.")
                        # ***تحديث مهم: مسح مسار الملف من قاعدة البيانات***
                        # لأن الملف غير موجود فعليًا، من الأفضل مسح المسار المخزن في قاعدة البيانات
                        # لتجنب محاولة الوصول إليه مرة أخرى في المستقبل
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (doc["id"],))
                        conn.commit()
                        conn.close()
                        # إعادة تحميل الصفحة لتحديث العرض
                        st.rerun()
                except Exception as e:
                    # في حالة حدوث أي خطأ آخر أثناء محاولة الوصول إلى الملف
                    st.error(f"❌ خطأ في الوصول إلى الملف: {e}")
                    # مسح المسار المخزن في قاعدة البيانات
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (doc["id"],))
                    conn.commit()
                    conn.close()
                    # إعادة تحميل الصفحة لتحديث العرض
                    st.rerun()
            # =========================================================
        with cols[3]:
            if doc["file_path"]:
                if st.button("حذف", key=f"del_{doc['id']}"):
                    try:
                        os.remove(doc["file_path"]) if os.path.exists(doc["file_path"]) else None
                    except Exception:
                        pass
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (doc["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
        with cols[4]:
            st.write("✅ مستوفى" if doc["satisfied"] else "❌ غير مستوفى")
            
            # ***تحديث مهم: التحقق من المستندات المطلوبة فقط***
            # فقط المستندات المطلوبة (required = 1) تؤثر على تمكين زر الحفظ
            # هذه القيمة تأتي الآن من قاعدة البيانات بعد التحديث بواسطة الأدمن
            if doc["required"] and not doc["file_path"]:
                all_required_uploaded = False # إذا كان مستند مطلوب غير مرفوع، قم بتعيين العلامة على False

    # ***تحديث مهم: عرض زر الحفظ فقط إذا كان في وضع التحرير النشط***
    if is_active_edit:
        # زر حفظ الطلب يصبح نشطًا فقط بعد رفع كل المستندات المطلوبة (التي required = 1)
        # المستندات الاختيارية (required = 0) لم تعد تمنع الحفظ
        if st.button("حفظ الطلب", disabled=not all_required_uploaded):
            # التحقق من المستندات المطلوبة لا يزال ضروريًا للحماية
            if not all_required_uploaded: 
                 st.error("لا يمكن حفظ الطلب: هناك مستندات مطلوبة لم يتم رفعها.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                # تحديث حالة الطلب إلى الحالة الافتراضية الأولى بعد الإنشاء
                # ***تحديث مهم: استخدام get_request_statuses() للحصول على القائمة الحالية***
                statuses = get_request_statuses()
                initial_status = statuses[0] if statuses else "جاري دراسة الطلب ومراجعة الأوراق"
                # تحديث الحالة و updated_at
                cur.execute("UPDATE requests SET status=?, updated_at=? WHERE id=?", (initial_status, datetime.now().isoformat(), request_id))
                conn.commit()
                conn.close()
                st.success("تم حفظ الطلب بنجاح. سيتم مراجعته من قبل الإدارة.")
                st.session_state.pop("active_request_id", None)
                # ***تحديث مهم: تنظيف علامة التحرير النشط***
                if f"editing_request_{request_id}" in st.session_state:
                    st.session_state.pop(f"editing_request_{request_id}", None)
                st.rerun() # إعادة التحميل لتحديث الواجهة
        elif not all_required_uploaded:
            # عرض رسالة فقط إذا كانت هناك مستندات مطلوبة ناقصة
            st.info("يرجى رفع جميع المستندات المطلوبة لتفعيل زر 'حفظ الطلب'.")
    # else:
    #     # إذا لم يكن في وضع التحرير النشط، لا تظهر زر الحفظ
    #     pass

# ... (دالة save_uploaded_file كما هي) ...


def save_uploaded_file(file, user: dict, request_id: int, doc_row):
    """حفظ ملف مرفوع من قبل المستخدم."""
    hospital_name = user["hospital_name"]
    # ***تحديث مهم: قصر أسماء الملفات لتجنب مشاكل المسار***
    dest_dir = STORAGE_DIR / safe_filename(hospital_name)[:50] / str(request_id) # قصر اسم المستشفى
    dest_dir.mkdir(parents=True, exist_ok=True)
    # ***تحديث مهم: الحفاظ على امتداد الملف الأصلي***
    fn = f"{safe_filename(doc_row['doc_type'])[:50]}{Path(file.name).suffix}" # قصر اسم نوع المستند واحتفاظ بالامتداد
    dest_path = dest_dir / fn
    try:
        with open(dest_path, "wb") as f:
            f.write(file.getbuffer())
        conn = get_conn()
        cur = conn.cursor()
        # تحديث updated_at في جدول documents
        cur.execute("""
            UPDATE documents
            SET file_name=?, file_path=?, uploaded_at=?
            WHERE id=?
        """, (fn, str(dest_path), datetime.now().isoformat(), doc_row["id"]))
        # تحديث updated_at في جدول requests أيضًا
        cur.execute("UPDATE requests SET updated_at=? WHERE id=?", (datetime.now().isoformat(), request_id))
        conn.commit()
        conn.close()
        st.success(f"تم رفع الملف: {fn}")
    except OSError as e:
        st.error(f"❌ فشل رفع الملف '{fn}': {e}")
        # محاولة حذف الملف الجزئي إن وجد
        if dest_path.exists():
            try:
                dest_path.unlink()
            except:
                pass


        
def save_uploaded_file(file, user: dict, request_id: int, doc_row):
    hospital_name = user["hospital_name"]
    dest_dir = STORAGE_DIR / safe_filename(hospital_name) / str(request_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    fn = f"{safe_filename(doc_row['doc_type'])}{Path(file.name).suffix}" # الحفاظ على امتداد الملف الأصلي
    dest_path = dest_dir / fn
    with open(dest_path, "wb") as f:
        f.write(file.getbuffer())
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE documents
        SET file_name=?, file_path=?, uploaded_at=?
        WHERE id=?
    """, (fn, str(dest_path), datetime.now().isoformat(), doc_row["id"]))
    conn.commit()
    conn.close()
    st.success(f"تم رفع الملف: {fn}")

def hospital_requests_ui(user: dict):
    st.markdown("<div class='subheader'>طلباتي</div>", unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    # عرض الطلبات بما في ذلك "طلب غير مكتمل"
    cur.execute("""
        SELECT r.id, s.name AS service_name, r.age_category, r.status, r.created_at, r.deleted_at
        FROM requests r
        JOIN services s ON s.id=r.service_id
        WHERE r.hospital_id=?
        ORDER BY r.created_at DESC
    """, (user["hospital_id"],))
    rows = cur.fetchall()
    conn.close()
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)
    if rows:
        req_ids = [r["id"] for r in rows]
        pick = st.selectbox("اختر طلبًا لإدارته", ["—"] + [str(i) for i in req_ids])
        if pick != "—":
            request_details_ui(int(pick), role="hospital")

# ... (الجزء العلوي من الدالة كما هو: استيراد البيانات وعرض معلومات الطلب) ...

# في ملف waiting_list_contracts_app.py

# في ملف waiting_list_contracts_app.py

def request_details_ui(request_id: int, role: str = "hospital"):
    """واجهة تفاصيل الطلب للمستخدم (المستشفى) مع التحكم في عرض زر الحفظ."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
               h.type AS hospital_type, s.name AS service_name
        FROM requests r
        JOIN hospitals h ON h.id=r.hospital_id
        JOIN services s ON s.id=r.service_id
        WHERE r.id=?
    """, (request_id,))
    r = cur.fetchone()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    docs = cur.fetchall()
    conn.close()

    if not r:
        st.error("الطلب غير موجود.")
        return

    st.markdown(f"<div class='subheader'>تفاصيل الطلب #{request_id}</div>", unsafe_allow_html=True)
    st.write(f"**المستشفى:** {r['hospital_name']} — ({r['hospital_code']}) — **النوع:** {r['hospital_type']} — **الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']}")

    # === إضافة عرض تواريخ الطلب ===
    try:
        # التأكد من أن created_at و updated_at كائنات datetime
        created_at_dt = r['created_at']
        if isinstance(created_at_dt, str):
            created_at_dt = datetime.fromisoformat(created_at_dt)
            
        info_text = f"**تاريخ التقديم:** {created_at_dt.strftime('%Y-%m-%d %H:%M:%S')}"

        if r['updated_at']:
            updated_at_dt = r['updated_at']
            # التأكد من أنه كائن datetime
            if isinstance(updated_at_dt, str):
                updated_at_dt = datetime.fromisoformat(updated_at_dt)
                
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

    # السماح بالتعديل/الحذف فقط إذا كانت الحالة "طلب غير مكتمل" أو حالات محددة أخرى
    can_edit = r['status'] in ["طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "يجب استيفاء متطلبات التعاقد"]

    if can_edit and role == "hospital":
        st.info("يمكنك تعديل أو حذف هذا الطلب لأن حالته 'طلب غير مكتمل' أو 'جارى دراسة الطلب ومراجعة الأوراق' أو 'يجب استيفاء متطلبات التعاقد'")
        col_del_edit, col_save_cancel = st.columns([1, 1])
        with col_del_edit:
            if st.button("🗑️ حذف الطلب"):
                for d in docs:
                    if d['file_path'] and os.path.exists(d['file_path']):
                        try:
                            os.remove(d['file_path'])
                        except Exception:
                            pass
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("DELETE FROM documents WHERE request_id=?", (request_id,))
                cur.execute("DELETE FROM requests WHERE id=?", (request_id,))
                conn.commit()
                conn.close()
                st.success("تم حذف الطلب بنجاح")
                # تنظيف متغيرات الجلسة
                st.session_state.pop("active_request_id", None)
                if f"editing_request_{request_id}" in st.session_state:
                    st.session_state.pop(f"editing_request_{request_id}", None)
                st.rerun()
            if st.button("✏️ تعديل الطلب"):
                # ***تحديث مهم: تعيين علامة التحرير النشط***
                st.session_state[f"editing_request_{request_id}"] = True
                st.session_state["active_request_id"] = request_id
                st.rerun()
        
        # ***تحديث مهم: التحقق مما إذا كان المستخدم في وضع التحرير النشط***
        is_currently_editing = st.session_state.get(f"editing_request_{request_id}", False)
        
        # عرض واجهة رفع المستندات فقط إذا كان في وضع التحرير النشط
        if st.session_state.get("active_request_id") == request_id and is_currently_editing:
            # ***تحديث مهم: استدعاء documents_upload_ui مع تمرير علم is_active_edit=True***
            documents_upload_ui(request_id, st.session_state.user, is_active_edit=True)
        elif st.session_state.get("active_request_id") == request_id and not is_currently_editing:
            # إذا كان الطلب نشطًا ولكن ليس في وضع التحرير، أظهر رسالة
            st.info("لقد دخلت إلى واجهة تحرير الطلب. يرجى رفع المستندات المطلوبة ثم النقر على 'حفظ الطلب'.")
            # عرض واجهة رفع المستندات بدون زر الحفظ النشط
            documents_upload_ui(request_id, st.session_state.user, is_active_edit=False)
    else:
        st.markdown("##### المستندات")
        for d in docs:
            c1, c2, c3, c4, c5 = st.columns([3,2,2,2,3])
            with c1:
                display_name = d['display_name'] or d['doc_type']
                st.write(display_name)
                st.caption("مطلوب" if d['required'] else "اختياري")
            with c2:
                # === تحديث مهم: التحقق من وجود الملف قبل محاولة تنزيله ===
                # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
                if d["file_path"]:
                    try:
                        # التحقق من أن الملف موجود فعليًا على القرص
                        if os.path.exists(d["file_path"]):
                            # إذا كان موجودًا، عرض زر التنزيل
                            with open(d["file_path"], "rb") as f:
                                st.download_button("تنزيل", data=f.read(), file_name=os.path.basename(d["file_path"]), key=f"dl_req_{d['id']}")
                        else:
                            # إذا لم يكن موجودًا، عرض رسالة للمستخدم
                            st.warning("⚠️ الملف غير متوفر على القرص.")
                            # ***تحديث مهم: مسح مسار الملف من قاعدة البيانات***
                            # لأن الملف غير موجود فعليًا، من الأفضل مسح المسار المخزن في قاعدة البيانات
                            # لتجنب محاولة الوصول إليه مرة أخرى في المستقبل
                            conn = get_conn()
                            cur = conn.cursor()
                            cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                            conn.commit()
                            conn.close()
                            # إعادة تحميل الصفحة لتحديث العرض
                            st.rerun()
                    except Exception as e:
                        # في حالة حدوث أي خطأ آخر أثناء محاولة الوصول إلى الملف
                        st.error(f"❌ خطأ في الوصول إلى الملف: {e}")
                        # مسح المسار المخزن في قاعدة البيانات
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                        conn.commit()
                        conn.close()
                        # إعادة تحميل الصفحة لتحديث العرض
                        st.rerun()
                # =========================================================
            with c3:
                st.write("✅ مستوفى" if d["satisfied"] else "❌ غير مستوفى")
            with c4:
                # === تحديث مهم: التحقق من تواريخ المستندات ===
                try:
                    uploaded_at_dt = d['uploaded_at']
                    if isinstance(uploaded_at_dt, str):
                        uploaded_at_dt = datetime.fromisoformat(uploaded_at_dt)
                    st.write(uploaded_at_dt.strftime('%Y-%m-%d %H:%M:%S') if uploaded_at_dt else "—")
                except Exception:
                    st.write(d['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S') if d['uploaded_at'] else "—")
                # =========================================================
            with c5:
                st.write(d['admin_comment'] or "")

    # ... (إجراءات الطلب: حذف نهائي، استرجاع، إغلاق) ...





def resources_download_ui():
    st.markdown("<div class='subheader'>ملفات متوفرة للتنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك تنزيل الملفات التالية لمساعدتك في عملية التقديم</div>", unsafe_allow_html=True)
    RESOURCES_DIR.mkdir(exist_ok=True)
    for filename in RESOURCE_FILES:
        filepath = RESOURCES_DIR / filename
        if filepath.exists():
            with open(filepath, "rb") as f:
                st.download_button(
                    label=f"📥 {filename}",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
        else:
            st.warning(f"الملف غير متوفر: {filename}")

# ... (تستمر في القسم التالي)
# ... (متابعة من القسم 4)

@st.cache_data(ttl=300, show_spinner=False)
def get_requests_data(hospital_id=None, filters=None):
    """جلب بيانات الطلبات مع التخزين المؤقت"""
    conn = get_conn()
    cur = conn.cursor()
    
    if hospital_id:  # للطلبات الخاصة بالمستشفى
        cur.execute("""
            SELECT r.id, s.name AS service_name, r.age_category, r.status, r.created_at, r.deleted_at
            FROM requests r
            JOIN services s ON s.id=r.service_id
            WHERE r.hospital_id=?
            ORDER BY r.created_at DESC
            LIMIT 100
        """, (hospital_id,))
    else:  # لجميع الطلبات (للأدمن)
        q = """SELECT r.id, h.name AS hospital, h.code AS code, h.type AS hospital_type,
                      s.name AS service, r.age_category, r.status, r.created_at, r.deleted_at
               FROM requests r
               JOIN hospitals h ON h.id=r.hospital_id
               JOIN services s ON s.id=r.service_id
               WHERE 1=1"""
        params = []
        
        if filters:
            if filters.get('show_deleted') == False:
                q += " AND r.deleted_at IS NULL"
            if filters.get('status') and filters['status'] != "الكل":
                q += " AND r.status=?"
                params.append(filters['status'])
        
        q += " ORDER BY r.created_at DESC LIMIT 200"
        cur.execute(q, tuple(params))
    
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
@st.cache_data(ttl=600, show_spinner=False)
def get_statistics_data(filters=None):
    """جلب بيانات الإحصائيات مع التخزين المؤقت"""
    conn = get_conn()
    cur = conn.cursor()
    
    where_conditions = ["r.deleted_at IS NULL"]
    params = []
    
    if filters:
        if filters.get('sector') and filters['sector'] != "الكل":
            where_conditions.append("h.sector = ?")
            params.append(filters['sector'])
    
    where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
    
    query_status = f"""
        SELECT r.status, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        WHERE {where_clause}
        GROUP BY r.status
        ORDER BY count DESC
        LIMIT 20
    """
    
    cur.execute(query_status, params)
    status_stats = cur.fetchall()
    
    conn.close()
    return {
        'status_stats': [dict(row) for row in status_stats],
    }
def admin_home():
    user = st.session_state.user
    logo_path_sidebar_admin = Path("static/logo.png")
    if logo_path_sidebar_admin.exists():
        st.sidebar.image(str(logo_path_sidebar_admin), width=80)
    st.markdown("<div class='header'><h2>لوحة التحكم - الأدمن/المراجع</h2></div>", unsafe_allow_html=True)
    if user["role"] == "admin":
        menu = st.sidebar.radio("القائمة", [
            "🏥 إدارة المستشفيات",
            "🧾 إدارة الطلبات",
            "📊 الإحصائيات",
            "🗂️ الطلبات المحذوفة",
            "🧩 إدارة الخدمات والأنواع",
            "👥 إدارة المستخدمين",
            "📥 ملفات متوفرة للتنزيل",
            "🚪 تسجيل الخروج",
        ])
    else: # reviewer
        menu = st.sidebar.radio("القائمة", [
            "🧾 مراجعة الطلبات",
            "📊 الإحصائيات",
            "🗂️ الطلبات المحذوفة",
            "📥 ملفات متوفرة للتنزيل",
            "🚪 تسجيل الخروج",
        ])
    if menu == "🏥 إدارة المستشفيات":
        admin_hospitals_ui()
    elif menu == "🧾 إدارة الطلبات" or menu == "🧾 مراجعة الطلبات":
        admin_requests_ui()
    elif menu == "📊 الإحصائيات":
        admin_statistics_ui()
    elif menu == "🗂️ الطلبات المحذوفة":
        admin_deleted_ui()
    elif menu == "🧩 إدارة الخدمات والأنواع":
        admin_lists_ui()
    elif menu == "👥 إدارة المستخدمين":
        admin_users_ui()
    elif menu == "📥 ملفات متوفرة للتنزيل":
        admin_resources_ui()
    elif menu == "🚪 تسجيل الخروج":
        st.session_state.pop("user", None)
        st.rerun()

def admin_hospitals_ui():
    st.markdown("<div class='subheader'>إدارة المستشفيات</div>", unsafe_allow_html=True)
    # استيراد من Excel
    st.markdown("#### 🔽 استيراد من ملف Excel")
    excel = st.file_uploader("اختر ملف Excel Sheet يحتوي: اسم المستشفى، القطاع، المحافظة، الكود، النوع", type=["xlsx", "xls"])
    if excel is not None:
        try:
            df = pd.read_excel(excel, sheet_name=0) # 0 تعني الورقة الأولى
            required_cols = ["اسم المستشفى", "القطاع", "المحافظه", "كود المستشفى"]
            for c in required_cols:
                if c not in df.columns:
                    st.error(f"العمود المطلوب مفقود: {c}")
                    return
            if "نوع المستشفى" not in df.columns:
                df["نوع المستشفى"] = "خاص"
            # توليد أسماء مستخدمين وكلمات مرور
            df["username"] = df["اسم المستشفى"].apply(generate_username)
            df["password"] = "1234"  # كلمة مرور افتراضية
            conn = get_conn()
            cur = conn.cursor()
            added, skipped = 0, 0
            for _, row in df.iterrows():
                try:
                    username = row["username"]
                    # تأكد من تفرّد اسم المستخدم
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
                        hash_pw(str(row["password"]).strip()),
                    ))
                    if cur.rowcount:
                        added += 1
                    else:
                        skipped += 1
                except Exception as e:
                    st.warning(f"تخطي صف: {e}")
            conn.commit()
            conn.close()
            st.success(f"تمت إضافة: {added} — تم التخطي (موجود): {skipped}")
            # تصدير ملف الاعتمادات
            out_path = EXPORTS_DIR / f"credentials_{datetime.now().strftime('%Y%m%d_%H%M?')}.xlsx"
            df.to_excel(out_path, index=False)
            st.download_button("📥 تنزيل ملف الاعتمادات (username/password)", 
                             data=open(out_path, 'rb').read(), 
                             file_name=out_path.name)
        except Exception as e:
            st.error(f"فشل الاستيراد: {e}")
    # إضافة يدوية
    st.markdown("#### ➕ إضافة مستشفى يدويًا")
    with st.expander("إضافة مستشفى جديد"):
        with st.form("add_hospital"):
            name = st.text_input("اسم المستشفى")
            sector = st.text_input("القطاع", help="اختر من القائمة أو أدخل يدويًا")
            gov = st.text_input("المحافظة", help="اختر من القائمة أو أدخل يدويًا")
            code = st.text_input("كود المستشفى")
            htype = st.text_input("نوع المستشفى", help="اختر من القائمة أو أدخل يدويًا")
            username = st.text_input("اسم المستخدم (سيتم توليد تلقائيًا من الاسم إن فارغ)", value="")
            password = st.text_input("كلمة المرور", type="password", value="1234")
            submitted = st.form_submit_button("إضافة")
            if submitted:
                if not all([name, sector, gov, code, password]):
                    st.error("يرجى ملء الحقول المطلوبة")
                else:
                    if not username:
                        username = generate_username(name)
                        # تأكد من التفرّد
                        base_username = username
                        conn = get_conn()
                        counter = 1
                        while conn.execute("SELECT id FROM hospitals WHERE username=?", (username,)).fetchone():
                            username = f"{base_username}{counter}"
                            counter += 1
                        conn.close()
                    try:
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO hospitals (name, sector, governorate, code, type, username, password_hash)
                            VALUES (?,?,?,?,?,?,?)
                        """, (name, sector, gov, code, htype, username, hash_pw(password)))
                        conn.commit()
                        conn.close()
                        st.success(f"تمت الإضافة. اسم المستخدم: {username}")
                    except sqlite3.IntegrityError:
                        st.error("كود المستشفى أو اسم المستخدم موجود مسبقًا")
    # عرض القائمة
    st.markdown("#### 📋 قائمة المستشفيات")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals ORDER BY name")
    hospitals = cur.fetchall()
    conn.close()
    if hospitals:
        df = pd.DataFrame([dict(h) for h in hospitals])
        st.dataframe(
        df[["id", "name", "sector", "governorate", "code", "type", "username"]].style.set_properties(**{
            'background-color': '#f8f9fa',
            'color': 'black',
            'border': '1px solid #dee2e6',
            'font-family': 'Cairo, sans-serif'
        }).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#1e40af'), ('color', 'white'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('padding', '12px')]},
            {'selector': 'tr:hover', 'props': [('background-color', '#e2e8f0')]}
        ]),
        use_container_width=True,
        height=400  # ارتفاع ثابت مع شريط تمرير
    )
        # إنشاء قائمة منسدلة للمستشفيات
        hospital_options = ["—"] + [f"{h['id']} — {h['name']}" for h in hospitals]
        hid = st.selectbox("اختر مستشفى للتعديل", hospital_options)
        if hid != "—":
            hid_int = int(hid.split(" — ")[0])
            
            # إيجاد المستشفى المختار من القائمة المحملة باستخدام المعرف
            selected_hospital_record = None
            for h in hospitals:
                if h['id'] == hid_int:
                    selected_hospital_record = h
                    break
            
            if selected_hospital_record:
                # --- إضافة زر حذف المستشفى ---
                st.markdown("---") # خط فاصل
                st.markdown(f"### إجراءات على المستشفى المحدد: {selected_hospital_record['name']}") # عرض اسم المستشفى الصحيح
                
                # استخدام expander لتجميع خيارات التعديل والحذف
                with st.expander("عرض خيارات التعديل والحذف", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ تعديل بيانات المستشفى", key=f"edit_hospital_{hid_int}"):
                            edit_hospital_ui(hid_int)
                    
                    with col2:
                        # استخدام متغير جلسة لحالة تأكيد الحذف
                        confirm_key = f"confirm_delete_hospital_{hid_int}"
                        if st.button("🗑️ حذف هذا المستشفى", key=f"delete_hospital_button_{hid_int}"):
                            # عند الضغط على زر الحذف، نعرض رسالة تأكيد
                            st.session_state[confirm_key] = True
                            st.warning(f"هل أنت متأكد أنك تريد حذف المستشفى '{selected_hospital_record['name']}' وجميع طلباته؟ هذا الإجراء لا يمكن التراجع عنه.")
                        
                        # التحقق مما إذا كان المستخدم قد أكد الحذف
                        if st.session_state.get(confirm_key, False):
                            # عرض أزرار التأكيد وإلغاء الأمر
                            st.markdown("---")
                            st.markdown("### ⚠️ تأكيد الحذف")
                            confirm_col1, confirm_col2 = st.columns(2)
                            with confirm_col1:
                                if st.button("✅ نعم، قم بالحذف", key=f"confirm_yes_{hid_int}"):
                                    # تنفيذ عملية الحذف
                                    hospital_name = selected_hospital_record['name'] # الحصول على اسم المستشفى للرسالة
                                    try:
                                        conn = get_conn()
                                        cur = conn.cursor()
                                        # 1. حذف الطلبات المرتبطة بالمستشفى أولاً لتجنب مشاكل الـ Foreign Key
                                        cur.execute("DELETE FROM requests WHERE hospital_id = ?", (hid_int,))
                                        # 2. حذف المستشفى نفسه
                                        cur.execute("DELETE FROM hospitals WHERE id = ?", (hid_int,))
                                        conn.commit()
                                        conn.close()
                                        st.success(f"✅ تم حذف المستشفى '{hospital_name}' وجميع طلباته بنجاح.")
                                        # حذف مفتاح التأكيد من الجلسة
                                        if confirm_key in st.session_state:
                                            del st.session_state[confirm_key]
                                        # إعادة تحميل الصفحة لتحديث القائمة
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ حدث خطأ أثناء حذف المستشفى '{hospital_name}': {e}")
                                        if 'conn' in locals():
                                            conn.close()
                            with confirm_col2:
                                if st.button("❌ إلغاء", key=f"confirm_no_{hid_int}"):
                                    # إلغاء عملية الحذف
                                    if confirm_key in st.session_state:
                                        del st.session_state[confirm_key]
                                    st.info("تم إلغاء عملية الحذف.")
                                    # إعادة تحميل الصفحة لإزالة رسالة التحذير
                                    st.rerun()
            else:
                st.error("لم يتم العثور على المستشفى المحدد.")


def edit_hospital_ui(hospital_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals WHERE id=?", (hospital_id,))
    h = cur.fetchone()
    st.markdown(f"<div class='subheader'>تعديل: {h['name']}</div>", unsafe_allow_html=True)
    with st.form("edit_h"):
        name = st.text_input("اسم المستشفى", h["name"])
        sector = st.text_input("القطاع", h["sector"], help="اختر من القائمة أو أدخل يدويًا")
        gov = st.text_input("المحافظة", h["governorate"], help="اختر من القائمة أو أدخل يدويًا")
        code = st.text_input("كود المستشفى", h["code"])
        htype = st.text_input("نوع المستشفى", h["type"], help="اختر من القائمة أو أدخل يدويًا")
        address = st.text_area("العنوان بالكامل", h["address"] or "")
        other_br = st.text_input("الفروع الأخرى", h["other_branches"] or "")
        other_br_addr = st.text_area("عناوين الفروع الأخرى", h["other_branches_address"] or "")
        lic_start = st.date_input("بداية الترخيص", 
                                value=pd.to_datetime(h["license_start"]).date() if h["license_start"] else date.today())
        lic_end = st.date_input("نهاية الترخيص", 
                              value=pd.to_datetime(h["license_end"]).date() if h["license_end"] else date.today())
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
                params = [name, sector, gov, code, htype, address, other_br, other_br_addr, 
                         str(lic_start), str(lic_end), manager, manager_phone, license_no, username]
                if new_pw:
                    q += ", password_hash=?"
                    params.append(hash_pw(new_pw))
                q += " WHERE id=?"
                params.append(hospital_id)
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(q, tuple(params))
                conn.commit()
                conn.close()
                st.success("تم التعديل بنجاح")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("كود المستشفى أو اسم المستخدم مستخدم مسبقًا")

def admin_requests_ui():
    st.markdown("<div class='subheader'>إدارة الطلبات</div>", unsafe_allow_html=True)
    st.markdown("#### تصفية الطلبات")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM services ORDER BY name")
    services = cur.fetchall()
    service_options = ["الكل"] + [s["name"] for s in services]
    cur.execute("SELECT id, name FROM hospitals ORDER BY name")
    hospitals = cur.fetchall()
    hospital_options = ["الكل"] + [h["name"] for h in hospitals]
    
    # 获取所有唯一的部门 (sector) 用于筛选
    cur.execute("SELECT DISTINCT sector FROM hospitals ORDER BY sector")
    sectors = cur.fetchall()
    sector_filter_options = ["الكل"] + [s["sector"] for s in sectors]
    
    conn.close()

    # 创建筛选控件的列布局
    # 增加一列用于部门筛选，另一列用于日期范围
    col1, col2, col3, col4, col5, col6 = st.columns(6) 
    with col1:
        selected_service = st.selectbox("الخدمة", service_options)
    with col2:
        selected_hospital = st.selectbox("المستشفى", hospital_options)
    with col3:
        request_id_input = st.text_input("ID الطلب (رقم)")
    with col4:
        # 新增：按部门筛选
        selected_hospital_sector = st.selectbox("القطاع", sector_filter_options) 
    with col5:
        # 新增：开始日期
        start_date = st.date_input("تاريخ البدء", value=None, format="YYYY/MM/DD")
    with col6:
        # 新增：结束日期
        end_date = st.date_input("تاريخ الانتهاء", value=None, format="YYYY/MM/DD")

    # 现有的状态筛选和显示删除项选项
    # 为了布局清晰，可以将它们放在新的一行
    status_col, deleted_col = st.columns(2)
    with status_col:
        # استبعاد "طلب غير مكتمل" من عرض الطلبات للمراجعة إلا إذا تم طلبها صراحة
        status_options = ["الكل"] + [s for s in get_request_statuses() if s != "طلب غير مكتمل"] + ["طلب غير مكتمل"]
        status = st.selectbox("الحالة", status_options)
    with deleted_col:
        show_deleted = st.checkbox("عرض المحذوفات؟")

    # 构建 SQL 查询语句和参数
    q = """SELECT r.id, h.name AS hospital, h.code AS code, h.type AS hospital_type,
                  s.name AS service, r.age_category, r.status, r.created_at, r.deleted_at
           FROM requests r
           JOIN hospitals h ON h.id=r.hospital_id
           JOIN services s ON s.id=r.service_id
           WHERE 1=1""" # 使用 WHERE 1=1 作为基础，方便动态添加条件
    params = []
    
    # 应用现有筛选条件
    if not show_deleted:
        q += " AND r.deleted_at IS NULL"
    if status != "الكل":
        q += " AND r.status=?"
        params.append(status)
    if selected_service != "الكل":
        q += " AND s.name=?"
        params.append(selected_service)
    if selected_hospital != "الكل":
        q += " AND h.name=?"
        params.append(selected_hospital)
    if request_id_input and request_id_input.isdigit():
        q += " AND r.id=?"
        params.append(int(request_id_input))
        
    # 应用新增的筛选条件
    # 1. 按医院部门筛选
    if selected_hospital_sector != "الكل":
        q += " AND h.sector=?"
        params.append(selected_hospital_sector)
    # 2. 按提交日期范围筛选
    # 注意：数据库中 created_at 是 TEXT 类型，存储 ISO 格式字符串 (e.g., '2023-10-27T10:30:00.123456')
    # 我们可以使用 DATE() 函数提取日期部分进行比较
    if start_date:
        q += " AND DATE(r.created_at) >= ?"
        params.append(start_date.isoformat()) # 转换为 'YYYY-MM-DD' 字符串
    if end_date:
        q += " AND DATE(r.created_at) <= ?"
        params.append(end_date.isoformat()) # 转换为 'YYYY-MM-DD' 字符串

    # 添加排序
    q += " ORDER BY r.created_at DESC"

    # 执行查询
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    # 显示结果
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)
    
    if rows:
        pick = st.selectbox("اختر طلبًا لإدارته", ["—"] + [str(r["id"]) for r in rows])
        if pick != "—":
            admin_request_detail_ui(int(pick))


# ... (الجزء العلوي من الدالة كما هو: استيراد البيانات وعرض معلومات الطلب) ...

# ... (الجزء العلوي من الدالة كما هو: استيراد البيانات وعرض معلومات الطلب) ...

def admin_request_detail_ui(request_id: int):
    """واجهة تفاصيل الطلب للمراجع/الأدمن مع تحديث تاريخ التعديل."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
               h.type AS hospital_type, s.name AS service_name
        FROM requests r
        JOIN hospitals h ON h.id=r.hospital_id
        JOIN services s ON s.id=r.service_id
        WHERE r.id=?
    """, (request_id,))
    r = cur.fetchone()
    cur.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,))
    docs = cur.fetchall()
    conn.close()

    if not r:
        st.error("الطلب غير موجود.")
        return

    st.markdown(f"<div class='subheader'>إدارة الطلب #{request_id}</div>", unsafe_allow_html=True)
    st.write(f"**المستشفى:** {r['hospital_name']} — ({r['hospital_code']}) — **النوع:** {r['hospital_type']} — **الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']} — **الحالة الحالية:** {r['status']}")

    colA, colB = st.columns([2,3])
    with colA:
        current_statuses = get_request_statuses()
        new_status = st.selectbox("الحالة", current_statuses,
                                index=current_statuses.index(r['status']) if r['status'] in current_statuses else 0)
        note = st.text_area("ملاحظة إدارية", r['admin_note'] or "")
        if st.button("حفظ الحالة"):
            conn = get_conn()
            cur = conn.cursor()
            closed_at = None
            # تحديث updated_at مع كل تغيير
            updated_at = datetime.now().isoformat()
            
            # إذا كانت الحالة الجديدة نهائية، قم بتحديث closed_at
            if is_final_status(new_status):
                closed_at = datetime.now().isoformat()
                cur.execute("UPDATE requests SET status=?, admin_note=?, closed_at=?, updated_at=? WHERE id=?",
                           (new_status, note, closed_at, updated_at, request_id))
            else:
                # إذا تم تغيير الحالة من نهائية إلى غير نهائية، قم بمسح closed_at
                if r['closed_at'] and not is_final_status(new_status):
                     cur.execute("UPDATE requests SET status=?, admin_note=?, closed_at=NULL, updated_at=? WHERE id=?",
                                (new_status, note, updated_at, request_id))
                else:
                     cur.execute("UPDATE requests SET status=?, admin_note=?, updated_at=? WHERE id=?",
                                (new_status, note, updated_at, request_id))
            conn.commit()
            conn.close()
            st.success("تم الحفظ")
            st.rerun()
    with colB:
        if st.button("تنزيل كل الملفات (ZIP)"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for d in docs:
                    # === تحديث مهم: التحقق من وجود الملف قبل محاولة إضافته إلى ZIP ===
                    # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
                    if d['file_path'] and os.path.exists(d['file_path']):
                        try:
                            zf.write(d['file_path'], arcname=f"{safe_filename(d['doc_type'])}{Path(d['file_path']).suffix}")
                        except Exception as e:
                            # في حالة حدوث خطأ، تجاهل الملف وتابع
                            pass
                    # =========================================================
            buf.seek(0)
            st.download_button("📥 تحميل الملفات", data=buf,
                             file_name=f"request_{request_id}_files.zip")

    st.markdown("##### المستندات")
    for d in docs:
        c1, c2, c3, c4, c5, c6 = st.columns([3,2,2,2,3,3])
        with c1:
            display_name = d['display_name'] or d['doc_type']
            st.write(display_name)
            st.caption("مطلوب" if d['required'] else "اختياري")
            # ***تحديث مهم: إضافة checkbox لتعديل required من واجهة الأدمن***
            # هذا يتيح للأدمن تغيير حالة المستند من مطلوب إلى اختياري والعكس
            req_toggle_admin = st.checkbox("مطلوب؟", value=bool(d['required']), key=f"req_admin_{d['id']}")
        with c2:
            sat_toggle = st.checkbox("مستوفى؟", value=bool(d['satisfied']), key=f"sat_{d['id']}")
        with c3:
            # === تحديث مهم: التحقق من وجود الملف قبل محاولة تنزيله ===
            # هذا يمنع حدوث خطأ FileNotFoundError إذا تم حذف الملف fisically
            if d["file_path"]:
                try:
                    # التحقق من أن الملف موجود فعليًا على القرص
                    if os.path.exists(d["file_path"]):
                        # إذا كان موجودًا، عرض زر التنزيل
                        with open(d["file_path"], "rb") as f:
                            st.download_button("تنزيل", data=f.read(), file_name=os.path.basename(d["file_path"]), key=f"dl_admin_{d['id']}")
                    else:
                        # إذا لم يكن موجودًا، عرض رسالة للمستخدم
                        st.warning("⚠️ الملف غير متوفر على القرص.")
                        # ***تحديث مهم: مسح مسار الملف من قاعدة البيانات***
                        # لأن الملف غير موجود فعليًا، من الأفضل مسح المسار المخزن في قاعدة البيانات
                        # لتجنب محاولة الوصول إليه مرة أخرى في المستقبل
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                        conn.commit()
                        conn.close()
                        # إعادة تحميل الصفحة لتحديث العرض
                        st.rerun()
                except Exception as e:
                    # في حالة حدوث أي خطأ آخر أثناء محاولة الوصول إلى الملف
                    st.error(f"❌ خطأ في الوصول إلى الملف: {e}")
                    # مسح المسار المخزن في قاعدة البيانات
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                    conn.commit()
                    conn.close()
                    # إعادة تحميل الصفحة لتحديث العرض
                    st.rerun()
            # =========================================================
        with c4:
            if d["file_path"]:
                if st.button("حذف", key=f"del_{d['id']}"):
                    try:
                        os.remove(d["file_path"]) if os.path.exists(d["file_path"]) else None
                    except Exception:
                        pass
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE documents SET file_name=NULL, file_path=NULL WHERE id=?", (d["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
        with c5:
            comment = st.text_input("تعليق", value=d['admin_comment'] or "", key=f"cm_{d['id']}")
        with c6:
            if st.button("حفظ", key=f"save_{d['id']}"):
                conn = get_conn()
                cur = conn.cursor()
                # ***تحديث مهم: حفظ القيمة الجديدة لـ required من checkbox ***
                new_required_value = 1 if req_toggle_admin else 0
                cur.execute("""
                    UPDATE documents SET required=?, satisfied=?, admin_comment=? WHERE id=?
                """, (new_required_value, 1 if sat_toggle else 0, comment, d['id']))
                conn.commit()
                conn.close()
                st.success("تم التحديث")

    st.markdown("##### الإجراءات")
    cols = st.columns(3)
    with cols[0]:
        if st.button("❌ حذف الطلب نهائيًا"):
            for d in docs:
                if d['file_path'] and os.path.exists(d['file_path']):
                    try:
                        os.remove(d['file_path'])
                    except Exception:
                        pass
            conn = get_conn()
            cur = conn.cursor()
            # استخدام updated_at هنا أيضًا
            cur.execute("UPDATE requests SET deleted_at=?, updated_at=? WHERE id=?", (datetime.now().isoformat(), datetime.now().isoformat(), request_id))
            conn.commit()
            conn.close()
            st.success("تم الحذف النهائي. يمكن للمستشفى تقديم طلب جديد لنفس الخدمة الآن.")
            st.rerun()
    with cols[1]:
        if st.button("🔄 استرجاع كـ 'إعادة تقديم'"):
            conn = get_conn()
            cur = conn.cursor()
            # استخدام updated_at هنا أيضًا
            cur.execute("UPDATE requests SET status='إعادة تقديم', deleted_at=NULL, updated_at=? WHERE id=?", (datetime.now().isoformat(), request_id))
            conn.commit()
            conn.close()
            st.success("تم الاسترجاع")
            st.rerun()
    with cols[2]:
        if st.button("🔒 إغلاق الطلب"):
            conn = get_conn()
            cur = conn.cursor()
            final_status = "مغلق"
            # استخدام updated_at هنا أيضًا
            cur.execute("UPDATE requests SET status=?, closed_at=?, updated_at=? WHERE id=?", (final_status, datetime.now().isoformat(), datetime.now().isoformat(), request_id))
            conn.commit()
            conn.close()
            st.success("تم الإغلاق — يمكن تقديم طلب جديد")

# ... (الجزء السفلي من الدالة كما هو) ...


# ... (تستمر في القسم التالي)
# ... (متابعة من القسم 5)

def admin_deleted_ui():
    st.markdown("<div class='subheader'>الطلبات المحذوفة</div>", unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, h.name AS hospital, s.name AS service, r.age_category,
               r.status, r.created_at, r.deleted_at
        FROM requests r
        JOIN hospitals h ON h.id=r.hospital_id
        JOIN services s ON s.id=r.service_id
        WHERE r.deleted_at IS NOT NULL
        ORDER BY r.deleted_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    df = pd.DataFrame([dict(x) for x in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)

def admin_lists_ui():
    st.markdown("<div class='subheader'>إدارة الخدمات وأنواع المستشفيات</div>", unsafe_allow_html=True)

    # إدارة الخدمات
    st.markdown("#### 🧩 الخدمات")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM services ORDER BY active DESC, name")
    services = cur.fetchall()
    conn.close()
    for service in services:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(service['name'])
        with col2:
            status = "مفعلة" if service['active'] else "معطلة"
            st.write(status)
        with col3:
            if st.button("تغيير الحالة" if service['active'] else "تفعيل", key=f"toggle_{service['id']}"):
                conn = get_conn()
                cur = conn.cursor()
                new_status = 0 if service['active'] else 1
                cur.execute("UPDATE services SET active=? WHERE id=?", (new_status, service['id']))
                conn.commit()
                conn.close()
                st.success("تم تغيير الحالة")
                st.rerun()

    with st.form("add_service"):
        sname = st.text_input("إضافة خدمة جديدة")
        s_active = st.checkbox("مفعلة؟", value=True)
        sub = st.form_submit_button("إضافة الخدمة")
        if sub and sname:
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO services (name, active) VALUES (?,?)", (sname.strip(), 1 if s_active else 0))
                conn.commit()
                conn.close()
                st.success("تمت الإضافة")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("الخدمة موجودة مسبقًا")

    # إدارة أنواع المستشفيات
    st.markdown("#### 🏥 أنواع المستشفيات")
    types = get_hospital_types()
    editable = st.text_input("أنواع المستشفيات (مفصولة بفواصل)", ",".join(types))
    if st.button("حفظ الأنواع"):
        new_types = [t.strip() for t in editable.split(",") if t.strip()]
        if new_types:
            set_hospital_types(new_types)
            st.success("تم الحفظ")

    # إدارة القطاعات
    st.markdown("#### 🏢 القطاعات")
    sectors = get_sectors()
    editable_sectors = st.text_input("القطاعات (مفصولة بفواصل)", ",".join(sectors))
    if st.button("حفظ القطاعات"):
        new_sectors = [s.strip() for s in editable_sectors.split(",") if s.strip()]
        if new_sectors:
            set_sectors(new_sectors)
            st.success("تم الحفظ")

    # إدارة المحافظات
    st.markdown("#### 🗺️ المحافظات")
    gov = get_governorates()
    editable_gov = st.text_input("المحافظات (مفصولة بفواصل)", ",".join(gov))
    if st.button("حفظ المحافظات"):
        new_gov = [g.strip() for g in editable_gov.split(",") if g.strip()]
        if new_gov:
            set_governorates(new_gov)
            st.success("تم الحفظ")

    # إدارة حالات الطلبات (للأدمن فقط)
    st.markdown("#### 📋 حالات الطلبات (للأدمن فقط)")
    current_statuses = get_request_statuses()
    st.write("الحالات الحالية:")
    st.write(", ".join(current_statuses))

    # إضافة/تعديل حالة جديدة
    with st.form("add_edit_status"):
        new_status_name = st.text_input("اسم الحالة الجديدة أو تعديل الحالية")
        # تحميل الإعدادات الحالية للحالة المحددة (إن وجدت)
        selected_status_for_edit = st.selectbox("اختر حالة لتعديل إعداداتها", [""] + current_statuses)
        prevents_new = st.checkbox("يمنع تقديم طلب جديد لنفس الخدمة", value=False)
        blocks_days = st.number_input("يمنع تقديم طلب لنفس الخدمة لمدة (أيام) - 0 للتعطيل", min_value=0, value=0)
        is_final = st.checkbox("حالة نهائية (تغلق الطلب)", value=False)

        if st.form_submit_button("إضافة/تعديل الحالة"):
             if new_status_name:
                 conn = get_conn()
                 cur = conn.cursor()
                 try:
                     # إضافة أو تحديث اسم الحالة
                     cur.execute("INSERT OR IGNORE INTO request_statuses (name) VALUES (?)", (new_status_name,))
                     # تحديث الإعدادات
                     cur.execute("""
                         INSERT INTO status_settings (status_name, prevents_new_request, blocks_service_for_days, is_final_state)
                         VALUES (?, ?, ?, ?)
                         ON CONFLICT(status_name) DO UPDATE SET
                         prevents_new_request=excluded.prevents_new_request,
                         blocks_service_for_days=excluded.blocks_service_for_days,
                         is_final_state=excluded.is_final_state
                     """, (new_status_name, 1 if prevents_new else 0, blocks_days, 1 if is_final else 0))
                     conn.commit()
                     st.success(f"تمت إضافة أو تعديل الحالة: {new_status_name}")
                     st.rerun()
                 except Exception as e:
                     st.error(f"خطأ: {e}")
                 finally:
                     conn.close()
             else:
                 st.warning("يرجى إدخال اسم الحالة.")

    # حذف حالة
    with st.form("delete_status"):
         status_to_delete = st.selectbox("اختر حالة لحذفها", [""] + [s for s in current_statuses if s != "طلب غير مكتمل"]) # منع حذف الحالة الافتراضية المؤقتة
         if st.form_submit_button("حذف الحالة"):
             if status_to_delete:
                 conn = get_conn()
                 cur = conn.cursor()
                 try:
                     # التحقق مما إذا كانت الحالة مستخدمة في أي طلب
                     cur.execute("SELECT COUNT(*) as c FROM requests WHERE status = ?", (status_to_delete,))
                     count = cur.fetchone()['c']
                     if count > 0:
                         st.warning(f"لا يمكن حذف الحالة '{status_to_delete}' لأنها مستخدمة في {count} طلب(طلبات).")
                     else:
                         cur.execute("DELETE FROM status_settings WHERE status_name = ?", (status_to_delete,))
                         cur.execute("DELETE FROM request_statuses WHERE name = ?", (status_to_delete,))
                         conn.commit()
                         st.success(f"تم حذف الحالة: {status_to_delete}")
                         st.rerun()
                 except Exception as e:
                     st.error(f"خطأ: {e}")
                 finally:
                     conn.close()
             else:
                 st.warning("يرجى اختيار حالة للحذف.")

    # إدارة أنواع المستندات
    st.markdown("#### 📄 أنواع المستندات المطلوبة (للأدمن فقط)")
    doc_types = get_document_types()
    st.write("الأنواع الحالية:")
    # عرض المستندات مع إمكانية التعديل
    edited_docs = []
    for doc in doc_types:
        with st.expander(f"تعديل: {doc['display_name']} ({doc['name']})"):
            new_display_name = st.text_input("الاسم المعروض", value=doc['display_name'], key=f"display_{doc['name']}")
            new_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟", value=bool(doc['is_video_allowed']), key=f"video_{doc['name']}")
            edited_docs.append({
                'name': doc['name'],
                'display_name': new_display_name,
                'is_video_allowed': new_is_video_allowed
            })
            if st.button("حفظ التعديل", key=f"save_doc_{doc['name']}"):
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE document_types
                    SET display_name = ?, is_video_allowed = ?
                    WHERE name = ?
                """, (new_display_name, 1 if new_is_video_allowed else 0, doc['name']))
                conn.commit()
                conn.close()
                st.success("تم حفظ التعديل")
                st.rerun()

    # إضافة نوع مستند جديد
    with st.form("add_doc_type"):
        st.markdown("##### إضافة نوع مستند جديد")
        new_doc_name = st.text_input("الاسم الداخلي (لا يمكن تغييره لاحقًا)")
        new_doc_display_name = st.text_input("الاسم المعروض")
        new_doc_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟")
        if st.form_submit_button("إضافة نوع مستند"):
            if new_doc_name and new_doc_display_name:
                conn = get_conn()
                cur = conn.cursor()
                try:
                    cur.execute("""
                        INSERT INTO document_types (name, display_name, is_video_allowed)
                        VALUES (?, ?, ?)
                    """, (new_doc_name, new_doc_display_name, 1 if new_doc_is_video_allowed else 0))
                    conn.commit()
                    st.success("تمت إضافة نوع المستند")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("الاسم الداخلي موجود مسبقًا")
                except Exception as e:
                    st.error(f"خطأ: {e}")
                finally:
                    conn.close()
            else:
                st.warning("يرجى ملء الحقول المطلوبة.")

        # === إدارة المستندات الاختيارية لأنواع المستشفيات ===
    st.markdown("#### 📄 إدارة المستندات الاختيارية لأنواع المستشفيات")
    
    # الحصول على أنواع المستشفيات
    hospital_types = get_hospital_types()
    # الحصول على جميع المستندات المتاحة
    all_doc_names = DOC_TYPES 

    if not hospital_types:
        st.info("لا توجد أنواع مستشفيات معرفة. يرجى التأكد من تهيئتها أولاً.")
    else:
        # عرض واجهة لكل نوع مستشفى
        for htype in hospital_types:
            with st.expander(f"تعديل المستندات لـ {htype}", expanded=False):
                st.markdown(f"### {htype}")
                
                # جلب المستندات الاختيارية الحالية لهذا النوع من قاعدة البيانات
                current_optional_docs = get_optional_docs_for_type(htype)
                
                # استخدام multiselect لاختيار المستندات الاختيارية
                selected_optional_docs = st.multiselect(
                    f"اختر المستندات الاختيارية لـ {htype}",
                    options=all_doc_names,
                    default=list(current_optional_docs),
                    key=f"multiselect_optional_docs_{htype}" # مفتاح فريد
                )
                
                # زر حفظ التغييرات
                if st.button(f"💾 حفظ التغييرات لـ {htype}", key=f"save_button_{htype}"):
                    try:
                        # استدعاء الدالة المساعدة لتحديث قاعدة البيانات
                        set_optional_docs_for_type(htype, selected_optional_docs)
                        st.success(f"✅ تم حفظ المستندات الاختيارية لـ {htype}")
                        # إعادة تحميل الصفحة لعرض التغييرات فورًا
                        st.rerun() 
                    except Exception as e:
                        st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")
def admin_users_ui():
    st.markdown("<div class='subheader'>إدارة المستخدمين</div>", unsafe_allow_html=True)
    st.markdown("#### 👤 المستخدمون الإداريون")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM admins ORDER BY id")
    admins = cur.fetchall()
    conn.close()
    for admin in admins:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
             st.markdown(f"<div style='padding: 10px; font-family: Cairo, sans-serif;'><b>{admin['username']}</b> ({admin['role']})</div>", unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ حذف", key=f"del_admin_{admin['id']}", help="حذف المستخدم"):
                if admin['username'] != 'admin':
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM admins WHERE id=?", (admin['id'],))
                    conn.commit()
                    conn.close()
                    st.success("تم الحذف")
                    st.rerun()
                else:
                    st.warning("لا يمكن حذف المستخدم الافتراضي")
        with col3:
            if st.button("إعادة تعيين كلمة المرور", key=f"reset_admin_{admin['id']}"):
                conn = get_conn()
                cur = conn.cursor()
                new_password = "1234"
                cur.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new_password), admin['id']))
                conn.commit()
                conn.close()
                st.success(f"تمت إعادة تعيين كلمة المرور إلى: {new_password}")
        with col4:
            st.write("")
    st.markdown("#### ➕ إضافة مستخدم")
    with st.form("add_admin"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        role = st.selectbox("الدور", ["admin", "reviewer"])
        sub = st.form_submit_button("إضافة")
        if sub:
            try:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", (u, hash_pw(p), role))
                conn.commit()
                conn.close()
                st.success("تمت الإضافة")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("اسم المستخدم موجود مسبقًا")
    st.markdown("#### 🔁 إعادة تعيين كلمة المرور")
    with st.form("reset_password"):
        user_type = st.radio("نوع المستخدم", ["مستشفى", "إداري"])
        if user_type == "مستشفى":
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, name, username FROM hospitals ORDER BY name")
            hospitals = cur.fetchall()
            conn.close()
            selected_hospital = st.selectbox("اختر المستشفى", [f"{h['id']} - {h['name']} ({h['username']})" for h in hospitals])
            new_password = st.text_input("كلمة المرور الجديدة", type="password", value="1234")
        else:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, username FROM admins WHERE username != 'admin' ORDER BY username")
            admins = cur.fetchall()
            conn.close()
            if admins:
                selected_admin = st.selectbox("اختر المستخدم الإداري", [f"{a['id']} - {a['username']}" for a in admins])
                new_password = st.text_input("كلمة المرور الجديدة", type="password")
            else:
                st.info("لا يوجد مستخدمين إداريين لإعادة تعيين كلمات مرورهم")
                selected_admin = None
                new_password = ""
        reset_sub = st.form_submit_button("إعادة تعيين")
        if reset_sub:
            try:
                conn = get_conn()
                cur = conn.cursor()
                if user_type == "مستشفى":
                    if selected_hospital:
                        hospital_id = int(selected_hospital.split(" - ")[0])
                        cur.execute("UPDATE hospitals SET password_hash=? WHERE id=?", (hash_pw(new_password), hospital_id))
                        conn.commit()
                        st.success(f"تمت إعادة تعيين كلمة المرور للمستشفى: {selected_hospital}")
                else:
                    if selected_admin:
                        admin_id = int(selected_admin.split(" - ")[0])
                        cur.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new_password), admin_id))
                        conn.commit()
                        st.success(f"تمت إعادة تعيين كلمة المرور للمستخدم: {selected_admin}")
                conn.close()
            except Exception as e:
                st.error(f"حدث خطأ: {str(e)}")

def admin_statistics_ui():
    st.markdown("<div class='subheader'>الإحصائيات</div>", unsafe_allow_html=True)
    st.markdown("#### تصفية الإحصائيات")
    
    # التصفيه حسب الخصائص الأساسية
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_sector = st.selectbox("القطاع", ["الكل"] + get_sectors())
    with col2:
        selected_service = st.selectbox("الخدمة", ["الكل"] + DEFAULT_SERVICES)
    with col3:
        selected_type = st.selectbox("نوع المستشفى", ["الكل"] + DEFAULT_HOSPITAL_TYPES)
    with col4:
        selected_status = st.selectbox("الحالة", ["الكل"] + get_request_statuses())

    # التصفيه حسب التاريخ
    st.markdown("#### تصفية حسب التاريخ")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("من تاريخ", value=None)
    with date_col2:
        end_date = st.date_input("إلى تاريخ", value=None)

    # بناء شروط الاستعلام
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
    
    # إضافة التصفيه حسب التاريخ
    if start_date:
        where_conditions.append("DATE(r.created_at) >= ?")
        params.append(start_date.isoformat())
    if end_date:
        where_conditions.append("DATE(r.created_at) <= ?")
        params.append(end_date.isoformat())

    # بناء جملة WHERE بشكل صحيح
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    conn = get_conn()
    cur = conn.cursor()
    
    # استعلامات الإحصائيات
    query_status = f"""
        SELECT r.status, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY r.status
        ORDER BY count DESC
    """
    cur.execute(query_status, params)
    status_stats = cur.fetchall()
    
    query_service = f"""
        SELECT s.name, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY s.name
        ORDER BY count DESC
    """
    cur.execute(query_service, params)
    service_stats = cur.fetchall()
    
    query_type = f"""
        SELECT h.type, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY h.type
        ORDER BY count DESC
    """
    cur.execute(query_type, params)
    type_stats = cur.fetchall()
    
    query_sector = f"""
        SELECT h.sector, COUNT(*) as count
        FROM requests r
        JOIN hospitals h ON r.hospital_id = h.id
        JOIN services s ON r.service_id = s.id
        {where_clause}
        GROUP BY h.sector
        ORDER BY count DESC
    """
    cur.execute(query_sector, params)
    sector_stats = cur.fetchall()
    conn.close()

    # عرض الإحصائيات النصية
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
    
    # محاولة عرض الإحصائيات البيانية
    plotly_available = False
    try:
        import plotly.express as px
        plotly_available = True
    except ImportError:
        st.info("لم يتم تثبيت مكتبة 'plotly'. سيتم عرض الإحصائيات بشكل نصي فقط. لتثبيتها، قم بتشغيل الأمر: `pip install plotly`")

    if plotly_available:
        st.markdown("---")
        st.markdown("#### 📊 الإحصائيات البيانية")
        try:
            # تحويل النتائج إلى قوائم من القواميس
            status_data = [dict(row) for row in status_stats]
            type_data = [dict(row) for row in type_stats]
            service_data = [dict(row) for row in service_stats]
            sector_data = [dict(row) for row in sector_stats]

            # عرض الرسوم البيانية
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
                st.markdown("<div class='stats-header'>حسب الحالة</div>", unsafe_allow_html=True)
                if len(status_data) > 0:
                    try:
                        status_df = pd.DataFrame(status_data)
                        fig_status = px.pie(status_df, values='count', names='status', 
                                           title='توزيع الطلبات حسب الحالة',
                                           color_discrete_sequence=px.colors.sequential.Blues_r)
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
                        fig_type = px.bar(type_df, x='type', y='count', 
                                         title='عدد الطلبات حسب نوع المستشفى',
                                         color='type',
                                         color_discrete_sequence=['#1f77b4', '#ff7f0e'])
                        fig_type.update_layout(xaxis_title="نوع المستشفى", yaxis_title="العدد")
                        st.plotly_chart(fig_type, use_container_width=True)
                    except Exception as e:
                        st.warning(f"خطأ في إنشاء الرسم البياني: {e}")
                else:
                    st.info("لا توجد بيانات")
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"حدث خطأ أثناء إنشاء الرسوم البيانية: {e}")

def admin_resources_ui():
    st.markdown("<div class='subheader'>إدارة ملفات التنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك رفع الملفات التالية لجعلها متوفرة للمستخدمين</div>", unsafe_allow_html=True)
    RESOURCES_DIR.mkdir(exist_ok=True)
    for filename in RESOURCE_FILES:
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
                st.rerun()

# ---------------------------- وظائف عامة ---------------------------- #
def change_password_ui(role: str, hospital_id: int = None):
    with st.form(f"change_pw_{role}"):
        old = st.text_input("كلمة المرور الحالية", type="password")
        new1 = st.text_input("كلمة المرور الجديدة", type="password")
        new2 = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
        sub = st.form_submit_button("تغيير")
        if sub:
            if new1 != new2:
                st.error("كلمتا المرور غير متطابقتين")
                return
            if role == "admin" or role == "reviewer":
                u = st.session_state.user
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT * FROM admins WHERE id=? AND password_hash=?", (u["admin_id"], hash_pw(old)))
                row = cur.fetchone()
                if not row:
                    st.error("كلمة المرور الحالية غير صحيحة")
                else:
                    cur.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new1), u["admin_id"]))
                    conn.commit()
                    conn.close()
                    st.success("تم التغيير")
            else: # hospital
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT * FROM hospitals WHERE id=? AND password_hash=?", (hospital_id, hash_pw(old)))
                row = cur.fetchone()
                if not row:
                    st.error("كلمة المرور الحالية غير صحيحة")
                else:
                    cur.execute("UPDATE hospitals SET password_hash=? WHERE id=?", (hash_pw(new1), hospital_id))
                    conn.commit()
                    conn.close()
                    st.success("تم التغيير")

# ---------------------------- تشغيل التطبيق ---------------------------- #
def main():
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True
    )
    if 'db_version_checked' not in st.session_state:
        run_ddl()
        st.session_state.db_version_checked = True
    
    if "user" not in st.session_state:
        login_ui()
    else:
        if st.session_state.user.get("role") == "hospital":
            hospital_home()
        else:
            admin_home()
    
    # عرض التذييل
    st.markdown("""
    <div class='footer'>
        <p>© 2025 المشروع القومي لقوائم الانتظار - التعاقد على الخدمات الجراحية</p>
        <p>تم التصميم بواسطة الغرفه المركزيه لقوائم الانتظار</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()






>>>>>>> c1eda4bcb7d38bac1f4ede5574e65e32f596a9e6
