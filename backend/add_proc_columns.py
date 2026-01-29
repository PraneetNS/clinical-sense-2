import sqlite3
import os

DB_PATH = "clinical_doc.db"

def add_columns():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if columns exist
        c.execute("PRAGMA table_info(procedures)")
        columns = [info[1] for info in c.fetchall()]
        
        if "admission_id" not in columns:
            print("Adding admission_id and source_note_id to procedures...")
            c.execute("ALTER TABLE procedures ADD COLUMN admission_id INTEGER")
            c.execute("ALTER TABLE procedures ADD COLUMN source_note_id INTEGER")
            conn.commit()
            print("Done.")
        else:
            print("Columns already exist.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()
