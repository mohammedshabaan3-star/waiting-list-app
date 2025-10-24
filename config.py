# -*- coding: utf-8 -*-
"""
ملف الإعدادات العامة للنظام
"""

import os
from pathlib import Path

# إعدادات قاعدة البيانات
DATABASE_CONFIG = {
    'path': Path("data/app.db"),
    'schema_version': 5,
    'backup_enabled': True,
    'backup_interval': 24  # ساعة
}

# إعدادات الملفات
FILE_CONFIG = {
    'storage_dir': Path("storage"),
    'exports_dir': Path("exports"),
    'resources_dir': Path("static"),
    'max_file_size': 200 * 1024 * 1024,  # 200 MB
    'allowed_extensions': {
        'documents': ['.pdf'],
        'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
        'images': ['.jpg', '.jpeg', '.png', '.gif']
    }
}

# إعدادات الأمان
SECURITY_CONFIG = {
    'password_min_length': 4,
    'session_timeout': 3600,  # ثانية
    'max_login_attempts': 5,
    'lockout_duration': 300  # ثانية
}

# إعدادات النظام
SYSTEM_CONFIG = {
    'app_title': "المشروع القومي لقوائم الانتظار - التعاقد على الخدمات الجراحية",
    'app_version': "5.0",
    'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
    'auto_backup': True,
    'cache_ttl': 3600,  # ثانية
    'file_watch_enabled': True
}

# إعدادات الواجهة
UI_CONFIG = {
    'theme': {
        'primary_color': "#1e40af",
        'background_color': "#ffffff",
        'secondary_background_color': "#f0f2f6",
        'text_color': "#262730"
    },
    'sidebar_width': 320,
    'max_table_height': 600,
    'items_per_page': 50
}

# إعدادات الإشعارات
NOTIFICATION_CONFIG = {
    'email_enabled': False,
    'sms_enabled': False,
    'in_app_notifications': True,
    'notification_retention_days': 30
}

# إعدادات التصدير
EXPORT_CONFIG = {
    'formats': ['xlsx', 'csv', 'pdf'],
    'max_records': 10000,
    'include_attachments': True,
    'compress_exports': True
}

# إعدادات المراقبة
MONITORING_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'logs/app.log',
    'max_log_size': 10 * 1024 * 1024,  # 10 MB
    'log_backup_count': 5,
    'performance_monitoring': True
}

def get_config(section: str = None):
    """الحصول على إعدادات قسم معين أو جميع الإعدادات"""
    configs = {
        'database': DATABASE_CONFIG,
        'file': FILE_CONFIG,
        'security': SECURITY_CONFIG,
        'system': SYSTEM_CONFIG,
        'ui': UI_CONFIG,
        'notification': NOTIFICATION_CONFIG,
        'export': EXPORT_CONFIG,
        'monitoring': MONITORING_CONFIG
    }
    
    if section:
        return configs.get(section, {})
    return configs

def update_config(section: str, key: str, value):
    """تحديث إعداد معين"""
    configs = get_config()
    if section in configs and key in configs[section]:
        configs[section][key] = value
        return True
    return False