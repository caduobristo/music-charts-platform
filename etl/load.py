import pandas as pd
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv


def get_db_connection():
    """Estabelecer conexão com o banco de dados"""
    config_path = Path(__file__).parent.parent / 'config' / '.env'
    load_dotenv(config_path)
    

    if os.path.exists('/.dockerenv'):
        db_host = 'db'
    else:
        db_host = os.getenv('DB_HOST', 'localhost')
    
    connection = psycopg2.connect(
        host=db_host,
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'music_charts'),
        user=os.getenv('DB_USER', 'music'),
        password=os.getenv('DB_PASSWORD', 'music123')
    )
    return connection


def load_artists(df_artists, cursor):
    """Carregar dados de artistas"""
    print("Carregando artistas...")
    
    for _, row in df_artists.iterrows():
        try:
            cursor.execute("""
                INSERT INTO artists (id, spotify_id, name, href, uri, image)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (spotify_id) DO NOTHING
            """, (
                int(row['id']),
                row['spotify_id'],
                row['name'],
                row.get('href'),
                row.get('uri'),
                row.get('image')
            ))
        except Exception as e:
            print(f"Erro ao carregar artista {row['id']}: {e}")
    
    print(f"Artistas carregados: {len(df_artists)} registros")


def load_albums(df_albums, cursor, connection):
    """Carregar dados de albums"""
    print("Carregando albums...")
    
    loaded_count = 0
    skipped_count = 0
    
    for _, row in df_albums.iterrows():
        try:
            # Pular albums sem artista válido
            if row['artist_id'] == -1:
                skipped_count += 1
                continue
            
            # Converter release_date para DATE se necessário
            release_date = row['release_date'] if pd.notna(row['release_date']) else None
            
            cursor.execute("""
                INSERT INTO albums (id, spotify_id, name, release_date, total_tracks, href, uri, url, image, artist_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (spotify_id) DO NOTHING
            """, (
                int(row['id']),
                row['spotify_id'],
                row['name'],
                release_date,
                int(row['total_tracks']) if pd.notna(row['total_tracks']) else None,
                row.get('href'),
                row.get('uri'),
                row.get('url'),
                row.get('image'),
                int(row['artist_id'])
            ))
            loaded_count += 1
        except psycopg2.IntegrityError as e:
            # Violação de foreign key ou unique constraint
            connection.rollback()
            skipped_count += 1
        except Exception as e:
            print(f"Erro ao carregar album {row['id']}: {e}")
            connection.rollback()
    
    print(f"Albums carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Albums pulados (artista não existe ou duplicado): {skipped_count} registros")


def load_tracks(df_tracks, cursor, connection):
    """Carregar dados de tracks"""
    print("Carregando tracks...")
    
    loaded_count = 0
    skipped_count = 0
    
    for _, row in df_tracks.iterrows():
        try:
            # Pular tracks sem artista válido
            if row['artist_id'] == -1:
                skipped_count += 1
                continue
            
            cursor.execute("""
                INSERT INTO tracks (id, spotify_id, name, duration_ms, explicit, disc_number, track_number, href, uri, url, artist_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (spotify_id) DO NOTHING
            """, (
                int(row['id']),
                row['spotify_id'],
                row['name'],
                int(row['duration_ms']) if pd.notna(row['duration_ms']) else None,
                row['explicit'] if pd.notna(row['explicit']) else False,
                int(row['disc_number']) if pd.notna(row['disc_number']) else None,
                int(row['track_number']) if pd.notna(row['track_number']) else None,
                row.get('href'),
                row.get('uri'),
                row.get('url'),
                int(row['artist_id'])
            ))
            loaded_count += 1
        except psycopg2.IntegrityError as e:
            # Violação de foreign key ou unique constraint
            connection.rollback()
            skipped_count += 1
        except Exception as e:
            print(f"Erro ao carregar track {row['id']}: {e}")
            connection.rollback()
    
    print(f"Tracks carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Tracks pulados (artista não existe ou duplicado): {skipped_count} registros")
    
    print(f"Tracks carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Tracks pulados (artista não existe ou duplicado): {skipped_count} registros")
    
    print(f"Tracks carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Tracks pulados (sem artista válido): {skipped_count} registros")


def load_audio_features(df_features, cursor, connection):
    """Carregar dados de audio features"""
    print("Carregando audio features...")
    
    loaded_count = 0
    skipped_count = 0
    
    for _, row in df_features.iterrows():
        try:
            # Pular audio features sem track válida
            if row['track_id'] == -1:
                skipped_count += 1
                continue
            
            cursor.execute("""
                INSERT INTO audio_features (id, track_id, href, isrc, acousticness, danceability, energy, 
                                           instrumentalness, key, liveness, loudness, mode, speechiness, tempo, valence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                int(row['id']),
                int(row['track_id']),
                row.get('href'),
                row.get('isrc'),
                float(row['acousticness']) if pd.notna(row['acousticness']) else None,
                float(row['danceability']) if pd.notna(row['danceability']) else None,
                float(row['energy']) if pd.notna(row['energy']) else None,
                float(row['instrumentalness']) if pd.notna(row['instrumentalness']) else None,
                int(row['key']) if pd.notna(row['key']) else None,
                float(row['liveness']) if pd.notna(row['liveness']) else None,
                float(row['loudness']) if pd.notna(row['loudness']) else None,
                int(row['mode']) if pd.notna(row['mode']) else None,
                float(row['speechiness']) if pd.notna(row['speechiness']) else None,
                float(row['tempo']) if pd.notna(row['tempo']) else None,
                float(row['valence']) if pd.notna(row['valence']) else None
            ))
            loaded_count += 1
        except psycopg2.IntegrityError as e:
            # Violação de foreign key - track não existe
            connection.rollback()
            skipped_count += 1
        except Exception as e:
            print(f"Erro ao carregar audio feature {row['id']}: {e}")
            connection.rollback()
    
    print(f"Audio features carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Audio features pulados (track não existe): {skipped_count} registros")


def load_rank_artists(df_rank, cursor, connection):
    """Carregar dados de ranking de artistas"""
    print("Carregando rankings de artistas...")
    
    loaded_count = 0
    skipped_count = 0
    
    for _, row in df_rank.iterrows():
        try:
            # Pular rankings sem artista válido
            if row['artist_id'] == -1:
                skipped_count += 1
                continue
            
            cursor.execute("""
                INSERT INTO rank_artists (id, artist_id, position, lw, weeks, peak)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                int(row['id']),
                int(row['artist_id']),
                int(row['position']) if pd.notna(row['position']) else None,
                int(row['lw']) if pd.notna(row['lw']) else None,
                int(row['weeks']) if pd.notna(row['weeks']) else None,
                int(row['peak']) if pd.notna(row['peak']) else None
            ))
            loaded_count += 1
        except psycopg2.IntegrityError as e:
            # Violação de foreign key - artista não existe
            connection.rollback()
            skipped_count += 1
        except Exception as e:
            print(f"Erro ao carregar ranking de artista {row['id']}: {e}")
            connection.rollback()
    
    print(f"Rankings de artistas carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Rankings de artistas pulados (artista não existe): {skipped_count} registros")


def load_rank_albums(df_rank, cursor, connection):
    """Carregar dados de ranking de albums"""
    print("Carregando rankings de albums...")
    
    loaded_count = 0
    skipped_count = 0
    
    for _, row in df_rank.iterrows():
        try:
            # Pular rankings sem album válido
            if row['album_id'] == -1:
                skipped_count += 1
                continue
            
            cursor.execute("""
                INSERT INTO rank_albums (id, album_id, position, lw, weeks, peak)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                int(row['id']),
                int(row['album_id']),
                int(row['position']) if pd.notna(row['position']) else None,
                int(row['lw']) if pd.notna(row['lw']) else None,
                int(row['weeks']) if pd.notna(row['weeks']) else None,
                int(row['peak']) if pd.notna(row['peak']) else None
            ))
            loaded_count += 1
        except psycopg2.IntegrityError as e:
            # Violação de foreign key - album não existe
            connection.rollback()
            skipped_count += 1
        except Exception as e:
            print(f"Erro ao carregar ranking de album {row['id']}: {e}")
            connection.rollback()
    
    print(f"Rankings de albums carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Rankings de albums pulados (album não existe): {skipped_count} registros")


def load_rank_tracks(df_rank, chart_name, cursor, connection):
    """Carregar dados de ranking de tracks"""
    print(f"Carregando rankings de tracks ({chart_name})...")
    
    loaded_count = 0
    skipped_count = 0
    
    for _, row in df_rank.iterrows():
        try:
            # Pular rankings sem track válida
            if row['track_id'] == -1:
                skipped_count += 1
                continue
            
            cursor.execute("""
                INSERT INTO rank_tracks (id, track_id, chart_name, position, lw, weeks, peak)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                int(row['id']),
                int(row['track_id']),
                chart_name,
                int(row['position']) if pd.notna(row['position']) else None,
                int(row['lw']) if pd.notna(row['lw']) else None,
                int(row['weeks']) if pd.notna(row['weeks']) else None,
                int(row['peak']) if pd.notna(row['peak']) else None
            ))
            loaded_count += 1
        except psycopg2.IntegrityError as e:
            # Violação de foreign key - track não existe
            connection.rollback()
            skipped_count += 1
        except Exception as e:
            print(f"Erro ao carregar ranking de track {row['id']}: {e}")
            connection.rollback()
    
    print(f"Rankings de tracks ({chart_name}) carregados: {loaded_count} registros")
    if skipped_count > 0:
        print(f"Rankings de tracks ({chart_name}) pulados (track não existe): {skipped_count} registros")


def load_all_data(data_dir='data/transformed'):
    """Carregar todos os dados no banco de dados"""
    print("INICIANDO CARREGAMENTO DOS DADOS")
    print(f"Diretório de dados: {data_dir}\n")
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 1. Carregar artistas primeira (tabela base)
        if os.path.exists(f"{data_dir}/artists.csv"):
            df_artists = pd.read_csv(f"{data_dir}/artists.csv")
            load_artists(df_artists, cursor)
            connection.commit()
            print()
        
        # 2. Carregar albums
        if os.path.exists(f"{data_dir}/albums.csv"):
            df_albums = pd.read_csv(f"{data_dir}/albums.csv")
            load_albums(df_albums, cursor, connection)
            connection.commit()
            print()
        
        # 3. Carregar tracks
        if os.path.exists(f"{data_dir}/tracks.csv"):
            df_tracks = pd.read_csv(f"{data_dir}/tracks.csv")
            load_tracks(df_tracks, cursor, connection)
            connection.commit()
            print()
        
        # 4. Carregar audio features
        if os.path.exists(f"{data_dir}/audio_features.csv"):
            df_features = pd.read_csv(f"{data_dir}/audio_features.csv")
            load_audio_features(df_features, cursor, connection)
            connection.commit()
            print()
        
        # 5. Carregar rankings
        ranks_dir = Path(data_dir) / 'ranks'
        if ranks_dir.exists():
            for rank_file in ranks_dir.glob('*.csv'):
                chart_name = rank_file.stem.split('_')[0]
                df_rank = pd.read_csv(rank_file)
                
                if chart_name == 'artist100':
                    load_rank_artists(df_rank, cursor, connection)
                elif chart_name == 'billboard200':
                    load_rank_albums(df_rank, cursor, connection)
                elif chart_name in ['hot100', 'global200']:
                    load_rank_tracks(df_rank, chart_name, cursor, connection)
                
                connection.commit()
                print()
        
        cursor.close()
        connection.close()
        
        print("CARREGAMENTO DOS DADOS CONCLUÍDO COM SUCESSO!")
    
    except Exception as e:
        print(f"Erro durante o carregamento: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        raise


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'data' / 'transformed'
    
    load_all_data(data_dir=str(data_dir))
