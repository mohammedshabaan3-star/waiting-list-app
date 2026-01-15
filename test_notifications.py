#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام الإشعارات
"""

import sys
import os
sys.path.append('.')

# استيراد الوظائف من التطبيق الرئيسي
from waiting_list_contracts_app import (
    create_notification, 
    get_user_notifications, 
    mark_notification_read, 
    get_unread_count,
    get_conn
)

def test_notifications_system():
    print("=== اختبار نظام الإشعارات ===")
    
    # اختبار إنشاء إشعار
    print("1. اختبار إنشاء إشعار...")
    result = create_notification(
        user_id=1, 
        user_role="hospital", 
        title="إشعار تجريبي", 
        message="هذا إشعار تجريبي لاختبار النظام",
        notification_type="info"
    )
    if result:
        print("تم إنشاء الإشعار بنجاح")
    else:
        print("فشل في إنشاء الإشعار")
    
    # اختبار الحصول على الإشعارات
    print("\n2. اختبار الحصول على الإشعارات...")
    notifications = get_user_notifications(user_id=1, user_role="hospital")
    print(f"عدد الإشعارات: {len(notifications)}")
    
    for notif in notifications[:3]:  # عرض أول 3 إشعارات
        print(f"   - {notif['title']}: {notif['message'][:50]}...")
    
    # اختبار عدد الإشعارات غير المقروءة
    print("\n3. اختبار عدد الإشعارات غير المقروءة...")
    unread_count = get_unread_count(user_id=1, user_role="hospital")
    print(f"عدد الإشعارات غير المقروءة: {unread_count}")
    
    # اختبار تعليم إشعار كمقروء
    if notifications:
        print("\n4. اختبار تعليم إشعار كمقروء...")
        first_notif = notifications[0]
        mark_result = mark_notification_read(first_notif['id'])
        if mark_result:
            print("تم تعليم الإشعار كمقروء")
            # فحص العدد مرة أخرى
            new_unread_count = get_unread_count(user_id=1, user_role="hospital")
            print(f"عدد الإشعارات غير المقروءة بعد التعليم: {new_unread_count}")
        else:
            print("فشل في تعليم الإشعار كمقروء")
    
    # فحص جدول الإشعارات في قاعدة البيانات
    print("\n5. فحص جدول الإشعارات في قاعدة البيانات...")
    try:
        with get_conn() as conn:
            # التحقق من وجود الجدول
            table_exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"
            ).fetchone()
            
            if table_exists:
                print("جدول الإشعارات موجود")
                
                # عرض هيكل الجدول
                columns = conn.execute("PRAGMA table_info(notifications)").fetchall()
                print("أعمدة الجدول:")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")
                
                # عدد الإشعارات الإجمالي
                total_count = conn.execute("SELECT COUNT(*) as count FROM notifications").fetchone()
                print(f"إجمالي الإشعارات في قاعدة البيانات: {total_count['count']}")
                
            else:
                print("جدول الإشعارات غير موجود!")
                return False
                
    except Exception as e:
        print(f"خطأ في فحص قاعدة البيانات: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_notifications_system()
    if success:
        print("\nنظام الإشعارات يعمل بشكل صحيح")
    else:
        print("\nيوجد مشكلة في نظام الإشعارات")