import psycopg2


def create_postgres_connection(properties):
    """
    :param properties: a tuple of the following form: (hostname, database_name, username, password). Where:
        hostname: hostname of the PosgtreSQL server to connect to;
        database_name: name of the database to use;
        username: username of the database account on behalf of whose the connection is being made;
        password: password of the database account.
    :return: connection object to the postgresql database
    """
    connection = psycopg2.connect(
        host=properties[0], database=properties[1], user=properties[2], password=properties[3]
    )
    return connection


def insert_match_postgres(connection, match):
    """
    :param connection: connection object of postgresql database
    :param match: a tuple of match in format of: (start_time, endtime, game_mode, map_name)
    :return: match_id of inserted match in format uuid
    """
    cur = connection.cursor()
    sql = """ INSERT INTO match(start_time, end_time, game_mode, map_name)
                VALUES(%s, %s, %s, %s) RETURNING match_id; """
    cur.execute(sql, match)
    match_id = cur.fetchone()[0]
    connection.commit()
    cur.close()
    return match_id


def insert_frag_postgres(connection, match_id, frags):
    """
    :param connection: connection object of postgresql database
    :param match_id: match id of frags to be inserted in format uuid
    :param frags: a list of tuple in format of: (frag_time, killer_name[, victim_name, weapon_code])
    """
    cur = connection.cursor()
    sql = """ INSERT INTO match_frag(match_id, frag_time, killer_name, victim_name, weapon_code)
                VALUES(%s, %s, %s, %s, %s); """
    for frag in frags:
        full_frag = (match_id,) + frag
        if len(full_frag) < 5:
            full_frag = full_frag + (None, None)
        cur.execute(sql, full_frag)
    connection.commit()
    cur.close()
