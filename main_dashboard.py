# Main Dashboard
import datetime
import streamlit as st
from hospital_dashboard import log_activity
from show import show_anonymization, show_audit_logs, show_analytics, show_gdpr_settings, show_add_patient, show_consent_banner, show_overview, show_patients


def main_dashboard():
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 User: {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.role.upper()}")
        st.markdown("---")
        
        # Calculate uptime
        uptime = datetime.datetime.now() - st.session_state.system_start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        st.markdown(f"**⏱️ System Uptime:** {hours}h {minutes}m")
        st.markdown(f"**🕐 Last Sync:** {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        st.markdown("---")
        if st.button("🚪 Logout", key="logout_button"):
            log_activity(
                st.session_state.user_id,
                st.session_state.role,
                "Logout",
                f"User {st.session_state.username} logged out"
            )
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.user_id = None
            st.rerun()
    
    # Show consent banner
    if not show_consent_banner():
        return
    
    # Main header
    st.markdown('<div class="main-header">🏥 Hospital Management Dashboard</div>', unsafe_allow_html=True)
    
    # Create tabs based on role
    if st.session_state.role == 'admin':
        tabs = st.tabs(["📊 Overview", "👥 Patients", "🔐 Anonymization", "📝 Audit Logs", "📈 Analytics", "⚙️ GDPR Settings"])
        
        with tabs[0]:
            show_overview()
        with tabs[1]:
            show_patients()
        with tabs[2]:
            show_anonymization()
        with tabs[3]:
            show_audit_logs()
        with tabs[4]:
            show_analytics()
        with tabs[5]:
            show_gdpr_settings()
    
    elif st.session_state.role == 'doctor':
        tabs = st.tabs(["📊 Overview", "👥 Patients"])
        
        with tabs[0]:
            show_overview()
        with tabs[1]:
            show_patients()
    
    else:  # receptionist
        tabs = st.tabs(["📊 Overview", "➕ Add Patient"])
        
        with tabs[0]:
            show_overview()
        with tabs[1]:
            show_add_patient()