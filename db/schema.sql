CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'doctor', 'receptionist') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
);

CREATE TABLE IF NOT EXISTS logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    role VARCHAR(50),
    action VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);