# Hospital Management System Dashboard

## Project Overview
A community hospital is transitioning from paper-based records to a **digital hospital management system** while ensuring compliance with **GDPR** and maintaining privacy, integrity, and availability of patient data.  

This project demonstrates a **privacy-centric, role-based dashboard** built using **Streamlit, Python, and MySQL**, with encrypted and anonymized patient data, secure activity logs, and role-based access control (RBAC).

---

## Scenario
The hospital requires a system that ensures:

- **Confidentiality:** Patient identities and medical data are masked or encrypted.  
- **Integrity:** Only authorized users can modify or audit data; all changes are logged.  
- **Availability:** System remains functional and responsive with proper exception handling.

---

## Features

### 1. Confidentiality
- Login authentication for users (Admin, Doctor, Receptionist).  
- Role-based access control:
  - **Admin:** Full access to raw and anonymized data.  
  - **Doctor:** View anonymized patient data only.  
  - **Receptionist:** Add/Edit patient records but cannot see sensitive fields.  
- Sensitive data anonymization/masking:
  - Name → `ANON_1021`  
  - Contact → `XXX-XXX-4592`  
- Optionally, sensitive fields are encrypted using Python's `hashlib` or `Fernet`.

### 2. Integrity
- Activity logs recording:
  - User ID & role  
  - Action type (login, data anonymization, record update)  
  - Timestamp & details  
- Database constraints and code validation to prevent unauthorized changes.  
- Admin-only **Integrity Audit Log** page.

### 3. Availability
- Stable dashboard and database connectivity.  
- Proper error handling for login and DB exceptions.  
- Data backup/export (CSV download).  
- Dashboard displays system uptime or last synchronization.

---

## Database Schema

**Users Table**

| user_id | username    | password  | role         |
|---------|------------|----------|-------------|
| 1       | admin      | admin123 | admin       |
| 2       | dr_bob     | doc123   | doctor      |
| 3       | alice_recep| rec123   | receptionist|

**Patients Table**

| patient_id | name | contact | diagnosis | anonymized_name | anonymized_contact | date_added |

**Logs Table**

| log_id | user_id | role | action | timestamp | details |

---

## Example Workflow
1. User logs in → authentication verifies credentials and assigns role.  
2. Role defines permitted actions.  
3. Admin triggers **Anonymize Data** → sensitive fields masked/encrypted.  
4. Doctor views anonymized patient data.  
5. Receptionist adds/edits records without seeing masked data.  
6. All actions logged with timestamps.  
7. Admin reviews audit logs and exports them if needed.

---

## Tech Stack
- **Python**: Backend logic and processing  
- **Streamlit**: Frontend dashboard and UI  
- **MySQL Workbench**: Database management and queries  
- **Optional Libraries:** `hashlib`, `cryptography` (Fernet) for data encryption

---

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/hospital-management-dashboard.git
cd hospital-management-dashboard
2. Create and Configure .env File
Create a .env in the root directory (never push your real .env to GitHub):

env
Copy code
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=hospital_db
Replace your_mysql_password with your local MySQL password.

Ensure MySQL server is running and database exists.

3. Install Dependencies
bash
Copy code
pip install -r requirements.txt
Example requirements.txt

nginx
Copy code
streamlit
mysql-connector-python
cryptography
4. Initialize Database
Run hospital_dashboard.py to create tables if they do not exist.

Or import hospital_db.sql into MySQL Workbench.

5. Run the Application
bash
Copy code
streamlit run main.py
Open the browser → navigate to http://localhost:8501/
