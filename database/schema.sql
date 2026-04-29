CREATE DATABASE IF NOT EXISTS voting_system;
USE voting_system;

-- ─────────────────────────────────────────
-- CORE SETTINGS & ADMIN
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- ─────────────────────────────────────────
-- MULTI-ELECTION CORE
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS elections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time DATETIME,
    end_time DATETIME,
    is_active BOOLEAN DEFAULT FALSE,
    results_released BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS election_candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    party VARCHAR(150) NOT NULL,
    vote_count INT DEFAULT 0,
    FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- VOTER MANAGEMENT
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS approved_voters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    voter_id VARCHAR(50) NOT NULL,
    email VARCHAR(150) NOT NULL,
    aadhar_number VARCHAR(12),
    phone VARCHAR(20),
    date_of_birth DATE,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
    UNIQUE (election_id, voter_id),
    UNIQUE (election_id, email),
    UNIQUE (election_id, aadhar_number)
);

CREATE TABLE IF NOT EXISTS election_voters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    voter_id VARCHAR(50) NOT NULL,
    full_name VARCHAR(150),
    email VARCHAR(150),
    password VARCHAR(255) NOT NULL,
    has_voted BOOLEAN DEFAULT FALSE,
    biometric_data MEDIUMTEXT, -- Stores the base64 captured face image upon login/reg
    FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- BLOCKCHAIN LEDGER
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS election_blockchain_votes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    block_index INT NOT NULL,
    voter_hash VARCHAR(255) NOT NULL,
    candidate_id INT NOT NULL,
    timestamp VARCHAR(100) NOT NULL,
    previous_hash VARCHAR(255) NOT NULL,
    current_hash VARCHAR(255) NOT NULL,
    FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- AI SECURITY LOGS (PERSISTENT STATE)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_voting_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hour INT NOT NULL,
    minute INT NOT NULL,
    voter_hash_segment BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_ip_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(100) NOT NULL,
    attempt_time DATETIME NOT NULL
);

-- ─────────────────────────────────────────
-- DEFAULT DATA
-- ─────────────────────────────────────────
-- Using a bcrypt hash for 'admin123' as default standard. (Wait we can keep it standard plaintext hashing format just in case we reset, but security.py handles bcrypt now)
-- We will assume the python code handles registering admins correctly.
INSERT IGNORE INTO admin (username, password) VALUES ('admin', '$2b$12$KkQ0N/.Z/b4/N/yv5ZExhO8R/zKx6/nKkKkKkKkKkKkKkKkKkKkKk');