SELECT match_id, victim_name AS player_name, COUNT(victim_name) AS death_count
FROM match_frag
WHERE victim_name IS NOT NULL
GROUP BY victim_name, match_id
ORDER BY match_id ASC, COUNT(victim_name) DESC;