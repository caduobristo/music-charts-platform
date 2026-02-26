import os
import base64
import requests

class SpotifyClient:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.token = self._get_token()

    def _get_token(self):
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        res = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"}
        )
        return res.json()["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def get_track_data(self, track, artist):
        # Busca informações básicas da música usando o nome da faixa e do artista

        q = f"track:{track} artist:{artist}"
        url = "https://api.spotify.com/v1/search"
        params = {"q": q, "type": "track", "limit": 1}

        res = requests.get(url, headers=self._headers(), params=params)
        if res.status_code != 200:
            print(f"Erro ao buscar track: {res.status_code} - {res.text}")
            return None
        res = res.json()
        if not res["tracks"]["items"]:
            # Se a busca com nome e artista não retornar resultados, tenta buscar apenas pelo nome da faixa
            params = {"q": f"track:{track}", "type": "track", "limit": 1}
            res = requests.get(url, headers=self._headers(), params=params)
            if res.status_code != 200:
                print(f"Erro ao buscar track (fallback): {res.status_code} - {res.text}")
                return None
            res = res.json()
            if not res["tracks"]["items"]:
                return None

        t = res["tracks"]["items"][0]

        return t
    
    def get_reccobeats_track(self, spotify_id):
        # Coleta o ID da música no ReccoBeats usando o ID do Spotify para buscar as features de áudio

        url = "https://api.reccobeats.com/v1/track?ids=" + spotify_id
        headers = {
            "Accept": "application/json"
        }

        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            print("Erro ao buscar tracks ReccoBeats:", res.status_code)
            return None

        tracks = res.json()
        content = tracks.get("content") if isinstance(tracks, dict) else None

        if content:
            return content[0]["id"]

        print("Track não encontrada na ReccoBeats")
        return None
    
    def get_audio_features(self, spotify_id):
        # Busca as features de áudio da música usando o ID do ReccoBeats correspondente ao ID do Spotify

        recco_id = self.get_reccobeats_track(spotify_id)
        if not recco_id:
            return None
        url = f"https://api.reccobeats.com/v1/track/{recco_id}/audio-features"
        headers = {"Accept": "application/json"}

        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            print("Erro audio features:", res.status_code)
            return None

        return res.json()

    def get_artist_data(self, artist):
        # Busca as informações do artista usando o nome do artista

        url = "https://api.spotify.com/v1/search"
        params = {"q": artist, "type": "artist", "limit": 1}

        res = requests.get(url, headers=self._headers(), params=params).json()
        if not res["artists"]["items"]:
            return None

        return res["artists"]["items"][0]

    def get_artist_by_id(self, artist_id):
        # Busca as informações do artista usando o ID do Spotify

        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        res = requests.get(url, headers=self._headers())

        if res.status_code != 200:
            print("Erro ao buscar artista:", res.status_code)
            return None

        return res.json()

    def get_album_data(self, album, artist):
        # Busca as informações do álbum usando o nome do álbum e o nome do artista

        q = f"album:{album} artist:{artist}"

        url = "https://api.spotify.com/v1/search"
        params = {"q": q, "type": "album", "limit": 1}

        res = requests.get(url, headers=self._headers(), params=params)
        if res.status_code != 200:
            print(f"Erro ao buscar album: {res.status_code} - {res.text}")
            return None
        res = res.json()
        if not res["albums"]["items"]:
            # Fallback: tenta buscar apenas pelo nome do album
            params = {"q": f"album:{album}", "type": "album", "limit": 1}
            res = requests.get(url, headers=self._headers(), params=params)
            if res.status_code != 200:
                print(f"Erro ao buscar album (fallback): {res.status_code} - {res.text}")
                return None
            res = res.json()
            if not res["albums"]["items"]:
                return None

        return res["albums"]["items"][0]

    def get_album_by_id(self, album_id):
        # Busca as informações do album usando o ID do Spotify

        url = f"https://api.spotify.com/v1/albums/{album_id}"
        res = requests.get(url, headers=self._headers())

        if res.status_code != 200:
            print("Erro ao buscar album:", res.status_code)
            return None

        return res.json()
    

def main():
    # Teste de coleta de dados do Spotify para uma música específica
    
    client = SpotifyClient()

    track_name = "Blinding Lights"
    artist_name = "The Weeknd"

    print("=== SEARCH TRACK ===")
    track = client.get_track_data(track_name, artist_name)
    print(track)

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