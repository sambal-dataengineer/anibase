CREATE TABLE IF NOT EXISTS external_links.links (
    id          SERIAL          PRIMARY KEY,
    media_id    INTEGER         NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    site        VARCHAR(100)    NOT NULL,
    url         TEXT            NOT NULL,
    type        VARCHAR(20),
    created_at  TIMESTAMP       DEFAULT NOW(),
    updated_at  TIMESTAMP       DEFAULT NOW()
);

ALTER TABLE external_links.links ADD CONSTRAINT links_media_url_unique UNIQUE (media_id, url);