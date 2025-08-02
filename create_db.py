import sqlite3

# Kết nối hoặc tạo cơ sở dữ liệu
conn = sqlite3.connect('database/hotel_guests.db')
c = conn.cursor()

# Tạo bảng guests
c.execute('''CREATE TABLE IF NOT EXISTS guests 
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              phone TEXT,
              face_encoding BLOB,
              checkin_time TEXT,
              checkout_time TEXT,
              status TEXT)''')

# Tạo bảng stats
c.execute('''CREATE TABLE IF NOT EXISTS stats 
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              action TEXT,
              count INTEGER,
              time TEXT)''')

# Lưu thay đổi
conn.commit()
print("Database and tables created successfully!")

# Đóng kết nối
conn.close()