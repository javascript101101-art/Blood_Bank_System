-- ၁။ Hospitals Table (PostgreSQL အတွက်)
CREATE TABLE IF NOT EXISTS hospitals (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    api_key CHAR(36) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ၂။ Hospital Requests Table (PostgreSQL အတွက်)
CREATE TABLE IF NOT EXISTS hospital_requests (
    id CHAR(36) PRIMARY KEY,
    hospital_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    contact_email VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    hospital_id CHAR(36),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);