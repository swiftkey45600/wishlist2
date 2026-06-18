PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    birthday TEXT,
    gender INTEGER
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    event_date TEXT,
    place TEXT,
    public_token TEXT UNIQUE,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gifts (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    price INTEGER,
    status TEXT NOT NULL DEFAULT 'available'
    CHECK (status IN ('available', 'reserved', 'bought')),
    description TEXT,
    picture_url TEXT,
    marketplace_url TEXT,
    category_id INTEGER,
    image_id INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY,
    gift_id INTEGER NOT NULL UNIQUE,
    reserver_name TEXT,
    is_anonymous INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY,
    image_path TEXT NOT NULL,
    image_type TEXT,
    hash TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS marketplaces (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    logo_url TEXT
);

INSERT OR IGNORE INTO users (id, name, login, password_hash)
VALUES (1, 'John Doe', 'johndoe', 'hashedpassword');
