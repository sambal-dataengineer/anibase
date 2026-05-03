CREATE TABLE IF NOT EXISTS metadata.details (
    id              SERIAL          PRIMARY KEY,
    media_id        INTEGER         NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    description     TEXT,
    episodes        SMALLINT,
    duration        SMALLINT,
    season          VARCHAR(10)     CHECK (season IN ('SPRING', 'SUMMER', 'FALL', 'WINTER')),
    season_year     SMALLINT,
    source          VARCHAR(30),
    trailer_id      VARCHAR(100),
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP       DEFAULT NOW()
);

ALTER TABLE metadata.details ADD CONSTRAINT details_media_id_unique UNIQUE (media_id);

ALTER TABLE metadata.details
    ADD COLUMN chapters SMALLINT,
    ADD COLUMN volumes SMALLINT,
    ADD COLUMN start_date DATE,
    ADD COLUMN end_date DATE,
    ADD COLUMN next_airing_episode SMALLINT,
    ADD COLUMN next_airing_at TIMESTAMP;