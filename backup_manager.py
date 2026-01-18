# -*- coding: utf-8 -*-
"""
نظام النسخ الاحتياطي التلقائي
===============================
نظام شامل للنسخ الاحتياطي التلقائي لقاعدة البيانات والملفات المرفوعة
"""

import os
import sqlite3
import shutil
import zipfile
import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
import sys
import io

class BackupManager:
    def __init__(self, db_path="data/app.db", storage_path="storage", backup_dir="backups"):
        self.db_path = db_path
        self.storage_path = storage_path
        self.backup_dir = backup_dir
        self.max_backups = 30  # الاحتفاظ بآخر 30 نسخة
        
        # إنشاء مجلد النسخ الاحتياطي إذا لم يكن موجوداً
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # إعداد نظام التسجيل مع دعم UTF-8
        # إعادة تعيين stdout إلى UTF-8 على ويندوز
        try:
            if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except:
            pass
        
        # إنشاء معالج السجلات مع UTF-8
        file_handler = logging.FileHandler(os.path.join(self.backup_dir, 'backup.log'), encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)
    
    def create_backup(self):
        """إنشاء نسخة احتياطية كاملة"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            self.logger.info(f"بدء إنشاء النسخة الاحتياطية: {backup_filename}")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # نسخ قاعدة البيانات
                if os.path.exists(self.db_path):
                    # إنشاء نسخة مؤقتة من قاعدة البيانات لضمان الاتساق
                    temp_db = f"{self.db_path}.backup_temp"
                    self._backup_database(self.db_path, temp_db)
                    zipf.write(temp_db, "app.db")
                    os.remove(temp_db)
                    self.logger.info("تم نسخ قاعدة البيانات بنجاح")
                
                # نسخ مجلد الملفات المرفوعة
                if os.path.exists(self.storage_path):
                    for root, dirs, files in os.walk(self.storage_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(self.storage_path))
                            zipf.write(file_path, arcname)
                    self.logger.info("تم نسخ الملفات المرفوعة بنجاح")
                
                # إضافة معلومات النسخة الاحتياطية
                backup_info = f"""معلومات النسخة الاحتياطية
تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
قاعدة البيانات: {self.db_path}
مجلد الملفات: {self.storage_path}
"""
                zipf.writestr("backup_info.txt", backup_info.encode('utf-8'))
            
            # تنظيف النسخ القديمة
            self._cleanup_old_backups()
            
            # تحديث إعدادات النسخ الاحتياطي في قاعدة البيانات
            self._update_backup_settings(backup_filename, os.path.getsize(backup_path))
            
            self.logger.info(f"تم إنشاء النسخة الاحتياطية بنجاح: {backup_filename}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}")
            return None
    
    def _backup_database(self, source_db, target_db):
        """إنشاء نسخة آمنة من قاعدة البيانات"""
        source_conn = sqlite3.connect(source_db)
        target_conn = sqlite3.connect(target_db)
        
        # نسخ قاعدة البيانات باستخدام backup API
        source_conn.backup(target_conn)
        
        source_conn.close()
        target_conn.close()
    
    def _cleanup_old_backups(self):
        """حذف النسخ الاحتياطية القديمة"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getctime(file_path)))
            
            # ترتيب النسخ حسب تاريخ الإنشاء
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # حذف النسخ الزائدة
            if len(backup_files) > self.max_backups:
                for file_path, _ in backup_files[self.max_backups:]:
                    os.remove(file_path)
                    self.logger.info(f"تم حذف النسخة الاحتياطية القديمة: {os.path.basename(file_path)}")
                    
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف النسخ القديمة: {str(e)}")
    
    def _update_backup_settings(self, filename, size):
        """تحديث إعدادات النسخ الاحتياطي في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # التحقق من وجود سجل في جدول backup_settings
            cur.execute("SELECT COUNT(*) FROM backup_settings")
            count = cur.fetchone()[0]
            
            current_time = datetime.now().isoformat()
            
            if count == 0:
                # إنشاء سجل جديد
                cur.execute("""
                    INSERT INTO backup_settings 
                    (auto_backup_enabled, backup_interval_hours, max_backups_to_keep, last_backup_time, next_backup_time) 
                    VALUES (1, 24, ?, ?, ?)
                """, (self.max_backups, current_time, current_time))
            else:
                # تحديث السجل الموجود
                cur.execute("""
                    UPDATE backup_settings 
                    SET last_backup_time = ?, next_backup_time = ?
                    WHERE id = 1
                """, (current_time, current_time))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث إعدادات النسخ الاحتياطي: {str(e)}")
    
    def restore_backup(self, backup_file):
        """استرجاع نسخة احتياطية"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_file)
            if not os.path.exists(backup_path):
                self.logger.error(f"ملف النسخة الاحتياطية غير موجود: {backup_file}")
                return False
            
            self.logger.info(f"بدء استرجاع النسخة الاحتياطية: {backup_file}")
            
            # إنشاء نسخة احتياطية من الوضع الحالي قبل الاسترجاع
            current_backup = self.create_backup()
            if current_backup:
                self.logger.info("تم إنشاء نسخة احتياطية من الوضع الحالي قبل الاسترجاع")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # استرجاع قاعدة البيانات
                if "app.db" in zipf.namelist():
                    zipf.extract("app.db", "temp_restore")
                    shutil.move("temp_restore/app.db", self.db_path)
                    os.rmdir("temp_restore")
                    self.logger.info("تم استرجاع قاعدة البيانات بنجاح")
                
                # استرجاع الملفات المرفوعة
                for member in zipf.namelist():
                    if member.startswith("storage/"):
                        zipf.extract(member, ".")
                        self.logger.info(f"تم استرجاع الملف: {member}")
            
            self.logger.info(f"تم استرجاع النسخة الاحتياطية بنجاح: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في استرجاع النسخة الاحتياطية: {str(e)}")
            return False
    
    def get_backup_list(self):
        """الحصول على قائمة النسخ الاحتياطية"""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, file)
                    stat = os.stat(file_path)
                    backups.append({
                        'filename': file,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # ترتيب حسب تاريخ الإنشاء (الأحدث أولاً)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على قائمة النسخ الاحتياطية: {str(e)}")
            return []
    
    def start_scheduler(self):
        """بدء جدولة النسخ الاحتياطي التلقائي"""
        # جدولة النسخ الاحتياطي يومياً في الساعة 2:00 صباحاً
        schedule.every().day.at("02:00").do(self.create_backup)
        
        # جدولة النسخ الاحتياطي الأسبوعي (يوم الجمعة في الساعة 1:00 صباحاً)
        schedule.every().friday.at("01:00").do(self._create_weekly_backup)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # فحص كل دقيقة
        
        # تشغيل الجدولة في خيط منفصل
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("تم بدء نظام النسخ الاحتياطي التلقائي")
    
    def _create_weekly_backup(self):
        """إنشاء نسخة احتياطية أسبوعية مع تسمية خاصة"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"weekly_backup_{timestamp}.zip"
        
        # نفس منطق create_backup لكن مع اسم مختلف
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(self.db_path):
                    temp_db = f"{self.db_path}.backup_temp"
                    self._backup_database(self.db_path, temp_db)
                    zipf.write(temp_db, "app.db")
                    os.remove(temp_db)
                
                if os.path.exists(self.storage_path):
                    for root, dirs, files in os.walk(self.storage_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(self.storage_path))
                            zipf.write(file_path, arcname)
                
                backup_info = f"""نسخة احتياطية أسبوعية
تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
نوع النسخة: أسبوعية
"""
                zipf.writestr("backup_info.txt", backup_info.encode('utf-8'))
            
            self.logger.info(f"تم إنشاء النسخة الاحتياطية الأسبوعية: {backup_filename}")
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء النسخة الاحتياطية الأسبوعية: {str(e)}")

# إنشاء مثيل عام لمدير النسخ الاحتياطي
backup_manager = BackupManager()