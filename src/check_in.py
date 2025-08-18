import face_recognition
import cv2
import sqlite3
import numpy as np
from datetime import datetime

def capture_face():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        cv2.imshow('Check-in - Press SPACE to capture', frame)
        
        if cv2.waitKey(1) & 0xFF == ord(' '):
            cap.release()
            cv2.destroyAllWindows()
            return frame
            
        elif cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return None

def get_face_encoding(frame):
    # Chuyển đổi sang định dạng uint8 nếu cần
    if frame.dtype != np.uint8:
        frame = frame.astype(np.uint8)
    
    # Chuyển BGR sang RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Đảm bảo hình ảnh có đúng kích thước và định dạng
    if len(rgb_frame.shape) != 3:
        print("Error: Image must be RGB (3 channels)")
        return None
    
    face_locations = face_recognition.face_locations(rgb_frame)
    
    if len(face_locations) == 0:
        return None
        
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    return face_encodings[0]

def save_guest(name, phone, face_encoding):
    conn = sqlite3.connect('database/hotel_guests.db')
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
    INSERT INTO guests (name, phone, face_encoding, checkin_time, status)
    VALUES (?, ?, ?, ?, ?)
    ''', (name, phone, face_encoding.tobytes(), current_time, 'checked_in'))
    
    guest_id = cursor.lastrowid
    
    cursor.execute('''
    INSERT INTO stats (guest_id, action, count, time)
    VALUES (?, ?, ?, ?)
    ''', (guest_id, 'check_in', 1, current_time))
    
    conn.commit()
    conn.close()

def check_existing_guest(face_encoding):
    conn = sqlite3.connect('database/hotel_guests.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, phone, status FROM guests')
    guests = cursor.fetchall()
    
    for guest in guests:
        guest_id, name, phone, status = guest
        
        # Get face encoding from DB
        cursor.execute('SELECT face_encoding FROM guests WHERE id = ?', (guest_id,))
        stored_encoding = np.frombuffer(cursor.fetchone()[0])
        
        match = face_recognition.compare_faces([stored_encoding], face_encoding)[0]
        
        if match:
            # Get guest history without guest_id
            cursor.execute('''
            SELECT action, time 
            FROM stats 
            WHERE guest_id = ?
            ORDER BY time DESC
            ''', (guest_id,))
            history = cursor.fetchall()
            
            conn.close()
            return guest_id, name, phone, status, history
            
    conn.close()
    return None

def update_guest(guest_id, name, phone, face_encoding):
    conn = sqlite3.connect('database/hotel_guests.db')
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update guest information
    cursor.execute('''
    UPDATE guests 
    SET name = ?, phone = ?, face_encoding = ?, 
        checkin_time = ?, status = "checked_in", checkout_time = NULL
    WHERE id = ?
    ''', (name, phone, face_encoding.tobytes(), current_time, guest_id))
    
    # Add check-in record to stats with guest_id
    cursor.execute('''
    INSERT INTO stats (guest_id, action, count, time)
    VALUES (?, ?, ?, ?)
    ''', (guest_id, 'check_in', 1, current_time))
    
    conn.commit()
    conn.close()

def main():
    print("=== Guest Check-in System ===")
    
    print("\nPlease look at the camera and press SPACE to capture...")
    frame = capture_face()
    
    if frame is None:
        print("No image captured!")
        return
        
    face_encoding = get_face_encoding(frame)
    
    if face_encoding is None:
        print("No face detected in the image!")
        return
    
    # Check if guest exists
    existing_guest = check_existing_guest(face_encoding)
    
    if existing_guest:
        guest_id, name, phone, status, history = existing_guest
        
        if status == "checked_in":
            print(f"\nGuest {name} is already checked in!")
            return
            
        print(f"\nWelcome back {name}!")
        print(f"Current Information:")
        print(f"Name: {name}")
        print(f"Phone: {phone}")
        
        # Display guest history
        print("\nYour recent check-in/check-out history:")
        for record in history:
            action, time = record
            print(f"- {action} at {time}")
        
        # Ask for name update
        update_name = input("\nWould you like to update your name? (y/n): ")
        if update_name.lower() == 'y':
            name = input("Enter new name: ")
        
        # Ask for phone update    
        update_phone = input("Would you like to update your phone number? (y/n): ")
        if update_phone.lower() == 'y':
            phone = input("Enter new phone number: ")
            
        # Update existing guest record
        update_guest(guest_id, name, phone, face_encoding)
        
    else:
        # New guest registration
        name = input("Enter guest name: ")
        phone = input("Enter guest phone: ")
        save_guest(name, phone, face_encoding)
    
    print(f"\nGuest {name} checked in successfully!")

if __name__ == "__main__":
    main()