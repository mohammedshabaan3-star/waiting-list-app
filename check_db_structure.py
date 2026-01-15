import sqlite3

conn = sqlite3.connect('data/app.db')
cur = conn.cursor()

# Check admins table structure
cur.execute('PRAGMA table_info(admins)')
admins_cols = cur.fetchall()
print('Admins columns:', [col[1] for col in admins_cols])

# Check hospitals table structure  
cur.execute('PRAGMA table_info(hospitals)')
hospitals_cols = cur.fetchall()
print('Hospitals columns:', [col[1] for col in hospitals_cols])

# Check requests table structure
cur.execute('PRAGMA table_info(requests)')
requests_cols = cur.fetchall()
print('Requests columns:', [col[1] for col in requests_cols])

# Check documents table structure
cur.execute('PRAGMA table_info(documents)')
documents_cols = cur.fetchall()
print('Documents columns:', [col[1] for col in documents_cols])

# Check for missing columns that should be added
print("\n=== Checking for missing columns ===")

# Check if sector column exists in admins
try:
    cur.execute("SELECT sector FROM admins LIMIT 1")
    print("OK: admins.sector exists")
except sqlite3.OperationalError:
    print("MISSING: admins.sector missing")

# Check if sector column exists in hospitals
try:
    cur.execute("SELECT sector FROM hospitals LIMIT 1")
    print("OK: hospitals.sector exists")
except sqlite3.OperationalError:
    print("MISSING: hospitals.sector missing")

# Check if updated_at column exists in documents
try:
    cur.execute("SELECT updated_at FROM documents LIMIT 1")
    print("OK: documents.updated_at exists")
except sqlite3.OperationalError:
    print("MISSING: documents.updated_at missing")

conn.close()