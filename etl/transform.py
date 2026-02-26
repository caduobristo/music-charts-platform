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


def transform_albums(df_album):
    print("Transformando albums...")
    
    # Extrair URL do Spotify
    df_album['url'] = df_album['external_urls'].apply(extract_spotify_url)
    df_album = df_album.drop(columns=['external_urls'])
    
    # Extrair URL da imagem
    df_album["image"] = df_album["images"].apply(get_image_url)
    df_album.drop(columns=['images'], inplace=True)
    
    # Extrair ID do artista
    df_album['artist_id'] = df_album['artists'].apply(get_artist_id)
    df_album.drop(columns=['artists'], inplace=True)
    
    # Remover colunas desnecessárias
    columns_to_drop = ['tracks', 'copyrights', 'genres', 'type', 'release_date_precision']
    columns_to_drop = [col for col in columns_to_drop if col in df_album.columns]
    if columns_to_drop:
        df_album.drop(columns=columns_to_drop, inplace=True)
    
    print(f"Albums transformados: {len(df_album)} registros")
    return df_album


def transform_artists(df_artist):
    print("Transformando artistas...")
    
    # Extrair URL da imagem
    df_artist['image'] = df_artist['images'].apply(get_image_url)
    df_artist.drop(columns=['images'], inplace=True)
    
    # Remover colunas desnecessárias
    columns_to_drop = ['type', 'external_urls']
    columns_to_drop = [col for col in columns_to_drop if col in df_artist.columns]
    if columns_to_drop:
        df_artist.drop(columns=columns_to_drop, inplace=True)
    
    print(f"Artistas transformados: {len(df_artist)} registros")
    return df_artist


def transform_tracks(df_tracks):
    print("Transformando tracks...")
    
    # Remover colunas desnecessárias
    columns_to_drop = ['available_markets', 'external_ids', 'popularity', 'preview_url']
    columns_to_drop = [col for col in columns_to_drop if col in df_tracks.columns]
    if columns_to_drop:
        df_tracks.drop(columns=columns_to_drop, inplace=True)
    
    # Extrair ID do artista
    df_tracks['artist_id'] = df_tracks['artists'].apply(get_artist_id)
    df_tracks.drop(columns=['artists'], inplace=True)
    
    # Extrair URL do Spotify
    df_tracks['url'] = df_tracks['external_urls'].apply(extract_spotify_url)
    df_tracks.drop(columns=['external_urls'], inplace=True)
    
    # Remover coluna type
    if 'type' in df_tracks.columns:
        df_tracks.drop(columns=['type'], inplace=True)
    
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


def transform_all_data(data_dir='data', output_dir='data/transformed'):
    print("COMEÇO TRANSFORMAÇÃO DOS DADOS")
    print(f"Diretório de dados: {data_dir}")
    print(f"Diretório de saída: {output_dir}")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ranks_output_dir = Path(output_dir) / 'ranks'
    ranks_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Transformar albums
    if os.path.exists(f"{data_dir}/albums.csv"):
        df_albums = pd.read_csv(f"{data_dir}/albums.csv")
        df_albums = transform_albums(df_albums)
        df_albums.to_csv(f"{output_dir}/albums.csv", index=False)
        print(f"Albums salvos em {output_dir}/albums.csv\n")
    
    # Transformar artistas
    if os.path.exists(f"{data_dir}/artists.csv"):
        df_artists = pd.read_csv(f"{data_dir}/artists.csv")
        df_artists = transform_artists(df_artists)
        df_artists.to_csv(f"{output_dir}/artists.csv", index=False)
        print(f"Artistas salvos em {output_dir}/artists.csv\n")
    
    # Transformar tracks
    if os.path.exists(f"{data_dir}/tracks.csv"):
        df_tracks = pd.read_csv(f"{data_dir}/tracks.csv")
        df_tracks = transform_tracks(df_tracks)
        df_tracks.to_csv(f"{output_dir}/tracks.csv", index=False)
        print(f"Tracks salvos em {output_dir}/tracks.csv\n")
    
    # Audio features não precisa de transformação
    if os.path.exists(f"{data_dir}/audio_features.csv"):
        df_features = pd.read_csv(f"{data_dir}/audio_features.csv")
        df_features.to_csv(f"{output_dir}/audio_features.csv", index=False)
        print(f"Audio features salvos em {output_dir}/audio_features.csv\n")
    
    # Transformar arquivos de ranks
    ranks_dir = Path(data_dir) / 'ranks'
    if ranks_dir.exists():
        for rank_file in ranks_dir.glob('*.csv'):
            chart_name = rank_file.stem.split('_')[0]
            df_ranks = pd.read_csv(rank_file)
            df_ranks = transform_ranks(df_ranks, chart_name)
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