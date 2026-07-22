-- ပထမဆုံး UUID Extension ကို Enable လုပ်ပါ
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ၁။ ဆေးရုံများစာရင်း (Global Master)
CREATE TABLE hospitals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    location TEXT,
    contact_email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ၂။ အသုံးပြုသူများ (Global Admin အပါအဝင် ဆေးရုံအားလုံးမှ)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID REFERENCES hospitals(id) ON DELETE CASCADE,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('Global_Admin', 'Hospital_Admin', 'Lab_Staff', 'Receptionist')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ၃။ အလှူရှင်များ (Global Consolidated)
CREATE TABLE donors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    dob DATE,
    blood_group VARCHAR(3) NOT NULL CHECK (blood_group IN ('A', 'B', 'AB', 'O')),
    rh_factor VARCHAR(10) NOT NULL CHECK (rh_factor IN ('Positive', 'Negative')),
    contact_phone VARCHAR(20),
    email VARCHAR(255),
    last_donation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ၄။ သွေးတိုက်စာရင်း (Global Consolidated)
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    blood_group VARCHAR(3) NOT NULL CHECK (blood_group IN ('A', 'B', 'AB', 'O')),
    rh_factor VARCHAR(10) NOT NULL CHECK (rh_factor IN ('Positive', 'Negative')),
    quantity_ml INTEGER NOT NULL DEFAULT 0 CHECK (quantity_ml >= 0),
    expiry_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Available' CHECK (status IN ('Available', 'Expired', 'Quarantined')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ၅။ သွေးလိုအပ်ချက်များ (Global Consolidated)
CREATE TABLE blood_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    requested_by_user_id UUID NOT NULL REFERENCES users(id),
    patient_name VARCHAR(255) NOT NULL,
    blood_group VARCHAR(3) NOT NULL CHECK (blood_group IN ('A', 'B', 'AB', 'O')),
    rh_factor VARCHAR(10) NOT NULL CHECK (rh_factor IN ('Positive', 'Negative')),
    quantity_ml INTEGER NOT NULL CHECK (quantity_ml > 0),
    urgency VARCHAR(20) DEFAULT 'Normal' CHECK (urgency IN ('Critical', 'Urgent', 'Normal')),
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Fulfilled', 'Rejected')),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fulfilled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ၆။ Sync Queue (Global မှာ အနာဂတ် Central Push အတွက် ထားရှိသော်လည်း Local က အဓိကသုံး)
CREATE TABLE sync_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID REFERENCES hospitals(id) ON DELETE CASCADE,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SYNCED', 'FAILED', 'CONFLICT')),
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_attempt_at TIMESTAMP
);

-- ၇။ Sync Logs (Global Master Log)
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sync_queue_id UUID REFERENCES sync_queue(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'CONFLICT_DETECTED')),
    error_message TEXT,
    conflict_details JSONB,
    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_hospital ON users(hospital_id);
CREATE INDEX idx_donors_hospital ON donors(hospital_id);
CREATE INDEX idx_inventory_hospital ON inventory(hospital_id);
CREATE INDEX idx_requests_hospital ON blood_requests(hospital_id);
CREATE INDEX idx_sync_queue_status ON sync_queue(status);
CREATE INDEX idx_sync_queue_hospital ON sync_queue(hospital_id);