-- The function returns the Lucky Luke
-- longest series of kills for each player and for each match.
-- It returns a set of records defined with the following columns:
--
-- match_id: identification of a match;
--
-- killer_name: name of a Lucky Luke player;
--
-- kill_count: the number of kills of the longest Lucky
-- Luke series of this player for this match.
CREATE OR REPLACE FUNCTION calculate_lucky_luke_killers(p_min_kill_count integer default 3,
                                                        p_max_time_between_kills integer default 10)
    RETURNS TABLE
            (
                match_id    uuid,
                killer_name text,
                kill_count  bigint
            )
AS
$$
DECLARE
    rec   RECORD;
    rec1  RECORD;
    count int;
    tmp   int;
BEGIN
    FOR rec IN
        select DISTINCT f.match_id, f.killer_name from match_frags f
        LOOP
            count := 1;
            tmp := 1;
            FOR rec1 IN
                (SELECT f.match_id,
                             f.frag_time,
                             f.killer_name,
                             f.frag_time -
                             lag(f.frag_time) over (order by f.match_id, f.killer_name, f.frag_time) as CHECK
                FROM match_frags f
                GROUP BY f.match_id, f.frag_time, f.killer_name)
                LOOP
                    IF rec.match_id = rec1.match_id AND rec.killer_name = rec1.killer_name AND
                       cast(extract(epoch from rec1.CHECK) as integer) <= p_max_time_between_kills
                    THEN
                        tmp := tmp + 1;
                    ELSIF rec.match_id = rec1.match_id AND rec.killer_name = rec1.killer_name AND
                          cast(extract(epoch from rec1.CHECK) as integer) > p_max_time_between_kills
                    THEN
                        IF tmp > count THEN
                            count := tmp; tmp := 0;
                        ELSIF tmp < count THEN
                            tmp := 0;
                        END IF;
                    END IF;
                END LOOP;
            IF count >= p_min_kill_count
            THEN
                match_id := rec.match_id;
                killer_name := rec.killer_name;
                kill_count := count;
                RETURN NEXT;
            END IF;
        END LOOP;
END;
$$ LANGUAGE PLPGSQL;



SELECT *
FROM calculate_lucky_luke_killers();
