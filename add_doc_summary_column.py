import sqlite3
import os

DB_PATH = "clinical_doc.db"

def add_summary_column():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if columns exist
        c.execute("PRAGMA table_info(documents)")
        columns = [info[1] for info in c.fetchall()]
        
        if "summary" not in columns:
            print("Adding summary to documents...")
            c.execute("ALTER TABLE documents ADD COLUMN summary TEXT")
            conn.commit()
            print("Done.")
        else:
            print("Columns already exist.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_summary_column()
