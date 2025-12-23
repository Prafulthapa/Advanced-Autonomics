-- Migration: Add Agent Fields to Existing Database
-- Run this AFTER backing up your database
-- Usage: sqlite3 data/data.db < migrations/add_agent_fields.sql

-- ============================================
-- STEP 1: Add new columns to leads table
-- ============================================

ALTER TABLE leads ADD COLUMN agent_enabled BOOLEAN DEFAULT 1;
ALTER TABLE leads ADD COLUMN agent_paused BOOLEAN DEFAULT 0;
ALTER TABLE leads ADD COLUMN next_agent_check_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN last_agent_action_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN follow_up_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN max_follow_ups INTEGER DEFAULT 3;
ALTER TABLE leads ADD COLUMN days_between_followups INTEGER DEFAULT 3;
ALTER TABLE leads ADD COLUMN priority_score REAL DEFAULT 5.0;
ALTER TABLE leads ADD COLUMN engagement_score REAL DEFAULT 0.0;
ALTER TABLE leads ADD COLUMN bounce_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN error_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN last_error_message TEXT;
ALTER TABLE leads ADD COLUMN agent_notes TEXT;

-- ============================================
-- STEP 2: Create agent_config table
-- ============================================

CREATE TABLE IF NOT EXISTS agent_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_running BOOLEAN DEFAULT 0,
    is_paused BOOLEAN DEFAULT 0,
    daily_email_limit INTEGER DEFAULT 50,
    hourly_email_limit INTEGER DEFAULT 10,
    emails_sent_today INTEGER DEFAULT 0,
    emails_sent_this_hour INTEGER DEFAULT 0,
    last_reset_date TEXT,
    last_hour_reset TIMESTAMP,
    business_hours_start TEXT DEFAULT '09:00',
    business_hours_end TEXT DEFAULT '17:00',
    timezone TEXT DEFAULT 'America/New_York',
    agent_check_interval INTEGER DEFAULT 5,
    inbox_check_interval INTEGER DEFAULT 15,
    respect_business_hours BOOLEAN DEFAULT 1,
    respect_unsubscribes BOOLEAN DEFAULT 1,
    pause_on_high_error_rate BOOLEAN DEFAULT 1,
    error_rate_threshold INTEGER DEFAULT 10,
    total_emails_sent INTEGER DEFAULT 0,
    total_replies_received INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    agent_started_at TIMESTAMP,
    agent_stopped_at TIMESTAMP,
    last_agent_run_at TIMESTAMP,
    next_agent_run_at TIMESTAMP,
    config_version TEXT DEFAULT '1.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default config
INSERT INTO agent_config (
    is_running,
    is_paused,
    daily_email_limit,
    hourly_email_limit,
    last_reset_date
) VALUES (
    0,
    0,
    50,
    10,
    date('now')
);

-- ============================================
-- STEP 3: Create agent_action_logs table
-- ============================================

CREATE TABLE IF NOT EXISTS agent_action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    action_result TEXT NOT NULL,
    lead_id INTEGER,
    lead_email TEXT,
    decision_reason TEXT,
    metadata TEXT,
    error_message TEXT,
    execution_time_ms INTEGER,
    agent_run_id TEXT,
    emails_sent_before INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads (id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_agent_enabled ON leads(agent_enabled);
CREATE INDEX IF NOT EXISTS idx_leads_next_check ON leads(next_agent_check_at);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_action_logs_type ON agent_action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_action_logs_timestamp ON agent_action_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_action_logs_lead ON agent_action_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_action_logs_run_id ON agent_action_logs(agent_run_id);

-- ============================================
-- STEP 4: Update existing leads with defaults
-- ============================================

-- Set next_agent_check_at for all 'new' leads to NOW (agent will check immediately)
UPDATE leads 
SET next_agent_check_at = datetime('now') 
WHERE status = 'new' AND next_agent_check_at IS NULL;

-- Set next_agent_check_at for 'contacted' leads to 3 days from last email
UPDATE leads 
SET next_agent_check_at = datetime(last_email_sent_at, '+3 days')
WHERE status = 'contacted' 
  AND last_email_sent_at IS NOT NULL 
  AND next_agent_check_at IS NULL;

-- ============================================
-- VERIFICATION QUERIES (run these to check)
-- ============================================

-- Check new columns exist
PRAGMA table_info(leads);

-- Check agent_config exists
SELECT * FROM agent_config;

-- Check agent_action_logs exists
SELECT COUNT(*) FROM agent_action_logs;

-- Check how many leads are ready for agent
SELECT 
    status,
    COUNT(*) as count,
    COUNT(CASE WHEN agent_enabled = 1 THEN 1 END) as agent_enabled_count
FROM leads
GROUP BY status;