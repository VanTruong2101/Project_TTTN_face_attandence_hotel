import streamlit as st
import cv2
import face_recognition
import pandas as pd
import numpy as np
from check_in import get_face_encoding, save_guest, check_existing_guest, update_guest
from check_out import update_checkout, get_checked_in_guests
import sqlite3
from datetime import datetime

def get_stats():
    conn = sqlite3.connect('database/hotel_guests.db')
    cursor = conn.cursor()
    
    # Get current date info
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_month = datetime.now().strftime('%Y-%m')
    current_year = datetime.now().strftime('%Y')
    
    # Daily stats
    cursor.execute('''
    SELECT action, COUNT(*) as count
    FROM stats 
    WHERE date(time) = date(?)
    GROUP BY action
    ''', (current_date,))
    daily_stats = dict(cursor.fetchall())
    
    # Weekly stats (last 7 days)
    cursor.execute('''
    SELECT action, COUNT(*) as count
    FROM stats 
    WHERE date(time) >= date(?, '-6 days')
    GROUP BY action
    ''', (current_date,))
    weekly_stats = dict(cursor.fetchall())
    
    # Monthly stats
    cursor.execute('''
    SELECT action, COUNT(*) as count
    FROM stats 
    WHERE strftime('%Y-%m', time) = ?
    GROUP BY action
    ''', (current_month,))
    monthly_stats = dict(cursor.fetchall())
    
    # Yearly stats
    cursor.execute('''
    SELECT action, COUNT(*) as count
    FROM stats 
    WHERE strftime('%Y', time) = ?
    GROUP BY action
    ''', (current_year,))
    yearly_stats = dict(cursor.fetchall())
    
    conn.close()
    return {
        'daily': daily_stats,
        'weekly': weekly_stats,
        'monthly': monthly_stats,
        'yearly': yearly_stats
    }

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
        
        # Add time period selector
        period = st.selectbox(
            "Select Time Period",
            ["Daily", "Weekly", "Monthly", "Yearly"]
        )
        
        if period == "Daily":
            stats = stats_data['daily']
            period_text = "Today"
        elif period == "Weekly":
            stats = stats_data['weekly']
            period_text = "Last 7 Days"
        elif period == "Monthly":
            stats = stats_data['monthly']
            period_text = "This Month"
        else:
            stats = stats_data['yearly']
            period_text = "This Year"
            
        st.subheader(f"Statistics for {period_text}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                f"Check-ins ({period_text})", 
                stats.get('check_in', 0),
            )
        with col2:
            st.metric(
                f"Check-outs ({period_text})", 
                stats.get('check_out', 0),
            )
        
        # Add chart
        if stats:
            chart_data = pd.DataFrame({
                'Action': ['Check-ins', 'Check-outs'],
                'Count': [stats.get('check_in', 0), stats.get('check_out', 0)]
            })
            st.bar_chart(chart_data.set_index('Action'))
            
        # Add detailed table
        st.subheader("Detailed Statistics")
        details = []
        for period_type, period_stats in stats_data.items():
            details.append({
                'Period': period_type.capitalize(),
                'Check-ins': period_stats.get('check_in', 0),
                'Check-outs': period_stats.get('check_out', 0)
            })
        st.table(pd.DataFrame(details))

if __name__ == '__main__':
    main()
