CREATE TABLE IF NOT EXISTS catalog.genres (
    id      SERIAL      PRIMARY KEY,
    name    VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS catalog.tags (
    id      SERIAL      PRIMARY KEY,
    name    VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS catalog.media_genres (
    media_id    INTEGER     NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    genre_id    INTEGER     NOT NULL REFERENCES catalog.genres(id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, genre_id)
);

CREATE TABLE IF NOT EXISTS catalog.media_tags (
    media_id    INTEGER     NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    tag_id      INTEGER     NOT NULL REFERENCES catalog.tags(id) ON DELETE CASCADE,
    tag_rank    SMALLINT,
    PRIMARY KEY (media_id, tag_id)
);