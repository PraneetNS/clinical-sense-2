import sqlite3

try:
    conn = sqlite3.connect('clinical_doc.db')
    cursor = conn.cursor()
    # Get table info
    info = cursor.execute("PRAGMA table_info(users)").fetchall()
    print("Users table columns:")
    for col in info:
        print(col)
    
    users = cursor.execute("SELECT email FROM users").fetchall()
    print("Emails:", users)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
