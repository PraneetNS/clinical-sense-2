import sqlite3
import os

db_path = "clinical_doc.db"
if not os.path.exists(db_path):
    print(f"Database file not found at {os.path.abspath(db_path)}")
else:
    print(f"Checking database at {os.path.abspath(db_path)}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print("Tables:", tables)
        
        # Check users content if table exists
        if ('users',) in tables:
            users = cursor.execute("SELECT * FROM users").fetchall()
            print("Users:", users)
        else:
            print("Users table NOT found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
