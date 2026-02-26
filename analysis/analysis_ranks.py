# %%

import pandas as pd

df_artist100 = pd.read_csv('../data/ranks/artist100_2026-02-26.csv')
df_billboard200= pd.read_csv('../data/ranks/billboard200_2026-02-26.csv')
df_global200 = pd.read_csv('../data/ranks/global200_2026-02-26.csv')
df_hot100 = pd.read_csv('../data/ranks/hot100_2026-02-26.csv')

#df_artist100.info()
#df_billboard200.info()
#df_global200.info()
df_hot100.info()

# %%

df_artist100.isna().sum()

# %%
df_billboard200.isna().sum()
# %%
df_global200.isna().sum()
# %%
df_hot100.isna().sum()
# %%
df_artist100['lw'].unique()
# %%
df_artist100["lw"] = (
    df_artist100["lw"]
      .replace("-", 0)
      .astype(int)                  
)
df_artist100['lw'].info()
# %%
df_artist100['lw'].unique()
# %%
