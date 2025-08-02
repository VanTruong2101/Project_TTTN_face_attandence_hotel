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
    
    # Update stats
    cursor.execute('''
    INSERT INTO stats (action, count, time)
    VALUES (?, ?, ?)
    ''', ('check_in', 1, current_time))
    
    conn.commit()
    conn.close()

def main():
    print("=== Guest Check-in System ===")
    name = input("Enter guest name: ")
    phone = input("Enter guest phone: ")
    
    print("\nPlease look at the camera and press SPACE to capture...")
    frame = capture_face()
    
    if frame is None:
        print("No image captured!")
        return
        
    face_encoding = get_face_encoding(frame)
    
    if face_encoding is None:
        print("No face detected in the image!")
        return
        
    save_guest(name, phone, face_encoding)
    print(f"\nGuest {name} checked in successfully!")

if __name__ == "__main__":
    main()