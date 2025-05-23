# utils.py
import os
from colorama import Fore, Style, init

# Inicializa colorama para o terminal (importante para funcionar no PowerShell)
init(autoreset=True)

def limpar_tela():
    """Limpa o console do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def finalizar_app():
    """Exibe mensagem de finalização e encerra o aplicativo."""
    limpar_tela()
    print(Fore.YELLOW + '👋 Finalizando o Sabor Express... Volte sempre!\n' + Style.RESET_ALL)

def opcao_invalida():
    """Exibe mensagem de opção inválida."""
    print(Fore.RED + '\n❌ Opção inválida! Por favor, escolha uma opção válida do menu.' + Style.RESET_ALL)
    input('\nPressione Enter para voltar ao menu principal...')

def caminho_arquivo(nome_arquivo):
    """Retorna o caminho completo para um arquivo na mesma pasta do script."""
    # os.path.abspath(__file__) pega o caminho completo do arquivo atual (utils.py)
    # os.path.dirname() pega o diretório desse arquivo
    # os.path.join() junta o diretório com o nome do arquivo desejado
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, nome_arquivo)
