import streamlit as st
import cv2
import face_recognition
import pandas as pd
import numpy as np
from check_in import get_face_encoding, save_guest, check_existing_guest, update_guest
from check_out import update_checkout, get_checked_in_guests
import sqlite3
from datetime import datetime
import time
import os

def get_current_stats():
    try:
        # Get absolute path to database
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'hotel_guests.db')
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found at {db_path}")
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Add error handling for each query
        try:
            cursor.execute('SELECT COUNT(*) FROM guests WHERE status = "checked_in"')
            current_present = cursor.fetchone()[0]
            
            cursor.execute('''
            SELECT COUNT(*) FROM stats 
            WHERE action = "check_in" AND date(time) = date(?)
            ''', (current_date,))
            total_checkins = cursor.fetchone()[0]
            
            cursor.execute('''
            SELECT COUNT(*) FROM stats 
            WHERE action = "check_out" AND date(time) = date(?)
            ''', (current_date,))
            total_checkouts = cursor.fetchone()[0]
            
            cursor.execute('''
            SELECT name, checkin_time 
            FROM guests 
            WHERE status = "checked_in"
            ORDER BY checkin_time DESC
            ''')
            present_guests = cursor.fetchall()
            
            return current_present, total_checkins, total_checkouts, present_guests
            
        except sqlite3.Error as e:
            st.error(f"Database error: {e}")
            return 0, 0, 0, []
            
    except Exception as e:
        st.error(f"Error: {e}")
        return 0, 0, 0, []
    finally:
        if 'conn' in locals():
            conn.close()
def main():
    st.set_page_config(
        page_title="Hotel Face Recognition System",
        layout="wide"  # Use wide layout for better dashboard view
    )
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Check In", "Check Out"])
    
    if page == "Dashboard":
        st.title("Hotel Face Recognition Dashboard")
        
        # Get real-time stats
        current_present, total_checkins, total_checkouts, present_guests = get_current_stats()
        
        # KPI Cards in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Currently Present",
                current_present,
                delta=None,
                help="Number of guests currently in the hotel"
            )
            
        with col2:
            st.metric(
                "Today's Check-ins",
                total_checkins,
                delta=None,
                help="Total check-ins today"
            )
            
        with col3:
            st.metric(
                "Today's Check-outs",
                total_checkouts,
                delta=None,
                help="Total check-outs today"
            )
        
        # Present Guests Table
        st.subheader("Currently Present Guests")
        if present_guests:
            df_guests = pd.DataFrame(
                present_guests,
                columns=['Guest Name', 'Check-in Time']
            )
            # Convert check-in time to more readable format
            df_guests['Check-in Time'] = pd.to_datetime(df_guests['Check-in Time']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(
                df_guests,
                column_config={
                    "Guest Name": st.column_config.TextColumn("Guest Name", width="medium"),
                    "Check-in Time": st.column_config.TextColumn("Check-in Time", width="medium")
                },
                hide_index=True,
            )
        else:
            st.info("No guests currently present in the hotel")
        
        st.empty()
        time.sleep(5)  # Refresh every 5 seconds
        st.rerun()
        
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
                    guest_id, name, phone, status, history = existing_guest
                    if status == "checked_in":
                        st.error(f"Guest {name} is already checked in!")
                    else:
                        st.success(f"Welcome back {name}!")
                        
                        # Display guest history
                        st.subheader("Guest History")
                        if history:
                            df_history = pd.DataFrame(
                                history,
                                columns=['Action', 'Time']  # Remove Guest ID from columns
                            )
                            # Convert time to more readable format
                            df_history['Time'] = pd.to_datetime(df_history['Time']).dt.strftime('%Y-%m-%d %H:%M')
                            df_history['Action'] = df_history['Action'].map({
                                'check_in': 'Check In',
                                'check_out': 'Check Out'
                            })
                            st.dataframe(
                                df_history,
                                column_config={
                                    "Action": st.column_config.TextColumn("Action", width="medium"),
                                    "Time": st.column_config.TextColumn("Time", width="medium")
                                },
                                hide_index=True,
                            )
                        else:
                            st.info("No history available")
                            
                        update_name = st.checkbox("Update name?")
                        if update_name:
                            name = st.text_input("New name", name)
                        update_phone = st.checkbox("Update phone?")
                        if update_phone:
                            phone = st.text_input("New phone", phone)
                        if st.button("Confirm Check In"):
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
                


if __name__ == '__main__':
    main()
