import sqlite3
DB='data/app.db'
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()
print('Top event_key counts:')
for row in cur.execute("SELECT COALESCE(event_key,'<NULL>') as ek, COUNT(*) as c FROM notifications GROUP BY event_key ORDER BY c DESC LIMIT 20"):
    print(row['ek'], row['c'])
print('\nRecent notifications:')
for row in cur.execute("SELECT id, COALESCE(event_key,'<NULL>') as ek, title, message, is_read, created_at FROM notifications ORDER BY datetime(created_at) DESC LIMIT 40"):
    print(row['id'], row['ek'], row['title'], row['is_read'], row['created_at'])
conn.close()
