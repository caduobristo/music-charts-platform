# %% 

import pandas as pd

df_artist = pd.read_csv('../data/artists.csv')
df_artist.head()
# %%

import ast

def get_image_url(value):
    try:
        data = ast.literal_eval(value)
        return data[0]["url"] if data else None
    except:
        return None
    
df_artist['image'] = df_artist['images'].apply(get_image_url)
df_artist.drop(columns=['images'], inplace=True)
df_artist.head()

# %%

df_artist['type'].unique()
df_artist.drop(columns=['type'], inplace=True)
df_artist.head()

# %%

df_artist['external_urls'].unique()
df_artist.drop(columns=['external_urls'], inplace=True)
df_artist.head()

# %% 

df_artist.isna().sum()
# %%

df_artist.info()
# %%
