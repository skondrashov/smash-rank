CREATE DATABASE IF NOT EXISTS MeleeData;
USE MeleeData

DROP TABLE IF EXISTS
    ratings,
    sets,
    tournaments,
    attended,
    users,
    players;


CREATE TABLE players(
    id      INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    tag     VARCHAR(50)  NOT NULL,
    sponsor VARCHAR(50),
    smashgg_id INT UNSIGNED,
    skill DOUBLE NOT NULL DEFAULT 1500.0
    /*
    -- tournaments attended:
        SELECT id FROM tournaments t
            JOIN sets s ON t.id = s.tournament_id
            WHERE s.winner_id={player_id} OR s.loser_id={player_id};
    -- data against an opponent:
        SELECT COUNT(*) FROM sets
            WHERE winner_id={player_id} AND loser_id={opponent_id} OR winner_id={opponent_id} AND loser_id={player_id};
    -- all sets in chronological order:
        SELECT * FROM sets s
            JOIN tournaments t ON t.id = s.tournament_id
            WHERE s.winner_id={player_id} OR s.loser_id={player_id}
            ORDER BY t.date, t.id, s.is_losers, s.sets_remaining;
    --
    */
);

CREATE TABLE users(
    id          INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50)  NOT NULL,
    password    BINARY(64)   NOT NULL,
    player_id   INT UNSIGNED,
    first_name  VARCHAR(50),
    last_name   VARCHAR(50),
    facebook_id VARCHAR(50)
    ,
    FOREIGN KEY (player_id)
        REFERENCES players(id)
        ON DELETE SET NULL
    -- add other profile information
);



CREATE TABLE tournaments(
    id       INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    name     VARCHAR(100) NOT NULL,
    series   VARCHAR(100),
    location VARCHAR(100) NOT NULL,
    date     TIMESTAMP    NOT NULL
    /*
    -- entrants can be found with (for example):
        SELECT (COUNT(winner_id) + COUNT(loser_id)) AS entrants
            FROM sets
            WHERE tournament_id={tournament_id} AND is_losers = FALSE AND sets_remaining=MAX(sets_remaining);
    */
);

CREATE TABLE attended(
    id              INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    player_id       INT UNSIGNED NOT NULL,
    tournament_id   INT UNSIGNED NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
);

-- bracket can be built using losers_bracket and sets_remaining, and displayed by matching match participants to prior match winner_ids
CREATE TABLE sets(
    id             INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    tournament_id  INT UNSIGNED     NOT NULL,
    winner_id      INT UNSIGNED     NOT NULL,
    loser_id       INT UNSIGNED     NOT NULL,
    best_of        SMALLINT,
    loser_wins     SMALLINT,
    sets_remaining SMALLINT UNSIGNED NOT NULL,
    is_losers      BOOLEAN          NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
        ON DELETE CASCADE,
    FOREIGN KEY (winner_id)     REFERENCES players(id),
    FOREIGN KEY (loser_id)      REFERENCES players(id)
);

CREATE TABLE ratings(
    id            INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    player_id     INT UNSIGNED NOT NULL,
    opponent_id   INT UNSIGNED NOT NULL,
    tournament_id INT UNSIGNED NOT NULL,
    set_id        INT UNSIGNED NOT NULL,
    rating        DOUBLE       NOT NULL,
    FOREIGN KEY (player_id)     REFERENCES players(id)     ON DELETE CASCADE,
    FOREIGN KEY (opponent_id)     REFERENCES players(id)     ON DELETE CASCADE,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
    FOREIGN KEY (set_id)        REFERENCES sets(id)        ON DELETE CASCADE
);