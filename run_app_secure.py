#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف تشغيل محسن وآمن للتطبيق - النسخة المحسنة
المشروع القومي لقوائم الانتظار - نظام التعاقد
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def check_python_version():
    """التحقق من إصدار Python"""
    if sys.version_info < (3, 9):
        print("❌ يتطلب Python 3.9 أو أحدث")
        print(f"الإصدار الحالي: {sys.version}")
        sys.exit(1)
    print(f"✅ إصدار Python مناسب: {sys.version}")

def install_requirements():
    """تثبيت المتطلبات المحسنة"""
    requirements_file = "requirements_fixed.txt"
    if not Path(requirements_file).exists():
        requirements_file = "requirements.txt"
    
    try:
        print("📦 تثبيت المتطلبات...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file, "--upgrade"
        ])
        print("✅ تم تثبيت جميع المتطلبات بنجاح")
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت المتطلبات: {e}")
        sys.exit(1)

def check_and_create_directories():
    """إنشاء المجلدات المطلوبة مع التحقق من الصلاحيات"""
    directories = ["data", "storage", "exports", "static"]
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            # التحقق من إمكانية الكتابة
            test_file = Path(directory) / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
        except PermissionError:
            print(f"❌ لا توجد صلاحيات كافية للكتابة في مجلد: {directory}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ خطأ في إنشاء المجلد {directory}: {e}")
            sys.exit(1)
    print("✅ تم التحقق من المجلدات المطلوبة")

def check_database_access():
    """التحقق من إمكانية الوصول لقاعدة البيانات"""
    try:
        import sqlite3
        db_path = Path("data/app.db")
        
        # إنشاء قاعدة بيانات تجريبية للاختبار
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)")
        conn.execute("DROP TABLE test_table")
        conn.close()
        print("✅ قاعدة البيانات تعمل بشكل صحيح")
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        sys.exit(1)

def run_security_check():
    """فحص أمني أساسي"""
    print("🔒 تشغيل الفحص الأمني...")
    
    # التحقق من وجود الملفات الحساسة
    sensitive_files = [".env", "config.ini", "secrets.txt"]
    for file in sensitive_files:
        if Path(file).exists():
            print(f"⚠️  تحذير: وجد ملف حساس: {file}")
    
    # التحقق من صلاحيات الملفات
    app_file = "waiting_list_contracts_app_final.py"
    if not Path(app_file).exists():
        app_file = "waiting_list_contracts_app.py"
    
    if Path(app_file).exists():
        print(f"✅ ملف التطبيق موجود: {app_file}")
    else:
        print("❌ ملف التطبيق غير موجود!")
        sys.exit(1)
    
    print("✅ اكتمل الفحص الأمني")

def run_streamlit():
    """تشغيل تطبيق Streamlit مع الإعدادات المحسنة"""
    try:
        # تحديد ملف التطبيق
        app_file = "waiting_list_contracts_app_final.py"
        if not Path(app_file).exists():
            app_file = "waiting_list_contracts_app.py"
        
        # إعداد متغيرات البيئة للأمان والأداء
        os.environ.update({
            "STREAMLIT_SERVER_HEADLESS": "true",
            "STREAMLIT_SERVER_ENABLE_CORS": "false",
            "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION": "true",
            "STREAMLIT_SERVER_MAX_UPLOAD_SIZE": "50",  # 50MB
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
            "STREAMLIT_GLOBAL_DEVELOPMENT_MODE": "false"
        })
        
        # أوامر التشغيل المحسنة
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_file,
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.fileWatcherType=auto",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=true",
            "--server.maxUploadSize=50",
            "--browser.gatherUsageStats=false",
            "--global.developmentMode=false"
        ]
        
        print("🚀 بدء تشغيل التطبيق المحسن...")
        print("📱 يمكنك الوصول للتطبيق على: http://localhost:8501")
        print("🔒 التطبيق يعمل في الوضع الآمن")
        print("⏹️  للإيقاف: اضغط Ctrl+C")
        print("=" * 60)
        
        process = subprocess.Popen(cmd)
        
        def signal_handler(sig, frame):
            print("\n🛑 إيقاف التطبيق...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ تم إيقاف التطبيق بأمان")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        
        process.wait()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")
        sys.exit(1)

def main():
    """الدالة الرئيسية المحسنة"""
    print("=" * 60)
    print("🏥 المشروع القومي لقوائم الانتظار - نظام التعاقد")
    print("🔒 النسخة المحسنة والآمنة")
    print("=" * 60)
    
    # فحوصات ما قبل التشغيل
    check_python_version()
    
    # تثبيت المتطلبات
    install_requirements()
    
    # إنشاء المجلدات والتحقق من الصلاحيات
    check_and_create_directories()
    
    # فحص قاعدة البيانات
    check_database_access()
    
    # فحص أمني
    run_security_check()
    
    # تشغيل التطبيق
    run_streamlit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف التطبيق بواسطة المستخدم")
        sys.exit(0)
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)