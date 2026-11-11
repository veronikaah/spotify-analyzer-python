import pandas as pd
import glob
import sqlite3
import streamlit as st

def complete_data_preparation():
    df: pd.DataFrame = load_your_data()
    df = clean_data(df)
    conn = get_database(df)
    return conn

def load_your_data() -> pd.DataFrame:
    files = glob.glob("data/Streaming_History_Audio_*.json")
    df = pd.concat([pd.read_json(f) for f in files], ignore_index=True)
    return df

def load_your_data_official() -> pd.DataFrame:
    files = st.file_uploader("Import your Spotify JSON files.", accept_multiple_files=True)
    df = pd.concat([pd.read_json(f) for f in files], ignore_index=True)
    return df

def convert_time(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = df["ts"].dt.strftime("%Y-%m-%d")
    df["time"] = df["ts"].dt.strftime("%H:%M:%S")

    df["day"] = df["ts"].dt.day
    df["month"] = df["ts"].dt.month
    df["year"] = df["ts"].dt.year
    df["day_of_week"] = df["ts"].dt.day_of_week
    df["day_of_year"] = df["ts"].dt.day_of_year

    df["minute"] = df["ts"].dt.minute
    df["hour"] = df["ts"].dt.hour

    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df["ts"] = pd.to_datetime(df["ts"])
    df["ts"] = df["ts"].dt.tz_convert("Europe/Prague")
    df = convert_time(df)

    df["ms_played"] = df["ms_played"] // 1000

    df = df.drop(columns=["platform", "ip_addr", "audiobook_title", "audiobook_uri", "audiobook_chapter_uri", "audiobook_chapter_title", 
                          "offline", "offline_timestamp", "incognito_mode"])

    df = df.rename(columns={
        "ms_played": "seconds_played",
        "master_metadata_track_name": "track",
        "master_metadata_album_artist_name": "artist",
        "master_metadata_album_album_name": "album"
    })

    
    df.drop_duplicates()
    return df

def get_database(df: pd.DataFrame) -> sqlite3.Connection:
    music = df[df["track"].notna()]
    music = music.drop(columns=["episode_name", "episode_show_name", "spotify_episode_uri"])

    podcasts = df[df["episode_name"].notna()]
    podcasts = podcasts.drop(columns=["artist", "track", "album", "shuffle"])

    conn = sqlite3.connect("spotify.db")
    music.to_sql("music", conn, if_exists="replace", index=False)
    podcasts.to_sql("podcasts", conn, if_exists="replace", index=False)
    return conn