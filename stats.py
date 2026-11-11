import glob
import sqlite3
# import os

import pandas as pd
import matplotlib.pyplot as plt

# TODO : study those libraries
import matplotlib.dates as mdates       # date axis for the monthly charts
from matplotlib.patches import Patch    # legend for the coloured phases




def get_time_window(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql("""
        WITH plays AS (
            SELECT day, month, year FROM music
            UNION ALL
            SELECT day, month, year FROM podcasts
        )
        SELECT * FROM (
            SELECT 'min' AS type, day, month, year
            FROM plays
            ORDER BY year, month, day
            LIMIT 1
        )
        UNION ALL
        SELECT * FROM (
            SELECT 'max' AS type, day, month, year
            FROM plays
            ORDER BY year DESC, month DESC, day DESC
            LIMIT 1
        )
    """, conn)
    return df


    
def activity(conn: sqlite3.Connection, mode: str, year=None, month=None, day=None, day_of_week=None, day_of_year=None, hour=None, music_or_podcasts=None):
    # errors
    if mode not in {"year", "month", "day", "day_of_week", "day_of_year", "hour"}:
        raise ValueError(f"invalid mode - has to be year/month/day/day_of_week/day_of_year/hour. You entered: {mode!r}")
    if music_or_podcasts not in (None, "music", "podcasts"):
       raise ValueError(f"music_or_podcasts has to be music/podcasts/None. (You entered: {music_or_podcasts!r})")

    # cannot specify atribute in its own statistics - cant limit hour in statistic by hour - RAISE ERROR 
    # this function is to be used by programms, not people, mistakes shouldnt be tolerated, i need to know about them
    if ((mode == "year" and year is not None) or
        (mode == "month" and month is not None) or
        (mode == "day" and day is not None) or
        (mode == "day_of_week" and day_of_week is not None) or
        (mode == "day_of_year" and day_of_year is not None) or
        (mode == "hour" and hour is not None)):

        raise ValueError("Atribute was specified in its own statistic function")


    # specify source
    if music_or_podcasts is not None:
        source = music_or_podcasts
    else:
        source = """(SELECT year, month, day, day_of_week, day_of_year, hour, seconds_played FROM music
                    UNION ALL
                    SELECT year, month, day, day_of_week, day_of_year, hour, seconds_played FROM podcasts)"""
    
    # conditions
    where = "WHERE 1=1"

    if year is not None:
        where += " AND year = " + str(year)
    if month is not None:
        where += " AND month = " + str(month)
    if day is not None:
        where += " AND day = " + str(day)
    if day_of_week is not None:
        where += " AND day_of_week = " + str(day_of_week)
    if day_of_year is not None:
        where += " AND day_of_year = " + str(day_of_year)
    if hour is not None:
        where += " AND hour = " + str(hour)

    df = pd.read_sql(f"""
            SELECT {mode}, CAST(ROUND(SUM(seconds_played) / 60.0, 0) AS INTEGER) AS minutes_played
            FROM {source}
            {where}
            GROUP BY {mode}
            ORDER BY {mode}
        """, conn)


    # fill empty rows with 0
    # TODO adjust for leap year
    min_value = {"month": 1, "day": 1, "day_of_week": 0, "day_of_year": 1, "hour": 0}
    max_value = {"month": 13, "day": 32, "day_of_week": 7, "day_of_year": 367, "hour": 24}


    if mode in {"month", "day", "day_of_week", "day_of_year", "hour"}:
        df = (df.set_index(mode)
                .reindex(range(min_value[mode], max_value[mode]), fill_value=0)
                .rename_axis(mode)
                .reset_index())
    return df


# extreme - napriklad nejvic busy extreme v inside, mesic v roce, 
'''
def get_extreme(extreme: str, in_par: str, in_par_value: int, music_or_podcasts=None):
    if music_or_podcasts is not None:
        source = "FROM " + music_or_podcasts
    else:
        source = """FROM (SELECT year, month, day, hour, seconds_played FROM music
                            UNION ALL
                            SELECT year, month, day, hour, seconds_played FROM podcasts)"""

    where = "WHERE 1=1"
    # nevim TODO
'''
    
# seskupim podle extremu - pro den seskupim konkretni dny, pro hodinu konkretni hodiny, pro mesice konkretni mesice
# volitelne parametry omezi mnozinu ve ktere se pohybujeme
# napriklad omezeni na nejvic hodinu v roce XXXX, nejvic mesic vubec, nejvic den v mesici XX, nejvic den v mesici XX a roce XXXX
# musim zabranit pouziti parametru pro mensi casovou jednotku - nesmi byt nejvic mesic v hodine XX nebo???? muzu asi, ale je to trochu jine vyznamove
# nebo to tak aspon pusobi
# s vsemi omezenimi uz jde spise o vylozene where filtrovaci formuli, ale to muze byt ok




def most_played(conn, mode: str, top_num: int, year=None, month=None, day=None, day_of_week=None, day_of_year=None, hour=None):
    where = "WHERE seconds_played >= 10"    
    if year is not None:
        where += " AND year = " + str(year)
    if month is not None:
        where += " AND month = " + str(month)
    if day is not None:
        where += " AND day = " + str(day)
    if day_of_week is not None:
        where += " AND day_of_week = " + str(day_of_week)
    if day_of_year is not None:
        where += " AND day_of_year = " + str(day_of_year)
    if hour is not None:
        where += " AND hour = " + str(hour)

    if mode == "track":
        select = "track, artist, album, COUNT(ts) AS plays"
        group_by = "spotify_track_uri"
        order_by = "COUNT(ts)"
    elif mode == "album":
        select = "album, artist, CAST(ROUND(SUM(seconds_played) / 60.0, 0) AS INTEGER) AS minutes_played"
        group_by = "album, artist"
        order_by = "SUM(seconds_played)"
    elif mode == "artist":
        select = "artist, COUNT(DISTINCT spotify_track_uri) AS distinct_tracks, CAST(ROUND(SUM(seconds_played) / 60.0, 0) AS INTEGER) AS minutes_played"
        group_by = "artist"
        order_by = "SUM(seconds_played)"
    else:
        raise ValueError(f"Wrong mode parameter - enter track/artist/album. You entered {mode}")

    
    df = pd.read_sql(f"""
        SELECT {select}
        FROM music
        {where}
        GROUP BY {group_by}
        ORDER BY {order_by} DESC
        LIMIT {top_num}
        """, conn)
    return df

def most_skipped(conn, mode: str, top_num: int, year=None, month=None, day=None, day_of_week=None, day_of_year=None, hour=None):
    where = "WHERE skipped = true"    
    if year is not None:
        where += " AND year = " + str(year)
    if month is not None:
        where += " AND month = " + str(month)
    if day is not None:
        where += " AND day = " + str(day)
    if day_of_week is not None:
        where += " AND day_of_week = " + str(day_of_week)
    if day_of_year is not None:
        where += " AND day_of_year = " + str(day_of_year)
    if hour is not None:
        where += " AND hour = " + str(hour)

    if mode == "track":
        select = "track, artist, album"
    elif mode == "album":
        select = "album, artist"
    elif mode == "artist":
        select = "artist"
    else:
        raise ValueError(f"Wrong mode parameter - enter track/artist/album. You entered {mode}")

    df = pd.read_sql(f"""
        SELECT {select}, COUNT(ts) AS count
        FROM music
        {where}
        GROUP BY {mode}
        ORDER BY COUNT(ts) DESC
        LIMIT {top_num}
        """, conn)
    return df