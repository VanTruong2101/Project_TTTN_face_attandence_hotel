import sqlite3
import os

def init_database():
    # Get absolute path to database directory
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
    db_path = os.path.join(db_dir, 'hotel_guests.db')
    
    # Create database directory if it doesn't exist
    os.makedirs(db_dir, exist_ok=True)
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create guests table
    cursor.execute('''CREATE TABLE IF NOT EXISTS guests 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT,
                      phone TEXT,
                      face_encoding BLOB,
                      checkin_time TEXT,
                      checkout_time TEXT,
                      status TEXT)''')
    
    # Create stats table
    cursor.execute('''CREATE TABLE IF NOT EXISTS stats 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      guest_id INTEGER,
                      action TEXT,
                      count INTEGER,
                      time TEXT,
                      FOREIGN KEY (guest_id) REFERENCES guests (id))''')
    
    conn.commit()
    print(f"Database initialized at: {db_path}")
    return db_path

if __name__ == "__main__":
    init_database()