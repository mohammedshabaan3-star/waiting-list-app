#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف تشغيل محسن للتطبيق مع نظام مراقبة التغييرات التلقائي
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def install_requirements():
    """تثبيت المتطلبات تلقائياً"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ تم تثبيت جميع المتطلبات بنجاح")
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت المتطلبات: {e}")
        sys.exit(1)

def check_and_create_directories():
    """إنشاء المجلدات المطلوبة إذا لم تكن موجودة"""
    directories = ["data", "storage", "exports", "static"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ تم التحقق من المجلدات المطلوبة")

def run_streamlit():
    """تشغيل تطبيق Streamlit"""
    try:
        # إعداد متغيرات البيئة لتحسين الأداء
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
        os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
        os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
        
        # تشغيل التطبيق
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "waiting_list_contracts_app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.fileWatcherType=auto",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false"
        ]
        
        print("🚀 بدء تشغيل التطبيق...")
        print("📱 يمكنك الوصول للتطبيق على: http://localhost:8501")
        print("⏹️  للإيقاف: اضغط Ctrl+C")
        
        process = subprocess.Popen(cmd)
        
        def signal_handler(sig, frame):
            print("\n🛑 إيقاف التطبيق...")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        process.wait()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")
        sys.exit(1)

def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🏥 المشروع القومي لقوائم الانتظار - نظام التعاقد")
    print("=" * 60)
    
    # التحقق من وجود ملف التطبيق
    if not Path("waiting_list_contracts_app.py").exists():
        print("❌ ملف التطبيق غير موجود!")
        sys.exit(1)
    
    # تثبيت المتطلبات
    if Path("requirements.txt").exists():
        print("📦 تثبيت المتطلبات...")
        install_requirements()
    
    # إنشاء المجلدات
    check_and_create_directories()
    
    # تشغيل التطبيق
    run_streamlit()

if __name__ == "__main__":
    main()