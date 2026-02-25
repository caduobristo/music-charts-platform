# %%

import pandas as pd

df_features = pd.read_csv('../data/audio_features.csv')
df_features.info()
# %%

df_features.isna().sum()