import sqlite3

conn = sqlite3.connect('data/app.db')
cur = conn.cursor()

# Check admin users and their password hashes
cur.execute('SELECT id, username, role, sector FROM admins')
admins = cur.fetchall()
print('=== Admin Users ===')
for admin in admins:
    print(f'ID: {admin[0]}, Username: {admin[1]}, Role: {admin[2]}, Sector: {admin[3]}')

# Check password hash format
cur.execute('SELECT username, password_hash FROM admins LIMIT 1')
admin = cur.fetchone()
if admin:
    hash_format = 'NEW (with salt)' if ':' in admin[1] else 'OLD (without salt)'
    print(f'Password hash format for {admin[0]}: {hash_format}')

# Check hospitals sample
cur.execute('SELECT COUNT(*) FROM hospitals WHERE sector IS NOT NULL')
hospitals_with_sector = cur.fetchone()[0]
print(f'Hospitals with sector: {hospitals_with_sector}/2198')

# Check requests sample
cur.execute('SELECT id, status, sector, governorate FROM requests LIMIT 3')
requests = cur.fetchall()
print('=== Sample Requests ===')
for req in requests:
    print(f'ID: {req[0]}, Status: {req[1]}, Sector: {req[2]}, Governorate: {req[3]}')

# Check document types
cur.execute('SELECT COUNT(*) FROM document_types')
doc_types_count = cur.fetchone()[0]
print(f'Document types count: {doc_types_count}')

# Check status settings
cur.execute('SELECT COUNT(*) FROM status_settings')
status_settings_count = cur.fetchone()[0]
print(f'Status settings count: {status_settings_count}')

# Check for NULL values in critical fields
cur.execute('SELECT COUNT(*) FROM hospitals WHERE name IS NULL OR name = ""')
hospitals_no_name = cur.fetchone()[0]
print(f'Hospitals without name: {hospitals_no_name}')

cur.execute('SELECT COUNT(*) FROM requests WHERE status IS NULL OR status = ""')
requests_no_status = cur.fetchone()[0]
print(f'Requests without status: {requests_no_status}')

conn.close()