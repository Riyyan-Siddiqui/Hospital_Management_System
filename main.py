# Main Application Logic
from hospital_dashboard import initialize_database
import streamlit as st
from login import login_page
from main_dashboard import main_dashboard


def main():
    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    # Initialize database
    if initialize_database():
        if not st.session_state.logged_in:
            login_page()
        else:
            main_dashboard()
    else:
        st.error("❌ Failed to initialize database. Please check MySQL connection settings.")
        st.info(
            "**Configuration Required:**\n"
            "1. Ensure MySQL server is running\n"
            "2. Update DB_CONFIG in the code with your credentials\n"
            "3. Grant necessary permissions to the MySQL user"
        )


if __name__ == "__main__":
    main()
