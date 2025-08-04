import streamlit as st
import cv2
import face_recognition
import numpy as np
from check_in import get_face_encoding, save_guest, check_existing_guest, update_guest
from check_out import update_checkout, get_checked_in_guests
import sqlite3

def get_stats():
    conn = sqlite3.connect('database/hotel_guests.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT action, SUM(count) as total
    FROM stats
    GROUP BY action
    ''')
    
    stats = dict(cursor.fetchall())
    conn.close()
    return stats

def main():
    st.set_page_config(page_title="Hotel Face Recognition System")
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Check In", "Check Out", "Statistics"])
    
    if page == "Home":
        st.title("Hotel Face Recognition System")
        st.write("Welcome! Please select an option from the sidebar.")
        
    elif page == "Check In":
        st.title("Guest Check-In")
        
        # Camera feed
        picture = st.camera_input("Take a picture")
        
        if picture:
            # Convert to cv2 format
            file_bytes = np.asarray(bytearray(picture.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            # Get face encoding
            face_encoding = get_face_encoding(frame)
            
            if face_encoding is not None:
                # Check if guest exists
                existing_guest = check_existing_guest(face_encoding)
                
                if existing_guest:
                    guest_id, name, phone, status = existing_guest
                    if status == "checked_in":
                        st.error(f"Guest {name} is already checked in!")
                    else:
                        st.success(f"Welcome back {name}!")
                        update_name = st.checkbox("Update name?")
                        if update_name:
                            name = st.text_input("New name", name)
                        update_phone = st.checkbox("Update phone?")
                        if update_phone:
                            phone = st.text_input("New phone", phone)
                        if st.button("Confirm Check In"):
                            # Use update_guest instead of save_guest
                            update_guest(guest_id, name, phone, face_encoding)
                            st.success(f"Guest {name} checked in successfully!")
                else:
                    # New guest registration
                    with st.form("check_in_form"):
                        name = st.text_input("Guest Name")
                        phone = st.text_input("Phone Number")
                        submit = st.form_submit_button("Check In")
                        
                        if submit:
                            save_guest(name, phone, face_encoding)
                            st.success(f"Guest {name} checked in successfully!")
            else:
                st.error("No face detected in the image!")
                
    elif page == "Check Out":
        st.title("Guest Check-Out")
        
        # Camera feed
        picture = st.camera_input("Take a picture")
        
        if picture:
            # Convert to cv2 format
            file_bytes = np.asarray(bytearray(picture.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            # Get face encoding
            face_encoding = get_face_encoding(frame)
            
            if face_encoding is not None:
                checked_in_guests = get_checked_in_guests()
                if checked_in_guests:
                    # Convert stored encodings back to numpy arrays
                    known_face_encodings = [np.frombuffer(guest[2]) for guest in checked_in_guests]
                    
                    # Use face_recognition.compare_faces instead of np.array_equal
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    
                    if True in matches:
                        first_match_index = matches.index(True)
                        guest_id = checked_in_guests[first_match_index][0]
                        name = checked_in_guests[first_match_index][1]
                        
                        update_checkout(guest_id)
                        st.success(f"Guest {name} checked out successfully!")
                    else:
                        st.error("Guest not found or already checked out!")
                else:
                    st.error("No checked-in guests found!")
            else:
                st.error("No face detected in the image!")
                
    elif page == "Statistics":
        st.title("Statistics")
        stats_data = get_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Check-ins", stats_data.get('check_in', 0))
        with col2:
            st.metric("Total Check-outs", stats_data.get('check_out', 0))

if __name__ == '__main__':
    main()
