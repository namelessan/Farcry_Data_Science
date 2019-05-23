SELECT match_id,
       victim_name as player_name,
       killer_name as worst_enemy_name,
       kill_count
FROM (
    SELECT match_id,
        killer_name,
        victim_name,
        count(killer_name) AS kill_count,
        ROW_NUMBER() OVER (
            PARTITION BY victim_name
            ORDER BY COUNT(killer_name) DESC
        ) AS row_number
    FROM match_frag
    WHERE victim_name IS NOT NULL
    GROUP BY match_id, 
             killer_name, 
             victim_name
) as worst_enemy_table
WHERE row_number = 1;