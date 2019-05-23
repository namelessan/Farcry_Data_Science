SELECT match_id, killer_name AS player_name, COUNT(victim_name) AS kill_count
FROM match_frag
GROUP BY killer_name, match_id
ORDER BY match_id ASC, COUNT(victim_name) DESC;