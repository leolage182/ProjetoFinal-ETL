import pandas as pd
from sqlalchemy import create_engine, text
import os
import unicodedata
import time

# Função para normalizar texto (remover acentos e caracteres especiais)
def normalize_text(text):
    """Remove acentos e caracteres especiais de strings"""
    if pd.isna(text):
        return text
    text = str(text).strip()
    # Normalizar caracteres Unicode (remover acentos)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text

# Configuração do banco
PG_USER = os.getenv("PG_USER", "user")
PG_PASS = os.getenv("PG_PASS", "secret")
PG_DB   = os.getenv("PG_DB", "dw")
PG_HOST = os.getenv("PG_HOST", "pg-dados")  # hostname do container Postgres na rede docker
PG_PORT = os.getenv("PG_PORT", "5432")

# string de conexão com configuração explícita de codificação
conn_str = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}?client_encoding=utf8"

print("Conexão:", conn_str)

time.sleep(3)


engine = create_engine(conn_str, echo=False)


import unicodedata
# Busca dados limpos em vez de dados brutos
csv_path = None
if os.path.exists("/app/data/filmes_clean_500.csv"):
    csv_path = "/app/data/filmes_clean_500.csv"
elif os.path.exists("data/filmes_clean_500.csv"):
    csv_path = "data/filmes_clean_500.csv"
elif os.path.exists("../etl-data-cleaning/filmes_clean_500.csv"):
    csv_path = "../etl-data-cleaning/filmes_clean_500.csv"
else:
    raise FileNotFoundError("Arquivo de dados limpos não encontrado. Execute primeiro o etl-data-cleaning.")

print("Lendo CSV:", csv_path)
df = pd.read_csv(csv_path)

# Os dados já estão limpos, apenas garantir que as colunas estão corretas
print("Colunas disponíveis:", df.columns.tolist())

# Garantir que temos as colunas esperadas
expected_cols = ["titulo", "ano_lancamento", "genero", "nota_imdb"]
missing_cols = [col for col in expected_cols if col not in df.columns]
if missing_cols:
    raise ValueError(f"Colunas faltando nos dados limpos: {missing_cols}")

# Selecionar apenas as colunas necessárias
df = df[expected_cols]

# Aplicar normalização de texto nos títulos
df["titulo"] = df["titulo"].apply(normalize_text)

print("Preview após transformação:")
print(df.head())

# 3) LOAD: gravar no Postgres - Data Warehouse (tabelas)
with engine.begin() as conn:
    # Criar tabela de filmes
    create_filmes_sql = """
    CREATE TABLE IF NOT EXISTS filmes (
        id SERIAL PRIMARY KEY,
        titulo TEXT,
        ano_lancamento INTEGER,
        genero TEXT,
        nota_imdb REAL
    );
    """
    conn.execute(text(create_filmes_sql))
    
    # Criar tabela de usuários (estrutura simples como filmes)
    create_usuarios_sql = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        email TEXT,
        genero TEXT,
        pais TEXT
    );
    """
    conn.execute(text(create_usuarios_sql))
    
    # Verificar se a tabela foi criada corretamente
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'usuarios' ORDER BY ordinal_position"))
    columns = result.fetchall()
    print(f"📋 Estrutura da tabela usuarios: {columns}")
    
    # Criar tabela de avaliações
    create_avaliacoes_sql = """
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES usuarios(id),
        filme_titulo VARCHAR(500) NOT NULL,
        nota DECIMAL(3,1) CHECK (nota >= 0 AND nota <= 10),
        comentario TEXT,
        data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn.execute(text(create_avaliacoes_sql))

    # Limpar dados existentes
    conn.execute(text("TRUNCATE TABLE avaliacoes CASCADE;"))
    conn.execute(text("TRUNCATE TABLE usuarios CASCADE;"))
    conn.execute(text("TRUNCATE TABLE filmes;"))


df.to_sql("filmes", engine, if_exists="append", index=False)

print("✅ Dados carregados na tabela 'filmes' (Data Warehouse).")

# === CARREGAR DADOS DE USUÁRIOS ===
print("\n=== CARREGANDO DADOS DE USUÁRIOS ===")

# Buscar arquivo de usuários limpos
usuarios_csv_path = None
if os.path.exists("/app/data/usuarios_clean.csv"):
    usuarios_csv_path = "/app/data/usuarios_clean.csv"
elif os.path.exists("data/usuarios_clean.csv"):
    usuarios_csv_path = "data/usuarios_clean.csv"
elif os.path.exists("../usuarios_clean.csv"):
    usuarios_csv_path = "../usuarios_clean.csv"
else:
    print("⚠️ Arquivo de usuários limpos não encontrado. Pulando carregamento de usuários.")

if usuarios_csv_path:
    print("Lendo CSV de usuários:", usuarios_csv_path)
    try:
        df_usuarios = pd.read_csv(usuarios_csv_path)
        print(f"📊 Dados carregados: {len(df_usuarios)} linhas")
        print(f"📊 Colunas: {list(df_usuarios.columns)}")
        print(f"📊 Primeiras 3 linhas dos dados:")
        print(df_usuarios.head(3).to_string())
        
        # Verificar se há dados nulos
        null_counts = df_usuarios.isnull().sum()
        if null_counts.sum() > 0:
            print(f"⚠️ Valores nulos encontrados: {null_counts.to_dict()}")
        
        # Remover coluna 'id' se existir (será auto-incrementada pelo PostgreSQL)
        if 'id' in df_usuarios.columns:
            df_usuarios = df_usuarios.drop('id', axis=1)
            print("🔧 Coluna 'id' removida (será auto-incrementada)")
        
        # Usar o mesmo método que funciona para filmes
        print("Carregando usuários usando df.to_sql()...")
        try:
            df_usuarios.to_sql("usuarios", engine, if_exists="append", index=False)
            print("✅ Dados de usuários carregados com sucesso!")
            
            # Verificar quantos usuários foram inseridos
            with engine.begin() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM usuarios"))
                count = result.scalar()
                print(f"📊 Total de usuários inseridos: {count}")
        except Exception as e:
            print(f"❌ Erro ao carregar usuários: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Erro ao carregar usuários: {e}")
        import traceback
        traceback.print_exc()

# === CARREGAR DADOS DE AVALIAÇÕES ===
print("\n=== CARREGANDO DADOS DE AVALIAÇÕES ===")

# Buscar arquivo de avaliações limpos
avaliacoes_csv_path = None
if os.path.exists("/app/data/avaliacoes_clean.csv"):
    avaliacoes_csv_path = "/app/data/avaliacoes_clean.csv"
elif os.path.exists("data/avaliacoes_clean.csv"):
    avaliacoes_csv_path = "data/avaliacoes_clean.csv"
elif os.path.exists("../avaliacoes_clean.csv"):
    avaliacoes_csv_path = "../avaliacoes_clean.csv"
else:
    print("⚠️ Arquivo de avaliações limpos não encontrado. Pulando carregamento de avaliações.")

if avaliacoes_csv_path:
    print("Lendo CSV de avaliações:", avaliacoes_csv_path)
    df_avaliacoes = pd.read_csv(avaliacoes_csv_path)
    
    # Verificar se temos usuários suficientes
    with engine.begin() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM usuarios"))
        total_usuarios = result.scalar()
        
        if total_usuarios == 0:
            print("⚠️ Nenhum usuário encontrado. Pulando carregamento de avaliações.")
        else:
            # Ajustar user_id para não exceder o número de usuários disponíveis
            max_user_id = df_avaliacoes['user_id'].max()
            if max_user_id > total_usuarios:
                print(f"⚠️ Ajustando user_id: máximo no CSV ({max_user_id}) > usuários disponíveis ({total_usuarios})")
                df_avaliacoes['user_id'] = ((df_avaliacoes['user_id'] - 1) % total_usuarios) + 1
            
            # Aplicar normalização nos títulos dos filmes para garantir correspondência
            df_avaliacoes['filme_titulo'] = df_avaliacoes['filme_titulo'].apply(normalize_text)
            
            # Carregar dados na tabela avaliacoes
            # Garantir que não temos a coluna 'id' que é auto-incrementada
            if 'id' in df_avaliacoes.columns:
                df_avaliacoes = df_avaliacoes.drop('id', axis=1)
            
            try:
                # Tentar inserção em lote primeiro
                df_avaliacoes.to_sql("avaliacoes", engine, if_exists="append", index=False, method='multi')
                print(f"✅ {len(df_avaliacoes)} avaliações carregadas na tabela 'avaliacoes'")
            except Exception as e:
                print(f"⚠️ Erro na inserção em lote: {e}")
                print("Tentando inserção linha por linha...")
                
                # Inserção linha por linha como fallback
                success_count = 0
                for index, row in df_avaliacoes.iterrows():
                    try:
                        row_df = pd.DataFrame([row])
                        row_df.to_sql("avaliacoes", engine, if_exists="append", index=False)
                        success_count += 1
                    except Exception as row_error:
                        print(f"❌ Erro na linha {index}: {row_error}")
                        print(f"Dados da linha: {row.to_dict()}")
                
                print(f"✅ {success_count}/{len(df_avaliacoes)} avaliações inseridas com sucesso")

# 4) Criar SQL Views para os Data Marts solicitados
print("\nCriando SQL Views para Data Marts...")

with engine.begin() as conn:
    # View 1: Top 10 filmes mais bem avaliados por gênero
    conn.execute(text("""
        CREATE OR REPLACE VIEW vw_top_filmes_por_genero AS
        SELECT 
            f.genero,
            f.titulo,
            f.ano_lancamento,
            ROUND(AVG(a.nota), 2) as nota_media,
            COUNT(a.id) as total_avaliacoes,
            ROW_NUMBER() OVER (PARTITION BY f.genero ORDER BY AVG(a.nota) DESC, COUNT(a.id) DESC) as ranking
        FROM filmes f
        INNER JOIN avaliacoes a ON f.titulo = a.filme_titulo
        GROUP BY f.genero, f.titulo, f.ano_lancamento
        HAVING COUNT(a.id) >= 1
        ORDER BY f.genero, ranking;
    """))
    
    # View 2: Top 5 usuários com mais avaliações
    conn.execute(text("""
        CREATE OR REPLACE VIEW vw_top_usuarios_avaliacoes AS
        SELECT 
            u.id,
            u.nome,
            u.email,
            COUNT(a.id) as total_avaliacoes,
            ROUND(AVG(a.nota), 2) as nota_media_dada,
            MIN(a.data_avaliacao) as primeira_avaliacao,
            MAX(a.data_avaliacao) as ultima_avaliacao
        FROM usuarios u
        INNER JOIN avaliacoes a ON u.id = a.user_id
        GROUP BY u.id, u.nome, u.email
        ORDER BY total_avaliacoes DESC, nota_media_dada DESC;
    """))
    
    # View 3: Top 10 filmes com piores avaliações por gênero
    conn.execute(text("""
        CREATE OR REPLACE VIEW vw_piores_filmes_por_genero AS
        SELECT 
            f.genero,
            f.titulo,
            f.ano_lancamento,
            ROUND(AVG(a.nota), 2) as nota_media,
            COUNT(a.id) as total_avaliacoes,
            ROW_NUMBER() OVER (PARTITION BY f.genero ORDER BY AVG(a.nota) ASC, COUNT(a.id) DESC) as ranking
        FROM filmes f
        INNER JOIN avaliacoes a ON f.titulo = a.filme_titulo
        GROUP BY f.genero, f.titulo, f.ano_lancamento
        HAVING COUNT(a.id) >= 1
        ORDER BY f.genero, ranking;
    """))
    
    # View 4: Número de avaliações por país
    conn.execute(text("""
        CREATE OR REPLACE VIEW vw_avaliacoes_por_pais AS
        SELECT 
            u.pais,
            COUNT(a.id) as total_avaliacoes,
            COUNT(DISTINCT u.id) as total_usuarios,
            ROUND(AVG(a.nota), 2) as nota_media_pais,
            MIN(a.data_avaliacao) as primeira_avaliacao,
            MAX(a.data_avaliacao) as ultima_avaliacao
        FROM usuarios u
        INNER JOIN avaliacoes a ON u.id = a.user_id
        GROUP BY u.pais
        ORDER BY total_avaliacoes DESC, nota_media_pais DESC;
    """))
    
    # View 5: Nota média por gênero dos usuários
    conn.execute(text("""
        CREATE OR REPLACE VIEW vw_nota_media_por_genero AS
        SELECT 
            f.genero,
            COUNT(a.id) as total_avaliacoes,
            ROUND(AVG(a.nota), 2) as nota_media_genero,
            COUNT(DISTINCT a.user_id) as usuarios_avaliaram,
            COUNT(DISTINCT f.titulo) as filmes_avaliados,
            MIN(a.nota) as nota_minima,
            MAX(a.nota) as nota_maxima
        FROM filmes f
        INNER JOIN avaliacoes a ON f.titulo = a.filme_titulo
        GROUP BY f.genero
        ORDER BY nota_media_genero DESC, total_avaliacoes DESC;
    """))

print("✅ SQL Views criadas:")
print("  - vw_top_filmes_por_genero (Top 10 filmes mais bem avaliados por gênero)")
print("  - vw_top_usuarios_avaliacoes (Top 5 usuários com mais avaliações)")
print("  - vw_piores_filmes_por_genero (Top 10 filmes com piores avaliações por gênero)")
print("  - vw_avaliacoes_por_pais (Número de avaliações por país)")
print("  - vw_nota_media_por_genero (Nota média por gênero dos usuários)")

# === RELATÓRIO FINAL ===
print("\n=== RELATÓRIO FINAL ===")
with engine.connect() as conn:
    total_filmes = conn.execute(text("SELECT COUNT(*) FROM filmes;")).scalar()
    total_usuarios = conn.execute(text("SELECT COUNT(*) FROM usuarios;")).scalar()
    total_avaliacoes = conn.execute(text("SELECT COUNT(*) FROM avaliacoes;")).scalar()
    
    print(f"Registros no Warehouse:")
    print(f"  - Filmes: {total_filmes}")
    print(f"  - Usuários: {total_usuarios}")
    print(f"  - Avaliações: {total_avaliacoes}")

print("Fim do ETL.")
