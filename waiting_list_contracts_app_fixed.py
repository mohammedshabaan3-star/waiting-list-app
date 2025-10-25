# -*- coding: utf-8 -*-
"""
نظام التعاقد على الخدمات الجراحية - المشروع القومي لقوائم الانتظار
---------------------------------------------------------------
برنامج ويب احترافي لإدارة طلبات التعاقد بين المستشفيات والمشروع القومي لقوائم الانتظار.
النسخة المحسنة والمصححة - جاهزة للنشر على Windows Server
"""

import os
import re
import io
import zipfile
import hashlib
import base64
import sqlite3
import secrets
import time
import threading
from datetime import datetime, date, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from passlib.hash import bcrypt

# ---------------------------- إعدادات أساسية ---------------------------- #
APP_TITLE = "المشروع القومي لقوائم الانتظار - التعاقد على الخدمات الجراحية"
DB_PATH = Path("data/app.db")
STORAGE_DIR = Path("storage")
EXPORTS_DIR = Path("exports")
RESOURCES_DIR = Path("static")

# إعداد نظام تشفير آمن لكلمات المرور
def secure_hash(password: str) -> str:
    """إنشاء تجزئة آمنة لكلمة المرور باستخدام bcrypt"""
    try:
        return bcrypt.hash(password)
    except Exception as e:
        st.error(f"خطأ في تشفير كلمة المرور: {e}")
        raise

def verify_password(password: str, stored_hash: str) -> bool:
    """التحقق من كلمة المرور مقابل التجزئة المحفوظة"""
    try:
        if stored_hash.startswith('$2b$'):
            return bcrypt.verify(password, stored_hash)
        else:
            # للتوافق مع التجزئة القديمة
            return stored_hash == old_hash_pw(password)
    except Exception as e:
        st.error(f"خطأ في التحقق من كلمة المرور: {e}")
        return False

def old_hash_pw(pw: str) -> str:
    """التجزئة القديمة للتوافق مع البيانات الموجودة"""
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

# إنشاء المجلدات المطلوبة
for directory in [DB_PATH.parent, STORAGE_DIR, EXPORTS_DIR, RESOURCES_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        st.error(f"خطأ في إنشاء المجلد {directory}: {e}")

# ---------------------------- أنماط CSS مخصصة ---------------------------- #
CSS_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
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
    
    .stButton>button {
        background-color: #1a56db;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #1e40af;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
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
    
    section[data-testid="stSidebar"] {
        width: 320px !important;
        background: linear-gradient(180deg, #87CEEB 0%, #B0E2FF 50%, #87CEFA 100%);
        color: white;
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
</style>
"""

st.markdown(CSS_STYLES, unsafe_allow_html=True)

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
    "بورسعيد", "السويس", "شمال سيناء", "جنوب سيناء",
    "كفر الشيخ", "مطروح", "الاقصر", "قنا", "بني سويف"
]
DEFAULT_SERVICES = [
    "جراحة أورام", "زراعة كبد", "جراحة الأوعية الدموية والقسطرة الطرفية",
    "قسطرة قلبية", "قلب مفتوح", "زراعة قوقعة", "جراحة عيون",
    "قسطرة مخية", "جراحة مخ وأعصاب", "جراحة عظام", "زراعة كلى"
]
AGE_CATEGORIES = ["كبار", "أطفال", "كبار وأطفال"]
DEFAULT_REQUEST_STATUSES = [
    "جاري دراسة الطلب ومراجعة الأوراق", "جارِ المعاينة", "يجب استيفاء متطلبات التعاقد",
    "قيد الانتظار", "مقبول", "مرفوض", "إرجاء التعاقد", "لا يوجد حاجة للتعاقد",
    "مغلق", "إعادة تقديم", "طلب غير مكتمل"
]

DOC_TYPES = [
    "ترخيص العلاج الحر موضح به التخصصات",
    "ترخيص الوحدات",
    "صورة بطاقة ضريبية للمنشأة سارية",
    "صورة حديثة للسجل التجاري",
    "طلب موجه لمدير المشروع بالتخصصات المطلوب المشاركة بها",
    "بيان معتمد بالسعة الاستيعابية الشهرية لكل تخصص",
    "بيان بالأجهزة والتجهيزات الطبية",
    "قائمة بالجراحين والأطباء",
    "بيانات السادة الجراحين والأطباء",
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
    "أخرى"
]

GOVERNMENT_OPTIONAL_DOCS = {
    "ترخيص العلاج الحر موضح به التخصصات",
    "صورة بطاقة ضريبية للمنشأة سارية",
    "صورة حديثة للسجل التجاري",
    "أخرى",
    "تقييم مكافحة العدوى (ذاتي)"
}

PRIVATE_OPTIONAL_DOCS = {
    "أخرى",
    "تقييم مكافحة العدوى من الجهة التابع لها المستشفى"
}

RESOURCE_FILES = [
    "متطلبات التعاقد.pdf", "طريقة التسجيل.pdf", "تعليمات هامة.pdf",
    "القلب المفتوح.pdf", "القسطره القلبيه.pdf", "الاوعيه الدمويه والقسطره الطرفيه.pdf",
    "القسطره المخيه.pdf", "المخ والاعصاب.pdf", "الرمد.pdf",
    "العظام.pdf", "الاورام.pdf", "زراعة الكبد.pdf",
    "زراعة الكلى.pdf", "زراعة القوقعه.pdf"
]

# إعدادات الحالات
STATUS_SETTINGS_DEFAULTS = {
    "open": {"طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "جارِ المعاينة", 
             "يجب استيفاء متطلبات التعاقد", "قيد الانتظار", "مقبول"},
    "blocked": {"مرفوض", "إرجاء التعاقد"},
    "final": {"إعادة تقديم", "مقبول", "مرفوض", "مغلق", "إرجاء التعاقد", "لا يوجد حاجة للتعاقد"}
}

# ---------------------------- أدوات مساعدة ---------------------------- #
def generate_username(hospital_name: str) -> str:
    """توليد اسم مستخدم آمن من اسم المستشفى"""
    if not hospital_name or not isinstance(hospital_name, str):
        return "hospital"
    
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
        elif char.isalnum():
            english_name += char
        else:
            english_name += "_"
    
    words = re.split(r"[_\s\-]+", english_name.lower())
    valid_words = [word for word in words if word and word.isalnum()]
    username = "".join(valid_words[:3])
    
    username = re.sub(r"[^\w]", "", username)
    username = username.strip("_")
    
    if not username or username[0].isdigit():
        username = "hospital_" + username
    
    return username[:20] or "hospital"

@contextmanager
def get_conn():
    """Context manager محسن لاتصالات قاعدة البيانات"""
    conn = None
    try:
        conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=30.0
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        yield conn
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            time.sleep(0.1)
            try:
                conn = sqlite3.connect(
                    DB_PATH,
                    check_same_thread=False,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                    timeout=30.0
                )
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                yield conn
            except sqlite3.Error as retry_error:
                st.error(f"خطأ في الاتصال بقاعدة البيانات: {retry_error}")
                raise
        else:
            st.error(f"خطأ في قاعدة البيانات: {e}")
            raise
    except Exception as e:
        st.error(f"خطأ غير متوقع في قاعدة البيانات: {e}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except sqlite3.Error:
                pass

def safe_filename(name: str) -> str:
    """إنشاء اسم ملف آمن"""
    if not name or not isinstance(name, str):
        return "file"
    
    # إزالة الأحرف الخطيرة
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
    name = re.sub(r'\s+', '_', name).strip('._')
    
    # تجنب أسماء الملفات المحجوزة في Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
        'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    if name.upper() in reserved_names:
        name = f"_{name}"
    
    return name[:255] or "file"

def validate_file_path(file_path: Union[str, Path]) -> bool:
    """التحقق من أمان مسار الملف"""
    try:
        path = Path(file_path).resolve()
        storage_path = STORAGE_DIR.resolve()
        return str(path).startswith(str(storage_path))
    except (OSError, ValueError):
        return False

def check_file_type(filename: str, is_video_allowed: bool) -> bool:
    """التحقق من نوع الملف المسموح"""
    if not filename or not isinstance(filename, str):
        return False
    
    ext = Path(filename).suffix.lower()
    allowed_extensions = {'.pdf'}
    
    if is_video_allowed:
        allowed_extensions.update({'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'})
    
    return ext in allowed_extensions

def is_video_only_document(doc_type_name: str) -> bool:
    """التحقق من المستندات التي تتطلب فيديو فقط"""
    video_only_documents = {"فيديو لغرف العمليات والإقامة"}
    return doc_type_name in video_only_documents

def parse_date_safely(date_str: str, default_value: Optional[date] = None) -> Optional[date]:
    """تحويل آمن للنص إلى تاريخ"""
    if not date_str or date_str == "غير محدد":
        return default_value
    
    try:
        dt = pd.to_datetime(date_str, errors='coerce')
        return dt.date() if pd.notna(dt) else default_value
    except Exception:
        return default_value

# ---------------------------- وظائف مساعدة للإعدادات ---------------------------- #
@st.cache_data(ttl=3600)
def get_list_from_meta(key: str, default_list: List[str]) -> List[str]:
    """الحصول على قائمة من جدول meta"""
    try:
        with get_conn() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            if row and row["value"]:
                return [item.strip() for item in row["value"].split(",") if item.strip()]
            return default_list
    except Exception as e:
        st.error(f"خطأ في جلب البيانات من meta: {e}")
        return default_list

def get_hospital_types() -> List[str]:
    """الحصول على أنواع المستشفيات"""
    return get_list_from_meta('hospital_types', DEFAULT_HOSPITAL_TYPES)

def set_hospital_types(types: List[str]) -> None:
    """تحديث أنواع المستشفيات"""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO meta(key,value) VALUES('hospital_types', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(types),)
            )
            conn.commit()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"خطأ في تحديث أنواع المستشفيات: {e}")

def get_sectors() -> List[str]:
    """الحصول على القطاعات"""
    return get_list_from_meta('sectors', DEFAULT_SECTORS)

def set_sectors(sectors: List[str]) -> None:
    """تحديث القطاعات"""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO meta(key,value) VALUES('sectors', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(sectors),)
            )
            conn.commit()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"خطأ في تحديث القطاعات: {e}")

def get_governorates() -> List[str]:
    """الحصول على المحافظات"""
    return get_list_from_meta('governorates', DEFAULT_GOVERNORATES)

def set_governorates(gov: List[str]) -> None:
    """تحديث المحافظات"""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO meta(key,value) VALUES('governorates', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (",".join(gov),)
            )
            conn.commit()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"خطأ في تحديث المحافظات: {e}")

def get_request_statuses() -> List[str]:
    """الحصول على حالات الطلبات"""
    try:
        with get_conn() as conn:
            rows = conn.execute("SELECT name FROM request_statuses ORDER BY id").fetchall()
            return [row['name'] for row in rows] if rows else DEFAULT_REQUEST_STATUSES
    except Exception as e:
        st.error(f"خطأ في جلب حالات الطلبات: {e}")
        return DEFAULT_REQUEST_STATUSES

@st.cache_data(ttl=600)
def get_preventing_statuses() -> set:
    """الحصول على الحالات التي تمنع تقديم طلب جديد"""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT status_name FROM status_settings WHERE prevents_new_request = 1"
            ).fetchall()
            return {row['status_name'] for row in rows}
    except Exception as e:
        st.error(f"خطأ في جلب الحالات المانعة: {e}")
        return set()

@st.cache_data(ttl=600)
def get_blocking_statuses() -> set:
    """الحصول على الحالات التي تمنع التقديم لفترة معينة"""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT status_name FROM status_settings WHERE blocks_service_for_days > 0"
            ).fetchall()
            return {row['status_name'] for row in rows}
    except Exception as e:
        st.error(f"خطأ في جلب الحالات المحجوبة: {e}")
        return set()

def is_final_status(status: str) -> bool:
    """التحقق من كون الحالة نهائية"""
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT is_final_state FROM status_settings WHERE status_name = ?",
                (status,)
            ).fetchone()
            return row and row['is_final_state'] == 1
    except Exception as e:
        st.error(f"خطأ في التحقق من الحالة النهائية: {e}")
        return False

def get_document_types() -> List[Dict[str, Any]]:
    """الحصول على أنواع المستندات"""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT name, display_name, is_video_allowed FROM document_types ORDER BY name"
            ).fetchall()
            return [
                {
                    'name': r['name'],
                    'display_name': r['display_name'],
                    'is_video_allowed': r['is_video_allowed']
                }
                for r in rows
            ]
    except Exception as e:
        st.error(f"خطأ في جلب أنواع المستندات: {e}")
        return []

def get_optional_docs_for_type(hospital_type: str) -> set:
    """الحصول على المستندات الاختيارية لنوع المستشفى"""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT doc_name FROM hospital_type_optional_docs WHERE hospital_type = ?",
                (hospital_type,)
            ).fetchall()
            return {row['doc_name'] for row in rows}
    except Exception as e:
        st.error(f"خطأ في جلب المستندات الاختيارية: {e}")
        return set()

def set_optional_docs_for_type(hospital_type: str, doc_names: List[str]) -> None:
    """تحديث المستندات الاختيارية لنوع المستشفى"""
    try:
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM hospital_type_optional_docs WHERE hospital_type = ?",
                (hospital_type,)
            )
            if doc_names:
                conn.executemany(
                    "INSERT OR IGNORE INTO hospital_type_optional_docs "
                    "(hospital_type, doc_name) VALUES (?, ?)",
                    [(hospital_type, name) for name in doc_names if name]
                )
            conn.commit()
        
        update_existing_requests_optional_docs()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"خطأ في تحديث المستندات الاختيارية: {e}")

def update_existing_requests_optional_docs() -> None:
    """تحديث المستندات الاختيارية في الطلبات الموجودة"""
    try:
        with get_conn() as conn:
            hospital_types = get_hospital_types()
            for htype in hospital_types:
                optional_docs = get_optional_docs_for_type(htype)
                all_doc_names = [dt['name'] for dt in get_document_types()]
                
                requests = conn.execute(
                    "SELECT r.id FROM requests r JOIN hospitals h ON r.hospital_id = h.id "
                    "WHERE h.type = ? AND r.deleted_at IS NULL",
                    (htype,)
                ).fetchall()
                
                for req in requests:
                    for doc_name in all_doc_names:
                        is_required = 0 if doc_name in optional_docs else 1
                        conn.execute(
                            "UPDATE documents SET required = ? "
                            "WHERE request_id = ? AND doc_type = ?",
                            (is_required, req['id'], doc_name)
                        )
            
            conn.commit()
    except Exception as e:
        st.error(f"خطأ في تحديث المستندات الموجودة: {e}")

def ensure_request_docs(request_id: int, hospital_type: str) -> None:
    """ضمان وجود جميع المستندات المطلوبة للطلب"""
    try:
        with get_conn() as conn:
            existing = {
                r["doc_type"] for r in conn.execute(
                    "SELECT doc_type FROM documents WHERE request_id=?",
                    (request_id,)
                ).fetchall()
            }
            
            optional_docs = get_optional_docs_for_type(hospital_type)
            all_doc_types = get_document_types()
            docs_to_insert = []
            
            for dt in all_doc_types:
                dt_name = dt['name']
                if dt_name not in existing:
                    required = 0 if dt_name in optional_docs else 1
                    docs_to_insert.append((
                        request_id, dt_name, dt['display_name'], required, 0, None,
                        dt['is_video_allowed']
                    ))
            
            if docs_to_insert:
                conn.executemany(
                    "INSERT INTO documents "
                    "(request_id, doc_type, display_name, required, satisfied, uploaded_at, is_video_allowed) "
                    "VALUES (?,?,?,?,?,?,?)",
                    docs_to_insert
                )
            
            # تحديث المستندات الموجودة
            for dt in all_doc_types:
                dt_name = dt['name']
                if dt_name in existing:
                    required = 0 if dt_name in optional_docs else 1
                    conn.execute(
                        "UPDATE documents SET required = ?, display_name = ?, is_video_allowed = ? "
                        "WHERE request_id = ? AND doc_type = ?",
                        (required, dt['display_name'], dt['is_video_allowed'], request_id, dt_name)
                    )
            
            conn.commit()
    except Exception as e:
        st.error(f"خطأ في ضمان المستندات: {e}")

def hospital_has_open_request(hospital_id: int, service_id: int, prevented_statuses: set) -> bool:
    """التحقق من وجود طلب مفتوح لنفس الخدمة"""
    if not prevented_statuses:
        return False
    
    try:
        with get_conn() as conn:
            placeholders = ",".join(["?"] * len(prevented_statuses))
            query = f"""
                SELECT 1 FROM requests
                WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL 
                AND status IN ({placeholders})
                LIMIT 1
            """
            params = [hospital_id, service_id] + list(prevented_statuses)
            return conn.execute(query, params).fetchone() is not None
    except Exception as e:
        st.error(f"خطأ في التحقق من الطلبات المفتوحة: {e}")
        return False

def hospital_blocked_from_request(hospital_id: int, service_id: int, blocked_statuses: set) -> bool:
    """التحقق من منع المستشفى من تقديم طلب لفترة معينة"""
    if not blocked_statuses:
        return False
    
    try:
        with get_conn() as conn:
            three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
            placeholders = ",".join(["?"] * len(blocked_statuses))
            query = f"""
                SELECT 1 FROM requests
                WHERE hospital_id=? AND service_id=? AND deleted_at IS NULL 
                AND status IN ({placeholders}) AND closed_at > ?
                LIMIT 1
            """
            params = [hospital_id, service_id] + list(blocked_statuses) + [three_months_ago]
            return conn.execute(query, params).fetchone() is not None
    except Exception as e:
        st.error(f"خطأ في التحقق من الحجب: {e}")
        return False

def is_hospital_profile_complete(hospital_id: int) -> bool:
    """التحقق من اكتمال ملف المستشفى"""
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT license_start, license_end, license_number, manager_name, "
                "manager_phone, address, type FROM hospitals WHERE id=?",
                (hospital_id,)
            ).fetchone()
            
            if not row:
                return False
            
            if row['type'] == 'حكومي':
                required_fields = [row['manager_name'], row['manager_phone'], row['address']]
            else:
                required_fields = [
                    row['license_start'], row['license_number'],
                    row['manager_name'], row['manager_phone'], row['address']
                ]
            
            return all(field and str(field).strip() for field in required_fields)
    except Exception as e:
        st.error(f"خطأ في التحقق من اكتمال الملف: {e}")
        return False

# ---------------------------- نظام قاعدة البيانات ---------------------------- #
DB_SCHEMA_VERSION = 5

def get_current_schema_version() -> int:
    """الحصول على إصدار قاعدة البيانات الحالي"""
    try:
        with get_conn() as conn:
            result = conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'"
            ).fetchone()
            return int(result['value']) if result else 0
    except Exception:
        return 0

def set_schema_version(version: int) -> None:
    """تحديث إصدار قاعدة البيانات"""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
                (str(version),)
            )
            conn.commit()
    except Exception as e:
        st.error(f"خطأ في تحديث إصدار قاعدة البيانات: {e}")

def run_migrations() -> None:
    """تشغيل migrations لتحديث قاعدة البيانات"""
    try:
        current_version = get_current_schema_version()
        
        if current_version < DB_SCHEMA_VERSION:
            with get_conn() as conn:
                # إضافة جدول activity_log
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        username TEXT,
                        user_role TEXT,
                        action TEXT NOT NULL,
                        details TEXT
                    )
                """)
                
                # إضافة الفهارس لتحسين الأداء
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_hospital_service ON requests(hospital_id, service_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_request_id ON documents(request_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log(timestamp)")
                
                conn.commit()
                set_schema_version(DB_SCHEMA_VERSION)
    except Exception as e:
        st.error(f"خطأ في migrations: {e}")

def run_ddl() -> None:
    """إنشاء جداول قاعدة البيانات"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            # إنشاء الجداول الأساسية
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT DEFAULT 'admin'
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hospitals (
                    id INTEGER PRIMARY KEY,
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
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    active INTEGER DEFAULT 1
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY,
                    hospital_id INTEGER,
                    service_id INTEGER,
                    age_category TEXT,
                    status TEXT DEFAULT 'طلب غير مكتمل',
                    admin_note TEXT,
                    created_at TEXT,
                    deleted_at TEXT,
                    closed_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
                    FOREIGN KEY (service_id) REFERENCES services(id)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    request_id INTEGER,
                    doc_type TEXT,
                    display_name TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    required INTEGER DEFAULT 1,
                    satisfied INTEGER DEFAULT 0,
                    admin_comment TEXT,
                    uploaded_at TEXT,
                    is_video_allowed INTEGER DEFAULT 0,
                    FOREIGN KEY (request_id) REFERENCES requests(id)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_types (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    is_video_allowed INTEGER DEFAULT 0
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hospital_type_optional_docs (
                    id INTEGER PRIMARY KEY,
                    hospital_type TEXT NOT NULL,
                    doc_name TEXT NOT NULL,
                    UNIQUE(hospital_type, doc_name)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    `key` TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS request_statuses (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS status_settings (
                    status_name TEXT PRIMARY KEY,
                    prevents_new_request INTEGER DEFAULT 0,
                    blocks_service_for_days INTEGER DEFAULT 0,
                    is_final_state INTEGER DEFAULT 0,
                    FOREIGN KEY (status_name) REFERENCES request_statuses(name) ON DELETE CASCADE
                )
            """)
            
            # إدراج البيانات الأولية
            if cur.execute("SELECT COUNT(1) FROM admins").fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)",
                    ("admin", secure_hash("admin123"), "admin")
                )
            
            if cur.execute("SELECT COUNT(1) FROM services").fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO services (name) VALUES (?)",
                    [(s,) for s in DEFAULT_SERVICES]
                )
            
            if cur.execute("SELECT COUNT(1) FROM document_types").fetchone()[0] == 0:
                video_allowed = {"فيديو لغرف العمليات والإقامة"}
                cur.executemany(
                    "INSERT INTO document_types (name, display_name, is_video_allowed) VALUES (?, ?, ?)",
                    [(d, d, 1 if d in video_allowed else 0) for d in DOC_TYPES]
                )
            
            if cur.execute("SELECT COUNT(1) FROM request_statuses").fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO request_statuses (name) VALUES (?)",
                    [(s,) for s in DEFAULT_REQUEST_STATUSES]
                )
            
            if cur.execute("SELECT COUNT(1) FROM status_settings").fetchone()[0] == 0:
                open_statuses = STATUS_SETTINGS_DEFAULTS["open"]
                blocked_statuses = STATUS_SETTINGS_DEFAULTS["blocked"]
                final_statuses = STATUS_SETTINGS_DEFAULTS["final"]
                settings = [
                    (s, 1 if s in open_statuses else 0, 90 if s in blocked_statuses else 0,
                     1 if s in final_statuses else 0)
                    for s in DEFAULT_REQUEST_STATUSES
                ]
                cur.executemany("INSERT INTO status_settings VALUES (?, ?, ?, ?)", settings)
            
            if cur.execute("SELECT COUNT(1) FROM hospital_type_optional_docs").fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO hospital_type_optional_docs (hospital_type, doc_name) VALUES (?, ?)",
                    [(\"حكومي\", d) for d in GOVERNMENT_OPTIONAL_DOCS] +
                    [(\"خاص\", d) for d in PRIVATE_OPTIONAL_DOCS]
                )
            
            conn.commit()
    except Exception as e:
        st.error(f"خطأ في إنشاء قاعدة البيانات: {e}")
        raise

def log_activity(action: str, details: str = "") -> None:
    """تسجيل نشاط المستخدم"""
    user = st.session_state.get("user")
    if not user:
        return
    
    try:
        username = user.get("username")
        user_role = user.get("role")
        
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO activity_log (timestamp, username, user_role, action, details) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), username, user_role, action, details)
            )
            conn.commit()
    except Exception as e:
        st.error(f"خطأ في تسجيل النشاط: {e}")