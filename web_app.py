from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash # Mantido para referência, mas a lógica está no data_manager
import os
import uuid # Para gerar secret_key

# Importa as funções do seu data_manager
from data_manager import (
    carregar_usuarios, salvar_usuarios, cadastrar_usuario, verificar_credenciais,
    carregar_restaurantes_por_usuario, salvar_restaurantes_por_usuario, # Pode não ser necessário expor salvar_restaurantes_por_usuario diretamente se adicionar/deletar já salvam
    adicionar_restaurante, buscar_restaurantes_do_usuario, buscar_restaurante_por_id,
    alternar_status_restaurante, deletar_restaurante,
    carregar_cardapios, salvar_cardapios, adicionar_item_cardapio,
    buscar_cardapio_do_restaurante, deletar_item_cardapio
)

app = Flask(__name__)
# GERAR UMA CHAVE SECRETA FORTE E ÚNICA AQUI
# Uma forma simples de gerar: os.urandom(24).hex()
app.secret_key = os.environ.get('SECRET_KEY', str(uuid.uuid4())) # Usa variável de ambiente ou gera uma para dev

# --- Rotas de Autenticação e Navegação Principal ---

@app.route('/')
def index():
    """
    Redireciona o usuário para a página de login se não estiver logado,
    ou para o dashboard/explorar dependendo do seu papel.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if session.get('user_role') == 'empresario':
        return redirect(url_for('dashboard'))
    elif session.get('user_role') == 'cliente':
        return redirect(url_for('explorar'))
    
    return redirect(url_for('login')) # Fallback caso user_role não esteja definido

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota para login de usuários.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        success, user_id, user_role = verificar_credenciais(username, password)

        if success:
            session['logged_in'] = True
            session['username'] = username
            session['user_role'] = user_role
            session['user_id'] = user_id
            
            flash('Login realizado com sucesso!', 'success')
            
            if user_role == 'empresario':
                return redirect(url_for('dashboard'))
            else: # role == 'cliente'
                return redirect(url_for('explorar'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """
    Rota para cadastro de novos usuários.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role'] # 'empresario' ou 'cliente'

        success, message = cadastrar_usuario(username, password, role)

        if success:
            flash('Conta criada com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    """
    Rota para deslogar o usuário, limpando a sessão.
    """
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_role', None)
    session.pop('user_id', None) 
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

# --- Rotas para Empresários ---

@app.route('/dashboard')
def dashboard():
    """
    Dashboard para usuários empresários, mostrando seus restaurantes.
    """
    if not session.get('logged_in') or session.get('user_role') != 'empresario':
        flash('Acesso negado. Faça login como empresário.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    if not user_id: 
        flash('Erro: ID de usuário não encontrado na sessão. Por favor, faça login novamente.', 'danger')
        return redirect(url_for('logout'))

    restaurantes = buscar_restaurantes_do_usuario(user_id)
    return render_template('dashboard.html', restaurantes=restaurantes, username=session.get('username'))

@app.route('/adicionar_restaurante', methods=['GET', 'POST']) # Nome da rota para corresponder ao template
def adicionar_restaurante_web():
    """
    Rota para empresários cadastrarem novos restaurantes.
    """
    if not session.get('logged_in') or session.get('user_role') != 'empresario':
        flash('Acesso negado. Faça login como empresário para cadastrar restaurantes.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Erro: ID de usuário não encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        nome = request.form['nome']
        categoria = request.form['categoria']
        localizacao = request.form['localizacao']

        if not nome or not categoria or not localizacao:
            flash('Nome, Categoria e Localização do restaurante são obrigatórios!', 'danger')
            return render_template('adicionar_restaurante.html') 

        adicionar_restaurante(user_id, nome, categoria, localizacao)
        flash(f'Restaurante "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('adicionar_restaurante.html')

@app.route('/alternar_status_restaurante/<restaurante_id>') # <restaurante_id> sem :int porque agora é UUID (string)
def alternar_status_restaurante_web(restaurante_id):
    """
    Rota para empresários alternarem o status de ativação/desativação de um restaurante.
    """
    if not session.get('logged_in') or session.get('user_role') != 'empresario':
        flash('Acesso negado. Faça login como empresário para alterar o status.', 'danger')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash('Erro: ID de usuário não encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('logout'))

    success = alternar_status_restaurante(user_id, restaurante_id)
    if success:
        flash(f'Status do restaurante alterado.', 'info')
    else:
        flash('Restaurante não encontrado ou erro ao alterar status.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/editar_restaurante/<restaurante_id>', methods=['GET', 'POST']) # <restaurante_id> sem :int
def editar_restaurante(restaurante_id):
    """
    Rota para empresários editarem os detalhes de um restaurante.
    """
    if not session.get('logged_in') or session.get('user_role') != 'empresario':
        flash('Acesso negado. Faça login como empresário.', 'danger')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash('Erro: ID de usuário não encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('logout'))

    restaurante = buscar_restaurante_por_id(restaurante_id) # Busca o restaurante por ID global
    
    # Verifica se o restaurante existe E se pertence ao usuário logado
    restaurantes_do_usuario = buscar_restaurantes_do_usuario(user_id)
    if not restaurante or not any(r['id'] == restaurante_id for r in restaurantes_do_usuario):
        flash('Restaurante não encontrado ou você não tem permissão para editá-lo.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Atualiza os dados do restaurante
        restaurante['nome'] = request.form['nome']
        restaurante['categoria'] = request.form['categoria']
        restaurante['localizacao'] = request.form['localizacao'] 

        # A forma mais simples de salvar a alteração é carregar tudo, encontrar e salvar
        # Isso pode ser otimizado no data_manager com uma função de 'atualizar_restaurante'
        all_restaurantes_data = carregar_restaurantes_por_usuario()
        user_id_str = str(user_id)
        if user_id_str in all_restaurantes_data:
            for i, r_item in enumerate(all_restaurantes_data[user_id_str]):
                if r_item['id'] == restaurante_id:
                    all_restaurantes_data[user_id_str][i] = restaurante # Atualiza o objeto no lugar
                    break
        salvar_restaurantes_por_usuario(all_restaurantes_data)

        flash(f'Restaurante "{restaurante["nome"]}" atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    # Assumindo que você terá um template 'editar_restaurante.html'
    return render_template('editar_restaurante.html', restaurante=restaurante)


@app.route('/deletar_restaurante_web/<restaurante_id>') # <restaurante_id> sem :int
def deletar_restaurante_web(restaurante_id):
    """
    Rota para empresários deletarem um restaurante e seu cardápio associado.
    """
    if not session.get('logged_in') or session.get('user_role') != 'empresario':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash('Erro: ID de usuário não encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('logout'))

    # Adicionalmente, verificar se o restaurante pertence ao usuário logado antes de deletar
    restaurantes_do_usuario = buscar_restaurantes_do_usuario(user_id)
    restaurante_pertence_ao_usuario = any(r['id'] == restaurante_id for r in restaurantes_do_usuario)

    if not restaurante_pertence_ao_usuario:
        flash('Você não tem permissão para deletar este restaurante.', 'danger')
        return redirect(url_for('dashboard'))

    success = deletar_restaurante(user_id, restaurante_id)
    if success:
        flash('Restaurante e seu cardápio foram deletados com sucesso!', 'success')
    else:
        flash('Erro ao deletar restaurante ou você não tem permissão.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/gerenciar_cardapio/<restaurante_id>', methods=['GET', 'POST']) # <restaurante_id> sem :int
def gerenciar_cardapio(restaurante_id):
    """
    Rota para empresários gerenciarem o cardápio de seus restaurantes
    (adicionar novos itens).
    """
    if not session.get('logged_in') or session.get('user_role') != 'empresario':
        flash('Acesso negado. Faça login como empresário.', 'danger')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash('Erro: ID de usuário não encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('logout'))

    restaurante = buscar_restaurante_por_id(restaurante_id)
    
    # Verifica se o restaurante existe E se pertence ao usuário logado
    restaurantes_do_usuario = buscar_restaurantes_do_usuario(user_id)
    if not restaurante or not any(r['id'] == restaurante_id for r in restaurantes_do_usuario):
        flash('Restaurante não encontrado ou você não tem permissão.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nome_prato = request.form['nome_prato']
        preco = request.form['preco']
        tipo = request.form['tipo']
        descricao = request.form.get('descricao', '')

        try:
            preco = float(preco)
            if preco <= 0:
                raise ValueError("Preço deve ser positivo.")
        except ValueError:
            flash('Preço inválido. Por favor, insira um número válido e positivo.', 'danger')
            return redirect(url_for('gerenciar_cardapio', restaurante_id=restaurante_id))

        adicionar_item_cardapio(restaurante_id, nome_prato, preco, tipo, descricao)
        flash(f'Item "{nome_prato}" adicionado ao cardápio.', 'success')
        return redirect(url_for('gerenciar_cardapio', restaurante_id=restaurante_id))

    itens_cardapio = buscar_cardapio_do_restaurante(restaurante_id)
    return render_template('gerenciar_cardapio.html', restaurante=restaurante, cardapio=itens_cardapio)

@app.route('/deletar_item_cardapio_web/<restaurante_id>/<item_id>') # <restaurante_id> e <item_id> sem :int
def deletar_item_cardapio_web(restaurante_id, item_id):
    """
    Rota para empresários deletarem um item do cardápio de um restaurante.
    """
    if not session.get('logged_in') or session.get('user_role') != 'empresario':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash('Erro: ID de usuário não encontrado. Faça login novamente.', 'danger')
        return redirect(url_for('logout'))

    # Verificar se o restaurante pertence ao usuário logado (segurança)
    restaurantes_do_usuario = buscar_restaurantes_do_usuario(user_id)
    restaurante_pertence_ao_usuario = any(r['id'] == restaurante_id for r in restaurantes_do_usuario)

    if not restaurante_pertence_ao_usuario:
        flash('Você não tem permissão para deletar itens deste cardápio.', 'danger')
        return redirect(url_for('dashboard'))

    success = deletar_item_cardapio(restaurante_id, item_id)
    if success:
        flash('Item do cardápio removido.', 'success')
    else:
        flash('Erro ao remover item do cardápio.', 'danger')
    return redirect(url_for('gerenciar_cardapio', restaurante_id=restaurante_id))

# --- Rotas para Clientes ---

@app.route('/explorar')
def explorar():
    """
    Rota para clientes explorarem restaurantes ativos.
    """
    if not session.get('logged_in') or session.get('user_role') != 'cliente':
        flash('Acesso negado. Faça login como cliente para explorar restaurantes.', 'danger')
        return redirect(url_for('login'))
    
    todos_restaurantes_ativos = []
    restaurantes_por_usuario_dict = carregar_restaurantes_por_usuario()
    for user_id_str, lista_restaurantes in restaurantes_por_usuario_dict.items():
        for restaurante in lista_restaurantes:
            # Garante que 'ativo' exista e seja True
            if restaurante.get('ativo') == True:
                todos_restaurantes_ativos.append(restaurante)

    return render_template('explorar.html', restaurantes=todos_restaurantes_ativos)

@app.route('/visualizar_cardapio/<restaurante_id>') # Alterado para refletir o nome do template e UUID
def visualizar_cardapio(restaurante_id):
    """
    Rota para clientes visualizarem o cardápio de um restaurante específico.
    """
    if not session.get('logged_in') or session.get('user_role') != 'cliente':
        flash('Acesso negado. Faça login como cliente para ver o cardápio.', 'danger')
        return redirect(url_for('login'))

    restaurante = buscar_restaurante_por_id(restaurante_id) # Buscar por ID único (UUID)
    
    if not restaurante or restaurante.get('ativo') == False:
        flash('Restaurante não encontrado ou inativo.', 'danger')
        return redirect(url_for('explorar'))

    itens_cardapio = buscar_cardapio_do_restaurante(restaurante_id)
    return render_template('visualizar_cardapio.html', restaurante=restaurante, itens_cardapio=itens_cardapio)


# --- Inicialização ---
if __name__ == '__main__':
    # Garante que os arquivos JSON existam ou sejam inicializados
    carregar_usuarios()
    carregar_restaurantes_por_usuario()
    carregar_cardapios()
    app.run(host='0.0.0.0', port=5000, debug=True)