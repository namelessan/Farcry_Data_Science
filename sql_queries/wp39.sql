SELECT match_id, COUNT(killer_name) AS suicide_count
FROM match_frag
WHERE victim_name IS NULL
GROUP BY match_id
ORDER BY COUNT(killer_name);