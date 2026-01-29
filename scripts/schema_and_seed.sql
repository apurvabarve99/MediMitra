-- ====================================
-- MediMitra Complete Database Schema & Seed Data
-- ====================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables
DROP TABLE IF EXISTS document_embeddings CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS bank_statements CASCADE;
DROP TABLE IF EXISTS pos_transactions CASCADE;
DROP TABLE IF EXISTS medicines CASCADE;
DROP TABLE IF EXISTS prescriptions CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table (for both patients and pharmacists)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    user_type VARCHAR(20) CHECK (user_type IN ('patient', 'pharmacist')),
    security_question VARCHAR(255),
    security_answer_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patients table (extended profile)
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    phone VARCHAR(20),
    emergency_contact VARCHAR(20),
    blood_group VARCHAR(5),
    allergies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctors table
CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    qualification VARCHAR(255),
    email VARCHAR(100),
    phone VARCHAR(20),
    consultation_fee DECIMAL(10, 2),
    available_days VARCHAR(100),
    available_hours VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments table
CREATE TABLE appointments (
    appointment_id VARCHAR(50) PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    doctor_id INTEGER REFERENCES doctors(doctor_id),
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    symptoms TEXT,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')),
    patient_name VARCHAR(100),
    patient_contact VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prescriptions table
CREATE TABLE prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    appointment_id VARCHAR(50) REFERENCES appointments(appointment_id),
    patient_id INTEGER REFERENCES patients(patient_id),
    doctor_id INTEGER REFERENCES doctors(doctor_id),
    prescription_date DATE NOT NULL,
    prescription_text TEXT,
    prescription_image_url TEXT,
    medicines JSONB,
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medicines inventory table
CREATE TABLE inventory_stock (
    stock_id SERIAL PRIMARY KEY,
    medicine_name VARCHAR(200) NOT NULL,
    batch_number VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100),
    expiry_date DATE NOT NULL,
    current_quantity INT NOT NULL DEFAULT 0,
    reorder_level INT DEFAULT 50, -- Trigger reorder when below this
    location VARCHAR(50), -- Shelf/rack number
    cost_price DECIMAL(10,2), -- Average cost
    selling_price DECIMAL(10,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(medicine_name, batch_number)
);

-- Inventory transactions log (audit trail)
CREATE TABLE inventory_transactions (
    transaction_id SERIAL PRIMARY KEY,
    medicine_name VARCHAR(200) NOT NULL,
    batch_number VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- 'IN' (from supplier), 'OUT' (sale), 'ADJUST' (manual)
    quantity INT NOT NULL, -- positive for IN, negative for OUT
    reference_type VARCHAR(20), -- 'POS', 'SUPPLIER_INVOICE', 'MANUAL'
    reference_id INT, -- Links to pos_sales.sale_id or supplier_invoices.invoice_id
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT
);

-- Indexes for inventory
CREATE INDEX idx_inventory_stock_medicine ON inventory_stock(medicine_name);
CREATE INDEX idx_inventory_stock_batch ON inventory_stock(batch_number);
CREATE INDEX idx_inventory_stock_expiry ON inventory_stock(expiry_date);
CREATE INDEX idx_inventory_transactions_date ON inventory_transactions(transaction_date);

-- POS transactions table
CREATE TABLE pos_sales (
    sale_id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    sale_date TIMESTAMP NOT NULL,
    pharmacy_location VARCHAR(100),
    pharmacist_id INT REFERENCES users(user_id),
    pharmacist_name VARCHAR(100),
    patient_id INT REFERENCES users(user_id) NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    cgst_amount DECIMAL(10,2),
    sgst_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2) NOT NULL,
    payment_mode VARCHAR(20),
    prescription_number VARCHAR(50) NULL,
    extracted_text TEXT, -- ✅ ONLY this - no image storage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pos_sale_items (
    item_id SERIAL PRIMARY KEY,
    sale_id INT REFERENCES pos_sales(sale_id) ON DELETE CASCADE,
    medicine_name VARCHAR(200) NOT NULL,
    batch_number VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for POS sales
CREATE INDEX idx_pos_sales_date ON pos_sales(sale_date);
CREATE INDEX idx_pos_sales_receipt ON pos_sales(receipt_number);
CREATE INDEX idx_pos_sale_items_batch ON pos_sale_items(batch_number);

-- Supplier invoices table

CREATE TABLE supplier_invoices (
    invoice_id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    invoice_date DATE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    supplier_gstin VARCHAR(20),
    supplier_address TEXT,
    supplier_phone VARCHAR(20),
    po_reference VARCHAR(50),
    delivery_date DATE,
    vehicle_number VARCHAR(20),
    subtotal DECIMAL(12,2) NOT NULL,
    cgst_amount DECIMAL(10,2),
    sgst_amount DECIMAL(10,2),
    total_amount DECIMAL(12,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    payment_terms VARCHAR(100),
    extracted_text TEXT, -- ✅ ONLY this - no image storage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- child table
CREATE TABLE supplier_invoice_items (
    item_id SERIAL PRIMARY KEY,
    invoice_id INT REFERENCES supplier_invoices(invoice_id) ON DELETE CASCADE,
    medicine_name VARCHAR(200) NOT NULL,
    batch_number VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100),
    expiry_date DATE NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Indexes for supplier invoices
CREATE INDEX idx_supplier_invoices_date ON supplier_invoices(invoice_date);
CREATE INDEX idx_supplier_invoices_number ON supplier_invoices(invoice_number);
CREATE INDEX idx_supplier_invoices_supplier ON supplier_invoices(supplier_name);
CREATE INDEX idx_supplier_invoice_items_batch ON supplier_invoice_items(batch_number);
CREATE INDEX idx_supplier_invoice_items_expiry ON supplier_invoice_items(expiry_date);


-- Bank transactions table
CREATE TABLE bank_transactions (
    record_id SERIAL PRIMARY KEY, 
    tran_id VARCHAR(20) UNIQUE NOT NULL,  
    txn_date DATE NOT NULL,
    cr_dr CHAR(2) CHECK (cr_dr IN ('CR', 'DR')), 
    amount DECIMAL(15, 2) NOT NULL,
    balance DECIMAL(15, 2) NOT NULL,
	description VARCHAR(250) NOT NULL,
    extracted_text TEXT,  -- Raw OCR output for debugging/verification
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by INTEGER,  
    approved_at TIMESTAMP,
    CONSTRAINT fk_approved_by FOREIGN KEY (approved_by) 
        REFERENCES users(user_id) ON DELETE SET NULL
);

-- Indexes on bank transactions
CREATE INDEX idx_bank_txn_date ON bank_transactions(txn_date);
CREATE INDEX idx_bank_tran_id ON bank_transactions(tran_id);
CREATE INDEX idx_bank_approved_by ON bank_transactions(approved_by);
CREATE INDEX idx_bank_cr_dr ON bank_transactions(cr_dr);


-- Chat sessions table
CREATE TABLE chat_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    session_data JSONB,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Vector embeddings table for RAG
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB,
    doc_type VARCHAR(50),
    source VARCHAR(255),  -- ADDED THIS LINE
    created_at TIMESTAMP DEFAULT NOW()
);


-- Create indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_user_type ON users(user_type);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_medicines_name ON medicines(medicine_name);
CREATE INDEX idx_document_embeddings_type ON document_embeddings(doc_type);
CREATE INDEX idx_bank_txn_date ON bank_transactions(txn_date);
CREATE INDEX idx_bank_tran_id ON bank_transactions(tran_id);
CREATE INDEX idx_bank_approved_by ON bank_transactions(approved_by);
CREATE INDEX idx_bank_cr_dr ON bank_transactions(cr_dr);

-- Create index for fast similarity search
CREATE INDEX idx_embeddings_cosine ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Seed Users (200 patients + 10 pharmacists)
INSERT INTO users (username, full_name, password_hash, email, phone, user_type, security_question, security_answer_hash)
SELECT 
    'patient' || gs AS username,
    (ARRAY['Aarav', 'Vivaan', 'Aditya', 'Arjun', 'Sai', 'Arnav', 'Ayaan', 'Krishna', 'Ishaan', 'Reyansh',
           'Ananya', 'Diya', 'Saanvi', 'Aadhya', 'Kiara', 'Navya', 'Pari', 'Sara', 'Avni', 'Myra'])[floor(random() * 20 + 1)] || ' ' ||
    (ARRAY['Sharma', 'Patel', 'Kumar', 'Singh', 'Reddy', 'Nair', 'Barve', 'Rajput', 'Selvam', 'Mani',
           'Murugan', 'Saravanan', 'Arunachalam', 'Kothandam', 'Venkatesh'])[floor(random() * 15 + 1)] AS full_name,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeWKL3Z3vWq2' AS password_hash, -- hashed 'password123'
    'patient' || gs || '@email.com' AS email,
    '+91' || (7000000000 + floor(random() * 3000000000)::bigint)::text AS phone,
    'patient' AS user_type,
    'What is your favorite color?' AS security_question,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeWKL3Z3vWq2' AS security_answer_hash
FROM generate_series(1, 200) gs;

-- Seed Pharmacist Users
INSERT INTO users (username, full_name, password_hash, email, phone, user_type, security_question, security_answer_hash)
SELECT 
    'pharmacist' || gs AS username,
    'Pharmacist ' || gs AS full_name,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeWKL3Z3vWq2' AS password_hash,
    'pharmacist' || gs || '@medimitra.com' AS email,
    '+91' || (9000000000 + gs)::text AS phone,
    'pharmacist' AS user_type,
    'What is your favorite color?' AS security_question,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeWKL3Z3vWq2' AS security_answer_hash
FROM generate_series(1, 10) gs;

-- Seed Patients (200)
INSERT INTO patients (user_id, full_name, date_of_birth, gender, address, phone, emergency_contact, blood_group, allergies)
SELECT 
    u.user_id,
    u.full_name,
    DATE '1950-01-01' + (random() * 20000)::int AS date_of_birth,
    CASE WHEN random() < 0.5 THEN 'Male' ELSE 'Female' END AS gender,
    'Address ' || u.user_id || ', Mangaluru, Karnataka' AS address,
    u.phone AS phone,
    '+91' || (7000000000 + floor(random() * 3000000000)::bigint)::text AS emergency_contact,
    (ARRAY['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])[floor(random() * 8 + 1)] AS blood_group,
    CASE WHEN random() < 0.3 THEN (ARRAY['Penicillin allergy', 'Dust allergy', 'Food allergy', 'Pollen allergy'])[floor(random() * 4 + 1)] ELSE NULL END AS allergies
FROM users u WHERE u.user_type = 'patient';

-- Insert 200 doctors with all specializations from symptom mappings
INSERT INTO doctors (full_name, specialization, qualification, email, phone, consultation_fee, available_days, available_hours, is_active)
SELECT 
    'Dr. ' || (ARRAY['Avyukth', 'Avnitha', 'Avyaan', 'Arun','Aishwarya', 'Apurva', 'Vivek', 'Aarav', 'Vivaan', 'Aditya', 'Priya', 
                     'Ananya', 'Rahul', 'Sneha', 'Amit', 'Divya', 'Rohan', 'Pooja', 'Karan', 'Neha', 'Arjun',
                     'Sanjay', 'Kavita', 'Manish', 'Deepa', 'Rajesh', 'Meera', 'Suresh', 'Lakshmi', 'Vijay', 'Rekha'])[floor(random() * 30 + 1)] || ' ' ||
    (ARRAY['Sharma', 'Patel', 'Kumar', 'Singh', 'Reddy', 'Nair', 'Barve', 'Rajput', 'Selvam', 'Mani',
           'Murugan', 'Saravanan', 'Arunachalam', 'Kothandam', 'Iyer', 'Gupta', 'Joshi', 'Desai', 'Rao', 'Varma'])[floor(random() * 20 + 1)] AS full_name,
    -- All 37 unique specializations from your symptom mappings
    (ARRAY[
        'General Medicine',
        'Cardiologist',
        'Neurologist',
        'Pulmonologist',
        'Gastroenterologist',
        'Orthopedic',
        'Dermatologist',
        'Endocrinologist',
        'Urologist',
        'Nephrologist',
        'ENT Specialist',
        'Ophthalmologist',
        'Psychiatrist',
        'Gynecologist',
        'Rheumatologist',
        'Oncologist',
        'Pediatrics',
        'Infectious Disease',
        'Allergist',
        'Vascular Surgeon',
        'Emergency Medicine',
        'Hepatologist',
        'General Surgeon',
        'Geriatrics',
        'Sports Medicine',
        'Trauma Surgery',
        'Podiatrist',
        'Obstetrician',
        'Reproductive Endocrinologist',
        'Audiologist',
        'Pain Management',
        'Hematologist',
        'Breast Surgeon',
        'Immunologist',
        'Critical Care',
        'Neonatologist',
        'Child Psychiatrist'
    ])[floor(random() * 37 + 1)] AS specialization,
    (ARRAY['MBBS, MD', 'MBBS, MS', 'MBBS, DNB', 'MBBS, MD, DM', 'MBBS, MS, MCh', 'MBBS, MD, MRCP'])[floor(random() * 6 + 1)] AS qualification,
    'doctor' || gs || '@medimitra.com' AS email,
    '+91' || (7000000000 + floor(random() * 3000000000)::bigint)::text AS phone,
    (400 + random() * 1600)::numeric(10,2) AS consultation_fee,
    (ARRAY[
        'Monday, Tuesday, Wednesday, Thursday, Friday, Saturday',
        'Monday, Wednesday, Friday, Saturday',
        'Tuesday, Thursday, Saturday, Sunday',
        'Monday, Tuesday, Wednesday, Thursday, Friday',
        'All Days'
    ])[floor(random() * 5 + 1)] AS available_days,
    (ARRAY[
        '09:00-21:00',
        '09:00-17:00',
        '10:00-18:00',
        '14:00-21:00',
        '08:00-16:00'
    ])[floor(random() * 5 + 1)] AS available_hours,
    TRUE AS is_active
FROM generate_series(1, 200) gs;


-- Seed Appointments (200)
INSERT INTO appointments (appointment_id, patient_id, doctor_id, appointment_date, appointment_time, symptoms, status, patient_name, patient_contact)
SELECT 
    'APT' || TO_CHAR(CURRENT_DATE + (random() * 60 - 30)::int, 'YYYYMMDD') || LPAD(floor(random() * 100000)::text, 5, '0') AS appointment_id,
    floor(random() * 200 + 1)::int AS patient_id,
    floor(random() * 200 + 1)::int AS doctor_id,
    CURRENT_DATE + (random() * 60 - 30)::int AS appointment_date,
    (TIME '09:00:00' + (floor(random() * 12)::int || ' hours')::interval + ((floor(random() * 4)::int * 15) || ' minutes')::interval) AS appointment_time,
    (ARRAY['Chest pain', 'Headache', 'Fever', 'Cough', 'Joint pain', 'Stomach pain', 
           'Breathing difficulty', 'Eye pain', 'Ear pain', 'Skin rash'])[floor(random() * 10 + 1)] AS symptoms,
    (ARRAY['scheduled', 'completed', 'scheduled', 'completed'])[floor(random() * 4 + 1)] AS status,
    (SELECT full_name FROM patients WHERE patient_id = floor(random() * 200 + 1)::int LIMIT 1) AS patient_name,
    '+91' || (7000000000 + floor(random() * 3000000000)::bigint)::text AS patient_contact
FROM generate_series(1, 200) gs;

-- Seed Prescriptions (150)
INSERT INTO prescriptions (appointment_id, patient_id, doctor_id, prescription_date, prescription_text, medicines, instructions)
SELECT 
    a.appointment_id,
    a.patient_id,
    a.doctor_id,
    a.appointment_date AS prescription_date,
    'Prescription for ' || a.symptoms AS prescription_text,
    jsonb_build_array(
        jsonb_build_object('name', 'Paracetamol 500mg', 'dosage', '1 tablet twice daily', 'duration', '5 days'),
        jsonb_build_object('name', 'Amoxicillin 250mg', 'dosage', '1 capsule thrice daily', 'duration', '7 days')
    ) AS medicines,
    'Take medicines after food. Complete the course. Rest adequately.' AS instructions
FROM appointments a
WHERE a.status = 'completed'
LIMIT 150;


-- seed inventory_stock

INSERT INTO inventory_stock (medicine_name, batch_number, manufacturer, expiry_date, current_quantity, reorder_level, location, cost_price, selling_price)
SELECT 
    (ARRAY[
        'Paracetamol 500mg', 'Paracetamol 650mg', 'Amoxicillin 250mg', 'Amoxicillin 500mg',
        'Azithromycin 250mg', 'Azithromycin 500mg', 'Ciprofloxacin 250mg', 'Ciprofloxacin 500mg',
        'Metformin 500mg', 'Metformin 850mg', 'Atorvastatin 10mg', 'Atorvastatin 20mg',
        'Amlodipine 5mg', 'Amlodipine 10mg', 'Losartan 25mg', 'Losartan 50mg',
        'Omeprazole 20mg', 'Omeprazole 40mg', 'Pantoprazole 20mg', 'Pantoprazole 40mg',
        'Ranitidine 150mg', 'Ranitidine 300mg', 'Cetirizine 5mg', 'Cetirizine 10mg',
        'Montelukast 5mg', 'Montelukast 10mg', 'Salbutamol Inhaler', 'Budesonide Inhaler',
        'Insulin Glargine 100IU', 'Insulin Aspart 100IU', 'Aspirin 75mg', 'Aspirin 150mg',
        'Clopidogrel 75mg', 'Clopidogrel 150mg', 'Levothyroxine 25mcg', 'Levothyroxine 50mcg',
        'Metoprolol 25mg', 'Metoprolol 50mg', 'Furosemide 20mg', 'Furosemide 40mg',
        'Gabapentin 100mg', 'Gabapentin 300mg', 'Pregabalin 75mg', 'Pregabalin 150mg',
        'Tramadol 50mg', 'Tramadol 100mg', 'Ibuprofen 200mg', 'Ibuprofen 400mg',
        'Diclofenac 50mg', 'Diclofenac 100mg', 'Sertraline 25mg', 'Sertraline 50mg',
        'Fluoxetine 10mg', 'Fluoxetine 20mg', 'Alprazolam 0.25mg', 'Alprazolam 0.5mg',
        'Clonazepam 0.5mg', 'Clonazepam 1mg', 'Lorazepam 1mg', 'Lorazepam 2mg',
        'Vitamin D3 60000IU', 'Vitamin D3 1000IU', 'Calcium Carbonate 500mg', 'Calcium Carbonate 1000mg',
        'Folic Acid 1mg', 'Folic Acid 5mg', 'Iron Tablets 100mg', 'Iron Tablets 200mg',
        'Multivitamin Capsules', 'Multivitamin Syrup', 'Zinc Sulphate 20mg', 'Zinc Sulphate 50mg',
        'Doxycycline 100mg', 'Doxycycline 200mg', 'Levofloxacin 250mg', 'Levofloxacin 500mg',
        'Clarithromycin 250mg', 'Clarithromycin 500mg', 'Cefixime 100mg', 'Cefixime 200mg',
        'Prednisolone 5mg', 'Prednisolone 10mg', 'Dexamethasone 0.5mg', 'Dexamethasone 4mg',
        'Hydrocortisone Cream 1%', 'Betamethasone Cream 0.1%', 'Clotrimazole Cream 1%', 'Miconazole Gel 2%',
        'Acyclovir 200mg', 'Acyclovir 400mg', 'Valacyclovir 500mg', 'Valacyclovir 1000mg',
        'Chlorpheniramine 4mg', 'Phenylephrine Drops', 'Guaifenesin Syrup', 'Dextromethorphan Syrup',
        'Domperidone 10mg', 'Ondansetron 4mg', 'Bisacodyl 5mg', 'Lactulose Syrup',
        'Enalapril 5mg', 'Enalapril 10mg', 'Ramipril 2.5mg', 'Ramipril 5mg',
        'Glimepiride 1mg', 'Glimepiride 2mg', 'Gliclazide 40mg', 'Gliclazide 80mg'
    ])[1 + (gs % 100)] AS medicine_name,
    'BATCH' || LPAD((100000 + gs)::TEXT, 6, '0') AS batch_number,
    (ARRAY['Sun Pharma', 'Cipla', 'Dr Reddys', 'Lupin', 'Torrent', 'Mankind', 'Alkem', 'Glenmark', 'Aurobindo', 'Zydus'])[1 + (gs % 10)] AS manufacturer,
    CURRENT_DATE + (90 + (gs % 730))::INT AS expiry_date,
    (50 + (random() * 450)::INT) AS current_quantity,
    (20 + (random() * 30)::INT) AS reorder_level,
    'Rack-' || (ARRAY['A', 'B', 'C', 'D', 'E'])[1 + (gs % 5)] || '-' || (1 + (gs % 20)) AS location,
    (5 + (random() * 95))::NUMERIC(10,2) AS cost_price,
    (10 + (random() * 190))::NUMERIC(10,2) AS selling_price
FROM generate_series(1, 200) gs;


-- ====================================
-- 2. SEED POS_SALES (200 receipts)
-- ====================================

INSERT INTO pos_sales (receipt_number, sale_date, pharmacy_location, pharmacist_id, pharmacist_name, patient_id, subtotal, cgst_amount, sgst_amount, total_amount, payment_mode, prescription_number, extracted_text)
SELECT 
    'POS-2026-' || LPAD(gs::TEXT, 6, '0') AS receipt_number,
    CURRENT_DATE - (random() * 365)::INT AS sale_date,
    (ARRAY['Mangaluru Main Branch', 'Mangaluru City Center', 'Udupi Branch', 'Manipal Branch'])[1 + (gs % 4)] AS pharmacy_location,
    201 + (gs % 10) AS pharmacist_id,
    'Pharmacist ' || (1 + (gs % 10)) AS pharmacist_name,
    CASE WHEN random() < 0.7 THEN 1 + (gs % 200) ELSE NULL END AS patient_id,
    (100 + (random() * 900))::NUMERIC(10,2) AS subtotal,
    (5 + (random() * 45))::NUMERIC(10,2) AS cgst_amount,
    (5 + (random() * 45))::NUMERIC(10,2) AS sgst_amount,
    (110 + (random() * 990))::NUMERIC(10,2) AS total_amount,
    (ARRAY['Cash', 'Card', 'UPI', 'Insurance'])[1 + (gs % 4)] AS payment_mode,
    CASE WHEN random() < 0.4 THEN 'RX-' || LPAD((gs * 37)::TEXT, 5, '0') ELSE NULL END AS prescription_number,
    'Receipt No: POS-2026-' || LPAD(gs::TEXT, 6, '0') || ' | Date: ' || TO_CHAR(CURRENT_DATE - (random() * 365)::INT, 'DD/MM/YYYY') || ' | Total: Rs. ' || (110 + (random() * 990))::NUMERIC(10,2)::TEXT AS extracted_text
FROM generate_series(1, 200) gs;


-- ====================================
-- 3. SEED POS_SALE_ITEMS (400-600 items, 2-3 per sale)
-- ====================================

INSERT INTO pos_sale_items (sale_id, medicine_name, batch_number, quantity, unit_price, total_price)
SELECT 
    ps.sale_id,
    ist.medicine_name,
    ist.batch_number,
    (1 + floor(random() * 5)::INT) AS quantity,
    ist.selling_price AS unit_price,
    (1 + floor(random() * 5)::INT) * ist.selling_price AS total_price
FROM pos_sales ps
CROSS JOIN LATERAL (
    SELECT medicine_name, batch_number, selling_price
    FROM inventory_stock
    ORDER BY random()
    LIMIT (2 + floor(random() * 2)::INT)
) ist;


-- ====================================
-- 4. SEED SUPPLIER_INVOICES (200 invoices)
-- ====================================

INSERT INTO supplier_invoices (invoice_number, invoice_date, supplier_name, supplier_gstin, supplier_address, supplier_phone, po_reference, delivery_date, vehicle_number, subtotal, cgst_amount, sgst_amount, total_amount, payment_status, payment_terms, extracted_text)
SELECT 
    'INV-' || TO_CHAR(CURRENT_DATE - (random() * 730)::INT, 'YYYYMMDD') || '-' || LPAD(gs::TEXT, 4, '0') AS invoice_number,
    CURRENT_DATE - (random() * 730)::INT AS invoice_date,
    (ARRAY[
        'MedSupply Co', 'PharmaDirect Ltd', 'HealthCare Distributors', 'MediSource Pvt Ltd', 
        'Wellness Suppliers', 'BioMed Traders', 'CarePlus Distributors', 'MedEx Solutions',
        'PharmaLink India', 'MediCare Wholesale', 'Apollo Distributors', 'HealthFirst Supplies'
    ])[1 + (gs % 12)] AS supplier_name,
    '29' || LPAD((1000000 + (gs * 123) % 9000000)::TEXT, 14, '0') AS supplier_gstin,
    (ARRAY['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata', 'Ahmedabad'])[1 + (gs % 8)] || ', India' AS supplier_address,
    '+91' || (8000000000 + (gs * 12345) % 1000000000)::BIGINT::TEXT AS supplier_phone,
    'PO-' || LPAD((1000 + gs)::TEXT, 5, '0') AS po_reference,
    CURRENT_DATE - (random() * 730)::INT + (1 + floor(random() * 7)::INT) AS delivery_date,
    'KA' || LPAD((gs % 100)::TEXT, 2, '0') || 'AB' || LPAD((1000 + gs)::TEXT, 4, '0') AS vehicle_number,
    (10000 + (random() * 90000))::NUMERIC(12,2) AS subtotal,
    (500 + (random() * 4500))::NUMERIC(10,2) AS cgst_amount,
    (500 + (random() * 4500))::NUMERIC(10,2) AS sgst_amount,
    (11000 + (random() * 99000))::NUMERIC(12,2) AS total_amount,
    (ARRAY['pending', 'pending', 'paid', 'partial'])[1 + (gs % 4)] AS payment_status,
    (ARRAY['Net 30 days', 'Net 45 days', 'Net 60 days', 'Immediate'])[1 + (gs % 4)] AS payment_terms,
    'Invoice No: INV-' || TO_CHAR(CURRENT_DATE - (random() * 730)::INT, 'YYYYMMDD') || '-' || LPAD(gs::TEXT, 4, '0') || ' | Supplier: MedSupply Co | Total: Rs. ' || (11000 + (random() * 99000))::NUMERIC(12,2)::TEXT AS extracted_text
FROM generate_series(1, 200) gs;


-- ====================================
-- 5. SEED SUPPLIER_INVOICE_ITEMS (400-800 items, 2-4 per invoice)
-- ====================================

INSERT INTO supplier_invoice_items (invoice_id, medicine_name, batch_number, manufacturer, expiry_date, quantity, unit_price, total_price)
SELECT 
    si.invoice_id,
    ist.medicine_name,
    ist.batch_number,
    ist.manufacturer,
    ist.expiry_date,
    (50 + floor(random() * 450)::INT) AS quantity,
    ist.cost_price AS unit_price,
    (50 + floor(random() * 450)::INT) * ist.cost_price AS total_price
FROM supplier_invoices si
CROSS JOIN LATERAL (
    SELECT medicine_name, batch_number, manufacturer, expiry_date, cost_price
    FROM inventory_stock
    ORDER BY random()
    LIMIT (2 + floor(random() * 3)::INT)
) ist;


-- ====================================
-- 6. SEED INVENTORY_TRANSACTIONS (200 audit records)
-- ====================================

INSERT INTO inventory_transactions (medicine_name, batch_number, transaction_type, quantity, reference_type, reference_id, transaction_date, remarks)
SELECT 
    ist.medicine_name,
    ist.batch_number,
    (ARRAY['IN', 'OUT', 'ADJUST'])[1 + (gs % 3)] AS transaction_type,
    CASE 
        WHEN (gs % 3) = 0 THEN (50 + floor(random() * 200)::INT)  -- IN (positive)
        WHEN (gs % 3) = 1 THEN -(1 + floor(random() * 50)::INT)   -- OUT (negative)
        ELSE (floor(random() * 20)::INT - 10)                     -- ADJUST (can be +/-)
    END AS quantity,
    CASE 
        WHEN (gs % 3) = 0 THEN 'SUPPLIER_INVOICE'
        WHEN (gs % 3) = 1 THEN 'POS'
        ELSE 'MANUAL'
    END AS reference_type,
    CASE 
        WHEN (gs % 3) = 0 THEN 1 + (gs % 200)  -- Link to supplier invoice
        WHEN (gs % 3) = 1 THEN 1 + (gs % 200)  -- Link to POS sale
        ELSE NULL
    END AS reference_id,
    CURRENT_DATE - (random() * 365)::INT AS transaction_date,
    CASE 
        WHEN (gs % 3) = 0 THEN 'Stock received from supplier'
        WHEN (gs % 3) = 1 THEN 'Medicine sold to customer'
        ELSE 'Manual stock adjustment - physical count'
    END AS remarks
FROM generate_series(1, 200) gs
CROSS JOIN LATERAL (
    SELECT medicine_name, batch_number
    FROM inventory_stock
    ORDER BY random()
    LIMIT 1
) ist;


-- ====================================
-- 7. SEED BANK_TRANSACTIONS (200 transactions)
-- ====================================

INSERT INTO bank_transactions (tran_id, txn_date, cr_dr, amount, balance, description, extracted_text, approved_by, approved_at)
WITH RECURSIVE 
    date_series AS (
        SELECT 
            DATE '2024-01-01' as base_date,
            1 as row_num
        UNION ALL
        SELECT 
            base_date + ((row_num / 3)::INT),
            row_num + 1
        FROM date_series
        WHERE row_num < 200
    ),
    transaction_data AS (
        SELECT 
            row_num,
            'S' || LPAD((9700000 + row_num)::TEXT, 8, '0') as tran_id,
            base_date as txn_date,
            (ARRAY[
                'PEN. JAN-2024 LESS TDS',
                'PEN. FEB-2024 LESS TDS',
                'PEN. MAR-2024 LESS TDS',
                'NEFT-SUPPLIER PAYMENT',
                'UPI-CUSTOMER PAYMENT',
                'SELF DEPOSIT',
                'ATM WITHDRAWAL',
                'MEDICINE PURCHASE',
                'SALARY CREDIT',
                'ELECTRICITY BILL PAYMENT',
                'WATER BILL - MUNICIPAL',
                'UPI-PHONEPE-GROCERY STORE',
                'UPI-GPAY-RESTAURANT PAYMENT',
                'INSURANCE PREMIUM PAYMENT',
                'RENT PAYMENT',
                'STAFF SALARY - PHARMACIST'
            ])[1 + floor(random() * 16)::INT] as description,
            100000.00 as initial_balance,
            (1000 + random() * 49000)::DECIMAL(15,2) as random_amount,
            CASE WHEN random() < 0.60 THEN 'DR' ELSE 'CR' END as cr_dr_flag
        FROM date_series
    ),
    running_balance_calc AS (
        SELECT 
            row_num,
            tran_id,
            txn_date,
            description,
            cr_dr_flag,
            random_amount,
            initial_balance + SUM(
                CASE WHEN cr_dr_flag = 'CR' THEN random_amount ELSE -random_amount END
            ) OVER (ORDER BY row_num ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as balance,
            'OCR: ' || tran_id || ' | Date: ' || TO_CHAR(txn_date, 'DD/MM/YYYY') || ' | Amt: ' || random_amount::TEXT as extracted_text,
            201 + (random() * 10)::INT as approved_by,
            txn_date + (interval '1 hour') + (interval '1 minute' * (random() * 120)::INT) as approved_at
        FROM transaction_data
    )
SELECT 
    tran_id,
    txn_date,
    cr_dr_flag as cr_dr,
    random_amount as amount,
    ROUND(balance, 2) as balance,
    description,
    extracted_text,
    approved_by,
    approved_at
FROM running_balance_calc
ORDER BY txn_date, row_num;



-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Database schema created successfully!';
    RAISE NOTICE '✅ Seed data inserted:';
    RAISE NOTICE '   - % users', (SELECT COUNT(*) FROM users);
    RAISE NOTICE '   - % patients', (SELECT COUNT(*) FROM patients);
    RAISE NOTICE '   - % doctors', (SELECT COUNT(*) FROM doctors);
    RAISE NOTICE '   - % appointments', (SELECT COUNT(*) FROM appointments);
    RAISE NOTICE '   - % prescriptions', (SELECT COUNT(*) FROM prescriptions);
    RAISE NOTICE '   - % medicines', (SELECT COUNT(*) FROM medicines);
    RAISE NOTICE '   - % POS transactions', (SELECT COUNT(*) FROM pos_transactions);
    RAISE NOTICE '   - % bank statements', (SELECT COUNT(*) FROM bank_statements);
END $$;
