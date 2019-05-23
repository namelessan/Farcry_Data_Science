--WP 46
CREATE DATABASE farcry ENCODING "utf-8";

--WP 47
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA farcry;

SELECT uuid_generate_v1();

CREATE TABLE match (
    match_id uuid NOT NULL DEFAULT uuid_generate_v1(),
    start_time TIMESTAMPTZ(3) NOT NULL,
    end_time TIMESTAMPTZ(3) NOT NULL,
    game_mode TEXT NOT NULL,
    map_name TEXT NOT NULL
);
CREATE TABLE match_frag (
    match_id uuid NOT NULL,
    frag_time TIMESTAMPTZ(3) NOT NULL,
    killer_name TEXT NOT NULL,
    victim_name TEXT,
    weapon_code TEXT
);
ALTER TABLE IF EXISTS match
    ADD CONSTRAINT pk_match_match_id PRIMARY KEY (match_id);
ALTER TABLE IF EXISTS match_frag
    ADD CONSTRAINT fk_match_frag_match_id FOREIGN KEY (match_id) REFERENCES match(match_id) ON UPDATE CASCADE;
