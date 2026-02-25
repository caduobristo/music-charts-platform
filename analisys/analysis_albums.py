# %%

import pandas as pd
df_album = pd.read_csv("../data/albums.csv")

# %%

df_album.head()
df_album.isna().sum()

# %%

df_album.info()

# %%

df_album['external_urls'].head()
# %%

def extract_spotify_url(external_urls_str):
    try:
        urls_dict = eval(external_urls_str)
        return urls_dict.get('spotify', '')
    except:
        return ''
    
df_album['url'] = df_album['external_urls'].apply(extract_spotify_url)
df_album = df_album.drop(columns=['external_urls'])
df_album.head()

# %% 

df_album['images'][0]

# %%

import ast

def get_album_url(value):
    try:
        data = ast.literal_eval(value)
        return data[0]["url"] if data else None
    except (ValueError, SyntaxError, TypeError):
        return None
    
df_album["image"] = df_album["images"].apply(get_album_url)
df_album.drop(columns=['images'], inplace=True)
df_album.head()

# %%

df_album['release_date_precision'].unique()

# %%

df_album['type'].unique()

# %%

df_album['artists'][0]
# %%

def get_artist_id(value):
    try:
        data = ast.literal_eval(value)
        return data[0]["id"] if data else None
    except (ValueError, SyntaxError, TypeError, KeyError):
        return None
    
df_album['artist_id'] = df_album['artists'].apply(get_artist_id)
df_album.drop(columns=['artists'], inplace=True)
df_album.head()

# %%

df_album['tracks'][200]
# %%

df_album['copyrights'][200]
# %%

df_album['genres'].unique()
# %%

df_album.drop(columns=['tracks', 'copyrights', 'genres', 'type',
                        'release_date_precision'], inplace=True)
df_album.head()

# %%
df_album.info()
# %%
datas_convertidas = pd.to_datetime(
    df_album["release_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

linhas_invalidas = df_album[datas_convertidas.isna()]
print(linhas_invalidas[["release_date"]])

# %%
df_album["release_date"] = pd.to_datetime(
    df_album["release_date"],
    format="mixed",
    errors="coerce"
)
df_album.info()
# %%
