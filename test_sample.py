"""
Script para teste rápido do fluxo de enriquecimento.
Processa apenas uma pequena amostra (ex: top 3 do Hot 100) para validar:
1. Autenticação Spotify Web API
2. Scraper da Billboard
3. Enriquecimento de Faixas (Spotify API)
4. Enriquecimento de Audio Features (ReccoBeats API)
5. Enriquecimento de Artistas e Álbuns com Pacing (150ms)
"""
import sys
from pathlib import Path

# Ajusta path para importar módulos da pasta ingestion
sys.path.append(str(Path(__file__).resolve().parent / "ingestion"))

from billboard_scraper import fetch_page, URL_HOT100
from spotify_enricher import SpotifyClient
from run_ingestion import process_track, normalize_artist
import pandas as pd


def run_quick_test():
    print("==================================================")
    print("   TESTE RÁPIDO DE METODOLOGIA (AMOSTRA REDUZIDA)  ")
    print("==================================================\n")

    # 1. Teste de Autenticação Spotify
    print("[1/5] Testando conexão e token do Spotify...")
    try:
        spotify = SpotifyClient()
        print("  -> Spotify autenticado com sucesso!\n")
    except Exception as e:
        print(f"  -> Falha ao autenticar no Spotify: {e}")
        print("  -> Verifique se config/.env possui SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET válidos.")
        return

    # 2. Teste do Scraper da Billboard (Hot 100)
    print("[2/5] Testando Billboard Scraper (Hot 100)...")
    ranking = fetch_page(URL_HOT100)
    sample = ranking[:3]  # Pega apenas os 3 primeiros
    print(f"  -> Sucesso! Total extraído: {len(ranking)} itens. Usando amostra de {len(sample)} itens:")
    for item in sample:
        print(f"     #{item['position']} - {item['title']} por {item['artist']}")
    print()

    # 3. Teste de Enriquecimento de Faixas no Spotify
    print("[3/5] Testando Busca de Faixas no Spotify...")
    artist_ids = []
    album_ids = []
    tracks_info = []

    for item in sample:
        track, artist_id, album_id = process_track(item, spotify)
        if track:
            spotify_id = track.get("id")
            print(f"  -> [Spotify OK] Faixa: '{track.get('name')}' | ID: {spotify_id}")
            if artist_id:
                artist_ids.append(artist_id)
            if album_id:
                album_ids.append(album_id)
            tracks_info.append({"title": item["title"], "spotify_id": spotify_id})
        else:
            print(f"  -> [Spotify] Não encontrada: {item['title']}")
    print()

    # 4. Teste Dedicado da API ReccoBeats (Audio Features)
    print("[4/5] Testando Enriquecimento via API ReccoBeats (Audio Features)...")
    for t in tracks_info:
        sp_id = t["spotify_id"]
        print(f"  -> Consultando ReccoBeats para '{t['title']}' (Spotify ID: {sp_id})...")
        recco_id = spotify.get_reccobeats_track(sp_id)
        if recco_id:
            print(f"     ReccoBeats ID resolvido: {recco_id}")
            features = spotify.get_audio_features(sp_id)
            if features:
                print(f"     [Features OK] Danceability: {features.get('danceability')}, Energy: {features.get('energy')}, Tempo: {features.get('tempo')} BPM, Loudness: {features.get('loudness')} dB, Valence: {features.get('valence')}")
            else:
                print("     [Aviso] Features não retornadas para este ID.")
        else:
            print(f"     [Aviso] Faixa não indexada no catálogo da ReccoBeats.")
    print()

    # 5. Teste de Enriquecimento de Artistas e Álbuns (Pacing 150ms)
    print("[5/5] Testando Enriquecimento de Artistas e Álbuns (Pacing 150ms & Retry 429)...")
    if artist_ids:
        print(f"  -> Buscando {len(artist_ids)} artista(s) no Spotify...")
        artists = spotify.get_artists_by_ids(artist_ids, pace_delay=0.15)
        for a in artists:
            print(f"     [Artista OK] {a.get('name')} | Popularidade: {a.get('popularity')} | Seguidores: {a.get('followers', {}).get('total')}")

    if album_ids:
        print(f"  -> Buscando {len(album_ids)} álbum(ns) no Spotify...")
        albums = spotify.get_albums_by_ids(album_ids, pace_delay=0.15)
        for alb in albums:
            print(f"     [Álbum OK] {alb.get('name')} | Lançamento: {alb.get('release_date')} | Total Faixas: {alb.get('total_tracks')}")

    print("\n==================================================")
    print("   TODOS OS TESTES FORAM CONCLUÍDOS COM SUCESSO!  ")
    print("==================================================")


if __name__ == "__main__":
    run_quick_test()

