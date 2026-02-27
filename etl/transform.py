import pandas as pd
import ast
import os
from pathlib import Path


def extract_spotify_url(external_urls_str):
    """Extrai o URL único do item"""
    try:
        urls_dict = eval(external_urls_str)
        return urls_dict.get('spotify', '')
    except:
        return ''


def get_image_url(value):
    """Extrai o URL único para imagem"""
    try:
        data = ast.literal_eval(value)
        return data[0]["url"] if data else None
    except (ValueError, SyntaxError, TypeError):
        return None


def get_artist_id(value):
    """Extrai o ID do artista"""
    try:
        data = ast.literal_eval(value)
        return data[0]["id"] if data else None
    except (ValueError, SyntaxError, TypeError, KeyError):
        return None


def transform_albums(df_album, df_artists):
    print("Transformando albums...")
    
    # Extrair URL do Spotify
    df_album['url'] = df_album['external_urls'].apply(extract_spotify_url)
    df_album = df_album.drop(columns=['external_urls'])
    
    # Extrair URL da imagem
    df_album["image"] = df_album["images"].apply(get_image_url)
    df_album.drop(columns=['images'], inplace=True)
    
    # Extrair spotify_id do artista
    df_album['artist_spotify_id'] = df_album['artists'].apply(get_artist_id)
    df_album.drop(columns=['artists'], inplace=True)
    
    # Criar mapeamento de spotify_id para id da tabela artists
    artist_mapping = df_artists.set_index('spotify_id')['id'].to_dict()
    
    # Substituir artist_spotify_id por artist_id (chave estrangeira)
    df_album['artist_id'] = df_album['artist_spotify_id'].map(artist_mapping)
    df_album.drop(columns=['artist_spotify_id'], inplace=True)
    
    # Converter artist_id para inteiro (substituir NaN por -1)
    df_album['artist_id'] = df_album['artist_id'].fillna(-1).astype(int)
    
    # Converter release_date para formato de data adequado
    if 'release_date' in df_album.columns:
        df_album['release_date'] = pd.to_datetime(
            df_album['release_date'],
            format="mixed",
            errors="coerce"
        )
    
    # Remover colunas desnecessárias
    columns_to_drop = ['tracks', 'copyrights', 'genres', 'type', 'release_date_precision', 
                       'query_title', 'query_artist']
    columns_to_drop = [col for col in columns_to_drop if col in df_album.columns]
    if columns_to_drop:
        df_album.drop(columns=columns_to_drop, inplace=True)
    
    # Renomear coluna 'id' para 'spotify_id' e criar nova coluna 'id' sequencial
    df_album.rename(columns={'id': 'spotify_id'}, inplace=True)
    df_album.insert(0, 'id', range(1, len(df_album) + 1))
    
    print(f"Albums transformados: {len(df_album)} registros")
    return df_album


def transform_artists(df_artist):
    print("Transformando artistas...")
    
    # Extrair URL da imagem
    df_artist['image'] = df_artist['images'].apply(get_image_url)
    df_artist.drop(columns=['images'], inplace=True)
    
    # Remover colunas desnecessárias ANTES de renomear
    columns_to_drop = ['type', 'external_urls', 'query_artist']
    columns_to_drop = [col for col in columns_to_drop if col in df_artist.columns]
    if columns_to_drop:
        df_artist.drop(columns=columns_to_drop, inplace=True)
    
    # Renomear coluna 'id' para 'spotify_id' e criar nova coluna 'id' sequencial
    df_artist.rename(columns={'id': 'spotify_id'}, inplace=True)
    df_artist.insert(0, 'id', range(1, len(df_artist) + 1))
    
    print(f"Artistas transformados: {len(df_artist)} registros")
    return df_artist


def transform_tracks(df_tracks, df_artists):
    print("Transformando tracks...")
    
    # Remover colunas desnecessárias
    columns_to_drop = ['available_markets', 'external_ids', 'popularity', 'preview_url']
    columns_to_drop = [col for col in columns_to_drop if col in df_tracks.columns]
    if columns_to_drop:
        df_tracks.drop(columns=columns_to_drop, inplace=True)
    
    # Extrair spotify_id do artista
    df_tracks['artist_spotify_id'] = df_tracks['artists'].apply(get_artist_id)
    df_tracks.drop(columns=['artists'], inplace=True)
    
    # Criar mapeamento de spotify_id para id da tabela artists
    artist_mapping = df_artists.set_index('spotify_id')['id'].to_dict()
    
    # Substituir artist_spotify_id por artist_id (chave estrangeira)
    df_tracks['artist_id'] = df_tracks['artist_spotify_id'].map(artist_mapping)
    df_tracks.drop(columns=['artist_spotify_id'], inplace=True)
    
    # Converter artist_id para inteiro (substituir NaN por -1)
    df_tracks['artist_id'] = df_tracks['artist_id'].fillna(-1).astype(int)
    
    # Extrair URL do Spotify
    df_tracks['url'] = df_tracks['external_urls'].apply(extract_spotify_url)
    df_tracks.drop(columns=['external_urls'], inplace=True)
    
    # Remover colunas desnecessárias
    columns_to_drop = ['type', 'query_title', 'query_artist', 'is_local', 'is_playable']
    columns_to_drop = [col for col in columns_to_drop if col in df_tracks.columns]
    if columns_to_drop:
        df_tracks.drop(columns=columns_to_drop, inplace=True)
    
    # Renomear coluna 'id' para 'spotify_id' e criar nova coluna 'id' sequencial
    df_tracks.rename(columns={'id': 'spotify_id'}, inplace=True)
    df_tracks.insert(0, 'id', range(1, len(df_tracks) + 1))
    
    print(f"Tracks transformados: {len(df_tracks)} registros")
    return df_tracks


def transform_ranks(df_ranks, chart_name):
    print(f"Transformando {chart_name}...")
    
    # Transformar coluna 'lw' se existir
    if 'lw' in df_ranks.columns:
        df_ranks["lw"] = (
            df_ranks["lw"]
              .replace("-", 0)
              .astype(int)
        )
    
    print(f"Ranks de {chart_name} transformados: {len(df_ranks)} registros")
    return df_ranks


def transform_audio_features(df_features, df_tracks):
    print("Transformando audio features...")
    
    # Criar mapeamento de spotify_id para id da tabela tracks
    track_mapping = df_tracks.set_index('spotify_id')['id'].to_dict()
    
    # Substituir spotify_id por track_id (chave estrangeira)
    df_features['track_id'] = df_features['spotify_id'].map(track_mapping)
    df_features.drop(columns=['spotify_id'], inplace=True)
    
    # Converter track_id para inteiro (substituir NaN por -1)
    df_features['track_id'] = df_features['track_id'].fillna(-1).astype(int)
    
    # Adicionar id sequencial
    df_features.insert(0, 'id', range(1, len(df_features) + 1))
    
    print(f"Audio features transformados: {len(df_features)} registros")
    return df_features


def transform_ranks_relational(df_ranks, chart_name, df_artists=None, df_albums=None, df_tracks=None):
    print(f"Transformando ranks de {chart_name} (relacional)...")
    
    # Transformar coluna 'lw' se existir
    if 'lw' in df_ranks.columns:
        # Substituir "-" por 0 e converter para numérico (valores inválidos viram NaN)
        df_ranks["lw"] = pd.to_numeric(
            df_ranks["lw"].replace("-", 0),
            errors='coerce'
        ).fillna(0).astype(int)
    
    # Determinar o tipo de chart e criar a relação apropriada
    if chart_name == 'artist100' and df_artists is not None:
        # Para artist100, spotify_id refere-se a artistas
        artist_mapping = df_artists.set_index('spotify_id')['id'].to_dict()
        df_ranks['artist_id'] = df_ranks['spotify_id'].map(artist_mapping).fillna(-1).astype(int)
        df_ranks.drop(columns=['spotify_id', 'artist', 'title'], inplace=True, errors='ignore')
    
    elif chart_name == 'billboard200' and df_albums is not None:
        # Para billboard200, spotify_id refere-se a albums
        album_mapping = df_albums.set_index('spotify_id')['id'].to_dict()
        df_ranks['album_id'] = df_ranks['spotify_id'].map(album_mapping).fillna(-1).astype(int)
        df_ranks.drop(columns=['spotify_id', 'artist', 'title'], inplace=True, errors='ignore')
    
    elif chart_name in ['hot100', 'global200'] and df_tracks is not None:
        # Para hot100 e global200, spotify_id refere-se a tracks
        track_mapping = df_tracks.set_index('spotify_id')['id'].to_dict()
        df_ranks['track_id'] = df_ranks['spotify_id'].map(track_mapping).fillna(-1).astype(int)
        df_ranks.drop(columns=['spotify_id', 'artist', 'title'], inplace=True, errors='ignore')
    
    # Adicionar id sequencial
    df_ranks.insert(0, 'id', range(1, len(df_ranks) + 1))
    
    print(f"Ranks de {chart_name} transformados: {len(df_ranks)} registros")
    return df_ranks


def transform_all_data(data_dir='data', output_dir='data/transformed'):
    print("COMEÇO TRANSFORMAÇÃO DOS DADOS")
    print(f"Diretório de dados: {data_dir}")
    print(f"Diretório de saída: {output_dir}")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ranks_output_dir = Path(output_dir) / 'ranks'
    ranks_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Transformar artistas primeiro (tabela base)
    df_artists = None
    if os.path.exists(f"{data_dir}/artists.csv"):
        df_artists = pd.read_csv(f"{data_dir}/artists.csv")
        df_artists = transform_artists(df_artists)
        df_artists.to_csv(f"{output_dir}/artists.csv", index=False)
        print(f"Artistas salvos em {output_dir}/artists.csv\n")
    
    # 2. Transformar albums (referencia artists)
    df_albums = None
    if os.path.exists(f"{data_dir}/albums.csv") and df_artists is not None:
        df_albums = pd.read_csv(f"{data_dir}/albums.csv")
        df_albums = transform_albums(df_albums, df_artists)
        df_albums.to_csv(f"{output_dir}/albums.csv", index=False)
        print(f"Albums salvos em {output_dir}/albums.csv\n")
    
    # 3. Transformar tracks (referencia artists)
    df_tracks = None
    if os.path.exists(f"{data_dir}/tracks.csv") and df_artists is not None:
        df_tracks = pd.read_csv(f"{data_dir}/tracks.csv")
        df_tracks = transform_tracks(df_tracks, df_artists)
        df_tracks.to_csv(f"{output_dir}/tracks.csv", index=False)
        print(f"Tracks salvos em {output_dir}/tracks.csv\n")
    
    # 4. Transformar audio features (referencia tracks)
    if os.path.exists(f"{data_dir}/audio_features.csv") and df_tracks is not None:
        df_features = pd.read_csv(f"{data_dir}/audio_features.csv")
        df_features = transform_audio_features(df_features, df_tracks)
        df_features.to_csv(f"{output_dir}/audio_features.csv", index=False)
        print(f"Audio features salvos em {output_dir}/audio_features.csv\n")
    
    # 5. Transformar arquivos de ranks (referencia artists, albums ou tracks conforme o chart)
    ranks_dir = Path(data_dir) / 'ranks'
    if ranks_dir.exists():
        for rank_file in ranks_dir.glob('*.csv'):
            chart_name = rank_file.stem.split('_')[0]
            df_ranks = pd.read_csv(rank_file)
            df_ranks = transform_ranks_relational(
                df_ranks, 
                chart_name, 
                df_artists=df_artists, 
                df_albums=df_albums, 
                df_tracks=df_tracks
            )
            output_path = ranks_output_dir / rank_file.name
            df_ranks.to_csv(output_path, index=False)
            print(f"Ranks de {chart_name} salvos em {output_path}\n")
    
    print("TRANSFORMAÇÃO DOS DADOS CONCLUÍDA COM SUCESSO!")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'data'
    output_dir = project_root / 'data' / 'transformed'
    
    transform_all_data(data_dir=str(data_dir), output_dir=str(output_dir))