from billboard_scraper import *
from spotify_enricher import *
from datetime import date
import pandas as pd
import json
import csv
import os
import re

RANKS = {
    "hot100": {
        "url": "https://www.billboard.com/charts/hot-100/",
        "type": "track"
    },
    "global200": {
        "url": "https://www.billboard.com/charts/billboard-global-200/",
        "type": "track"
    },
    "billboard200": {
        "url": "https://www.billboard.com/charts/billboard-200/",
        "type": "album"
    },
    "artist100": {
        "url": "https://www.billboard.com/charts/artist-100/",
        "type": "artist"
    }
}

def normalize_artist(artist):
    # Normaliza o nome do artista (API do Spotify tem problemas com feats)
    artist = artist.lower().strip()

    patterns = [
        r"\s*\(.*?feat.*?\)",
        r"\s*\(.*?with.*?\)",
        r"\s*feat\.?",
        r"\s*featuring.*",
        r"\s*with.*",
    ]

    for p in patterns:
        artist = re.sub(p, "", artist)

    artist = re.sub(r"([a-z])x([a-z])", r"\1 x \2", artist)
    artist = re.sub(r"([a-z])vs\.?([a-z])", r"\1 vs \2", artist)
    artist = re.sub(r"&", " & ", artist)
    artist = re.sub(r"presents", " presents ", artist)

    # Usa apenas o artista principal quando ha varios separadores
    separators = r"\s+(?:x|vs\.?|and|&|presents|feat\.?|featuring|with)\s+"
    parts = re.split(separators, artist)
    primary = parts[0] if parts else artist

    return re.sub(r"\s+", " ", primary).strip().title()

def save_rank_csv(chart_name, rows):
    path = f"data/ranks/{chart_name}.csv"
    os.makedirs("data/ranks", exist_ok=True)

    write_header = not os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())

        if write_header:
            writer.writeheader()

        writer.writerows(rows)

def load_existing_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0)
    return pd.DataFrame()

def process_track(item, spotify):
    title = item["title"]
    artist = normalize_artist(item["artist"])

    print(f"Track: {title} - {artist}")

    track = spotify.get_track_data(title, artist)
    if not track:
        print("Não achou no Spotify")
        return None, None, None
    
    artist_id = track["artists"][0]["id"]
    album_id = track["album"]["id"]

    return track, artist_id, album_id

def process_album(item, spotify):
    album = item["title"]
    artist = normalize_artist(item["artist"])

    print(f"Album: {album} - {artist}")

    data = spotify.get_album_data(album, artist)
    if not data:
        return None, None
    
    artist_id = data['artists'][0]['id']
    
    return data, artist_id

def process_artist(item, spotify):
    artist = normalize_artist(item["artist"])

    print(f"Artist: {artist}")

    data = spotify.get_artist_data(artist)
    if not data:
        return
    
    return data

def already_seen(df, **filters):
    if df.empty:
        return False
    for col in filters.keys():
        if col not in df.columns:
            return False
    mask = pd.Series(True, index=df.index)
    for col, value in filters.items():
        mask &= (df[col] == value)
    return mask.any()

def run_pipeline():
    spotify = SpotifyClient()

    df_track = load_existing_csv("data/tracks.csv")
    df_artist = load_existing_csv("data/artists.csv")
    df_album = load_existing_csv("data/albums.csv")
    df_features = load_existing_csv("data/audio_features.csv")

    artist_ids = []
    album_ids = []

    today = date.today().isoformat()

    for chart_name, cfg in RANKS.items():
        print(f"\n=== Coletando ranking: {chart_name} ===")

        ranking = fetch_page(cfg["url"])

        save_rank_csv(chart_name + "_" + today, ranking)

        print(f"{len(ranking)} linhas salvas no CSV.")

        for item in ranking:
            try:
                if cfg["type"] == "track":
                    title = item["title"]
                    artist = normalize_artist(item["artist"])

                    # Verifica se a música já foi procurada
                    if already_seen(df_track, query_title=title, query_artist=artist):
                        print("Track ja buscada, pulando.")
                        continue

                    df_item, artist_id, album_id = process_track(item, spotify)
                    if artist_id and artist_id not in artist_ids:
                        artist_ids.append(artist_id)
                    if album_id and album_id not in album_ids:
                        album_ids.append(album_id)

                    if df_item is not None:
                        # Colunas adicionadas para controle de duplicidade
                        df_item["query_title"] = title
                        df_item["query_artist"] = artist
                        df_track = pd.concat([df_track, pd.DataFrame([df_item])])

                        # Coletas as features de áudio usando o ID do Spotify da música
                        spotify_id = df_item.get("id")
                        if spotify_id and not already_seen(df_features, spotify_id=spotify_id):
                            features = spotify.get_audio_features(spotify_id)
                            if features is not None:
                                features["spotify_id"] = spotify_id
                                df_features = pd.concat([df_features, pd.DataFrame([features])])

                elif cfg["type"] == "album":
                    album = item["title"]
                    artist = normalize_artist(item["artist"])

                    # Verifica se o album já foi procurada
                    if already_seen(df_album, query_title=album, query_artist=artist):
                        print("Album ja buscado, pulando.")
                        continue

                    df_item, artist_id = process_album(item, spotify)
                    if artist_id and artist_id not in artist_ids:
                        artist_ids.append(artist_id)

                    if df_item is not None:
                        # Colunas adicionadas para controle de duplicidade
                        df_item["query_title"] = album
                        df_item["query_artist"] = artist
                        df_album = pd.concat([df_album, pd.DataFrame([df_item])])

                elif cfg["type"] == "artist":
                    artist = normalize_artist(item["artist"])
                    # Verifica se o artista já foi procurado
                    if already_seen(df_artist, query_artist=artist):
                        print("Artista ja buscado, pulando.")
                        continue

                    df_item = process_artist(item, spotify)
                    if df_item is not None:
                        # Colunas adicionadas para controle de duplicidade
                        df_item["query_artist"] = artist
                        df_artist = pd.concat([df_artist, pd.DataFrame([df_item])])

            except Exception as e:
                print("Erro:", e)

    for artist_id in sorted(set(artist_ids)):
        # Processa os artistas usando o ID do Spotify, para artistas fora do ranking de artistas (ex: artistas de álbuns e faixas)
        if already_seen(df_artist, id=artist_id):
            continue

        artist_data = spotify.get_artist_by_id(artist_id)
        if artist_data is not None:
            artist_data["query_artist"] = artist_data.get("name")
            df_artist = pd.concat([df_artist, pd.DataFrame([artist_data])])

    for album_id in sorted(set(album_ids)):
        # Processa os álbuns usando o ID do Spotify, para álbuns fora do ranking de álbuns (ex: álbuns de faixas)
        if already_seen(df_album, id=album_id):
            continue

        album_data = spotify.get_album_by_id(album_id)
        if album_data is not None:
            album_data["query_title"] = album_data.get("name")
            if album_data.get("artists"):
                album_data["query_artist"] = album_data["artists"][0].get("name")
            df_album = pd.concat([df_album, pd.DataFrame([album_data])])

    df_track.to_csv(f'data/tracks.csv')
    df_album.to_csv(f'data/albums.csv')
    df_artist.to_csv(f'data/artists.csv')
    df_features.to_csv(f'data/audio_features.csv')

if __name__ == "__main__":
    run_pipeline()