-- ==============================================================================
-- AUTOMATED B2B LEAD INTELLIGENCE SYSTEM - DATABASE MIGRATION SCHEMA (STAGE 1 & STAGE 2)
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Main Qualified Leads Table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,                    -- 'linkedin', 'threads', 'facebook', 'web'
    post_url TEXT UNIQUE NOT NULL,                    -- Primary duplicate key
    author_name VARCHAR(255),
    author_url TEXT,
    post_text TEXT NOT NULL,
    posted_at TIMESTAMPTZ,
    matched_keywords JSONB DEFAULT '[]'::jsonb,
    service_needed VARCHAR(150),
    intent VARCHAR(50) CHECK (intent IN (
        'DIRECT_REQUEST', 'HIRING_AGENCY', 'OUTSOURCING', 'RECOMMENDATION_REQUEST', 
        'BUSINESS_PROBLEM', 'SELLING_SERVICE', 'HIRING_EMPLOYEE', 'IRRELEVANT'
    )),
    lead_score INT CHECK (lead_score BETWEEN 0 AND 100),
    lead_temperature VARCHAR(20) CHECK (lead_temperature IN ('HOT', 'WARM', 'COLD', 'IRRELEVANT')),
    urgency VARCHAR(20) CHECK (urgency IN ('HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')),
    budget_signal VARCHAR(100),
    business_type VARCHAR(100),
    qualification_reason TEXT,
    suggested_outreach_angle TEXT,
    status VARCHAR(30) DEFAULT 'NEW' CHECK (status IN (
        'NEW', 'QUALIFIED', 'CONTACTED', 'RESPONDED', 'CONVERTED', 'REJECTED'
    )),
    post_text_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_post_url ON leads(post_url);
CREATE INDEX IF NOT EXISTS idx_leads_post_text_hash ON leads(post_text_hash);
CREATE INDEX IF NOT EXISTS idx_leads_status_temp ON leads(status, lead_temperature);

-- 2. Lead Sources Catalog
CREATE TABLE IF NOT EXISTS lead_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE NOT NULL,
    collector_endpoint TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    daily_quota INT DEFAULT 1000
);

INSERT INTO lead_sources (source_name, collector_endpoint, daily_quota) VALUES
('Python Collector (LinkedIn Search)', 'http://python_collector:8000/api/v1/collect', 2500),
('Python Collector (Threads Search)', 'http://python_collector:8000/api/v1/collect', 2500),
('Python Collector (Facebook Search)', 'http://python_collector:8000/api/v1/collect', 2500)
ON CONFLICT (source_name) DO NOTHING;

-- 3. Lead Scores Breakdown Table (Auditing)
CREATE TABLE IF NOT EXISTS lead_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    base_score INT,
    intent_points INT,
    company_points INT,
    budget_points INT,
    urgency_points INT,
    penalties INT,
    final_score INT,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Lead Processing & Rejected Audit Logs
CREATE TABLE IF NOT EXISTS lead_processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50),
    post_url TEXT,
    post_text_hash VARCHAR(64),
    status VARCHAR(50),                             -- 'PROCESSED', 'REJECTED_IRRELEVANT', 'REJECTED_SELLER', 'REJECTED_FULLTIME_JOB', 'DUPLICATE'
    rejection_reason TEXT,
    ai_raw_response JSONB,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Configurable Keyword Dictionary
CREATE TABLE IF NOT EXISTS lead_keywords (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(50) NOT NULL,               -- 'SERVICE_KEYWORDS', 'INTENT_KEYWORDS', 'HIRING_KEYWORDS', 'PROBLEM_KEYWORDS', 'ENGLISH_KEYWORDS', 'INDONESIAN_KEYWORDS'
    language VARCHAR(10) NOT NULL,                 -- 'ID', 'EN'
    keyword_phrase VARCHAR(255) NOT NULL UNIQUE,
    weight_bonus INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Seed Keywords Catalog
INSERT INTO lead_keywords (group_name, language, keyword_phrase, weight_bonus) VALUES
-- SERVICE_KEYWORDS
('SERVICE_KEYWORDS', 'ID', 'website', 10),
('SERVICE_KEYWORDS', 'EN', 'website development', 10),
('SERVICE_KEYWORDS', 'EN', 'landing page', 10),
('SERVICE_KEYWORDS', 'EN', 'web development', 10),
('SERVICE_KEYWORDS', 'EN', 'web app', 10),
('SERVICE_KEYWORDS', 'ID', 'aplikasi', 10),
('SERVICE_KEYWORDS', 'EN', 'software', 10),
('SERVICE_KEYWORDS', 'EN', 'ERP', 10),
('SERVICE_KEYWORDS', 'ID', 'sistem informasi', 10),
('SERVICE_KEYWORDS', 'EN', 'hosting', 10),
('SERVICE_KEYWORDS', 'ID', 'maintenance website', 10),
('SERVICE_KEYWORDS', 'EN', 'backup', 10),
('SERVICE_KEYWORDS', 'ID', 'otomatisasi', 10),
('SERVICE_KEYWORDS', 'EN', 'developer', 10),
('SERVICE_KEYWORDS', 'EN', 'programmer', 10),
('SERVICE_KEYWORDS', 'EN', 'IT agency', 10),
('SERVICE_KEYWORDS', 'EN', 'software house', 10),

-- INTENT_KEYWORDS
('INTENT_KEYWORDS', 'ID', 'butuh', 10),
('INTENT_KEYWORDS', 'ID', 'mencari', 10),
('INTENT_KEYWORDS', 'ID', 'cari', 10),
('INTENT_KEYWORDS', 'ID', 'nyari', 10),
('INTENT_KEYWORDS', 'ID', 'rekomendasi', 10),
('INTENT_KEYWORDS', 'EN', 'need', 10),
('INTENT_KEYWORDS', 'EN', 'looking for', 10),
('INTENT_KEYWORDS', 'EN', 'searching for', 10),
('INTENT_KEYWORDS', 'EN', 'hiring', 10),
('INTENT_KEYWORDS', 'EN', 'wanted', 10),
('INTENT_KEYWORDS', 'EN', 'recommendation', 10),

-- PROBLEM_KEYWORDS
('PROBLEM_KEYWORDS', 'ID', 'tidak punya website', 5),
('PROBLEM_KEYWORDS', 'ID', 'website lama', 5),
('PROBLEM_KEYWORDS', 'ID', 'website error', 5),
('PROBLEM_KEYWORDS', 'ID', 'butuh website baru', 5),
('PROBLEM_KEYWORDS', 'ID', 'butuh sistem', 5),
('PROBLEM_KEYWORDS', 'ID', 'proses manual', 5),
('PROBLEM_KEYWORDS', 'ID', 'ingin otomatisasi', 5),
('PROBLEM_KEYWORDS', 'EN', 'need help', 5),
('PROBLEM_KEYWORDS', 'EN', 'need a developer', 5),

-- INDONESIAN COMBINATIONS
('INDONESIAN_KEYWORDS', 'ID', 'butuh website', 10),
('INDONESIAN_KEYWORDS', 'ID', 'butuh orang untuk bikin website', 10),
('INDONESIAN_KEYWORDS', 'ID', 'mencari web developer', 10),
('INDONESIAN_KEYWORDS', 'ID', 'butuh developer', 10),
('INDONESIAN_KEYWORDS', 'ID', 'ada yang bisa buat website?', 10),
('INDONESIAN_KEYWORDS', 'ID', 'rekomendasi jasa website', 10),
('INDONESIAN_KEYWORDS', 'ID', 'butuh agency untuk website', 10),
('INDONESIAN_KEYWORDS', 'ID', 'ada yg bisa bantu bikin web?', 10),
('INDONESIAN_KEYWORDS', 'ID', 'butuh org buat bikin website', 10),
('INDONESIAN_KEYWORDS', 'ID', 'nyari developer', 10),
('INDONESIAN_KEYWORDS', 'ID', 'nyari vendor website', 10),
('INDONESIAN_KEYWORDS', 'ID', 'ada rekomendasi developer?', 10),
('INDONESIAN_KEYWORDS', 'ID', 'siapa yang bisa bantu website?', 10),
('INDONESIAN_KEYWORDS', 'ID', 'lagi cari agency', 10),
('INDONESIAN_KEYWORDS', 'ID', 'lagi cari orang yang bisa bikin aplikasi', 10),
('INDONESIAN_KEYWORDS', 'ID', 'butuh programmer', 10),

-- ENGLISH COMBINATIONS
('ENGLISH_KEYWORDS', 'EN', 'looking for a web developer', 10),
('ENGLISH_KEYWORDS', 'EN', 'looking for a website developer', 10),
('ENGLISH_KEYWORDS', 'EN', 'need someone to build a website', 10),
('ENGLISH_KEYWORDS', 'EN', 'need a developer', 10),
('ENGLISH_KEYWORDS', 'EN', 'looking for a software agency', 10),
('ENGLISH_KEYWORDS', 'EN', 'need help with website', 10),
('ENGLISH_KEYWORDS', 'EN', 'need landing page', 10),
('ENGLISH_KEYWORDS', 'EN', 'need hosting', 10),
('ENGLISH_KEYWORDS', 'EN', 'need website maintenance', 10),
('ENGLISH_KEYWORDS', 'EN', 'website developer needed', 10),
('ENGLISH_KEYWORDS', 'EN', 'developer wanted', 10),
('ENGLISH_KEYWORDS', 'EN', 'looking for IT company', 10),
('ENGLISH_KEYWORDS', 'EN', 'looking for software house', 10)
ON CONFLICT (keyword_phrase) DO NOTHING;
