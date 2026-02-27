# Music Charts Platform

Plataforma de coleta, transformação e armazenamento de dados de rankings musicais da Billboard, enriquecidos com metadados do Spotify. O pipeline é executado através do Apache Airflow no Docker.

## Requisitos

- Docker
- Credenciais de API do Spotify
- Portas livres: 8080 (Airflow), 5432 (Postgres), 5433 (Postgres do Airflow)

Opcional (para rodar sem Docker):
- Python 3.11+

## Quickstart

```bash
# Clonar e configurar
git clone <repository>
cd music-charts-platform
cp config/.env.example config/.env

# Editar config/.env com credenciais Spotify
# SPOTIFY_CLIENT_ID=seu_id
# SPOTIFY_CLIENT_SECRET=seu_secret

# Iniciar
docker-compose up -d

# Acessar Airflow
# http://localhost:8080 (admin / admin)
```

## Pipeline ETL

O pipeline executa três etapas sequencialmente:

### 1. Ingestão

Coleta dados da Billboard e enriquece com informações do Spotify.

**Dados coletados:**
- Rankings: Hot 100, Global 200, Billboard 200, Artist 100
- Artistas, Albums, Tracks, Características musicais

**Como funciona:**

O scraper da Billboard usa BeautifulSoup para extrair os dados de cada chart (tabelas HTML). Os dados brutos contêm apenas nomes e posições. Depois, para cada item do ranking, faz uma busca na Spotify API por artista + nome da música ou album.

Com o `track_id` do Spotify, consulta a API ReccoBeats para resolver o ID interno e então buscar as audio features no endpoint `/v1/track/{recco_id}/audio-features`.

**Ferramentas usadas:**
- **BeautifulSoup**: Parse do HTML da Billboard
- **Requests**: Requisições HTTP para Billboard e Spotify
- **Spotify Web API**: Busca de dados (search endpoint)
  - Retorna: IDs do Spotify, URIs, metadados, imagens
  - Rate limit: Respeita limites da API com retry automático
- **Pandas**: Estruturação dos dados em DataFrames

**Saída:**
CSVs com os dados brutos em `data/`:
- `artists.csv`: ~225 artistas únicos
- `albums.csv`: ~326 albums únicos  
- `tracks.csv`: ~247 tracks únicas
- `audio_features.csv`: Características musicais (danceability, energy, etc)
- `ranks/`: Arquivos separados por chart (hot100, global200, billboard200, artist100)

**Arquivo:** `ingestion/run_ingestion.py`

---

### 2. Transformação

Normaliza os dados em um modelo relacional (primeira forma normal).

**O que acontece:**

O transform recebe os CSVs brutos e faz a limpeza:
- **IDs sequenciais**: Cria coluna `id` com valores 1, 2, 3... para cada tabela
- **Mapeamento de relacionamentos**: Converte `spotify_id` em `artist_id` através de dicionários de busca
- **Limpeza de colunas**: Remove campos desnecessários (tipos, URLs de imagens em lista, etc)
- **Conversão de tipos**: Strings para inteiros, dates, floats
- **Tratamento de valores faltantes**: NaN vira -1 para foreign keys inválidas

**Ferramentas usadas:**
- **Pandas**: Manipulação de DataFrames
  - `apply()`: Extração de dados aninhados (JSON em string)
  - `set_index().to_dict()`: Mapeamento de relações
  - `pd.to_numeric()` e `pd.to_datetime()`: Conversão de tipos
  - `fillna()`: Preenchimento de valores nulos
- **AST (Abstract Syntax Tree)**: Parse de estruturas Python em string (lists, dicts)

**Transformações principais:**

1. **Artists**: Renomeia `id` -> `spotify_id`, cria novo `id` sequencial
2. **Albums**: Mapeia artista através do `spotify_id` -> `artist_id`, converte `release_date` para DATE
3. **Tracks**: Idem albums, mantém duração e número da faixa
4. **Audio Features**: Remove registros de tracks que não foram mapeadas (-1)
5. **Rankings**: Cria tabelas diferentes por tipo de chart (artist100, billboard200, hot100, global200)

**Saída:**
CSVs normalizados em `data/transformed/`:
- IDs são únicos e sequenciais
- Foreign keys apontam para IDs válidos existentes na tabela pai

**Arquivo:** `etl/transform.py`

---

### 3. Carregamento

Insere os dados transformados no PostgreSQL com validação de integridade.

**O que acontece:**

Para cada tabela, lê o CSV transformado e faz INSERT no banco. Trata erros de forma granular:
- **Validação de Foreign Keys**: Pula registros cujo `artist_id`, `album_id` ou `track_id` é -1
- **Violações de Constraint**: Captura IntegrityError do psycopg2, faz rollback, conta como skip
- **Conexão com Docker**: Detecta se está rodando em container Docker e ajusta host (`db` vs `localhost`)

**Ferramentas usadas:**
- **psycopg2**: Driver PostgreSQL para Python
  - `cursor.execute()`: Executa queries paramétrizadas
  - `connection.rollback()`: Desfaz transaction em caso de erro
  - `ON CONFLICT`: Ignora duplicatas (Upsert)
- **Context Manager**: Garante fechamento de conexões
- **Tratamento de Exceções**: Capturada exceção específica `psycopg2.IntegrityError`

**Fluxo de carga:**

1. Artists primeiro (tabela independente)
2. Depois Albums e Tracks (dependem de Artists)
3. Audio Features (depende de Tracks)
4. Rankings (depende das acima)

Cada tabela é carregada com commits intermediários (não tudo em uma transação).

**Relatório de execução:**
```
Artistas carregados: 225 registros
Albums carregados: 324 registros
Albums pulados (artista não existe ou duplicado): 2 registros
Tracks carregados: 247 registros
Audio features carregados: 113 registros
Audio features pulados (track não existe): 1 registros
...
```

**Arquivo:** `etl/load.py`

---

## Executar o Pipeline

### Usando Airflow (Recomendado)

1. Acesse http://localhost:8080
2. Faça login (admin / admin)
3. Localize a DAG `music_charts_etl`
4. Clique em "Trigger DAG"

O pipeline executará automaticamente todas as três etapas.

### Executar manualmente

```bash
# Dentro do container
docker exec -it music_app bash

# Pipeline completo
python ingestion/run_ingestion.py
python etl/transform.py
python etl/load.py
```

## Banco de Dados

### Tabelas

- **artists**: Artistas (tabela base)
- **albums**: Albums com referência a artista
- **tracks**: Músicas com referência a artista
- **audio_features**: Características musicais
- **rank_artists**: Posições de artistas
- **rank_albums**: Posições de albums
- **rank_tracks**: Posições de tracks

### Conectar ao banco

```bash
docker exec -it music_db psql -U music -d music_charts
```

