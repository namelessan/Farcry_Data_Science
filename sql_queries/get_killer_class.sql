CREATE OR REPLACE FUNCTION get_killer_class (weapon_code VARCHAR(50))
    RETURNS VARCHAR(50) AS
$$
BEGIN
    CASE
        WHEN weapon_code IN ('Machete', 'Falcon', 'MP5') THEN
            RETURN 'Hitman';
        WHEN weapon_code IN ('SniperRifle') THEN
            RETURN 'Sniper';
        WHEN weapon_code IN ('AG36', 'OICW', 'P90', 'M4', 'Shotgun', 'M249') THEN
            RETURN 'Commando';
        WHEN weapon_code IN ('Rocket', 'VehicleRocket', 'HandGrenade', 'StickyExplosive', 'Boat',
                             'Vehicle', 'VehicleMountedRocketMG', 'VehicleMountedAutoMG', 'MG',
                             'VehicleMountedMG', 'OICWGrenade', 'AG36Grenade') THEN
            RETURN 'Psychopath';
        ELSE
            RETURN 'No Name';
    END CASE;
END
$$
LANGUAGE PLPGSQL;