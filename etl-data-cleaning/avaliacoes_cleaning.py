import pandas as pd
import unicodedata

# === Ler CSV bruto ===
try:
    # Ler do arquivo montado da raiz do projeto
    df = pd.read_csv("/app/input/avaliacoes_raw.csv", on_bad_lines='skip', engine='python')
except FileNotFoundError:
    try:
        # Fallback para arquivo local
        df = pd.read_csv("avaliacoes_raw.csv", on_bad_lines='skip', engine='python')
    except FileNotFoundError:
        # Último fallback
        df = pd.read_csv("../avaliacoes_raw.csv", on_bad_lines='skip', engine='python')

# === Padronizar nomes das colunas: remover espaços e acentos ===
def normalize_col(col):
    col = col.strip()
    col = unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode('ASCII')
    col = col.replace(' ', '').replace('-', '').replace('_', '')
    return col.lower()

df.columns = [normalize_col(c) for c in df.columns]

# === Renomear colunas manualmente ===
df = df.rename(columns={
    "userid": "user_id",
    "filmetitulo": "filme_titulo",
    "nota": "nota",
    "comentario": "comentario"
})

# === Limpeza dos dados ===
# Verificar duplicatas
duplicatas = df.duplicated().sum()

# Remover duplicatas
df = df.drop_duplicates()

# Verificar valores nulos
nulos = df.isnull().sum().sum()

# === Tratar valores nulos e tipos ===
df["user_id"] = df["user_id"].fillna(0).astype(int)
df["nota"] = df["nota"].fillna(5.0).astype(float)  # Nota padrão 5.0
df["filme_titulo"] = df["filme_titulo"].str.strip()
df["comentario"] = df["comentario"].fillna("Sem comentário").str.strip()

# === Validações específicas ===
# Validar notas (entre 0 e 10)
df = df[(df["nota"] >= 0) & (df["nota"] <= 10)]

# Validar user_id (deve ser maior que 0)
df = df[df["user_id"] > 0]

# Remover registros com campos obrigatórios vazios
df = df.dropna(subset=["user_id", "filme_titulo", "nota"])

# Limitar tamanho do comentário (máximo 500 caracteres)
df["comentario"] = df["comentario"].str[:500]

# === Salvar CSV limpo ===
try:
    df.to_csv("/app/data/avaliacoes_clean.csv", index=False, encoding="utf-8")
    arquivo_saida = "/app/data/avaliacoes_clean.csv"
except:
    try:
        # Fallback local
        df.to_csv("avaliacoes_clean.csv", index=False, encoding="utf-8")
        arquivo_saida = "avaliacoes_clean.csv"
    except:
        df.to_csv("../avaliacoes_clean.csv", index=False, encoding="utf-8")
        arquivo_saida = "../avaliacoes_clean.csv"

# === Relatório de limpeza ===
print("Limpeza de dados de avaliações concluída!")
if duplicatas > 0:
    print(f"Removidas {duplicatas} duplicatas")
if nulos > 0:
    print(f"Tratados {nulos} valores nulos")
print(f"Registros finais: {len(df)}")
print(f"Dados salvos em: {arquivo_saida}")