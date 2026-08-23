from billboard_scraper import *
from spotify_enricher import *
from datetime import date
from pathlib import Path
import pandas as pd
import json
import csv
import os
import re
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REQUEST_PACE_DELAY = 0.15  # 150ms entre buscas para sustentabilidade de taxa da API

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
    artist = str(artist).lower().strip()

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


def save_rank_csv(chart_name, rows, base_dir=DATA_DIR):
    ranks_dir = base_dir / "ranks"
    ranks_dir.mkdir(parents=True, exist_ok=True)
    path = ranks_dir / f"{chart_name}.csv"

    if not rows:
        return

    # Ordem de colunas padrão para manter consistência
    default_fields = ["position", "title", "artist", "lw", "peak", "weeks", "spotify_id"]
    all_fields = list(default_fields)
    for row in rows:
        for k in row.keys():
            if k not in all_fields:
                all_fields.append(k)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def load_existing_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def process_track(item, spotify):
    title = item["title"]
    artist = normalize_artist(item["artist"])

    print(f"Track: {title} - {artist}")

    track = spotify.get_track_data(title, artist)
    if not track:
        print("Não achou no Spotify")
        return None, None, None
    
    artist_id = track.get("artists", [{}])[0].get("id")
    album_id = track.get("album", {}).get("id")

    return track, artist_id, album_id


def process_album(item, spotify):
    album = item["title"]
    artist = normalize_artist(item["artist"])

    print(f"Album: {album} - {artist}")

    data = spotify.get_album_data(album, artist)
    if not data:
        return None, None
    
    artist_id = data.get('artists', [{}])[0].get('id')
    
    return data, artist_id


def process_artist(item, spotify):
    artist = normalize_artist(item["title"])

    print(f"Artist: {artist}")

    data = spotify.get_artist_data(artist)
    if not data:
        return None
    
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


def run_ingestion():
    spotify = SpotifyClient()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    tracks_csv_path = DATA_DIR / "tracks.csv"
    artists_csv_path = DATA_DIR / "artists.csv"
    albums_csv_path = DATA_DIR / "albums.csv"
    features_csv_path = DATA_DIR / "audio_features.csv"

    df_track = load_existing_csv(tracks_csv_path)
    df_artist = load_existing_csv(artists_csv_path)
    df_album = load_existing_csv(albums_csv_path)
    df_features = load_existing_csv(features_csv_path)

    artist_ids = []
    album_ids = []

    today = date.today().isoformat()

    for chart_name, cfg in RANKS.items():
        print(f"\n=== Coletando ranking: {chart_name} ===")

        ranking = fetch_page(cfg["url"])

        print(f"{len(ranking)} linhas coletadas.")

        for item in ranking:
            try:
                time.sleep(REQUEST_PACE_DELAY)

                if cfg["type"] == "track":
                    title = item["title"]
                    artist = normalize_artist(item["artist"])

                    # Verifica se a música já foi procurada
                    if already_seen(df_track, query_title=title, query_artist=artist):
                        print("Track ja buscada, pulando.")
                        matches = df_track[(df_track['query_title'] == title) & (df_track['query_artist'] == artist)]
                        if not matches.empty and 'id' in matches.columns and pd.notna(matches['id'].iloc[0]):
                            item["spotify_id"] = matches['id'].iloc[0]
                        continue

                    df_item, artist_id, album_id = process_track(item, spotify)
                    if artist_id and artist_id not in artist_ids:
                        artist_ids.append(artist_id)
                    if album_id and album_id not in album_ids:
                        album_ids.append(album_id)

                    if df_item is not None:
                        df_item["query_title"] = title
                        df_item["query_artist"] = artist
                        df_track = pd.concat([df_track, pd.DataFrame([df_item])], ignore_index=True)
                        
                        item["spotify_id"] = df_item.get("id")

                        spotify_id = df_item.get("id")
                        if spotify_id and not already_seen(df_features, spotify_id=spotify_id):
                            features = spotify.get_audio_features(spotify_id)
                            if features is not None:
                                features["spotify_id"] = spotify_id
                                df_features = pd.concat([df_features, pd.DataFrame([features])], ignore_index=True)

                elif cfg["type"] == "album":
                    album = item["title"]
                    artist = normalize_artist(item["artist"])

                    # Verifica se o album já foi procurado
                    if already_seen(df_album, query_title=album, query_artist=artist):
                        print("Album ja buscado, pulando.")
                        matches = df_album[(df_album['query_title'] == album) & (df_album['query_artist'] == artist)]
                        if not matches.empty and 'id' in matches.columns and pd.notna(matches['id'].iloc[0]):
                            item["spotify_id"] = matches['id'].iloc[0]
                        continue

                    df_item, artist_id = process_album(item, spotify)
                    if artist_id and artist_id not in artist_ids:
                        artist_ids.append(artist_id)

                    if df_item is not None:
                        df_item["query_title"] = album
                        df_item["query_artist"] = artist
                        df_album = pd.concat([df_album, pd.DataFrame([df_item])], ignore_index=True)
                        
                        item["spotify_id"] = df_item.get("id")

                elif cfg["type"] == "artist":
                    artist = normalize_artist(item["title"])
                    # Verifica se o artista já foi procurado
                    if already_seen(df_artist, query_artist=artist):
                        print("Artista ja buscado, pulando.")
                        matches = df_artist[df_artist['query_artist'] == artist]
                        if not matches.empty and 'id' in matches.columns and pd.notna(matches['id'].iloc[0]):
                            item["spotify_id"] = matches['id'].iloc[0]
                        continue

                    df_item = process_artist(item, spotify)
                    if df_item is not None:
                        df_item["query_artist"] = artist
                        df_artist = pd.concat([df_artist, pd.DataFrame([df_item])], ignore_index=True)
                        
                        item["spotify_id"] = df_item.get("id")

            except Exception as e:
                print("Erro no item:", e)

        # Salva o ranking com a data do dia
        save_rank_csv(chart_name + "_" + today, ranking)
        print(f"{len(ranking)} linhas salvas no CSV.")

    # Busca em lote de artistas pendentes (até 50 por chamada)
    pending_artists = [a_id for a_id in sorted(set(artist_ids)) if not already_seen(df_artist, id=a_id)]
    if pending_artists:
        print(f"\nBuscando {len(pending_artists)} artistas em lote via Spotify...")
        artists_data = spotify.get_artists_by_ids(pending_artists)
        artists_rows = []
        for a in artists_data:
            if a:
                a["query_artist"] = a.get("name")
                artists_rows.append(a)
        if artists_rows:
            df_artist = pd.concat([df_artist, pd.DataFrame(artists_rows)], ignore_index=True)
            print(f"{len(artists_rows)} artistas adicionados em lote.")

    # Busca em lote de álbuns pendentes (até 20 por chamada)
    pending_albums = [alb_id for alb_id in sorted(set(album_ids)) if not already_seen(df_album, id=alb_id)]
    if pending_albums:
        print(f"\nBuscando {len(pending_albums)} álbuns em lote via Spotify...")
        albums_data = spotify.get_albums_by_ids(pending_albums)
        albums_rows = []
        for alb in albums_data:
            if alb:
                alb["query_title"] = alb.get("name")
                if alb.get("artists") and len(alb["artists"]) > 0:
                    alb["query_artist"] = alb["artists"][0].get("name")
                albums_rows.append(alb)
        if albums_rows:
            df_album = pd.concat([df_album, pd.DataFrame(albums_rows)], ignore_index=True)
            print(f"{len(albums_rows)} álbuns adicionados em lote.")

    df_track.to_csv(tracks_csv_path, index=False)
    df_album.to_csv(albums_csv_path, index=False)
    df_artist.to_csv(artists_csv_path, index=False)
    df_features.to_csv(features_csv_path, index=False)
    print("\nIngestão concluída com sucesso!")


if __name__ == "__main__":
    run_ingestion()
