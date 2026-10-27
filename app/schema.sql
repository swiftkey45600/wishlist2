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
    cover_image_id INTEGER,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (cover_image_id) REFERENCES images(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS gifts (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    price INTEGER,
    status TEXT NOT NULL DEFAULT 'available'
    CHECK (status IN ('available', 'reserved', 'bought')),
    priority TEXT NOT NULL DEFAULT 'normal'
    CHECK (priority IN ('high', 'normal', 'low')),
    description TEXT,
    picture_url TEXT,
    marketplace_url TEXT,
    category_id INTEGER,
    image_id INTEGER,
    contribution_goal INTEGER CHECK (contribution_goal > 0),
    share_in_recommendations INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE (event_id, name),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gift_tags (
    gift_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (gift_id, tag_id),
    FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gift_questions (
    id INTEGER PRIMARY KEY,
    gift_id INTEGER NOT NULL,
    guest_name TEXT NOT NULL CHECK (length(trim(guest_name)) BETWEEN 1 AND 100),
    text TEXT NOT NULL CHECK (length(trim(text)) BETWEEN 1 AND 2000),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    answer TEXT CHECK (answer IS NULL OR length(trim(answer)) BETWEEN 1 AND 2000),
    answered_at TEXT,
    FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS gift_questions_gift_id ON gift_questions(gift_id, id);

CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY,
    gift_id INTEGER NOT NULL UNIQUE,
    reserver_name TEXT,
    reserver_id INTEGER,
    secret_word_hash TEXT,
    is_fundraising INTEGER NOT NULL DEFAULT 0,
    is_anonymous INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE,
    FOREIGN KEY (reserver_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY,
    image_path TEXT NOT NULL,
    image_type TEXT,
    hash TEXT NOT NULL UNIQUE,
    owner_id INTEGER,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gift_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    contributor_name TEXT,
    contributor_id INTEGER,
    secret_word_hash TEXT,
    is_anonymous INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE,
    FOREIGN KEY (contributor_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS contributions_gift_id ON contributions(gift_id);

CREATE TABLE IF NOT EXISTS guest_reservation_rate_limits (
    key TEXT PRIMARY KEY,
    attempts INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
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

INSERT OR IGNORE INTO marketplaces (slug, name, base_url)
VALUES ('ozon', 'Ozon', 'https://www.ozon.ru');

INSERT OR IGNORE INTO marketplaces (slug, name, base_url)
VALUES ('wb', 'WB', 'https://www.wildberries.ru');

INSERT OR IGNORE INTO marketplaces (slug, name, base_url)
VALUES ('yandex-market', 'Я.Маркет', 'https://market.yandex.ru');

INSERT OR IGNORE INTO marketplaces (slug, name, base_url)
VALUES ('aliexpress', 'AliExpress', 'https://aliexpress.ru');
