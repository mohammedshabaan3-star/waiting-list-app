#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix missing sector column in database
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")

def fix_sector_column():
    """Add missing sector column to hospitals table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if sector column exists
        cursor.execute("PRAGMA table_info(hospitals)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sector' not in columns:
            print("Adding missing sector column to hospitals table...")
            cursor.execute("ALTER TABLE hospitals ADD COLUMN sector TEXT")
            conn.commit()
            print("[OK] Successfully added sector column")
        else:
            print("[OK] Sector column already exists")
            
        # Check if sector column exists in requests table
        cursor.execute("PRAGMA table_info(requests)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sector' not in columns:
            print("Adding missing sector column to requests table...")
            cursor.execute("ALTER TABLE requests ADD COLUMN sector TEXT")
            conn.commit()
            print("[OK] Successfully added sector column to requests table")
        else:
            print("[OK] Sector column already exists in requests table")
            
        # Check if sector column exists in admins table
        cursor.execute("PRAGMA table_info(admins)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sector' not in columns:
            print("Adding missing sector column to admins table...")
            cursor.execute("ALTER TABLE admins ADD COLUMN sector TEXT")
            conn.commit()
            print("[OK] Successfully added sector column to admins table")
        else:
            print("[OK] Sector column already exists in admins table")
            
        conn.close()
        print("[SUCCESS] Database schema fix completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Error fixing database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_sector_column()