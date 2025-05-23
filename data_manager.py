import json
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

# --- Configurações dos arquivos JSON ---
USUARIOS_FILE = 'usuarios.json'
RESTAURANTES_FILE = 'restaurantes.json' # Para guardar restaurantes por usuario
CARADAPIOS_FILE = 'cardapios.json'

# --- Funções Auxiliares para carregar/salvar JSON ---

def carregar_json(filename):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        if filename == USUARIOS_FILE:
            return [] # Retorna uma lista vazia para usuarios.json se não existir ou estiver vazio
        elif filename == RESTAURANTES_FILE:
            return {}
        elif filename == CARADAPIOS_FILE:
            return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError: # Se o JSON estiver malformado
            if filename == USUARIOS_FILE:
                return [] # Garante que seja uma lista vazia
            else:
                return {}
            
def salvar_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Funções de Usuários ---

def carregar_usuarios():
    return carregar_json(USUARIOS_FILE)

def salvar_usuarios(usuarios):
    salvar_json(usuarios, USUARIOS_FILE)

def cadastrar_usuario(username, password, role):
    usuarios = carregar_usuarios()
    if any(u['username'] == username for u in usuarios):
        return False, 'Nome de usuário já existe.'
    
    hashed_password = generate_password_hash(password)
    new_user = {
        'id': len(usuarios) + 1, # ID simples, considerar UUID para produção
        'username': username,
        'password': hashed_password,
        'role': role
    }
    usuarios.append(new_user)
    salvar_usuarios(usuarios)
    return True, 'Usuário cadastrado com sucesso!'

def verificar_credenciais(username, password):
    usuarios = carregar_usuarios()
    for user in usuarios:
        if user['username'] == username and check_password_hash(user['password'], password):
            return True, user['id'], user['role']
    return False, None, None

def buscar_usuario_por_id(user_id):
    usuarios = carregar_usuarios()
    return next((u for u in usuarios if u['id'] == user_id), None)

# --- Funções de Restaurantes ---

def carregar_restaurantes_por_usuario():
    return carregar_json(RESTAURANTES_FILE)

def salvar_restaurantes_por_usuario(restaurantes_data):
    salvar_json(restaurantes_data, RESTAURANTES_FILE)

def adicionar_restaurante(user_id, nome, categoria, localizacao):
    restaurantes_data = carregar_restaurantes_por_usuario()
    user_id_str = str(user_id) # Garante que a chave seja string para JSON

    if user_id_str not in restaurantes_data:
        restaurantes_data[user_id_str] = []

    # Gerar um ID único para o restaurante
    new_restaurant_id = str(uuid.uuid4()) # ID global único
    
    new_restaurant = {
        'id': new_restaurant_id,
        'nome': nome,
        'categoria': categoria,
        'localizacao': localizacao,
        'ativo': True # Restaurante é ativo por padrão ao ser criado
    }
    restaurantes_data[user_id_str].append(new_restaurant)
    salvar_restaurantes_por_usuario(restaurantes_data)
    return new_restaurant # Retorna o restaurante criado para acesso ao ID

def buscar_restaurantes_do_usuario(user_id):
    restaurantes_data = carregar_restaurantes_por_usuario()
    user_id_str = str(user_id)
    return restaurantes_data.get(user_id_str, [])

def buscar_restaurante_por_id(restaurante_id):
    restaurantes_data = carregar_restaurantes_por_usuario()
    for user_id_str, lista_restaurantes in restaurantes_data.items():
        for r in lista_restaurantes:
            if r['id'] == restaurante_id:
                return r
    return None

def alternar_status_restaurante(user_id, restaurante_id):
    restaurantes_data = carregar_restaurantes_por_usuario()
    user_id_str = str(user_id)

    if user_id_str in restaurantes_data:
        for r in restaurantes_data[user_id_str]:
            if r['id'] == restaurante_id:
                r['ativo'] = not r.get('ativo', True) # Inverte o status, padrão é ativo
                salvar_restaurantes_por_usuario(restaurantes_data)
                return True
    return False

def deletar_restaurante(user_id, restaurante_id):
    restaurantes_data = carregar_restaurantes_por_usuario()
    user_id_str = str(user_id)

    if user_id_str in restaurantes_data:
        initial_len = len(restaurantes_data[user_id_str])
        restaurantes_data[user_id_str] = [
            r for r in restaurantes_data[user_id_str] if r['id'] != restaurante_id
        ]
        if len(restaurantes_data[user_id_str]) < initial_len:
            salvar_restaurantes_por_usuario(restaurantes_data)
            # Também deleta o cardápio associado
            cardapios = carregar_cardapios()
            if restaurante_id in cardapios:
                del cardapios[restaurante_id]
                salvar_cardapios(cardapios)
            return True
    return False

# --- Funções de Cardápio ---

def carregar_cardapios():
    return carregar_json(CARADAPIOS_FILE)

def salvar_cardapios(cardapios):
    salvar_json(cardapios, CARADAPIOS_FILE)

def adicionar_item_cardapio(restaurante_id, nome_prato, preco, tipo, descricao=""):
    cardapios = carregar_cardapios()
    restaurante_id_str = str(restaurante_id) # Garante que a chave seja string

    if restaurante_id_str not in cardapios:
        cardapios[restaurante_id_str] = []

    # Gerar um ID único para o item do cardápio
    new_item_id = str(uuid.uuid4())
    
    new_item = {
        'id': new_item_id,
        'nome_prato': nome_prato,
        'preco': float(preco),
        'tipo': tipo,
        'descricao': descricao
    }
    cardapios[restaurante_id_str].append(new_item)
    salvar_cardapios(cardapios)
    return True

def buscar_cardapio_do_restaurante(restaurante_id):
    cardapios = carregar_cardapios()
    restaurante_id_str = str(restaurante_id)
    return cardapios.get(restaurante_id_str, [])

def deletar_item_cardapio(restaurante_id, item_id):
    cardapios = carregar_cardapios()
    restaurante_id_str = str(restaurante_id)
    item_id_str = str(item_id) # Garante que o ID do item também seja string

    if restaurante_id_str in cardapios:
        initial_len = len(cardapios[restaurante_id_str])
        cardapios[restaurante_id_str] = [
            item for item in cardapios[restaurante_id_str] if item['id'] != item_id_str
        ]
        if len(cardapios[restaurante_id_str]) < initial_len:
            salvar_cardapios(cardapios)
            return True
    return False