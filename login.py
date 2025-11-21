
# Login Page


import streamlit as st
from hospital_dashboard import authenticate_user, log_activity


def login_page():
    st.markdown('<div class="main-header">🏥 Hospital Management System</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Secure Login")
        st.info("**Default Credentials:**\n- Admin: `admin` / `admin123`\n- Doctor: `dr_bob` / `doc123`\n- Receptionist: `alice_recep` / `rec123`")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user['username'] #type: ignore
                    st.session_state.role = user['role'] #type: ignore
                    st.session_state.user_id = user['user_id'] #type: ignore
                    
                    log_activity(user['user_id'], user['role'], "Login", f"User {username} logged in") #type: ignore
                    st.success(f"Welcome, {username}!")
                    st.rerun() 
                else:
                    st.error("Invalid credentials!")
                    log_activity(None, None, "Failed Login", f"Failed login attempt for {username}")
            else:
                st.warning("Please enter both username and password")