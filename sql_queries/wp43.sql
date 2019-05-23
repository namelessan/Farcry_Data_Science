SELECT
	m.match_id,
	start_time,
	end_time,
	f2.player_count,
	m2.kill_suicide_count
FROM match as m
INNER JOIN
(
	SELECT f.match_id, count(f.killer_name) as player_count
	FROM
	(
		SELECT DISTINCT match_id, killer_name
		FROM match_frag
		UNION
		SELECT DISTINCT match_id, victim_name
		FROM match_frag
	) as f
	GROUP BY f.match_id
) AS f2
ON m.match_id = f2.match_id

INNER JOIN
(
	SELECT f3.match_id, COUNT(f3.killer_name) AS kill_suicide_count
	FROM match_frag f3
	GROUP BY f3.match_id
) as m2
ON m.match_id = m2.match_id

