SELECT killer_name AS player_name, COUNT(victim_name) AS kill_count
FROM match_frag
GROUP BY killer_name
ORDER BY COUNT(victim_name) DESC, killer_name ASC;