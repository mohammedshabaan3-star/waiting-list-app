#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار النظام المحسن
"""

import sqlite3
import os
import sys
from pathlib import Path

def test_database_connection():
    """اختبار الاتصال بقاعدة البيانات"""
    try:
        db_path = Path("data/app.db")
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        print("✅ اختبار قاعدة البيانات: نجح")
        return True
    except Exception as e:
        print(f"❌ اختبار قاعدة البيانات: فشل - {e}")
        return False

def test_required_directories():
    """اختبار وجود المجلدات المطلوبة"""
    directories = ["data", "storage", "exports", "static", ".streamlit"]
    success = True
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ تم إنشاء المجلد: {directory}")
            except Exception as e:
                print(f"❌ فشل إنشاء المجلد {directory}: {e}")
                success = False
        else:
            print(f"✅ المجلد موجود: {directory}")
    
    return success

def test_requirements():
    """اختبار المتطلبات"""
    required_modules = [
        'streamlit',
        'pandas',
        'openpyxl',
        'plotly',
        'streamlit_option_menu',
        'passlib',
        'watchdog'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ المكتبة متوفرة: {module}")
        except ImportError:
            print(f"❌ المكتبة مفقودة: {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n📦 لتثبيت المكتبات المفقودة:")
        print(f"pip install {' '.join(missing_modules)}")
        return False
    
    return True

def test_file_permissions():
    """اختبار صلاحيات الملفات"""
    test_file = Path("test_write.tmp")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        test_file.unlink()
        print("✅ صلاحيات الكتابة: متوفرة")
        return True
    except Exception as e:
        print(f"❌ صلاحيات الكتابة: غير متوفرة - {e}")
        return False

def test_migrations_system():
    """اختبار نظام migrations"""
    try:
        # استيراد الدوال من الملف الرئيسي
        sys.path.append('.')
        from waiting_list_contracts_app import get_current_schema_version, run_migrations, DB_SCHEMA_VERSION
        
        current_version = get_current_schema_version()
        print(f"✅ إصدار قاعدة البيانات الحالي: {current_version}")
        print(f"✅ الإصدار المطلوب: {DB_SCHEMA_VERSION}")
        
        if current_version < DB_SCHEMA_VERSION:
            print("🔄 تشغيل migrations...")
            run_migrations()
            new_version = get_current_schema_version()
            print(f"✅ تم التحديث إلى الإصدار: {new_version}")
        else:
            print("✅ قاعدة البيانات محدثة")
        
        return True
    except Exception as e:
        print(f"❌ اختبار نظام migrations: فشل - {e}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار النظام المحسن")
    print("=" * 50)
    
    tests = [
        ("اختبار المجلدات المطلوبة", test_required_directories),
        ("اختبار صلاحيات الملفات", test_file_permissions),
        ("اختبار المتطلبات", test_requirements),
        ("اختبار قاعدة البيانات", test_database_connection),
        ("اختبار نظام migrations", test_migrations_system)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"⚠️  {test_name} فشل")
    
    print("\n" + "=" * 50)
    print(f"📊 النتائج: {passed}/{total} اختبار نجح")
    
    if passed == total:
        print("🎉 جميع الاختبارات نجحت! النظام جاهز للتشغيل")
        print("\n🚀 لتشغيل النظام:")
        print("python run_app.py")
        return True
    else:
        print("❌ بعض الاختبارات فشلت. يرجى إصلاح المشاكل قبل التشغيل")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)