-- Tabela de artistas (base do modelo)
CREATE TABLE IF NOT EXISTS artists (
    id SERIAL PRIMARY KEY,
    spotify_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    href TEXT,
    uri TEXT,
    image TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de albums (referencia artists)
CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    spotify_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    release_date DATE,
    total_tracks INT,
    href TEXT,
    uri TEXT,
    url TEXT,
    image TEXT,
    artist_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

-- Tabela de tracks (referencia artists)
CREATE TABLE IF NOT EXISTS tracks (
    id SERIAL PRIMARY KEY,
    spotify_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    duration_ms INT,
    explicit BOOLEAN,
    disc_number INT,
    track_number INT,
    href TEXT,
    uri TEXT,
    url TEXT,
    artist_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

-- Tabela de audio features (referencia tracks)
CREATE TABLE IF NOT EXISTS audio_features (
    id SERIAL PRIMARY KEY,
    track_id INT NOT NULL,
    href TEXT,
    isrc VARCHAR(255),
    acousticness DECIMAL(5, 4),
    danceability DECIMAL(5, 4),
    energy DECIMAL(5, 4),
    instrumentalness DECIMAL(5, 4),
    key INT,
    liveness DECIMAL(5, 4),
    loudness DECIMAL(7, 3),
    mode INT,
    speechiness DECIMAL(5, 4),
    tempo DECIMAL(7, 3),
    valence DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

-- Tabela de rankings de artistas (artist100)
CREATE TABLE IF NOT EXISTS rank_artists (
    id SERIAL PRIMARY KEY,
    artist_id INT NOT NULL,
    position INT NOT NULL,
    lw INT,
    weeks INT,
    peak INT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

-- Tabela de rankings de albums (billboard200)
CREATE TABLE IF NOT EXISTS rank_albums (
    id SERIAL PRIMARY KEY,
    album_id INT NOT NULL,
    position INT NOT NULL,
    lw INT,
    weeks INT,
    peak INT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);

-- Tabela de rankings de tracks (hot100 e global200)
CREATE TABLE IF NOT EXISTS rank_tracks (
    id SERIAL PRIMARY KEY,
    track_id INT NOT NULL,
    chart_name VARCHAR(100) NOT NULL,
    position INT NOT NULL,
    lw INT,
    weeks INT,
    peak INT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

-- Índices para melhorar performance nas queries
CREATE INDEX IF NOT EXISTS idx_albums_artist_id ON albums(artist_id);
CREATE INDEX IF NOT EXISTS idx_albums_spotify_id ON albums(spotify_id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist_id ON tracks(artist_id);
CREATE INDEX IF NOT EXISTS idx_tracks_spotify_id ON tracks(spotify_id);
CREATE INDEX IF NOT EXISTS idx_audio_features_track_id ON audio_features(track_id);
CREATE INDEX IF NOT EXISTS idx_rank_artists_position ON rank_artists(position);
CREATE INDEX IF NOT EXISTS idx_rank_albums_position ON rank_albums(position);
CREATE INDEX IF NOT EXISTS idx_rank_tracks_position ON rank_tracks(position);
CREATE INDEX IF NOT EXISTS idx_rank_tracks_chart ON rank_tracks(chart_name);