CREATE DATABASE IF NOT EXISTS voting_system;
USE voting_system;

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Voters table
CREATE TABLE IF NOT EXISTS voters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    voter_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    has_voted BOOLEAN DEFAULT FALSE
);

-- Candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    party VARCHAR(150) NOT NULL,
    vote_count INT DEFAULT 0
);

-- Blockchain votes table
CREATE TABLE IF NOT EXISTS blockchain_votes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    block_index INT NOT NULL,
    voter_hash VARCHAR(255) NOT NULL,
    candidate_id INT NOT NULL,
    timestamp VARCHAR(100) NOT NULL,
    previous_hash VARCHAR(255) NOT NULL,
    current_hash VARCHAR(255) NOT NULL
);

-- Election status table
CREATE TABLE IF NOT EXISTS election_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    is_active BOOLEAN DEFAULT FALSE
);

-- Default data
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');
INSERT INTO election_status (is_active) VALUES (FALSE);
INSERT INTO candidates (name, party) VALUES
('Candidate A', 'Party Alpha'),
('Candidate B', 'Party Beta'),
('Candidate C', 'Party Gamma');