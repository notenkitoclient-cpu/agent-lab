-- エージェント（ツール）台帳
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE,           
    name TEXT,
    github_url TEXT,
    source TEXT,                
    stars INTEGER,              
    forks INTEGER,
    language TEXT,              
    topics TEXT,                
    description TEXT,
    growth_score REAL,          
    agent_score REAL,           
    created_at DATE,            
    discovered_at DATE,
    last_updated DATE           
);

-- 実験ログ管理
CREATE TABLE experiments (
    id TEXT PRIMARY KEY,        
    agent_id TEXT,              
    title TEXT,
    summary TEXT,               
    created_at DATE,
    file_path TEXT              
);

-- 高速化・検索用インデックス
CREATE INDEX idx_agents_slug ON agents(slug);
CREATE INDEX idx_experiments_agent ON experiments(agent_id);
