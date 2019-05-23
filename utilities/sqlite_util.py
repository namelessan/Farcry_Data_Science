import sqlite3


def create_connection(file_pathname):

    """ create a database connection to the SQLite database
        specified by file_pathname
    :param file_pathname: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(file_pathname)
        return conn
    except Error as e:
        print(e)

    return None


def insert_match(conn, match):
    """
    Create a new match into the match table
    :param conn: connection object of sqlite database
    :param match: a tuple of match information: (start_time, endtime, game_mode, map_name)
    :return: match id
    """
    sql = ''' INSERT INTO match(start_time, end_time, game_mode, map_name)
              VALUES(?, ?, ?, ?) '''
    cur = conn.cursor()
    try:
        with conn:
            cur.execute(sql, match)
            return cur.lastrowid
    except sqlite3.IntegrityError:
        print("Coudn't add the value twice")


def insert_frag(conn, frag):
    """
    Create a new frag into the match_frag table
    :param conn: connection object of sqlite database
    :param frag: a tuple of frag information: ()
    :return: match_id
    """
    sql = ''' INSERT INTO match_frag(match_id, frag_time, killer_name, victim_name, weapon_code)
              VALUES(?, ?, ?, ?, ?) '''
    cur = conn.cursor()
    try:
        with conn:
            cur.execute(sql, frag)
            return cur.lastrowid
    except sqlite3.IntegrityError:
        print("Coudn't add the value twice")