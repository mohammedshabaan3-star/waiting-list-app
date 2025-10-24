#!/bin/bash

# المشروع القومي لقوائم الانتظار - نظام التعاقد المحسن
# ملف تشغيل سريع

echo "🏥 المشروع القومي لقوائم الانتظار - نظام التعاقد المحسن"
echo "============================================================"

# التحقق من وجود Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 غير مثبت. يرجى تثبيت Python3 أولاً"
    exit 1
fi

# التحقق من وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 غير مثبت. يرجى تثبيت pip3 أولاً"
    exit 1
fi

# إنشاء المجلدات المطلوبة
echo "📁 إنشاء المجلدات المطلوبة..."
mkdir -p data storage exports static .streamlit

# تثبيت المتطلبات
echo "📦 تثبيت المتطلبات..."
pip3 install -r requirements.txt

# تشغيل التطبيق
echo "🚀 بدء تشغيل التطبيق..."
echo "📱 يمكنك الوصول للتطبيق على: http://localhost:8501"
echo "⏹️  للإيقاف: اضغط Ctrl+C"
echo ""

python3 run_app.py