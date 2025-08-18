import face_recognition
import cv2
import sqlite3
import numpy as np
from datetime import datetime

def get_checked_in_guests():
    conn = sqlite3.connect('database/hotel_guests.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, face_encoding FROM guests WHERE status = "checked_in"')
    guests = cursor.fetchall()
    
    conn.close()
    return guests

def update_checkout(guest_id):
    conn = sqlite3.connect('database/hotel_guests.db')
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update guest status
    cursor.execute('''
    UPDATE guests 
    SET status = "checked_out", checkout_time = ?
    WHERE id = ?
    ''', (current_time, guest_id))
    
    # Add check-out record to stats with guest_id
    cursor.execute('''
    INSERT INTO stats (guest_id, action, count, time)
    VALUES (?, ?, ?, ?)
    ''', (guest_id, 'check_out', 1, current_time))
    
    conn.commit()
    conn.close()

def main():
    print("=== Guest Check-out System ===")
    guests = get_checked_in_guests()
    
    if not guests:
        print("No checked-in guests found!")
        return
        
    # Convert stored encodings back to numpy arrays
    known_face_encodings = [np.frombuffer(guest[2]) for guest in guests]
    known_names = [guest[1] for guest in guests]
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            
            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
                guest_id = guests[first_match_index][0]
                
                update_checkout(guest_id)
                print(f"\nGuest {name} checked out successfully!")
                cap.release()
                cv2.destroyAllWindows()
                return
        
        cv2.imshow('Check-out - Press q to quit', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()