import sqlite3
import os

DB_PATH = "clinical_doc.db"

def add_column():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(medications)")
        columns = [info[1] for info in c.fetchall()]
        
        if "source_note_id" not in columns:
            print("Adding source_note_id to medications...")
            c.execute("ALTER TABLE medications ADD COLUMN source_note_id INTEGER")
            conn.commit()
            print("Done.")
        else:
            print("source_note_id already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()
