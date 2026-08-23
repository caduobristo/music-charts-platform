import os
import time
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

config_path = Path(__file__).resolve().parent.parent / 'config' / '.env'
load_dotenv(config_path)

REQUEST_TIMEOUT = 15


class SpotifyClient:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET devem estar configurados no .env")
        
        self.token = self._get_token()

    def _get_token(self):
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        try:
            res = requests.post(
                "https://accounts.spotify.com/api/token",
                headers={"Authorization": f"Basic {auth}"},
                data={"grant_type": "client_credentials"},
                timeout=REQUEST_TIMEOUT
            )
        except Exception as e:
            raise ConnectionError(f"Falha de conexao ao autenticar com Spotify: {e}")
        
        if res.status_code != 200:
            print(f"Erro na autenticacao Spotify: {res.status_code}")
            print(f"Resposta: {res.text}")
            raise Exception(f"Falha na autenticacao com Spotify: {res.status_code} - {res.text}")
        
        token_data = res.json()
        if "access_token" not in token_data:
            print(f"Resposta da API nao contem access_token: {token_data}")
            raise KeyError(f"access_token nao encontrado na resposta: {token_data}")
        
        return token_data["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _spotify_get(self, url, params=None, max_retries=3):
        """Executa GET na API do Spotify com timeout, auto-renovação de token (401) e tratamento de Rate Limit (429)."""
        for attempt in range(max_retries):
            try:
                res = requests.get(url, headers=self._headers(), params=params, timeout=REQUEST_TIMEOUT)
                if res.status_code == 401:
                    print("Token Spotify expirado. Renovando token...")
                    self.token = self._get_token()
                    continue
                elif res.status_code == 429:
                    retry_after = int(res.headers.get("Retry-After", 5))
                    wait_time = retry_after + 1
                    print(f"Rate limit atingido (HTTP 429). Aguardando {wait_time}s (tentativa {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                elif res.status_code >= 400:
                    print(f"Erro na API Spotify ({res.status_code} - {url}): {res.text}")
                    return None
                return res
            except Exception as e:
                print(f"Erro na requisicao Spotify ({url}): {e}")
                time.sleep(1)
        return None
    
    def get_track_data(self, track, artist):
        # Busca informações básicas da música usando o nome da faixa e do artista
        q = f"track:{track} artist:{artist}"
        url = "https://api.spotify.com/v1/search"
        params = {"q": q, "type": "track", "limit": 1}

        res = self._spotify_get(url, params=params)
        if res is None or res.status_code != 200:
            return None

        res_json = res.json()
        items = res_json.get("tracks", {}).get("items", [])
        if not items:
            # Fallback: busca apenas pelo nome da faixa
            params = {"q": f"track:{track}", "type": "track", "limit": 1}
            res = self._spotify_get(url, params=params)
            if res is None or res.status_code != 200:
                return None
            res_json = res.json()
            items = res_json.get("tracks", {}).get("items", [])
            if not items:
                return None

        return items[0]
    
    def get_reccobeats_track(self, spotify_id):
        # Coleta o ID da música no ReccoBeats usando o ID do Spotify para buscar as features de áudio
        url = "https://api.reccobeats.com/v1/track?ids=" + spotify_id
        headers = {"Accept": "application/json"}

        try:
            res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            print(f"Erro de conexao ReccoBeats: {e}")
            return None

        if res.status_code != 200:
            print(f"Erro ao buscar tracks ReccoBeats: {res.status_code}")
            return None

        tracks = res.json()
        content = tracks.get("content") if isinstance(tracks, dict) else None

        if content and len(content) > 0 and "id" in content[0]:
            return content[0]["id"]

        return None
    
    def get_audio_features(self, spotify_id):
        # Busca as features de áudio da música usando o ID do ReccoBeats correspondente ao ID do Spotify
        recco_id = self.get_reccobeats_track(spotify_id)
        if not recco_id:
            return None

        url = f"https://api.reccobeats.com/v1/track/{recco_id}/audio-features"
        headers = {"Accept": "application/json"}

        try:
            res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            print(f"Erro ao conectar ReccoBeats audio-features: {e}")
            return None

        if res.status_code != 200:
            print(f"Erro audio features ReccoBeats: {res.status_code}")
            return None

        return res.json()

    def get_artist_data(self, artist):
        # Busca as informações do artista usando o nome do artista
        url = "https://api.spotify.com/v1/search"
        params = {"q": artist, "type": "artist", "limit": 1}

        res = self._spotify_get(url, params=params)
        if res is None or res.status_code != 200:
            return None

        res_json = res.json()
        items = res_json.get("artists", {}).get("items", [])
        if not items:
            return None

        return items[0]

    def get_artist_by_id(self, artist_id):
        # Busca as informações do artista usando o ID do Spotify
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        res = self._spotify_get(url)

        if res is None or res.status_code != 200:
            return None

        return res.json()

    def get_artists_by_ids(self, artist_ids, pace_delay=0.15):
        """Busca informações de múltiplos artistas com tratamento de rate limit e pacing."""
        if not artist_ids:
            return []

        all_artists = []
        for a_id in artist_ids:
            artist = self.get_artist_by_id(a_id)
            if artist:
                all_artists.append(artist)
            if pace_delay > 0:
                time.sleep(pace_delay)
        return all_artists

    def get_album_data(self, album, artist):
        # Busca as informações do álbum usando o nome do álbum e o nome do artista
        q = f"album:{album} artist:{artist}"
        url = "https://api.spotify.com/v1/search"
        params = {"q": q, "type": "album", "limit": 1}

        res = self._spotify_get(url, params=params)
        if res is None or res.status_code != 200:
            return None

        res_json = res.json()
        items = res_json.get("albums", {}).get("items", [])
        if not items:
            # Fallback: tenta buscar apenas pelo nome do album
            params = {"q": f"album:{album}", "type": "album", "limit": 1}
            res = self._spotify_get(url, params=params)
            if res is None or res.status_code != 200:
                return None
            res_json = res.json()
            items = res_json.get("albums", {}).get("items", [])
            if not items:
                return None

        return items[0]

    def get_album_by_id(self, album_id):
        # Busca as informações do album usando o ID do Spotify
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        res = self._spotify_get(url)

        if res is None or res.status_code != 200:
            return None

        return res.json()

    def get_albums_by_ids(self, album_ids, pace_delay=0.15):
        """Busca informações de múltiplos álbuns com tratamento de rate limit e pacing."""
        if not album_ids:
            return []

        all_albums = []
        for alb_id in album_ids:
            album = self.get_album_by_id(alb_id)
            if album:
                all_albums.append(album)
            if pace_delay > 0:
                time.sleep(pace_delay)
        return all_albums


def main():
    client = SpotifyClient()

    track_name = "Blinding Lights"
    artist_name = "The Weeknd"

    print("=== SEARCH TRACK ===")
    track = client.get_track_data(track_name, artist_name)
    print(track)

    if track:
        track_id = track["id"]

        print("\n=== AUDIO FEATURES ===")
        features = client.get_audio_features(track_id)
        print(features)

        print("\n=== ARTIST ===")
        artist = client.get_artist_data(artist_name)
        print(artist)

        print("\n=== ALBUM ===")
        album = client.get_album_data(track["album"]["name"], artist_name)
        print(album)


if __name__ == "__main__":
    main()
