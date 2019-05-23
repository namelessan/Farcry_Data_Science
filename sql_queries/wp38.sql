SELECT match_id, count(killer_name) as suicide_count
FROM match_frag
GROUP BY match_id
ORDER BY COUNT(killer_name) DESC;