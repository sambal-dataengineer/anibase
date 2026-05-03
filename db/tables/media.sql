CREATE TABLE IF NOT EXISTS media.media (
    id              INTEGER PRIMARY KEY,
    title_romaji    VARCHAR(255),
    title_english   VARCHAR(255),
    type            VARCHAR(10)     NOT NULL CHECK (type IN ('ANIME', 'MANGA')),
    format          VARCHAR(20),
    status          VARCHAR(30),
    cover_image_url TEXT,
    average_score   SMALLINT,
    popularity      INTEGER,
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP       DEFAULT NOW()
);

ALTER TABLE media.media ADD COLUMN title_native TEXT;