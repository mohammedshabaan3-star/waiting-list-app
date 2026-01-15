import sqlite3

conn = sqlite3.connect('data/app.db')
cur = conn.cursor()

# Check tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('Tables:', [t[0] for t in tables])

# Check counts
cur.execute('SELECT COUNT(*) FROM requests')
print('Requests count:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM hospitals')
print('Hospitals count:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM admins')
print('Admins count:', cur.fetchone()[0])

conn.close()