from datetime import datetime, timezone, timedelta
import re
import csv
from utilities.sqlite_util import create_connection, insert_match, insert_frag
from utilities.postgres_util import create_postgres_connection, insert_match_postgres, insert_frag_postgres


def read_log_file(log_file_pathname):
    """
    :param log_file_pathname: relative or absolute path to the log file
    :return: a string of file content
        example:
        >>>read_log_file('./log00.txt')
        Log Started at Friday, November 09, 2018 12:22:07
        FileVersion: 1.1.3.1395
        ...
    """

    try:
        with open(log_file_pathname, 'r') as file:
            file_content = file.read()
        return file_content

    # this is not finished, need to add more exception to handle: reading permission denied....
    except PermissionError:
        print('Reading permission denied: please add reading mode to the file')


def get_timezone(log_data):
    """
    :param log_data: string content of log file
    :return: the number of time zone in string format
        example:
            >>>get_timezone(log_data)
            -5
    """
    try:
        # the timezone is stored in log file in the format:
        # (g_timezone,-5) or (g_timezone,0).

        pattern = r"\(g_timezone,(.*)\)"
        timezone = re.findall(pattern, log_data)[0]

        return int(timezone)
    except ValueError:
        print('Can not find the timezone in log file')


def parse_log_start_time(log_data):
    """
    :param log_data: String content read from log file
    :return: a datetime object that shows when the log file is created
        example:
        >>>parse_log_start_time(log_data)
        datetime.datetime(2019, 5, 15, 17, 19, 51, 502927,
                          tzinfo=datetime.timezone(datetime.timedelta(-1, 68400)))
    """

    pattern = r"Log Started at (.+)"
    time_string = re.findall(pattern, log_data)[0]

    format_time = '%A, %B %d, %Y %H:%M:%S'
    timestamp = datetime.strptime(time_string, format_time)

    time_zone = get_timezone(log_data)

    # Update timestamp with timezone and return
    return timestamp.replace(tzinfo=timezone(timedelta(hours=time_zone)))


def parse_match_mode_and_map(log_data):
    """
    :param log_data: String content read from log file
    :return: a tuple of mode and map of the game session:
        example: (mode, map) = ('FFA', 'mp_surf')
    """
    pattern = r"-* Loading level Levels/(\w+), mission (\w+) -*"
    matches = re.findall(pattern, log_data)
    if matches:
        return matches[0][::-1]
    raise ValueError('Cannot find mode and map in the log file')


def remove_empty_elem(frags):
    """
    :param frags: List of tupple in format (frag_time, frager_name, victim_name, weapon_code)
                  or (frag_time, frager_name, '', '').
                example:[('26:32', 'papazark', 'lamonthe', 'AG36'),
                         ('27:07', 'theprophete', 'lamonthe', 'Rocket'),
                         ('27:18', 'theprophete', '', ''),...]
    :return: List of tupple without empty element
    """
    clean_frags = []

    for frag in frags:
        clean_frag = []
        for elem in frag:

            # Only save element that store values
            if elem:
                clean_frag.append(elem)

        clean_frags.append(tuple(clean_frag))

    return clean_frags


def add_timezone_to_frag(frags, start_time):
    """
    :param frags: List of tupple in format (frag_time, frager_name, victim_name, weapon_code)
                  or (frag_time, frager_name).
            example:[('26:32', 'papazark', 'lamonthe', 'AG36'),
                     ('27:07', 'theprophete', 'lamonthe', 'Rocket'),
                     ('27:18', 'theprophete'),...]
    :param start_time: a datetime object that show the start time of game session
    :return: List of tupple with updated fragtime by a datetime object with timezone.
            example:[(datetime.datetime(2018, 11, 9, 13, 0, 9,
                 tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                 'cyap', 'lamonthe', 'AG36Grenade'),
                 (datetime.datetime(2018, 11, 9, 13, 53, 19,
                 tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                 'cyap', 'papazark', 'AG36')]
    """
    timezone_frags = []
    last_frag_minute = 0
    for frag in frags:
        frag_minute, frag_second = list(map(int, frag[0].split(':')))

        # increase time by 1 hour if the minute of timestamp of next frag is smaller than last one.
        if frag_minute < last_frag_minute:
            start_time = start_time + timedelta(hours=1)

        # update the last frag minute to compare to next one
        last_frag_minute = frag_minute

        # update string timestamp by datetime object
        frag_time = start_time.replace(minute=frag_minute, second=frag_second)
        timezone_frag = [frag_time] + list(frag[1:])

        timezone_frags.append(tuple(timezone_frag))

    return timezone_frags


def parse_frags(log_data):
    """
    :param log_data: String content read from log file
    :return: List of tuple in the format: (frag_time, frager_name, victim_name, weapon_code) or (frag_time, frager_name)
            if player suicided.
            example:[(datetime.datetime(2018, 11, 9, 13, 0, 9,
                     tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                     'cyap', 'lamonthe', 'AG36Grenade'),
                     (datetime.datetime(2018, 11, 9, 13, 53, 19,
                     tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                     'cyap', 'papazark', 'AG36')]
    """
    pattern = r"<(.+?)> <Lua> (.+) killed (?:itself|(.+) with (.+))"
    frags = re.findall(pattern, log_data)
    clean_frags = remove_empty_elem(frags)
    start_time = parse_log_start_time(log_data)
    timezone_frags = add_timezone_to_frag(clean_frags, start_time)
    return timezone_frags


def prettify_frags(frags):
    """
    :param frags: List of tupple of frags in the game in format of:
                  (frag_time_datetime_object, frager_name, victim_name,
                   weapon_code) or (frag_time, frager_name)
                 example:
                        [(datetime.datetime(2018, 11, 9, 13, 0, 9,
                         tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                         'cyap', 'lamonthe', 'AG36Grenade'),
                         (datetime.datetime(2018, 11, 9, 13, 53, 19,
                         tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                         'cyap', 'papazark', 'AG36')]
    :return: List of prettyfied frags.
            example:
                ['[2019-03-01 16:22:54-05:00] 😛 cyap 🔫 😦 cynthia',
                 '[2019-03-01 16:24:48-05:00] 😛 cynthia 🔫 😦 cyap',
                 '[2019-03-01 16:25:06-05:00] 😛 cyap 🔫 😦 cynthia',
                ]
    """

    WEAPON_ICON = {}
    WEAPON_ICON.update(dict.fromkeys(['Vehicle'], '🚙'))
    WEAPON_ICON.update(dict.fromkeys([
        'Falcon', 'Shotgun', 'P90', 'MP5', 'M4', 'AG36',
        'OICW', 'SniperRifle', 'M249', 'VehicleMountedAutoMG', 'VehicleMountedMG', 'MG'], '🔫'))
    WEAPON_ICON.update(dict.fromkeys(
        ['HandGrenade', 'AG36Grenade', 'OICWGrenade', 'StickyExplosive'], '💣'))
    WEAPON_ICON.update(dict.fromkeys(
        ['Rocket', 'VehicleMountedRocketMG', 'VehicleRocket'], '🚀'))
    WEAPON_ICON.update(dict.fromkeys(['Machete'], '🔪'))
    WEAPON_ICON.update(dict.fromkeys(['Boat'], '🚤'))

    KILLER_ICON = '😛'
    VICTIM_ICON = '😦'
    SUICIDE_ICON = '☠'

    pretty_frags = []

    for frag in frags:
        timestamp = '[' + frag[0].isoformat(' ') + ']'
        if len(frag) > 2:
            frag_string = ' '.join(
                [timestamp, KILLER_ICON, frag[1], WEAPON_ICON[frag[3]], VICTIM_ICON, frag[2]])
        else:
            frag_string = ' '.join(
                [timestamp, VICTIM_ICON, frag[1], SUICIDE_ICON])
        pretty_frags.append(frag_string)

    return pretty_frags


def get_time_after_last_frag(log_data, last_frag):
    """
    :param log_data: String content read from log file
    :param last_frag: Tuple of last frag in format:
                    (frag_time_datetime_object, frager_name, victim_name,
                     weapon_code) or (frag_time, frager_name)
    :return: time after last frag in string format: '00:09'
    """
    list_log_data = log_data.split('\n')

    last_frag_time = ':'.join(
        list(map(str, [last_frag[0].minute, last_frag[0].second])))
    last_frag_frager = last_frag[1]

    i = 0
    # Determine index of last frag in log data
    for line in list_log_data:
        if last_frag_time in line and last_frag_frager in line:
            break
        i += 1

    # Get time after last frag
    time_after_last_frag = re.findall(r"^<(.{5})>", list_log_data[i+1])[0]

    return time_after_last_frag


def get_start_time_match(log_data):
    """
    :param log_data: String content read from log file
    :return: Start time in format of: 'HH:MM'. Ex: '24:19'
    """
    try:
        return re.findall(r"Precaching level ... <(.+?)> done", log_data)[0]
    except IndexError:
        return 'Start time not found'


def get_end_time_match(log_data):
    """
    :param log_data: String content read from log file
    :return: End time in format of: 'HH:MM'. Ex: '24:19'
    """
    try:
        return re.findall(r"<(.+?)> == Statistics", log_data)[0]
    except IndexError:
        return 'End time not found'


def parse_game_session_start_and_end_times(log_data, frags):
    """
    :param log_data: String content read of log file
    :param frags: List of tupple of frags in the game in format of:
                  (frag_time_datetime_object, frager_name, victim_name,
                   weapon_code) or (frag_time, frager_name)
                 example:
                        [(datetime.datetime(2018, 11, 9, 13, 0, 9,
                         tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                         'cyap', 'lamonthe', 'AG36Grenade'),
                         (datetime.datetime(2018, 11, 9, 13, 53, 19,
                         tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                         'cyap', 'papazark', 'AG36')]
    :return: start and end time of game session in datetime object format
            example:
                (datetime.datetime(2018, 11, 9, 12, 36, 5, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                (datetime.datetime(2018, 11, 9, 13, 53, 19, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400)))
    """

    start_time_match = get_start_time_match(log_data)
    # If Start time cannot be found, log file don't have game session time data
    if 'Start time not found' in start_time_match:
        return "game doesn't start"
    start_time_minute, start_time_second = list(
        map(int, start_time_match.split(':')))

    end_time_match = get_end_time_match(log_data)
    # If cannot find the time when the match end, use the time after the last frags instead
    if 'End time not found' in end_time_match:
        end_time_match = get_time_after_last_frag(log_data, frags[-1])
    end_time_minute, end_time_second = list(
        map(int, end_time_match.split(':')))

    first_frag_time = frags[0][0]
    last_frag_time = frags[-1][0]

    # If start time minute is greater than first frag time minute,
    # that means start time hour is smaller than first frag time hour
    if first_frag_time.minute < start_time_minute:
        first_frag_time = first_frag_time - timedelta(hours=1)
    start_session_time = first_frag_time.replace(
        minute=start_time_minute, second=start_time_second)

    # If end time minute is smaller then last frag time minute, that means
    # end time hour is greater than last frag time hour
    if end_time_minute < last_frag_time.minute:
        last_frag_time = last_frag_time + timedelta(hours=1)
    end_session_time = last_frag_time.replace(
        minute=end_time_minute, second=end_time_second)

    return start_session_time, end_session_time


def write_frag_csv_file(log_file_pathname, frags):
    """
    :param log_file_pathname: csv file path to write data on
    :param frags: data to be written, List of tupple in format of:
                [(datetime.datetime(2018, 11, 9, 13, 0, 9,
                tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                'cyap', 'lamonthe', 'AG36Grenade'),
                (datetime.datetime(2018, 11, 9, 13, 53, 19,
                tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                'cyap', 'papazark', 'AG36')]
    :return: no return, but data is written into the file
    """
    try:
        with open(log_file_pathname, 'w') as csvfile:
            filewriter = csv.writer(
                csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for frag in frags:
                filewriter.writerow(frag)
    except PermissionError:
        print('Cannot write into file, please change file mode')
        raise


def insert_match_to_sqlite(file_pathname, start_time, end_time, game_mode, map_name, frags):
    """
    :param file_pathname:  the path and name of the Far Cry's SQLite database
    :param start_time: a datetime.datetime object with time zone information corresponding to the start of the game session.
    :param end_time: a datetime.datetime object with time zone information corresponding to the end of the game session.
    :param game_mode: multiplayer mode of the game session:
                    - ASSAULT: there are two teams, one is defending a flag and the other
                    team is attacking it. Each maps has 3 flags and if after 20 minutes
                    not all flags are captured, the teams switch sides. The flags are on fixed
                    positions in the map and only one flag at the time is active;
                    - TDM (Team DeathMatch): the are two teams. Players of one team kill
                    members of the other team;
                    - FFA (Free-For-All): players kill anyone they can find.
    :param map_name: name of the map that was played.
    :param frags: a list of tuples of the following form:(frag_time, killer_name[, victim_name, weapon_code]). Where:
                frag_time (required): datetime.datetime with time zone when the frag occurred;
                killer_name (required): username of the player who fragged another or killed himself;
                victim_name (optional): username of the player who has been fragged;
                weapon_code (optional): code of the weapon that was used to frag.
    :return: the identifier of the match that has been inserted.
    """
    connection = create_connection(file_pathname)
    match = (start_time, end_time, game_mode, map_name)
    match_id = insert_match(connection, match)
    insert_frags_to_sqlite(connection, match_id, frags)
    connection.close()
    return match_id


def insert_frags_to_sqlite(connection, match_id, frags):
    """
    Insert a new frag into the match_frag table
    :param connection: a sqlite3 Connection object
    :param match_id: the identifier of a match
    :param frags: a list of frags, as passed to the function insert_match_to_sqlite, that occurred during this match.
    :return: No return
    """
    for frag in frags:
        full_frag = (match_id,) + frag
        if len(full_frag) < 5:
            full_frag = full_frag + (None, None,)
        insert_frag(connection, full_frag)


def insert_match_to_postgresql(properties, start_time, end_time, game_mode, map_name, frags):
    """
    :param properties: a tuple of the following form: (hostname, database_name, username, password). Where:
        hostname: hostname of the PosgtreSQL server to connect to;
        database_name: name of the database to use;
        username: username of the database account on behalf of whose the connection is being made;
        password: password of the database account.
    :param start_time: a datetime.datetime object with time zone information corresponding to the start of the game session
    :param end_time: a datetime.datetime object with time zone information corresponding to the end of the game session
    :param game_mode: multiplayer mode of the game session (ASSAULT, TDM, FFA)
    :param map_name: name of the map that was played.
    :param frags: a list of tuples of the following form: (frag_time, killer_name[, victim_name, weapon_code]). Where:
        frag_time (required): datetime.datetime with time zone when the frag occurred;
        killer_name (required): username of the player who fragged another or killed himself;
        victim_name (optional): username of the player who has been fragged;
        weapon_code (optional): code of the weapon that was used to frag.
    """
    connection = create_postgres_connection(properties)
    match = (start_time, end_time, game_mode, map_name)
    match_id = insert_match_postgres(connection, match)
    insert_frag_postgres(connection, match_id, frags)
    connection.close()
    return match_id


def calculate_serial_killers(frags):
    """
    :param frags: A list of tuple in format of:
        [(frag_time_datetime_object, frager_name, victim_name,
          weapon_code) or (frag_time, frager_name),...]
    :return: dictionary of killers with their longest kill series, where the key corresponds to
             the name of a player and the value corresponds to a list of frag times of the player's longest series
        Example:
        {
            player_name: [
                (frag_time, victim_name, weapon_code),
                (frag_time, victim_name, weapon_code),
                ...
            ],
            ...
        }

    """
    serial_kills = {}
    for frag in frags:
        if len(frag) == 4:
            frag_time, killer_name, victim_name, weapon_code = frag
            if killer_name not in serial_kills:
                serial_kills[killer_name] = [[]]
            if victim_name in serial_kills and serial_kills[victim_name][-1]:
                serial_kills[victim_name].append([])
            if killer_name in serial_kills:
                serial_kills[killer_name][-1].append(
                    (frag_time, victim_name, weapon_code))
        else:
            frag_time, killer_name = frag
            if killer_name in serial_kills and serial_kills[killer_name][-1]:
                serial_kills[killer_name].append([])
    serial_killers = {}
    for key, value in serial_kills.items():
        temp_result = max(value, key=lambda v: len(v))
        serial_killers[key] = temp_result
    return serial_killers


def calculate_serial_losers(frags):
    """
    :param frags: A list of tuple in format of:
        [(frag_time_datetime_object, frager_name, victim_name,
          weapon_code) or (frag_time, frager_name),...]
    :return: dictionary of losers with their longest kill series, where the key corresponds to
             the name of a player and the value corresponds to a list of frag times of the player's longest series
        Example:
        {
            player_name: [
                (frag_time, victim_name, weapon_code),
                (frag_time, victim_name, weapon_code),
                ...
            ],
            ...
        }

    """

    serial_loses = {}
    for frag in frags:
        if len(frag) == 4:
            frag_time, killer_name, victim_name, weapon_code = frag
            if victim_name not in serial_loses:
                serial_loses[victim_name] = [[]]
            if killer_name in serial_loses and serial_loses[killer_name][-1]:
                serial_loses[killer_name].append([])
            if victim_name in serial_loses:
                serial_loses[victim_name][-1].append((frag_time, killer_name, weapon_code))
        else:
            frag_time, killer_name = frag
            if killer_name in serial_loses and serial_loses[killer_name][-1]:
                serial_loses[killer_name].append([(frag_time, killer_name)])
    serial_losers = {}
    for key, value in serial_loses.items():
        temp_result = max(value, key=lambda v: len(v))
        serial_losers[key] = temp_result
    return serial_losers


if __name__ == '__main__':
    log_file_content = read_log_file('./logs/log00.txt')
    frags = parse_frags(log_file_content)
    # start_time, end_time = parse_game_session_start_and_end_times(
    #     log_file_content, frags)
    # game_mode, map_name = parse_match_mode_and_map(log_file_content)
    # properties = ('localhost', 'farcry', 'postgres', 'linh3lan')
    # match_id = insert_match_to_postgresql(
    #     properties, start_time, end_time, game_mode, map_name, frags)
    # print(match_id)
    # serial_killers = calculate_serial_killers(frags)
    # for player_name, kill_series in serial_killers.items():
    #     print('[%s]' % player_name)
    #     print('\n'.join([', '.join(([str(e) for e in kill]))
    #         for kill in kill_series]))
    serial_losers = calculate_serial_losers(frags)
    for player_name, lose_series in serial_losers.items():
        print('[%s]' % player_name)
        print('\n'.join([', '.join(([str(e) for e in kill]))
            for kill in lose_series]))
