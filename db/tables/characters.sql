CREATE TABLE IF NOT EXISTS characters.characters (
    id              INTEGER         PRIMARY KEY,
    name_full       VARCHAR(255),
    name_native     VARCHAR(255),
    image_url       TEXT,
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP       DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS characters.media_characters (
    media_id        INTEGER         NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    character_id    INTEGER         NOT NULL REFERENCES characters.characters(id) ON DELETE CASCADE,
    role            VARCHAR(20)     CHECK (role IN ('MAIN', 'SUPPORTING', 'BACKGROUND')),
    PRIMARY KEY (media_id, character_id)
);