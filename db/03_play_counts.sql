CREATE TABLE IF NOT EXISTS subscriber_song_play (
 subscriber_id integer NOT NULL REFERENCES subscribers(subscriber_id),
 song_id integer NOT NULL REFERENCES songs(song_id),
 num_rep bigint NOT NULL CHECK (num_rep >= 0),
 PRIMARY KEY (subscriber_id, song_id)
);
CREATE TABLE IF NOT EXISTS song_daily_play (
 song_id integer NOT NULL REFERENCES songs(song_id),
 play_date date NOT NULL,
 num_rep bigint NOT NULL CHECK (num_rep >= 0),
 PRIMARY KEY (song_id, play_date)
);
