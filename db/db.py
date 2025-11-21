# Database Functions
from copy import Error
import mysql.connector
import streamlit as st
from config import config
import hashlib


def create_connection():
    """Create database connection with error handling"""
    try:
        connection = mysql.connector.connect(**config.DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None

def initialize_database():
    """Initialize database and create tables"""
    try:
        # Connect without database first
        temp_config = config.DB_CONFIG.copy()
        db_name = temp_config.pop('database')
        connection = mysql.connector.connect(**temp_config)
        cursor = connection.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'doctor', 'receptionist') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                contact VARCHAR(50) NOT NULL,
                diagnosis TEXT,
                anonymized_name VARCHAR(50),
                anonymized_contact VARCHAR(50),
                encrypted_name TEXT,
                encrypted_contact TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_retention_date DATE,
                is_anonymized BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                role VARCHAR(50),
                action VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Insert default users if not exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0: #type: ignore
            default_users = [
                ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin'),
                ('dr_bob', hashlib.sha256('doc123'.encode()).hexdigest(), 'doctor'),
                ('alice_recep', hashlib.sha256('rec123'.encode()).hexdigest(), 'receptionist')
            ]
            cursor.executemany(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                default_users
            )
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        st.error(f"Database initialization error: {e}")
        return False
