from venv import create
import streamlit as st
import mysql.connector
from mysql.connector import Error
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from cryptography.fernet import Fernet
import base64
import os
from config import config
from db.db import create_connection, initialize_database

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state=config.INITIAL_SIDEBAR_STATE
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-msg {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-msg {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


# Encryption key generation (store this securely in production)
ENCRYPTION_KEY = b'8cozhW9kSi6zJQw3xLvMp_6T3Nq3qjWPHvXFnwi4IxE='  # Generated key

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'consent_given' not in st.session_state:
    st.session_state.consent_given = False
if 'system_start_time' not in st.session_state:
    st.session_state.system_start_time = datetime.now()


def log_activity(user_id, role, action, details=""):
    """Log user activity"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO logs (user_id, role, action, details) VALUES (%s, %s, %s, %s)",
                (user_id, role, action, details)
            )
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        st.error(f"Logging error: {e}")

def authenticate_user(username, password):
    """Authenticate user credentials"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                "SELECT user_id, username, role FROM users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            return user
    except Error as e:
        st.error(f"Authentication error: {e}")
        return None

def encrypt_data(data):
    """Encrypt data using Fernet"""
    try:
        f = Fernet(ENCRYPTION_KEY)
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        st.error(f"Encryption error: {e}")
        return None

def decrypt_data(encrypted_data):
    """Decrypt data using Fernet"""
    try:
        f = Fernet(ENCRYPTION_KEY)
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        st.error(f"Decryption error: {e}")
        return None

def anonymize_name(name, patient_id):
    """Anonymize patient name"""
    return f"ANON_{patient_id:04d}"

def anonymize_contact(contact):
    """Anonymize contact number"""
    if len(contact) >= 4:
        return "XXX-XXX-" + contact[-4:]
    return "XXX-XXX-XXXX"

def add_patient(name, contact, diagnosis, encrypt=False):
    """Add new patient record"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            
            # Set data retention date (90 days from now for GDPR compliance)
            retention_date = (datetime.now() + timedelta(days=90)).date()
            
            if encrypt:
                encrypted_name = encrypt_data(name)
                encrypted_contact = encrypt_data(contact)
                cursor.execute(
                    """INSERT INTO patients (name, contact, diagnosis, encrypted_name, 
                       encrypted_contact, data_retention_date, is_anonymized) 
                       VALUES (%s, %s, %s, %s, %s, %s, FALSE)""",
                    (name, contact, diagnosis, encrypted_name, encrypted_contact, retention_date)
                )
            else:
                cursor.execute(
                    """INSERT INTO patients (name, contact, diagnosis, data_retention_date, is_anonymized) 
                       VALUES (%s, %s, %s, %s, FALSE)""",
                    (name, contact, diagnosis, retention_date)
                )
            
            connection.commit()
            patient_id = cursor.lastrowid
            cursor.close()
            connection.close()
            
            log_activity(
                st.session_state.user_id,
                st.session_state.role,
                "Add Patient",
                f"Added patient ID: {patient_id}"
            )
            return True
    except Error as e:
        st.error(f"Error adding patient: {e}")
        return False

def anonymize_patient_data(patient_id):
    """Anonymize specific patient data"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT name, contact FROM patients WHERE patient_id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if patient:
                anon_name = anonymize_name(patient['name'], patient_id) #type: ignore
                anon_contact = anonymize_contact(patient['contact']) #type: ignore
                
                cursor.execute(
                    """UPDATE patients SET anonymized_name = %s, anonymized_contact = %s, 
                       is_anonymized = TRUE WHERE patient_id = %s""",
                    (anon_name, anon_contact, patient_id)
                )
                connection.commit()
                
                log_activity(
                    st.session_state.user_id,
                    st.session_state.role,
                    "Anonymize Data",
                    f"Anonymized patient ID: {patient_id}"
                )
            
            cursor.close()
            connection.close()
            return True
    except Error as e:
        st.error(f"Error anonymizing data: {e}")
        return False

def anonymize_all_patients():
    """Anonymize all patient records"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT patient_id, name, contact FROM patients")
            patients = cursor.fetchall()
            
            for patient in patients:
                anon_name = anonymize_name(patient['name'], patient['patient_id']) #type: ignore
                anon_contact = anonymize_contact(patient['contact']) #type: ignore
                
                cursor.execute(
                    """UPDATE patients SET anonymized_name = %s, anonymized_contact = %s, 
                       is_anonymized = TRUE WHERE patient_id = %s""",
                    (anon_name, anon_contact, patient['patient_id']) #type: ignore
                )
            
            connection.commit()
            cursor.close()
            connection.close()
            
            log_activity(
                st.session_state.user_id,
                st.session_state.role,
                "Bulk Anonymization",
                f"Anonymized {len(patients)} patient records"
            )
            return True
    except Error as e:
        st.error(f"Error in bulk anonymization: {e}")
        return False

def get_patients(role):
    """Get patients based on role"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            if role == 'admin':
                cursor.execute("""
                    SELECT patient_id, name, contact, diagnosis, 
                           anonymized_name, anonymized_contact, 
                           date_added, data_retention_date, is_anonymized
                    FROM patients ORDER BY patient_id DESC
                """)
            elif role == 'doctor':
                cursor.execute("""
                    SELECT patient_id, anonymized_name as name, 
                           anonymized_contact as contact, diagnosis, 
                           date_added, is_anonymized
                    FROM patients WHERE is_anonymized = TRUE 
                    ORDER BY patient_id DESC
                """)
            else:  # receptionist
                cursor.execute("""
                    SELECT patient_id, 'HIDDEN' as name, 'HIDDEN' as contact, 
                           'HIDDEN' as diagnosis, date_added
                    FROM patients ORDER BY patient_id DESC
                """)
            
            patients = cursor.fetchall()
            cursor.close()
            connection.close()
            
            log_activity(
                st.session_state.user_id,
                st.session_state.role,
                "View Patients",
                f"Accessed patient records"
            )
            
            return patients
    except Error as e:
        st.error(f"Error fetching patients: {e}")
        return []

def get_logs():
    """Get all activity logs"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT l.log_id, l.user_id, u.username, l.role, l.action, 
                       l.timestamp, l.details
                FROM logs l
                JOIN users u ON l.user_id = u.user_id
                ORDER BY l.timestamp DESC
                LIMIT 100
            """)
            logs = cursor.fetchall()
            cursor.close()
            connection.close()
            return logs
    except Error as e:
        st.error(f"Error fetching logs: {e}")
        return []

def get_activity_stats():
    """Get activity statistics for dashboard"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Get action counts by day (last 7 days)
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM logs
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            daily_stats = cursor.fetchall()
            
            # Get action counts by type
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM logs
                GROUP BY action
                ORDER BY count DESC
            """)
            action_stats = cursor.fetchall()
            
            cursor.close()
            connection.close()
            return daily_stats, action_stats
    except Error as e:
        st.error(f"Error fetching stats: {e}")
        return [], []

def check_data_retention():
    """Check and flag patients past retention date"""
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT patient_id, name, data_retention_date
                FROM patients
                WHERE data_retention_date < CURDATE()
            """)
            expired = cursor.fetchall()
            cursor.close()
            connection.close()
            return expired
    except Error as e:
        st.error(f"Error checking retention: {e}")
        return []


