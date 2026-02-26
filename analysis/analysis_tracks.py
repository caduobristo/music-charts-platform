# %%

import pandas as pd 

df = pd.read_csv('../data/tracks.csv')
df.head()

# %%

df.info()

# %%
df.isna().sum()

# %%

df.drop(columns=['available_markets', 'external_ids', 
                 'popularity', 'preview_url'], inplace=True)

# %%
import ast

def get_artist_id(value):
    try:
        data = ast.literal_eval(value)
        return data[0]["id"] if data else None
    except (ValueError, SyntaxError, TypeError, KeyError):
        return None
    
df['artist_id'] = df['artists'].apply(get_artist_id)
df.drop(columns=['artists'], inplace=True)
df.head()
# %%

df['disc_number'].unique()
# %%

def extract_spotify_url(external_urls_str):
    try:
        urls_dict = eval(external_urls_str)
        return urls_dict.get('spotify', '')
    except:
        return ''
    
df['url'] = df['external_urls'].apply(extract_spotify_url)
df.drop(columns=['external_urls'], inplace=True)
df.head()
# %%

df['type'].unique()
df.drop(columns=['type'], inplace=True)
df.head()
# %%

df.info()
# %%
