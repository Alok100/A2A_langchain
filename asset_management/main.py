import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import psycopg2
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'database': os.getenv('DB_NAME', 'moback_employees')
}
# file_path = "assets/Moback IDC ASSETS  Inventory.xlsx"

# # Read the first sheet
# df = pd.read_excel(file_path)

def get_connection():
    """Create database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        exit(1)

def authenticate_user(email, password):
    "Veryfy user cradencials"
    conn = get_connection()
    if not conn:
        print("❌ Error connecting to database")
        return False,None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, email, role, designation, department_id
        FROM employees
        WHERE email = %s AND password = %s AND status = 'active'
    """, (email, password))

    employee = cursor.fetchone()



    if employee:
        print(f"✅ User authenticated: {employee[1]}")
        user_data = {
            'id': employee[0],
            'full_name': employee[1],
            'email': employee[2],
            'role': employee[3],
            'designation': employee[4],
            'department_id': employee[5]
        }
        cursor.close()
        conn.close()
        return True,user_data
    else:
        print("❌ Invalid email or password")
        cursor.close()
        conn.close()
        return False,None

def show_login_page():
    "Display the login page"
    st.title("Employee Portal login") 
    with st.form("login_form"):
        email= st.text_input("Email", placeholder="Enter your email")
        password= st.text_input("Password", placeholder="Enter your password", type="password")
        submit_button= st.form_submit_button("Login")
        if submit_button:
            success, user_data = authenticate_user(email, password)
            if success:
                st.success(f"Welcome, {user_data['full_name']}!")
                st.session_state['logged_in'] = True  
                st.session_state['user_data'] = user_data
                st.session_state['user_role'] = user_data['role']
                st.rerun()
            else:
                st.error("Invalid email or password")

def show_chat_interface():
    "Display the chat interface"
    user = st.session_state.user_data
    with st.sidebar:
        st.title("User Information")
        st.write(f"Name: {user['full_name']}")
        st.write(f"Email: {user['email']}")
        st.write(f"Designation: {user['designation']}")
        st.write(f"Role: {user['role']}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_data= None
            st.rerun()
    st.title("💬 Asset Management Chat")

def handle_query(user, query):
    pass

def main():
    st.set_page_config(
        page_title="Moback Asset Management",
        page_icon="💼",
        layout="wide"
    )
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None


    
    # Show appropriate page based on login status
    if st.session_state.logged_in:
        show_chat_interface()
    else:
        show_login_page()

if __name__ == "__main__":
    main()






