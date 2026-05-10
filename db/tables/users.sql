-- Core user accounts
CREATE TABLE IF NOT EXISTS users.users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT         NOT NULL,
    created_at    TIMESTAMP    DEFAULT now()
);

-- Watchlist: one entry per user per title, freeform status
CREATE TABLE IF NOT EXISTS users.watchlist (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users.users(id) ON DELETE CASCADE,
    media_id   INTEGER NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    status     VARCHAR(100),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (user_id, media_id)
);

-- Named private lists
CREATE TABLE IF NOT EXISTS users.lists (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER      NOT NULL REFERENCES users.users(id) ON DELETE CASCADE,
    name       VARCHAR(100) NOT NULL,
    created_at TIMESTAMP    DEFAULT now()
);

-- Items inside a list
CREATE TABLE IF NOT EXISTS users.list_items (
    list_id    INTEGER   NOT NULL REFERENCES users.lists(id)  ON DELETE CASCADE,
    media_id   INTEGER   NOT NULL REFERENCES media.media(id)  ON DELETE CASCADE,
    added_at   TIMESTAMP DEFAULT now(),
    PRIMARY KEY (list_id, media_id)
);