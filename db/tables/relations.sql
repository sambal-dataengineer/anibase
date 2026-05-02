CREATE TABLE IF NOT EXISTS relations.media_relations (
    id                  SERIAL      PRIMARY KEY,
    media_id            INTEGER     NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    related_media_id    INTEGER     NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    relation_type       VARCHAR(30) CHECK (relation_type IN (
                            'SEQUEL', 'PREQUEL', 'ALTERNATIVE',
                            'SIDE_STORY', 'CHARACTER', 'SUMMARY',
                            'PARENT', 'SPIN_OFF', 'ADAPTATION', 'OTHER'
                        )),
    UNIQUE (media_id, related_media_id)
);

CREATE TABLE IF NOT EXISTS relations.recommendations (
    id                          SERIAL      PRIMARY KEY,
    media_id                    INTEGER     NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    recommended_media_id        INTEGER     NOT NULL REFERENCES media.media(id) ON DELETE CASCADE,
    rating                      INTEGER,
    UNIQUE (media_id, recommended_media_id)
);