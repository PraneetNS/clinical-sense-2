import sqlite3

try:
    conn = sqlite3.connect('clinical_doc.db')
    cursor = conn.cursor()
    users = cursor.execute("SELECT email, role FROM users").fetchall()
    print("Available Users:")
    for email, role in users:
        print(f"Email: {email} (Role: {role})")
    conn.close()
except Exception as e:
    print(f"Error reading users: {e}")
