# -*- coding: utf-8 -*-
"""
نظام التعاقد على الخدمات الجراحية - المشروع القومي لقوائم الانتظار
---------------------------------------------------------------
برنامج ويب احترافي لإدارة طلبات التعاقد بين المستشفيات والمشروع القومي لقوائم الانتظار.
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

# ---------------------------- إعدادات أساسية ---------------------------- #
APP_TITLE = "المشروع القومي لقوائم الانتظار - التعاقد على الخدمات الجراحية"
DB_PATH = Path("data/app.db")
STORAGE_DIR = Path("storage")
EXPORTS_DIR = Path("exports")
RESOURCES_DIR = Path("static")

# إعداد نظام تجزئة كلمة المرور البسيط والموثوق
def secure_hash(password: str, salt: str = None) -> str:
    """إنشاء تجزئة آمنة لكلمة المرور مع salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    combined = f"{salt}:{password}"
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return f"{salt}:{hash_obj.hexdigest()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """التحقق من كلمة المرور مقابل التجزئة المحفوظة"""
    try:
        if ':' not in stored_hash:
            # تجزئة قديمة بدون salt
            return stored_hash == old_hash_pw(password)
        
        salt, hash_part = stored_hash.split(':', 1)
        expected_hash = secure_hash(password, salt)
        return expected_hash == stored_hash
    except Exception:
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
    "تعليمات هامة.pdf",
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
    """Context manager for database connections."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()

def hash_pw(pw: str) -> str:
    """إنشاء تجزئة جديدة لكلمة المرور"""
    return secure_hash(pw)

def old_hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def check_file_type(filename: str, is_video_allowed: bool) -> bool:
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
    VIDEO_ONLY_DOCUMENTS = {"فيديو لغرف العمليات والإقامة"}
    return doc_type_name in VIDEO_ONLY_DOCUMENTS

def parse_date_safely(date_str: str, default_value=None):
    """محاولة تحويل نص إلى تاريخ بأمان، وإرجاع قيمة افتراضية عند الفشل."""
    if not date_str:
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

def get_hospital_types() -> list:
    return get_list_from_meta('hospital_types', DEFAULT_HOSPITAL_TYPES)

def set_hospital_types(types: list):
    with get_conn() as conn:
        conn.execute("INSERT INTO meta(key,value) VALUES('hospital_types', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (",".join(types),))
        conn.commit()

def get_sectors() -> list:
    return get_list_from_meta('sectors', DEFAULT_SECTORS)

def set_sectors(sectors: list):
    with get_conn() as conn:
        conn.execute("INSERT INTO meta(key,value) VALUES('sectors', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (",".join(sectors),))
        conn.commit()

def get_governorates() -> list:
    return get_list_from_meta('governorates', DEFAULT_GOVERNORATES)

def set_governorates(gov: list):
    with get_conn() as conn:
        conn.execute("INSERT INTO meta(key,value) VALUES('governorates', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (",".join(gov),))
        conn.commit()

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

def get_document_types() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT name, display_name, is_video_allowed FROM document_types ORDER BY name").fetchall()
        return [{'name': r['name'], 'display_name': r['display_name'], 'is_video_allowed': r['is_video_allowed']} for r in rows]

def get_optional_docs_for_type(hospital_type: str) -> set:
    with get_conn() as conn:
        rows = conn.execute("SELECT doc_name FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,)).fetchall()
        return {row['doc_name'] for row in rows}

def set_optional_docs_for_type(hospital_type: str, doc_names: list):
    with get_conn() as conn:
        conn.execute("DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?", (hospital_type,))
        if doc_names:
            conn.executemany("INSERT OR IGNORE INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", 
                             [(hospital_type, name) for name in doc_names if name])
        conn.commit()

def ensure_request_docs(request_id: int, hospital_type: str):
    with get_conn() as conn:
        existing = {r["doc_type"] for r in conn.execute("SELECT doc_type FROM documents WHERE request_id=?", (request_id,)).fetchall()}
        optional_docs = get_optional_docs_for_type(hospital_type)
        all_doc_types = [dt['name'] for dt in get_document_types()]
        docs_to_insert = []
        for dt_name in all_doc_types:
            if dt_name not in existing:
                required = 0 if dt_name in optional_docs else 1
                docs_to_insert.append((request_id, dt_name, dt_name, required, 0, None))
        if docs_to_insert:
            conn.executemany(
                "INSERT INTO documents (request_id, doc_type, display_name, required, satisfied, uploaded_at) VALUES (?,?,?,?,?,?)",
                docs_to_insert
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
        row = conn.execute("SELECT license_start, license_end, license_number, manager_name, manager_phone, address FROM hospitals WHERE id=?", (hospital_id,)).fetchone()
        if not row: return False
        required_fields = [row['license_start'], row['license_end'], row['license_number'], row['manager_name'], row['manager_phone'], row['address']]
        return all(field and str(field).strip() for field in required_fields)

# ---------------------------- إعداد قاعدة البيانات ---------------------------- #
DB_SCHEMA_VERSION = 4

def run_ddl():
    with get_conn() as conn:
        cur = conn.cursor()
        
        cur.execute("""CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'admin')""")
        cur.execute("""CREATE TABLE IF NOT EXISTS hospitals (id INTEGER PRIMARY KEY, name TEXT NOT NULL, sector TEXT, governorate TEXT, code TEXT UNIQUE, type TEXT DEFAULT 'خاص', address TEXT, other_branches TEXT, other_branches_address TEXT, license_start TEXT, license_end TEXT, manager_name TEXT, manager_phone TEXT, license_number TEXT, username TEXT UNIQUE, password_hash TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY, name TEXT UNIQUE, active INTEGER DEFAULT 1)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY, hospital_id INTEGER, service_id INTEGER, age_category TEXT, status TEXT DEFAULT 'طلب غير مكتمل', admin_note TEXT, created_at TEXT, deleted_at TEXT, closed_at TEXT, updated_at TEXT, FOREIGN KEY (hospital_id) REFERENCES hospitals(id), FOREIGN KEY (service_id) REFERENCES services(id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, request_id INTEGER, doc_type TEXT, display_name TEXT, file_name TEXT, file_path TEXT, required INTEGER DEFAULT 1, satisfied INTEGER DEFAULT 0, admin_comment TEXT, uploaded_at TEXT, is_video_allowed INTEGER DEFAULT 0, FOREIGN KEY (request_id) REFERENCES requests(id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS document_types (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL, description TEXT, is_video_allowed INTEGER DEFAULT 0)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS hospital_type_optional_docs (id INTEGER PRIMARY KEY, hospital_type TEXT NOT NULL, doc_name TEXT NOT NULL, UNIQUE(hospital_type, doc_name))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS meta (`key` TEXT PRIMARY KEY, value TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS request_statuses (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS status_settings (status_name TEXT PRIMARY KEY, prevents_new_request INTEGER DEFAULT 0, blocks_service_for_days INTEGER DEFAULT 0, is_final_state INTEGER DEFAULT 0, FOREIGN KEY (status_name) REFERENCES request_statuses(name) ON DELETE CASCADE)""")

        # --- إضافة جديدة: جدول سجل النشاط ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                username TEXT,
                user_role TEXT,
                action TEXT NOT NULL,
                details TEXT
            )""")
        def add_column_if_not_exists(table, column, definition):
            try:
                cur.execute(f"SELECT {column} FROM {table} LIMIT 1")
            except sqlite3.OperationalError:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        
        add_column_if_not_exists("requests", "updated_at", "TEXT")
        add_column_if_not_exists("requests", "closed_at", "TEXT")
        add_column_if_not_exists("documents", "is_video_allowed", "INTEGER DEFAULT 0")

        if cur.execute("SELECT COUNT(1) FROM admins").fetchone()[0] == 0:
            cur.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", ("admin", hash_pw("admin123"), "admin"))
        
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

        cur.execute("DELETE FROM hospital_type_optional_docs")
        cur.executemany("INSERT INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)", 
                        [("حكومي", d) for d in GOVERNMENT_OPTIONAL_DOCS] + [("خاص", d) for d in PRIVATE_OPTIONAL_DOCS])
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
            with get_conn() as conn:
                # البحث عن المستخدم (مستشفى أو إداري)
                hospital_user = conn.execute("SELECT * FROM hospitals WHERE username=?", (username,)).fetchone()
                admin_user = conn.execute("SELECT * FROM admins WHERE username=?", (username,)).fetchone()
                user_data = hospital_user or admin_user
                table_name = "hospitals" if hospital_user else "admins"

                if user_data:
                    # 1. التحقق من التجزئة القديمة (sha256) أولاً
                    if user_data['password_hash'] == old_hash_pw(password):
                        st.info("...جاري تحديث نظام الأمان")
                        new_bcrypt_hash = hash_pw(password)
                        conn.execute(f"UPDATE {table_name} SET password_hash=? WHERE id=?", (new_bcrypt_hash, user_data['id']))
                        conn.commit()
                        role = "hospital" if hospital_user else user_data["role"]
                        st.session_state.user = {"role": role, **dict(user_data)}
                        log_activity("تسجيل الدخول")
                        st.success("تم تسجيل الدخول وتحديث الأمان بنجاح")
                        st.rerun()
                    else:
                        # 2. إذا لم تكن التجزئة القديمة، حاول التحقق باستخدام النظام الجديد
                        if verify_password(password, user_data['password_hash']):
                            role = "hospital" if hospital_user else user_data["role"]
                            st.session_state.user = {"role": role, **dict(user_data)}
                            log_activity("تسجيل الدخول")
                            st.success("تم تسجيل الدخول بنجاح")
                            st.rerun()
                
                # تأخير بسيط لمنع هجمات التوقيت
                if not ('user' in st.session_state):
                    secure_hash("dummy_password_to_time_attack")
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
            license_start = st.date_input("بداية الترخيص", value=parse_date_safely(hospital['license_start']))
            license_number = st.text_input("رقم الترخيص", value=hospital['license_number'] or "")
            manager_name = st.text_input("مدير المستشفى", value=hospital['manager_name'] or "")
        with col4:
            license_end = st.date_input("نهاية الترخيص", value=parse_date_safely(hospital['license_end']))
            manager_phone = st.text_input("هاتف المدير", value=hospital['manager_phone'] or "")
            address = st.text_area("عنوان المستشفى", value=hospital['address'] or "", height=100)

        if st.form_submit_button("حفظ البيانات"):
            try:
                with get_conn() as conn:
                    conn.execute("""
                        UPDATE hospitals SET address=?, license_start=?, license_end=?, 
                        manager_name=?, manager_phone=?, license_number=? WHERE id=?
                    """, (address, str(license_start) if license_start else None, str(license_end) if license_end else None, 
                          manager_name, manager_phone, license_number, user["id"]))
                    conn.commit()
                st.session_state["profile_update_success"] = True # تعيين علامة النجاح
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

def hospital_new_request_ui(user: dict):
    """واجهة تقديم طلب تعاقد جديد للمستشفى مع إعادة التحميل الصحيحة."""
    if not is_hospital_profile_complete(user["id"]):  # تغيير hospital_id إلى id
        st.warning("⚠️ يجب إكمال بيانات المستشفى الأساسية أولاً (بداية الترخيص، نهاية الترخيص، رقم الترخيص، مدير المستشفى، هاتف المدير، عنوان المستشفى)")
        hospital_dashboard_ui(user)
        return

    with get_conn() as conn:
        cur = conn.cursor()
        services = conn.execute("SELECT id, name FROM services WHERE active=1 ORDER BY name").fetchall()

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
    """واجهة رفع المستندات المطلوبة مع التحقق من رفع المستندات الإلزامية فقط."""
    st.markdown("<div class='subheader'>رفع المستندات المطلوبة</div>", unsafe_allow_html=True)
    
    with get_conn() as conn:
        docs = conn.execute("SELECT * FROM documents WHERE request_id=? ORDER BY id", (request_id,)).fetchall()

    all_required_uploaded = all(doc['satisfied'] for doc in docs if doc['required'])
    
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
            is_video_allowed_flag = doc['is_video_allowed'] if 'is_video_allowed' in doc.keys() else 0
            
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
            render_file_downloader(doc, key_prefix=f"doc_upload_{doc['id']}")
        with cols[3]:
            if doc["file_path"]:
                if st.button("حذف", key=f"del_{doc['id']}"):
                    try:
                        os.remove(doc["file_path"]) if os.path.exists(doc["file_path"]) else None
                    except Exception:
                        pass
                    with get_conn() as conn:
                        conn.execute("UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?", (doc["id"],))
                        conn.commit()
                    st.rerun()
        with cols[4]:
            st.write("✅ مستوفى" if doc["satisfied"] else "❌ غير مستوفى")
            
    if is_active_edit:
        if st.button("حفظ الطلب", disabled=not all_required_uploaded):
            if not all_required_uploaded: 
                 st.error("لا يمكن حفظ الطلب: هناك مستندات مطلوبة لم يتم رفعها.")
            else:
                with get_conn() as conn:
                    statuses = get_request_statuses()
                    initial_status = statuses[0] if statuses else "جاري دراسة الطلب ومراجعة الأوراق"
                    conn.execute("UPDATE requests SET status=?, updated_at=? WHERE id=?", (initial_status, datetime.now().isoformat(), request_id))
                    conn.commit()
                log_activity("تقديم طلب مكتمل", f"طلب رقم: {request_id}")
                st.success("تم حفظ الطلب بنجاح. سيتم مراجعته من قبل الإدارة.")
                st.session_state.pop("active_request_id", None)
                if f"editing_request_{request_id}" in st.session_state:
                    st.session_state.pop(f"editing_request_{request_id}", None)
                st.rerun()
        elif not all_required_uploaded:
            st.info("يرجى رفع جميع المستندات المطلوبة لتفعيل زر 'حفظ الطلب'.")

# ... (دالة save_uploaded_file كما هي) ...
# تعديل دالة save_uploaded_file لتعمل بشكل أفضل
def save_uploaded_file(file, user: dict, request_id: int, doc_row):
    """حفظ ملف مرفوع من قبل المستخدم"""
    if file is None:
        return
    
    try:
        hospital_name = user["name"]
        dest_dir = STORAGE_DIR / safe_filename(hospital_name)[:50] / str(request_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # إنشاء اسم ملف آمن
        file_ext = Path(file.name).suffix.lower()
        fn = f"{safe_filename(doc_row['doc_type'])[:50]}{file_ext}"
        dest_path = dest_dir / fn

        # حفظ الملف
        with open(dest_path, "wb") as f:
            f.write(file.getbuffer())
            
        # تحديث قاعدة البيانات
        now_iso = datetime.now().isoformat()
        with get_conn() as conn:
            conn.execute(
                "UPDATE documents SET file_name=?, file_path=?, uploaded_at=?, satisfied=1 WHERE id=?",
                (fn, str(dest_path), now_iso, doc_row["id"])
            )
            conn.execute("UPDATE requests SET updated_at=? WHERE id=?", (now_iso, request_id))
            conn.commit()
        
        return True
        
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء حفظ الملف: {e}")
        return False

def render_file_downloader(doc: sqlite3.Row, key_prefix: str = "dl"):
    """دالة موحدة لعرض زر تنزيل الملف مع التحقق من وجوده."""
    if doc["file_path"]:
        try:
            file_path_obj = Path(doc["file_path"])
            if file_path_obj.exists() and file_path_obj.is_file():
                with open(file_path_obj, "rb") as f:
                    st.download_button("تنزيل", data=f.read(), file_name=file_path_obj.name, key=f"{key_prefix}_{doc['id']}")
            else:
                st.warning("⚠️ الملف غير موجود على الخادم.")
                # مسح المسار غير الصالح من قاعدة البيانات
                with get_conn() as conn:
                    conn.execute("UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?", (doc["id"],))
                    conn.commit()
                st.rerun()
        except Exception as e:
            st.error(f"❌ خطأ في الوصول للملف: {e}")
            with get_conn() as conn:
                conn.execute("UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?", (doc["id"],))
                conn.commit()
            st.rerun()
    else:
        st.caption("— لم يتم الرفع")

def hospital_requests_ui(user: dict):
    st.markdown("<div class='subheader'>طلباتي</div>", unsafe_allow_html=True)
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT r.id, s.name AS service_name, r.status, r.created_at, r.updated_at
            FROM requests r JOIN services s ON s.id=r.service_id
            WHERE r.hospital_id=? ORDER BY r.created_at DESC
        """, (user["id"],)).fetchall()

    if not rows:
        st.info("لا يوجد لديك طلبات حالية.")
        return

    df = pd.DataFrame([dict(r) for r in rows])
    st.dataframe(df, use_container_width=True)
    
    req_ids = [str(r["id"]) for r in rows]
    pick = st.selectbox("اختر طلبًا لعرض تفاصيله", ["—"] + req_ids)
    if pick != "—":
        request_details_ui(int(pick))

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
                for d in docs:
                    if d['file_path'] and os.path.exists(d['file_path']):
                        try:
                            os.remove(d['file_path'])
                        except Exception:
                            pass
                with get_conn() as conn:
                    conn.execute("DELETE FROM documents WHERE request_id=?", (request_id,))
                    conn.execute("DELETE FROM requests WHERE id=?", (request_id,))
                    conn.commit()
                log_activity("حذف طلب", f"طلب رقم: {request_id}")

                st.success("تم حذف الطلب بنجاح")
                # تنظيف متغيرات الجلسة
                st.session_state.pop("active_request_id", None)
                if f"editing_request_{request_id}" in st.session_state:
                    st.session_state.pop(f"editing_request_{request_id}", None)
                st.rerun()

    if can_edit and role == "hospital":
        if st.button("✏️ تعديل الطلب"):
            st.session_state[f"editing_request_{request_id}"] = True
            st.rerun()

    is_editing = st.session_state.get(f"editing_request_{request_id}", False)
    if is_editing:
        documents_upload_ui(request_id, st.session_state.user, is_active_edit=True)
    else:
        display_request_documents_readonly(docs)

def display_request_documents_readonly(docs: list):
    """دالة لعرض المستندات في وضع القراءة فقط."""
    st.markdown("##### المستندات")
    for d in docs:
        c1, c2, c3, c4, c5 = st.columns([3,2,2,2,3])
        with c1:
            display_name = d['display_name'] or d['doc_type']
            st.write(display_name)
            st.caption("مطلوب" if d['required'] else "اختياري")
        with c2:
            render_file_downloader(d, key_prefix=f"readonly_{d['id']}")
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
                            old_hash_pw(str(row["password"]).strip()), # استخدام التجزئة القديمة عند الاستيراد
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
            password = st.text_input("كلمة المرور", type="password", value="1234")
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
                            """, (name, sector, gov, code, htype, username, old_hash_pw(password))) # استخدام التجزئة القديمة عند الإضافة اليدوية
                            conn.commit()
                        st.success(f"تمت الإضافة. اسم المستخدم: {username}")
                    except sqlite3.IntegrityError:
                        st.error("كود المستشفى أو اسم المستخدم موجود مسبقًا")
    
    st.markdown("#### 📋 قائمة المستشفيات")
    with get_conn() as conn:
        hospitals = conn.execute("SELECT * FROM hospitals ORDER BY name").fetchall()
    
    if hospitals:
        df = pd.DataFrame([dict(h) for h in hospitals])
        st.dataframe(
            df[["id", "name", "sector", "governorate", "code", "type", "username"]],
            use_container_width=True,
            height=400
        )
        
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
        st.info("لا توجد مستشفيات مسجلة")

def edit_hospital_ui(hospital_id: int):
    with get_conn() as conn:
        h = conn.execute("SELECT * FROM hospitals WHERE id=?", (hospital_id,)).fetchone()

    if not h:
        st.error("المستشفى غير موجود.")
        return

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
        lic_start = st.date_input("بداية الترخيص", value=parse_date_safely(h["license_start"], default_value=date.today()))
        lic_end = st.date_input("نهاية الترخيص", value=parse_date_safely(h["license_end"], default_value=date.today()))
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
                         str(lic_start) if lic_start else None,
                         str(lic_end) if lic_end else None,
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

def admin_requests_ui():
    st.markdown("<div class='subheader'>إدارة الطلبات</div>", unsafe_allow_html=True)
    st.markdown("#### تصفية الطلبات")
    
    with get_conn() as conn:
        services = conn.execute("SELECT id, name FROM services ORDER BY name").fetchall()
        hospitals = conn.execute("SELECT id, name FROM hospitals ORDER BY name").fetchall()
        sectors = conn.execute("SELECT DISTINCT sector FROM hospitals ORDER BY sector").fetchall()

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

    q = """SELECT r.id, h.name AS hospital, h.code AS code, h.type AS hospital_type,
                  s.name AS service, r.age_category, r.status, r.created_at, r.deleted_at
           FROM requests r
           JOIN hospitals h ON h.id=r.hospital_id
           JOIN services s ON s.id=r.service_id
           WHERE 1=1"""
    params = []
    
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
        
    if selected_hospital_sector != "الكل":
        q += " AND h.sector=?"
        params.append(selected_hospital_sector)
    if start_date:
        q += " AND DATE(r.created_at) >= ?"
        params.append(start_date.isoformat())
    if end_date:
        q += " AND DATE(r.created_at) <= ?"
        params.append(end_date.isoformat()) 

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

    st.markdown(f"<div class='subheader'>إدارة الطلب #{request_id}</div>", unsafe_allow_html=True)
    st.write(f"**المستشفى:** {r['hospital_name']} — ({r['hospital_code']}) — **النوع:** {r['hospital_type']} — **الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']} — **الحالة الحالية:** {r['status']}")

    colA, colB = st.columns([2,3])
    with colA:
        current_statuses = get_request_statuses()
        new_status = st.selectbox("الحالة", current_statuses, index=current_statuses.index(r['status']) if r['status'] in current_statuses else 0)
        note = st.text_area("ملاحظة إدارية", r['admin_note'] or "")
        if st.button("حفظ الحالة"):
            with get_conn() as conn:
                closed_at = None
                updated_at = datetime.now().isoformat()
                
                if is_final_status(new_status):
                    closed_at = datetime.now().isoformat()
                    conn.execute("UPDATE requests SET status=?, admin_note=?, closed_at=?, updated_at=? WHERE id=?", (new_status, note, closed_at, updated_at, request_id))
                else:
                    if r['closed_at'] and not is_final_status(new_status):
                         conn.execute("UPDATE requests SET status=?, admin_note=?, closed_at=NULL, updated_at=? WHERE id=?", (new_status, note, updated_at, request_id))
                    else:
                         conn.execute("UPDATE requests SET status=?, admin_note=?, updated_at=? WHERE id=?", (new_status, note, updated_at, request_id))
                conn.commit()
            log_activity("تحديث حالة طلب", f"طلب رقم: {request_id}، الحالة الجديدة: {new_status}")
            st.success("تم الحفظ")
            st.rerun()
    with colB:
        if st.button("تنزيل كل الملفات (ZIP)"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for d in docs:
                    if d['file_path'] and os.path.exists(d['file_path']):
                        try:
                            zf.write(d['file_path'], arcname=f"{safe_filename(d['doc_type'])}{Path(d['file_path']).suffix}")
                        except Exception:
                            pass
            buf.seek(0)
            st.download_button("📥 تحميل الملفات", data=buf, file_name=f"request_{request_id}_files.zip")

    st.markdown("##### المستندات")
    for d in docs:
        c1, c2, c3, c4, c5, c6 = st.columns([3,2,2,2,3,3])
        with c1:
            display_name = d['display_name'] or d['doc_type']
            st.write(display_name)
            st.caption("مطلوب" if d['required'] else "اختياري")
            req_toggle_admin = st.checkbox("مطلوب؟", value=bool(d['required']), key=f"req_admin_{d['id']}")
        with c2:
            sat_toggle = st.checkbox("مستوفى؟", value=bool(d['satisfied']), key=f"sat_{d['id']}")
        with c3:
            if d["file_path"]:
                try:
                    if os.path.exists(d["file_path"]):
                        with open(d["file_path"], "rb") as f:
                            st.download_button("تنزيل", data=f.read(), file_name=os.path.basename(d["file_path"]), key=f"dl_admin_{d['id']}")
                    else:
                        st.warning("⚠️ الملف غير متوفر على القرص.")
                        with get_conn() as conn:
                            conn.execute("UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?", (d["id"],))
                            conn.commit()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ خطأ في الوصول إلى الملف: {e}")
                    with get_conn() as conn:
                        conn.execute("UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?", (d["id"],))
                        conn.commit()
                    st.rerun()
        with c4:
            if d["file_path"]:
                if st.button("حذف", key=f"del_{d['id']}"):
                    try:
                        os.remove(d["file_path"]) if os.path.exists(d["file_path"]) else None
                    except Exception:
                        pass
                    with get_conn() as conn:
                        conn.execute("UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?", (d["id"],))
                        conn.commit()
                    st.rerun()
        with c5:
            comment = st.text_input("تعليق", value=d['admin_comment'] or "", key=f"cm_{d['id']}")
        with c6:
            if st.button("حفظ", key=f"save_{d['id']}"):
                with get_conn() as conn:
                    new_required_value = 1 if req_toggle_admin else 0
                    conn.execute("UPDATE documents SET required=?, satisfied=?, admin_comment=? WHERE id=?", (new_required_value, 1 if sat_toggle else 0, comment, d['id']))
                    conn.commit()
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
            with get_conn() as conn:
                conn.execute("UPDATE requests SET deleted_at=?, updated_at=? WHERE id=?", (datetime.now().isoformat(), datetime.now().isoformat(), request_id))
                conn.commit()
            log_activity("حذف طلب نهائي", f"طلب رقم: {request_id}")
            st.success("تم الحذف النهائي. يمكن للمستشفى تقديم طلب جديد لنفس الخدمة الآن.")
            st.rerun()
    with cols[1]:
        if st.button("🔄 استرجاع كـ 'إعادة تقديم'"):
            with get_conn() as conn:
                conn.execute("UPDATE requests SET status='إعادة تقديم', deleted_at=NULL, updated_at=? WHERE id=?", (datetime.now().isoformat(), request_id))
                conn.commit()
            log_activity("استرجاع طلب", f"طلب رقم: {request_id}")
            st.success("تم الاسترجاع")
            st.rerun()
    with cols[2]:
        if st.button("🔒 إغلاق الطلب"):
            with get_conn() as conn:
                final_status = "مغلق"
                conn.execute("UPDATE requests SET status=?, closed_at=?, updated_at=? WHERE id=?", (final_status, datetime.now().isoformat(), datetime.now().isoformat(), request_id))
                conn.commit()
            log_activity("إغلاق طلب", f"طلب رقم: {request_id}")
            st.success("تم الإغلاق — يمكن تقديم طلب جديد")

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

def admin_statistics_ui():
    st.markdown("<div class='subheader'>الإحصائيات</div>", unsafe_allow_html=True)
    
    st.markdown("#### تصفية الإحصائيات")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sectors = get_sectors()
        selected_sector = st.selectbox("القطاع", ["الكل"] + sectors)
    
    with col2:
        with get_conn() as conn:
            services = [s['name'] for s in conn.execute("SELECT name FROM services WHERE active=1").fetchall()]
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

    st.markdown("#### 🏥 أنواع المستشفيات")
    types = get_hospital_types()
    editable = st.text_input("أنواع المستشفيات (مفصولة بفواصل)", ",".join(types))
    if st.button("حفظ الأنواع"):
        new_types = [t.strip() for t in editable.split(",") if t.strip()]
        if new_types:
            set_hospital_types(new_types)
            st.success("تم الحفظ")

    st.markdown("#### 🏢 القطاعات")
    sectors = get_sectors()
    editable_sectors = st.text_input("القطاعات (مفصولة بفواصل)", ",".join(sectors))
    if st.button("حفظ القطاعات"):
        new_sectors = [s.strip() for s in editable_sectors.split(",") if s.strip()]
        if new_sectors:
            set_sectors(new_sectors)
            st.success("تم الحفظ")

    st.markdown("#### 🗺️ المحافظات")
    gov = get_governorates()
    editable_gov = st.text_input("المحافظات (مفصولة بفواصل)", ",".join(gov))
    if st.button("حفظ المحافظات"):
        new_gov = [g.strip() for g in editable_gov.split(",") if g.strip()]
        if new_gov:
            set_governorates(new_gov)
            st.success("تم الحفظ")

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
                    conn.execute("UPDATE document_types SET display_name = ?, is_video_allowed = ? WHERE name = ?", (new_display_name, 1 if new_is_video_allowed else 0, doc['name']))
                    conn.commit()
                st.success("تم حفظ التعديل")
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
                        conn.execute("INSERT INTO document_types (name, display_name, is_video_allowed) VALUES (?, ?, ?)", (new_doc_name, new_doc_display_name, 1 if new_doc_is_video_allowed else 0))
                        conn.commit()
                    st.success("تمت إضافة نوع المستند")
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
                        st.success(f"✅ تم حفظ المستندات الاختيارية لـ {htype}")
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
                    new_password = "1234"
                    conn.execute("UPDATE admins SET password_hash=? WHERE id=?", (hash_pw(new_password), admin['id']))
                    conn.commit()
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
                with get_conn() as conn:
                    conn.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", (u, hash_pw(p), role))
                    conn.commit()
                st.success("تمت الإضافة")
                st.rerun()
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
            new_password = st.text_input("كلمة المرور الجديدة", type="password", value="1234")
            
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
                st.rerun()

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
                if user:
                    if verify_password(old_pw, user['password_hash']):
                        conn.execute(f"UPDATE {user_table} SET password_hash=? WHERE id=?", (hash_pw(new_pw1), user_id))
                        conn.commit()
                        st.success("تم تغيير كلمة المرور بنجاح.")
                        log_activity("تغيير كلمة المرور")
                        st.info("يرجى تسجيل الدخول مرة أخرى باستخدام كلمة المرور الجديدة.")
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error("كلمة المرور الحالية غير صحيحة.")
                else:
                    st.error("لم يتم العثور على المستخدم.")

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


    # تهيئة قاعدة البيانات إذا لزم الأمر
    if 'db_setup_done' not in st.session_state:
        try:
            run_ddl()
            st.session_state.db_setup_done = True
        except Exception as e:
            st.error(f"❌ خطأ في تهيئة النظام: {e}")
            return
    
    # التحقق من حالة تسجيل الدخول
    if "user" not in st.session_state:
        # عرض واجهة الدخول
        login_ui()
    else:
        # توجيه المستخدم بناءً على الدور
        role = st.session_state.user.get("role")
        
        # إضافة رسالة ترحيبية بسيطة
        if "welcome_shown" not in st.session_state:
            user_name = st.session_state.user.get("name", st.session_state.user.get("username", "المستخدم"))
            st.toast(f"مرحباً بعودتك {user_name}! 👋", icon="🏨")
            st.session_state.welcome_shown = True
        
        if role == "hospital":
            hospital_home()
        elif role in ["admin", "reviewer"]:
            admin_home()
        else:
            st.error("❌ دور المستخدم غير معروف")
            st.session_state.pop("user", None)
            st.rerun()
    
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
