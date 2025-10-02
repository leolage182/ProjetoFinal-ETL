from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'movie_rating_secret_key_2024'

# Configuração do banco de dados PostgreSQL
PG_USER = os.getenv("PG_USER", "user")
PG_PASS = os.getenv("PG_PASS", "secret")
PG_DB = os.getenv("PG_DB", "dw")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")

def get_db_connection():
    """Retorna conexão com PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS,
            port=PG_PORT
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar com PostgreSQL: {e}")
        return None

# Função removida - tabelas agora são criadas no ETL

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/usuarios')
def usuarios():
    """Lista todos os usuários"""
    conn = get_db_connection()
    usuarios_list = []
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT id, nome, email, genero, pais FROM usuarios ORDER BY nome")
            usuarios_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar usuários: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('usuarios.html', usuarios=usuarios_list)

@app.route('/filmes')
def filmes():
    """Lista todos os filmes do catálogo"""
    conn = get_db_connection()
    filmes_list = []
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT titulo, ano_lancamento, genero, nota_imdb FROM filmes ORDER BY titulo")
            filmes_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar filmes: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('filmes.html', filmes=filmes_list)

@app.route('/avaliacoes')
def avaliacoes():
    """Lista todas as avaliações"""
    conn = get_db_connection()
    avaliacoes_list = []
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("""
                SELECT a.id, u.nome as usuario_nome, a.filme_titulo, a.nota, 
                       a.comentario, a.data_avaliacao
                FROM avaliacoes a
                JOIN usuarios u ON a.user_id = u.id
                ORDER BY a.data_avaliacao DESC
            """)
            avaliacoes_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar avaliações: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('avaliacoes.html', avaliacoes=avaliacoes_list)

@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    """Cadastra novo usuário"""
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        email = request.form['email'].strip()
        
        if not nome or not email:
            flash('Nome e email são obrigatórios!', 'error')
            return render_template('cadastrar_usuario.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Verificar se email já existe
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = %s", (email,))
                if cursor.fetchone()[0] > 0:
                    flash('Email já cadastrado!', 'error')
                    cursor.close()
                    conn.close()
                    return render_template('cadastrar_usuario.html')
                
                # Inserir novo usuário
                cursor.execute(
                    "INSERT INTO usuarios (nome, email) VALUES (%s, %s)",
                    (nome, email)
                )
                conn.commit()
                cursor.close()
                conn.close()
                
                flash('Usuário cadastrado com sucesso!', 'success')
                return redirect(url_for('usuarios'))
                
            except Exception as e:
                flash(f'Erro ao cadastrar usuário: {e}', 'error')
                if conn:
                    conn.close()
        else:
            flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('cadastrar_usuario.html')

@app.route('/avaliar_filme', methods=['GET', 'POST'])
@app.route('/avaliar_filme/<filme>', methods=['GET', 'POST'])
def avaliar_filme(filme=None):
    """Avalia um filme"""
    # Se não veio pela URL, tenta pegar da query string
    if not filme:
        filme = request.args.get('filme')
    if request.method == 'POST':
        user_id = request.form['user_id']
        filme_titulo = request.form['filme_titulo'].strip()
        nota = request.form['nota']
        comentario = request.form['comentario'].strip()
        
        if not user_id or not filme_titulo or not nota:
            flash('Usuário, filme e nota são obrigatórios!', 'error')
            return redirect(url_for('avaliar_filme'))
        
        try:
            nota = float(nota)
            if nota < 0 or nota > 10:
                flash('Nota deve estar entre 0 e 10!', 'error')
                return redirect(url_for('avaliar_filme'))
        except ValueError:
            flash('Nota deve ser um número válido!', 'error')
            return redirect(url_for('avaliar_filme'))
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO avaliacoes (user_id, filme_titulo, nota, comentario) VALUES (%s, %s, %s, %s)",
                    (user_id, filme_titulo, nota, comentario)
                )
                conn.commit()
                cursor.close()
                conn.close()
                
                flash('Avaliação cadastrada com sucesso!', 'success')
                return redirect(url_for('avaliacoes'))
                
            except Exception as e:
                flash(f'Erro ao cadastrar avaliação: {e}', 'error')
                if conn:
                    conn.close()
        else:
            flash('Erro de conexão com o banco de dados', 'error')
    
    # Buscar usuários e filmes para os selects
    usuarios_list = []
    filmes_list = []
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Buscar usuários
            cursor.execute("SELECT id, nome, email FROM usuarios ORDER BY nome")
            usuarios_list = cursor.fetchall()
            
            # Buscar filmes
            cursor.execute("SELECT DISTINCT titulo FROM filmes ORDER BY titulo")
            filmes_list = cursor.fetchall()
            
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    
    return render_template('avaliar_filme.html', usuarios=usuarios_list, filmes=filmes_list, filme_selecionado=filme)

@app.route('/api/filmes')
def api_filmes():
    """API para buscar filmes"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("SELECT titulo, ano_lancamento, genero, nota_imdb FROM filmes ORDER BY titulo")
            filmes = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Converter para lista de dicionários
            filmes_list = []
            for filme in filmes:
                filmes_list.append({
                    'titulo': filme['titulo'],
                    'ano_lancamento': filme['ano_lancamento'],
                    'genero': filme['genero'],
                    'nota_imdb': float(filme['nota_imdb']) if filme['nota_imdb'] else 0
                })
            
            return jsonify(filmes_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Erro de conexão com banco'}), 500

# Rotas para Data Marts
@app.route('/data-marts')
def data_marts():
    """Página principal dos Data Marts"""
    return render_template('data_marts.html')

@app.route('/data-marts/top-filmes-por-genero')
def top_filmes_por_genero():
    """Data Mart: Top 10 filmes mais bem avaliados por gênero"""
    conn = get_db_connection()
    data = []
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("""
                SELECT genero, titulo, ano_lancamento, nota_media, total_avaliacoes, ranking
                FROM vw_top_filmes_por_genero
                WHERE ranking <= 10
                ORDER BY genero, ranking
            """)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('top_filmes_por_genero.html', filmes=data)

@app.route('/data-marts/top-usuarios-avaliacoes')
def top_usuarios_avaliacoes():
    """Data Mart: Top 5 usuários com mais avaliações"""
    conn = get_db_connection()
    data = []
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("""
                SELECT id, nome, email, total_avaliacoes, nota_media_dada, 
                       primeira_avaliacao, ultima_avaliacao
                FROM vw_top_usuarios_avaliacoes
                LIMIT 5
            """)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('top_usuarios_avaliacoes.html', usuarios=data)

@app.route('/data-marts/piores-filmes-por-genero')
def piores_filmes_por_genero():
    """Data Mart: Top 10 filmes com piores avaliações por gênero"""
    conn = get_db_connection()
    data = []
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("""
                SELECT genero, titulo, ano_lancamento, nota_media, total_avaliacoes, ranking
                FROM vw_piores_filmes_por_genero
                WHERE ranking <= 10
                ORDER BY genero, ranking
            """)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('piores_filmes_por_genero.html', filmes=data)

# Novas rotas para consultas analíticas específicas

@app.route('/data-marts/top-filmes-populares')
def top_filmes_populares():
    """Consulta Analítica: Top 5 filmes mais populares por gênero"""
    conn = get_db_connection()
    data = []
    query_sql = ""
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query_sql = """
                SELECT genero, titulo, ano_lancamento, nota_media, total_avaliacoes, ranking
                FROM vw_top_filmes_por_genero
                WHERE ranking <= 5
                ORDER BY genero, ranking
            """
            cursor.execute(query_sql)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('top_filmes_populares.html', filmes=data, query_sql=query_sql)

@app.route('/data-marts/numero-filmes-avaliados')
def numero_filmes_avaliados():
    """Consulta Analítica: Número de filmes avaliados por usuário top"""
    conn = get_db_connection()
    data = []
    query_sql = ""
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query_sql = """
                SELECT u.nome, u.email, u.total_avaliacoes,
                       COUNT(DISTINCT a.filme_titulo) as filmes_unicos_avaliados,
                       u.nota_media_dada,
                       u.primeira_avaliacao, u.ultima_avaliacao
                FROM vw_top_usuarios_avaliacoes u
                JOIN avaliacoes a ON u.id = a.user_id
                GROUP BY u.id, u.nome, u.email, u.total_avaliacoes, u.nota_media_dada, 
                         u.primeira_avaliacao, u.ultima_avaliacao
                ORDER BY u.total_avaliacoes DESC
                LIMIT 10
            """
            cursor.execute(query_sql)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('numero_filmes_avaliados.html', usuarios=data, query_sql=query_sql)

@app.route('/data-marts/top-filmes-odiados')
def top_filmes_odiados():
    """Consulta Analítica: Top 5 filmes mais odiados por gênero"""
    conn = get_db_connection()
    data = []
    query_sql = ""
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query_sql = """
                SELECT genero, titulo, ano_lancamento, nota_media, total_avaliacoes, ranking
                FROM vw_piores_filmes_por_genero
                WHERE ranking <= 5
                ORDER BY genero, ranking
            """
            cursor.execute(query_sql)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('top_filmes_odiados.html', filmes=data, query_sql=query_sql)

@app.route('/data-marts/avaliacoes-por-pais')
def avaliacoes_por_pais():
    """Data Mart: Número de avaliações por país"""
    conn = get_db_connection()
    data = []
    query_sql = ""
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query_sql = """
                SELECT pais, total_avaliacoes, total_usuarios, nota_media_pais,
                       primeira_avaliacao, ultima_avaliacao
                FROM vw_avaliacoes_por_pais
                ORDER BY total_avaliacoes DESC
            """
            cursor.execute(query_sql)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('avaliacoes_por_pais.html', paises=data, query_sql=query_sql)

@app.route('/data-marts/nota-media-por-genero')
def nota_media_por_genero():
    """Data Mart: Nota média por gênero dos usuários"""
    conn = get_db_connection()
    data = []
    query_sql = ""
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query_sql = """
                SELECT genero, total_avaliacoes, nota_media_genero, usuarios_avaliaram,
                       filmes_avaliados, nota_minima, nota_maxima
                FROM vw_nota_media_por_genero
                ORDER BY nota_media_genero DESC
            """
            cursor.execute(query_sql)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {e}', 'error')
            if conn:
                conn.close()
    else:
        flash('Erro de conexão com o banco de dados', 'error')
    
    return render_template('nota_media_por_genero.html', generos=data, query_sql=query_sql)

if __name__ == '__main__':
    print("Inicializando aplicação...")
    print("ℹ️  Tabelas são criadas automaticamente pelo processo ETL")
    print("🚀 Iniciando servidor Flask...")
    app.run(host='0.0.0.0', port=5000, debug=True)