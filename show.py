import streamlit as st
from hospital_dashboard import anonymize_all_patients, add_patient, create_connection, ENCRYPTION_KEY, get_activity_stats, get_logs, check_data_retention, log_activity, Error, get_patients, anonymize_patient_data
import plotly.express as px
from datetime import datetime
import pandas as pd

def show_anonymization():
    st.markdown("### 🔐 Data Anonymization")
    
    st.info("**Anonymization Process:**\n"
            "- Names → ANON_#### format\n"
            "- Contacts → XXX-XXX-#### format\n"
            "- Original data is preserved but hidden from non-admin users")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Bulk Anonymization")
        if st.button("🔒 Anonymize All Patients", key="bulk_anon"):
            with st.spinner("Anonymizing all patient records..."):
                if anonymize_all_patients():
                    st.success("All patient records have been anonymized!")
                    st.rerun()
    
    with col2:
        st.markdown("#### Encryption Status")
        try:
            connection = create_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT COUNT(*) as count FROM patients WHERE encrypted_name IS NOT NULL")
                encrypted_count = cursor.fetchone()['count'] #type: ignore
                cursor.close()
                connection.close()
                st.metric("Encrypted Records", encrypted_count) #type: ignore
        except Error as e:
            st.error(f"Error: {e}")

def show_audit_logs():
    st.markdown("### 📝 Integrity Audit Logs")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.selectbox("Filter by Action:", ["All", "Login", "Logout", "Add Patient", 
                                                            "View Patients", "Anonymize Data", "GDPR Consent"])
    with col2:
        date_filter = st.date_input("Filter by Date:", datetime.now())
    with col3:
        limit = st.selectbox("Show records:", [50, 100, 200, 500])
    
    # Get logs
    all_logs = get_logs()
    
    if all_logs:
        df_logs = pd.DataFrame(all_logs)
        
        # Apply filters
        if action_filter != "All":
            df_logs = df_logs[df_logs['action'] == action_filter]
        
        if date_filter:
            df_logs['date'] = pd.to_datetime(df_logs['timestamp']).dt.date
            df_logs = df_logs[df_logs['date'] == date_filter]
        
        df_logs = df_logs.head(limit)
        
        # Display logs
        st.dataframe(
            df_logs[['log_id', 'timestamp', 'username', 'role', 'action', 'details']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export logs
        csv = df_logs.to_csv(index=False)
        st.download_button(
            label="📥 Export Audit Logs",
            data=csv,
            file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No audit logs found")

def show_analytics():
    st.markdown("### 📈 Real-Time Analytics")
    
    daily_stats, action_stats = get_activity_stats() #type: ignore
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Daily Activity (Last 7 Days)")
        if daily_stats:
            df_daily = pd.DataFrame(daily_stats)
            fig = px.line(df_daily, x='date', y='count', markers=True,
                         labels={'count': 'Actions', 'date': 'Date'},
                         title='User Actions Per Day')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data available")
    
    with col2:
        st.markdown("#### Action Distribution")
        if action_stats:
            df_actions = pd.DataFrame(action_stats)
            fig = px.pie(df_actions, values='count', names='action',
                        title='Actions by Type')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No action data available")
    
    # User activity heatmap
    st.markdown("#### Activity Heatmap")
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT DATE(timestamp) as date, HOUR(timestamp) as hour, COUNT(*) as count
                FROM logs
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(timestamp), HOUR(timestamp)
            """)
            heatmap_data = cursor.fetchall()
            cursor.close()
            connection.close()
            
            if heatmap_data:
                df_heat = pd.DataFrame(heatmap_data)
                pivot_data = df_heat.pivot_table(values='count', index='hour', columns='date', fill_value=0)
                fig = px.imshow(pivot_data, 
                               labels=dict(x="Date", y="Hour of Day", color="Activity Count"),
                               title="Activity Heatmap (Last 7 Days)")
                st.plotly_chart(fig, use_container_width=True)
    except Error as e:
        st.error(f"Error loading analytics: {e}")

def show_gdpr_settings():
    st.markdown("### ⚙️ GDPR Compliance Settings")
    
    # Data retention check
    st.markdown("#### 📅 Data Retention Management")
    expired = check_data_retention()
    
    if expired:
        st.warning(f"⚠️ {len(expired)} patient record(s) have exceeded retention period!")
        df_expired = pd.DataFrame(expired)
        st.dataframe(df_expired, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Delete Expired Records"):
            try:
                connection = create_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("DELETE FROM patients WHERE data_retention_date < CURDATE()")
                    deleted_count = cursor.rowcount
                    connection.commit()
                    cursor.close()
                    connection.close()
                    
                    log_activity(
                        st.session_state.user_id,
                        st.session_state.role,
                        "Data Retention",
                        f"Deleted {deleted_count} expired records"
                    )
                    st.success(f"Deleted {deleted_count} expired record(s)")
                    st.rerun()
            except Error as e:
                st.error(f"Error deleting records: {e}")
    else:
        st.success("✅ All patient records are within retention period")
    
    st.markdown("---")
    
    # Encryption settings
    st.markdown("#### 🔐 Encryption Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Encryption Key Active**\n\nFernet symmetric encryption is enabled for reversible anonymization.")
    
    with col2:
        if st.button("🔑 View Encryption Key"):
            st.code(ENCRYPTION_KEY.decode(), language="text")
            st.warning("⚠️ Keep this key secure! Loss will make data unrecoverable.")
    
    st.markdown("---")
    
    # GDPR compliance checklist
    st.markdown("#### ✅ GDPR Compliance Checklist")
    
    checklist = {
        "Lawfulness, Fairness, Transparency": "✅ User consent obtained via banner",
        "Purpose Limitation": "✅ Data used only for healthcare purposes",
        "Data Minimization": "✅ Only necessary data collected",
        "Accuracy": "✅ Integrity logs maintain data accuracy",
        "Storage Limitation": "✅ 90-day retention policy enforced",
        "Integrity & Confidentiality": "✅ Encryption and anonymization active",
        "Accountability": "✅ Audit logs track all data processing"
    }
    
    for principle, status in checklist.items():
        st.markdown(f"**{principle}:** {status}")
    
    st.markdown("---")
    
    # System backup
    st.markdown("#### 💾 System Backup")
    if st.button("📦 Create Full Backup"):
        try:
            connection = create_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                
                # Export all tables
                cursor.execute("SELECT * FROM patients")
                patients_backup = cursor.fetchall()
                
                cursor.execute("SELECT * FROM logs")
                logs_backup = cursor.fetchall()
                
                cursor.close()
                connection.close()
                
                # Create backup files
                backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                df_patients = pd.DataFrame(patients_backup)
                df_logs = pd.DataFrame(logs_backup)
                
                patients_csv = df_patients.to_csv(index=False)
                logs_csv = df_logs.to_csv(index=False)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.download_button(
                        "📥 Download Patients Backup",
                        patients_csv,
                        file_name=f"patients_backup_{backup_time}.csv",
                        mime="text/csv"
                    )
                with col_b:
                    st.download_button(
                        "📥 Download Logs Backup",
                        logs_csv,
                        file_name=f"logs_backup_{backup_time}.csv",
                        mime="text/csv"
                    )
                
                st.success("Backup created successfully!")
                log_activity(
                    st.session_state.user_id,
                    st.session_state.role,
                    "System Backup",
                    "Full system backup created"
                )
        except Error as e:
            st.error(f"Backup error: {e}")

def show_add_patient():
    st.markdown("### ➕ Add New Patient")
    
    with st.form("add_patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Patient Name*", placeholder="John Doe")
            contact = st.text_input("Contact Number*", placeholder="123-456-7890")
        
        with col2:
            diagnosis = st.text_area("Diagnosis*", placeholder="Enter diagnosis details...")
            use_encryption = st.checkbox("🔐 Enable Fernet Encryption (Reversible)", value=True)
        
        st.markdown("---")
        submitted = st.form_submit_button("➕ Add Patient")
        
        if submitted:
            if name and contact and diagnosis:
                if add_patient(name, contact, diagnosis, encrypt=use_encryption):
                    st.success(f"Patient '{name}' added successfully!")
                    if use_encryption:
                        st.info("✅ Data has been encrypted using Fernet encryption")
                    st.balloons()
            else:
                st.error("Please fill all required fields!")
    
    st.markdown("---")
    
    # Show recent additions (for receptionist)
    st.markdown("### 📋 Recent Additions")
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT patient_id, date_added 
                FROM patients 
                ORDER BY date_added DESC 
                LIMIT 10
            """)
            recent = cursor.fetchall()
            cursor.close()
            connection.close()
            
            if recent:
                df_recent = pd.DataFrame(recent)
                st.dataframe(df_recent, use_container_width=True, hide_index=True)
            else:
                st.info("No records yet")
    except Error as e:
        st.error(f"Error: {e}")

# GDPR Consent Banner
def show_consent_banner():
    if not st.session_state.consent_given:
        st.markdown("""
            <div class="warning-msg">
                <h4>🔒 GDPR Compliance Notice</h4>
                <p>This system processes personal health data in compliance with GDPR regulations. 
                By continuing, you consent to:</p>
                <ul>
                    <li>Processing of personal data for healthcare purposes</li>
                    <li>Data retention for 90 days from record creation</li>
                    <li>Activity logging for security and audit purposes</li>
                    <li>Anonymization of sensitive information</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("I Consent", key="consent_button"):
                st.session_state.consent_given = True
                log_activity(
                    st.session_state.user_id,
                    st.session_state.role,
                    "GDPR Consent",
                    "User provided GDPR consent"
                )
                st.rerun()
        return False
    return True

def show_overview():
    st.markdown("### 📊 System Overview")
    
    # Get statistics
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT COUNT(*) as count FROM patients")
            total_patients = cursor.fetchone()['count'] #type: ignore 
            
            cursor.execute("SELECT COUNT(*) as count FROM patients WHERE is_anonymized = TRUE")
            anonymized_patients = cursor.fetchone()['count'] #type: ignore 
            
            cursor.execute("SELECT COUNT(*) as count FROM logs WHERE DATE(timestamp) = CURDATE()")
            today_activities = cursor.fetchone()['count'] #type: ignore 
            
            cursor.execute("SELECT COUNT(*) as count FROM patients WHERE data_retention_date < CURDATE()")
            expired_records = cursor.fetchone()['count'] #type: ignore 
            
            cursor.close()
            connection.close()
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Patients", total_patients, delta=None) #type: ignore
            with col2:
                st.metric("Anonymized Records", anonymized_patients, #type: ignore
                         delta=f"{(anonymized_patients/total_patients*100):.1f}%" if total_patients > 0 else "0%") #type: ignore
            with col3:
                st.metric("Today's Activities", today_activities) #type: ignore
            with col4:
                st.metric("⚠️ Expired Records", expired_records,  #type: ignore
                         delta="Action Required" if expired_records > 0 else "All Current", #type: ignore
                         delta_color="inverse")
            
            # Recent activity
            st.markdown("### 📋 Recent Activity")
            recent_logs = get_logs()[:10] #type: ignore
            if recent_logs:
                df_logs = pd.DataFrame(recent_logs)
                df_logs = df_logs[['timestamp', 'username', 'role', 'action', 'details']]
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("No recent activity")
    
    except Error as e:
        st.error(f"Error loading overview: {e}")

def show_patients():
    st.markdown("### 👥 Patient Records")
    
    patients = get_patients(st.session_state.role)
    
    if patients:
        df = pd.DataFrame(patients)
        
        if st.session_state.role == 'admin':
            st.markdown("**Full Access Mode** - Viewing all patient data")
            
            # Toggle between raw and anonymized view
            view_mode = st.radio("View Mode:", ["Raw Data", "Anonymized Data"], horizontal=True)
            
            if view_mode == "Raw Data":
                display_df = df[['patient_id', 'name', 'contact', 'diagnosis', 'date_added', 'data_retention_date']]
            else:
                display_df = df[['patient_id', 'anonymized_name', 'anonymized_contact', 'diagnosis', 'date_added']]
                display_df.columns = ['patient_id', 'name', 'contact', 'diagnosis', 'date_added']
        
        elif st.session_state.role == 'doctor':
            st.markdown("**Anonymized View** - Patient identities are protected")
            display_df = df[['patient_id', 'name', 'contact', 'diagnosis', 'date_added']]
        
        else:  # receptionist
            st.markdown("**Limited Access** - Sensitive data is hidden")
            display_df = df[['patient_id', 'date_added']]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export option
        if st.session_state.role in ['admin', 'doctor']:
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"patients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            if st.session_state.role == 'admin':
                # Individual anonymization
                st.markdown("---")
                st.markdown("### 🔒 Individual Anonymization")
                patient_ids = df['patient_id'].tolist()
                selected_id = st.selectbox("Select Patient ID to Anonymize:", patient_ids)
                
                if st.button("Anonymize Selected Patient"):
                    if anonymize_patient_data(selected_id):
                        st.success(f"Patient ID {selected_id} has been anonymized!")
                        st.rerun()
    else:
        st.info("No patient records found")
