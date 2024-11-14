import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date
import time
import hashlib

# Database connection function
def get_database_connection():
    return mysql.connector.connect(
        host="localhost",
        user="bhoomi_dbms",
        password="bhoomi@23dbms",
        database="mentor_mentee"
    )


# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Registration function
def register_user(name, department, contact, password, user_type):
    if not name or not department or not contact or not password:
        st.error("All fields are required")
        return False
    if len(password) < 8:
        st.error("Password must be at least 8 characters long")
        return False
    conn = get_database_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    
    try:
        if user_type == "Mentor":
            cursor.execute("""
                INSERT INTO Mentor (Name, Department, Contact_Info, Password) 
                VALUES (%s, %s, %s, %s)
            """, (name, department, contact, hashed_password))
        else:
            # For mentee, we need to assign a mentor
            cursor.execute("SELECT Mentor_ID, Name FROM Mentor")
            mentors = cursor.fetchall()
            if not mentors:
                st.error("No mentors available for assignment. Please try again later.")
                return False
                
            # Assign to mentor with least mentees
            cursor.execute("""
                SELECT m.Mentor_ID, COUNT(me.Mentee_ID) as mentee_count
                FROM Mentor m
                LEFT JOIN Mentee me ON m.Mentor_ID = me.Mentor_ID
                GROUP BY m.Mentor_ID
                ORDER BY mentee_count ASC
                LIMIT 1
            """)
            mentor_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO Mentee (Name, Mentor_ID, Academic_Details, Contact_Info, Password) 
                VALUES (%s, %s, %s, %s, %s)
            """, (name, mentor_id, department, contact, hashed_password))
        
        conn.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

# Registration function for students
def register_student(name, details, contact, password):
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.callproc('AssignStudentToMentor', [name, details, contact, hash_password(password)])
        conn.commit()
        st.success("Registration successful! You have been assigned to a mentor.")
    except mysql.connector.Error as err:
        st.error(f"Error registering student: {err}")
    finally:
        cursor.close()
        conn.close()

# Login function
def login(username, password, user_type):
    conn = get_database_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    
    try:
        if user_type == "Mentor":
            cursor.execute("""
                SELECT Mentor_ID, Name 
                FROM Mentor 
                WHERE Name = %s AND Password = %s
            """, (username, hashed_password))
        else:
            cursor.execute("""
                SELECT Mentee_ID, Name 
                FROM Mentee 
                WHERE Name = %s AND Password = %s
            """, (username, hashed_password))
        
        result = cursor.fetchone()
        if result:
            st.session_state.logged_in = True
            st.session_state.user_type = user_type
            st.session_state.user_id = result[0]
            return True
        return False
    finally:
        cursor.close()
        conn.close()

# Registration page
def show_registration():
    st.subheader("Register New Account")
    user_type = st.selectbox("Register as", ["Mentor", "Mentee"])
    name = st.text_input("Full Name")
    department = st.text_input("Department" if user_type == "Mentor" else "Academic Details")
    contact = st.text_input("Contact Information")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords don't match!")
            return
        
        if user_type == "Mentor":
            if register_user(name, department, contact, password, user_type):
                st.success("Registration successful! Please login.")
                time.sleep(2)
                st.experimental_rerun()
        else:
            if register_student(name, department, contact, password):
                time.sleep(2)
                st.experimental_rerun()

# Main login page
def show_login():
    st.title("Mentor-Mentee Management System")
    
    # Create tabs for Login and Registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        user_type = st.selectbox("Select User Type", ["Mentor", "Mentee"], key="login_user_type")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login(username, password, user_type):
                st.success("Login successful!")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
    
    with tab2:
        show_registration()

# Mentor Dashboard
def mentor_dashboard():
    st.title(f"Welcome, Mentor!")
    menu = st.sidebar.selectbox(
        "Menu",
        ["View Students", "Schedule Meeting", "View Meetings", "Add Meeting Report"]
    )
    
    if menu == "View Students":
        show_student_list()
    elif menu == "Schedule Meeting":
        schedule_meeting()
    elif menu == "View Meetings":
        view_meetings()
    elif menu == "Add Meeting Report":
        add_meeting_report()

def show_student_list():
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.callproc('GetStudentListAndCount', [st.session_state.user_id])
    
    for result in cursor.stored_results():
        data = result.fetchall()
        if data:
            df = pd.DataFrame(data, columns=["Mentee ID", "Name", "Academic Details", "Contact Info"])
            st.write("Your Students:")
            st.dataframe(df)
    
    cursor.close()
    conn.close()

def schedule_meeting():
    meeting_date = st.date_input("Meeting Date", key="meeting_date")
    if meeting_date < date.today():
        st.error("Cannot schedule meetings in the past")
        return
    st.subheader("Schedule New Meeting")
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Get mentees for the current mentor
    cursor.execute("SELECT Mentee_ID, Name FROM Mentee WHERE Mentor_ID = %s", 
                  (st.session_state.user_id,))
    mentees = cursor.fetchall()
    
    if mentees:
        mentee_dict = {name: id for id, name in mentees}
        selected_mentee = st.selectbox("Select Student", list(mentee_dict.keys()), key="selected_mentee")
        meeting_date = st.date_input("Meeting Date", key="meeting_date_2")
        meeting_time = st.time_input("Meeting Time", key="meeting_time")
        agenda = st.text_area("Agenda", key="meeting_agenda")
        
        if st.button("Schedule Meeting", key="schedule_meeting"):
            try:
                cursor.callproc('AddMeeting', 
                              [st.session_state.user_id, mentee_dict[selected_mentee],
                               meeting_date, meeting_time, agenda])
                conn.commit()
                st.success("Meeting scheduled successfully!")
            except Exception as e:
                st.error(f"Error scheduling meeting: {str(e)}")
    else:
        st.warning("No mentees assigned to you yet.")
    
    cursor.close()
    conn.close()

def view_meetings():
    conn = get_database_connection()
    cursor = conn.cursor()

    st.subheader("Upcoming Meetings")
    cursor.execute("""
        SELECT m.Meeting_ID, me.Name, m.Date, m.Time, m.Agenda
        FROM Meeting m
        JOIN Mentee me ON m.Mentee_ID = me.Mentee_ID
        WHERE m.Mentor_ID = %s AND m.Date >= CURRENT_DATE
        ORDER BY m.Date, m.Time
    """, (st.session_state.user_id,))

    meetings = cursor.fetchall()
    if meetings:
        # Filter out meetings that have already occurred
        upcoming_meetings = [m for m in meetings if m[2] >= date.today()]
        if upcoming_meetings:
            # Create columns for the layout
            for meeting in upcoming_meetings:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"""
                    **Student:** {meeting[1]}  
                    **Date:** {meeting[2]}  
                    **Time:** {meeting[3]}  
                    **Agenda:** {meeting[4]}
                    """)
                
                with col2:
                    if st.button("Delete Meeting", key=f"delete_{meeting[0]}"):
                        if delete_meeting(meeting[0]):
                            st.experimental_rerun()
                
                st.divider()
        else:
            st.info("No upcoming meetings scheduled.")
    else:
        st.info("No upcoming meetings scheduled.")

    cursor.close()
    conn.close()

def add_meeting_report():
    st.subheader("Add Meeting Report")
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Get recent meetings
    cursor.execute("""
        SELECT m.Meeting_ID, me.Name, m.Date, m.Time
        FROM Meeting m
        JOIN Mentee me ON m.Mentee_ID = me.Mentee_ID
        WHERE m.Mentor_ID = %s AND m.Date <= CURRENT_DATE
        ORDER BY m.Date DESC LIMIT 10
    """, (st.session_state.user_id,))
    
    meetings = cursor.fetchall()
    if meetings:
        meeting_dict = {f"{row[1]} - {row[2]} {row[3]}": row[0] for row in meetings}
        selected_meeting = st.selectbox("Select Meeting", list(meeting_dict.keys()))
        report_text = st.text_area("Report")
        
        if st.button("Submit Report"):
            try:
                cursor.callproc('AddMeetingReport', 
                              [meeting_dict[selected_meeting], 
                               st.session_state.user_id, report_text])
                conn.commit()
                st.success("Report submitted successfully!")
            except Exception as e:
                st.error(f"Error submitting report: {str(e)}")
    else:
        st.info("No completed meetings found.")
    
    cursor.close()
    conn.close()

def delete_meeting(meeting_id):
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Call the stored procedure
        args = [meeting_id, st.session_state.user_id, 0]  # 0 is for OUT parameter
        result = cursor.callproc('DeleteMeeting', args)
        conn.commit()
        
        # Check if deletion was successful (check OUT parameter)
        if result[2]:  # Third parameter (index 2) is our OUT parameter
            st.success("Meeting deleted successfully!")
            return True
        else:
            st.error("Unable to delete meeting. Please ensure it exists and you have permission.")
            return False
            
    except mysql.connector.Error as err:
        st.error(f"Error deleting meeting: {str(err)}")
        return False
    finally:
        cursor.close()
        conn.close()


# Mentee Dashboard
def mentee_dashboard():
    st.title(f"Welcome, Student!")
    
    # Get the mentee's mentor name
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT m.Name FROM Mentee me JOIN Mentor m ON me.Mentor_ID = m.Mentor_ID WHERE me.Mentee_ID = %s", (st.session_state.user_id,))
    mentor_name = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    # Display the mentor name in a sidebar
    st.sidebar.write(f"Your mentor is: **{mentor_name}**")
    
    menu = st.sidebar.selectbox(
        "Menu",
        ["View Upcoming Meetings", "View Meeting Reports", "View Notifications"]
    )
    
    if menu == "View Upcoming Meetings":
        view_upcoming_meetings_mentee()
    elif menu == "View Meeting Reports":
        view_meeting_reports()
    elif menu == "View Notifications":
        view_notifications()

def view_upcoming_meetings_mentee():
    conn = get_database_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.Meeting_ID, me.Name as Mentor, m.Date, m.Time, m.Agenda
        FROM Meeting m
        JOIN Mentor me ON m.Mentor_ID = me.Mentor_ID
        WHERE m.Mentee_ID = %s AND m.Date >= CURRENT_DATE
        ORDER BY m.Date, m.Time
    """, (st.session_state.user_id,))
    
    meetings = [row for row in cursor.fetchall() if row[2] >= date.today()]
    
    if meetings:
        df = pd.DataFrame(meetings, 
                         columns=["Meeting ID", "Mentor", "Date", "Time", "Agenda"])
        st.write("Your Upcoming Meetings:")
        st.dataframe(df)
    else:
        st.info("No upcoming meetings scheduled.")
    
    cursor.close()
    conn.close()

def view_meeting_reports():
    conn = get_database_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT mr.Report_Date, m.Date as Meeting_Date, me.Name as Mentor, mr.Report_Text
        FROM Meeting_Report mr
        JOIN Meeting m ON mr.Meeting_ID = m.Meeting_ID
        JOIN Mentor me ON mr.Mentor_ID = me.Mentor_ID
        WHERE m.Mentee_ID = %s
        ORDER BY mr.Report_Date DESC
    """, (st.session_state.user_id,))
    
    reports = cursor.fetchall()
    if reports:
        df = pd.DataFrame(reports, 
                         columns=["Report Date", "Meeting Date", "Mentor", "Report"])
        st.write("Your Meeting Reports:")
        st.dataframe(df)
    else:
        st.info("No meeting reports available.")
    
    cursor.close()
    conn.close()

def view_notifications():
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 'New meeting scheduled' as Message, m.Date as Notification_Date
        FROM Meeting m
        WHERE m.Mentee_ID = %s AND m.Date >= CURRENT_DATE
        UNION
        SELECT 'Meeting report available' as Message, mr.Report_Date as Notification_Date
        FROM Meeting_Report mr
        JOIN Meeting m ON mr.Meeting_ID = m.Meeting_ID
        WHERE m.Mentee_ID = %s
        ORDER BY Notification_Date DESC
    """, (st.session_state.user_id, st.session_state.user_id))

    notifications = cursor.fetchall()
    if notifications:
        df = pd.DataFrame(notifications, columns=["Message", "Notification_Date"])
        st.write("Your Notifications:")
        st.dataframe(df)
    else:
        st.info("No notifications available.")

    cursor.close()
    conn.close()

# Main app logic
def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        if st.session_state.user_type == "Mentor":
            mentor_dashboard()
        else:
            mentee_dashboard()
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.user_id = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()