import pandas as pd
import unicodedata

# === Ler CSV bruto ===
try:
    # Ler do arquivo montado da raiz do projeto
    df = pd.read_csv("/app/input/usuarios_raw.csv", on_bad_lines='skip', engine='python')
except FileNotFoundError:
    try:
        # Fallback para arquivo local
        df = pd.read_csv("usuarios_raw.csv", on_bad_lines='skip', engine='python')
    except FileNotFoundError:
        # Último fallback
        df = pd.read_csv("../usuarios_raw.csv", on_bad_lines='skip', engine='python')

# === Padronizar nomes das colunas: remover espaços e acentos ===
def normalize_col(col):
    col = col.strip()
    col = unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode('ASCII')
    col = col.replace(' ', '').replace('-', '').replace('_', '')
    return col.lower()

df.columns = [normalize_col(c) for c in df.columns]

# === Renomear colunas manualmente ===
df = df.rename(columns={
    "nome": "nome",
    "email": "email", 
    "genero": "genero",
    "pais": "pais"
})

# === Limpeza dos dados ===
# Verificar duplicatas
duplicatas = df.duplicated().sum()

# Remover duplicatas
df = df.drop_duplicates()

# Verificar valores nulos
nulos = df.isnull().sum().sum()

# === Tratar valores nulos e tipos ===
df["nome"] = df["nome"].str.strip()
df["email"] = df["email"].str.strip().str.lower()
df["genero"] = df["genero"].str.strip()
df["pais"] = df["pais"].str.strip()

# === Normalizar caracteres especiais (remover acentos) ===
def normalize_text(text):
    """Remove acentos e caracteres especiais de strings"""
    if pd.isna(text):
        return text
    text = str(text).strip()
    # Normalizar caracteres Unicode (remover acentos)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text

# Aplicar normalização nas colunas de texto
df["nome"] = df["nome"].apply(normalize_text)
df["pais"] = df["pais"].apply(normalize_text)

# === Validações específicas ===
# Validar emails (formato básico)
df = df[df["email"].str.contains("@", na=False)]

# Remover registros com campos obrigatórios vazios
df = df.dropna(subset=["nome", "email", "genero", "pais"])

# === Salvar CSV limpo ===
try:
    df.to_csv("/app/data/usuarios_clean.csv", index=False, encoding="utf-8")
    arquivo_saida = "/app/data/usuarios_clean.csv"
except:
    try:
        # Fallback local
        df.to_csv("usuarios_clean.csv", index=False, encoding="utf-8")
        arquivo_saida = "usuarios_clean.csv"
    except:
        df.to_csv("../usuarios_clean.csv", index=False, encoding="utf-8")
        arquivo_saida = "../usuarios_clean.csv"

# === Relatório de limpeza ===
print("Limpeza de dados de usuários concluída!")
if duplicatas > 0:
    print(f"Removidas {duplicatas} duplicatas")
if nulos > 0:
    print(f"Tratados {nulos} valores nulos")
print(f"Registros finais: {len(df)}")
print(f"Dados salvos em: {arquivo_saida}")