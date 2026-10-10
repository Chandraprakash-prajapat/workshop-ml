-- DROP DATABASE IF EXISTS clinic;
-- CREATE DATABASE clinic;
-- USE clinic; 

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,            -- bcrypt hash, never plain password
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE TABLE IF NOT EXISTS doctors (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) UNIQUE,
    specialty VARCHAR(60)
);
 
CREATE TABLE IF NOT EXISTS slots (                  -- one row = one bookable time of one doctor
    id         INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id  INT,
    slot_time  DATETIME,
    is_booked  TINYINT DEFAULT 0,
    UNIQUE KEY uq_slot (doctor_id, slot_time),      -- a doctor can't have two slots at one time
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);
 
CREATE TABLE IF NOT EXISTS appointments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    doctor_id  INT,
    slot_id    INT,
    status     VARCHAR(12) NOT NULL DEFAULT 'booked',   -- booked or cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    FOREIGN KEY (slot_id)   REFERENCES slots(id)
);
 
CREATE TABLE IF NOT EXISTS patient_history (        -- which doctor treated which problem (returning patients)
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    doctor_id  INT,
    problem    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);
 
CREATE TABLE IF NOT EXISTS summaries (              -- short running summary per patient (saves AI tokens)
    user_id    INT PRIMARY KEY,
    summary    TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
 
CREATE TABLE IF NOT EXISTS screenings (             -- every covid screening a logged-in patient runs
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    age        INT,
    gender     VARCHAR(10),
    fever      FLOAT,
    cough      VARCHAR(10),
    city       VARCHAR(60),
    result     VARCHAR(10),                              -- Positive or Negative (model output)
    confidence FLOAT,
    source     VARCHAR(10),                              -- form or chat
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Added by clinic staff on the /admin page (a patient can only read these)
CREATE TABLE IF NOT EXISTS prescriptions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    doctor_id  INT,
    medicine   VARCHAR(150) NOT NULL,
    dosage     VARCHAR(150),
    notes      VARCHAR(300),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

CREATE TABLE IF NOT EXISTS bills (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    description VARCHAR(200) NOT NULL,
    amount      DECIMAL(10,2) NOT NULL,
    status      VARCHAR(10) DEFAULT 'pending',      -- pending or paid
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS medical_records (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    doctor_id   INT,
    title       VARCHAR(150) NOT NULL,
    record_type VARCHAR(40),                        -- e.g. Lab report, X-ray, Visit note
    summary     VARCHAR(500),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

INSERT IGNORE INTO doctors (name, specialty) VALUES
    ('Dr. Suresh Verma',  'General Physician'),
    ('Dr. Anita Rao',     'General Physician'),
    ('Dr. Rahul Mehta',   'Neurologist'),
    ('Dr. Kavita Nair',   'Neurologist'),
    ('Dr. Imran Khan',    'Orthopedic'),
    ('Dr. Sunita Joshi',  'Orthopedic'),
    ('Dr. Arjun Sethi',   'Gastroenterologist'),
    ('Dr. Meera Iyer',    'Gastroenterologist'),
    ('Dr. Neha Kapoor',   'Dermatologist'),
    ('Dr. Vikram Bose',   'ENT');
 


CREATE TABLE IF NOT EXISTS api_logs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id      INT NULL,
    role         VARCHAR(20),
    method       VARCHAR(8),
    path         VARCHAR(100),
    status_code  INT,
    tool         VARCHAR(200),
    tokens_in    INT DEFAULT 0,
    tokens_out   INT DEFAULT 0,
    tokens_total INT DEFAULT 0,
    latency_ms   INT DEFAULT 0
);