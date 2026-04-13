-- Migration: Create roleplay_sessions and roleplay_messages tables
-- Created: 2026-04-13

-- Create users table if not exists (base table)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create roleplay_sessions table
CREATE TABLE IF NOT EXISTS roleplay_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tool_id VARCHAR(50) DEFAULT 'roleplay',
    questionnaire_content TEXT NOT NULL,
    rag_index_data TEXT,
    status VARCHAR(20) DEFAULT 'in_progress',
    duration INTEGER DEFAULT 1800,
    remaining_time INTEGER DEFAULT 1800,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create roleplay_messages table
CREATE TABLE IF NOT EXISTS roleplay_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_topic VARCHAR(100),
    context_chunks TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES roleplay_sessions(id)
);

-- Create indexes for roleplay_messages
CREATE INDEX IF NOT EXISTS idx_roleplay_messages_session_id ON roleplay_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_roleplay_messages_timestamp ON roleplay_messages(timestamp);