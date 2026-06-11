-- Tabela de Partidas
CREATE TABLE IF NOT EXISTS matches (
    match_hash TEXT PRIMARY KEY,
    battle_time TEXT NOT NULL,
    mode TEXT NOT NULL,
    map TEXT NOT NULL,
    duration INTEGER
);

-- Tabela de Jogadores
CREATE TABLE IF NOT EXISTS players (
    tag TEXT PRIMARY KEY,
    name TEXT,
    scanned INTEGER DEFAULT 0 -- 0 para pendente, 1 para concluído
);

-- Tabela de Relação 
CREATE TABLE IF NOT EXISTS match_players (
    match_hash TEXT NOT NULL,
    player_tag TEXT NOT NULL,
    team_id INTEGER NOT NULL, -- 0 para um time, 1 para o outro
    brawler_name TEXT NOT NULL,
    power INTEGER,
    trophies INTEGER,
    result TEXT NOT NULL, -- O resultado foi isolado aqui
    PRIMARY KEY (match_hash, player_tag),
    FOREIGN KEY (match_hash) REFERENCES matches(match_hash),
    FOREIGN KEY (player_tag) REFERENCES players(tag)
);