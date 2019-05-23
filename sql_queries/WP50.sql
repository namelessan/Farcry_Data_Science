SELECT match_id,
       killer_name AS player_name,
       victim_name AS favorite_victim_name,
       kill_count
FROM (
         SELECT match_id,
                killer_name,
                victim_name,
                COUNT(victim_name) AS kill_count,
                ROW_NUMBER() OVER (
                    PARTITION BY killer_name
                    ORDER BY
                        COUNT(victim_name) DESC,
                        match_id ASC
                    ) AS row_number
         FROM match_frag
         WHERE victim_name IS NOT NULL
         GROUP BY match_id,
                  killer_name,
                  victim_name
     ) AS killer_victim_table
WHERE row_number = '1';