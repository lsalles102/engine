#!/usr/bin/env python3
"""
PyCheatEngine - Sistema de Engenharia Reversa e Manipulação de Memória
Arquivo principal de inicialização do programa

Este é o ponto de entrada principal do PyCheatEngine, oferecendo opções para
executar tanto a interface gráfica quanto a interface de linha de comando.

Autor: PyCheatEngine Team
Versão: 1.0.0
"""

import sys
import os
import ctypes
import platform
import argparse
from typing import Optional

def check_admin_privileges() -> bool:
    """
    Verifica se o programa está sendo executado com privilégios administrativos
    
    Returns:
        bool: True se tem privilégios administrativos, False caso contrário
    """
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Para sistemas Unix-like
            return os.geteuid() == 0
    except Exception:
        return False

def request_admin_privileges():
    """
    Solicita privilégios administrativos para o programa
    """
    if platform.system() == "Windows":
        try:
            # Tenta reexecutar o programa como administrador
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1
            )
        except Exception as e:
            print(f"Erro ao solicitar privilégios administrativos: {e}")
    else:
        print("Execute o programa com 'sudo' para obter privilégios administrativos:")
        print(f"sudo python3 {sys.argv[0]}")

def show_banner():
    """Exibe o banner do programa"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                              PyCheatEngine v1.0.0                           ║
║                    Sistema de Engenharia Reversa e Manipulação              ║
║                              de Memória em Python                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Funcionalidades:                                                           ║
║  • Scanner de memória com múltiplos tipos de dados                          ║
║  • Resolução de cadeias de ponteiros (pointer chains)                       ║
║  • Scanner de padrões de bytes (AOB) com suporte a wildcards                ║
║  • Interface gráfica intuitiva                                              ║
║  • Interface de linha de comando                                            ║
║  • Sistema de sessões para salvar/carregar estado                           ║
║                                                                              ║
║  AVISO: Este programa requer privilégios administrativos para acessar       ║
║         a memória de outros processos. Use com responsabilidade!            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_main_menu() -> str:
    """
    Exibe o menu principal e retorna a escolha do usuário
    
    Returns:
        str: Opção escolhida pelo usuário
    """
    menu = """
Escolha uma opção:

[1] Interface Gráfica (GUI) - Recomendado para usuários iniciantes
[2] Interface de Linha de Comando (CLI) - Para usuários avançados
[3] Mostrar informações do sistema
[4] Verificar privilégios
[5] Ajuda
[0] Sair

"""
    print(menu)
    
    while True:
        try:
            choice = input("Digite sua opção (0-5): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5']:
                return choice
            else:
                print("Opção inválida. Digite um número entre 0 e 5.")
        except (EOFError, KeyboardInterrupt):
            return '0'

def show_system_info():
    """Exibe informações do sistema"""
    try:
        import psutil
        
        print("\n" + "="*60)
        print("INFORMAÇÕES DO SISTEMA")
        print("="*60)
        
        # Informações básicas
        print(f"Sistema Operacional: {platform.system()} {platform.release()}")
        print(f"Arquitetura: {platform.machine()}")
        print(f"Versão Python: {sys.version}")
        
        # Informações de memória
        memory = psutil.virtual_memory()
        print(f"Memória Total: {memory.total / (1024**3):.2f} GB")
        print(f"Memória Disponível: {memory.available / (1024**3):.2f} GB")
        print(f"Uso de Memória: {memory.percent}%")
        
        # Informações de CPU
        print(f"CPU: {platform.processor()}")
        print(f"Núcleos: {psutil.cpu_count(logical=False)} físicos, {psutil.cpu_count(logical=True)} lógicos")
        
        # Privilégios
        is_admin = check_admin_privileges()
        print(f"Privilégios Administrativos: {'Sim' if is_admin else 'Não'}")
        
        # Número de processos
        process_count = len(psutil.pids())
        print(f"Processos em Execução: {process_count}")
        
        print("="*60)
        
    except ImportError:
        print("\nErro: Biblioteca 'psutil' não encontrada.")
        print("Instale com: pip install psutil")
    except Exception as e:
        print(f"\nErro ao obter informações do sistema: {e}")

def show_help():
    """Exibe informações de ajuda"""
    help_text = """
AJUDA - PyCheatEngine

REQUISITOS:
• Windows (recomendado) ou Linux
• Python 3.8 ou superior
• Privilégios administrativos
• Bibliotecas: psutil, tkinter (GUI)

COMO USAR:

1. Interface Gráfica (GUI):
   - Mais fácil para iniciantes
   - Interface visual intuitiva
   - Todas as funcionalidades disponíveis através de menus

2. Interface de Linha de Comando (CLI):
   - Para usuários avançados
   - Controle total via comandos
   - Ideal para automação e scripts

FUNCIONALIDADES PRINCIPAIS:

• Scanner de Memória:
  - Busca valores na memória de processos
  - Suporte a int32, int64, float, double, string
  - Comparações: igual, maior, menor, alterado, etc.

• Ponteiros:
  - Resolução de cadeias de ponteiros
  - Útil para valores que mudam de endereço
  - Suporte a múltiplos níveis de indireção

• Scanner AOB (Array of Bytes):
  - Busca padrões de bytes na memória
  - Suporte a wildcards (??)
  - Útil para encontrar código específico

• Sessões:
  - Salva estado atual do programa
  - Carrega sessões anteriores
  - Formato JSON legível

SEGURANÇA:
• Use apenas em processos próprios ou autorizados
• Não utilize para trapacear em jogos online
• Cuidado com processos críticos do sistema

TROUBLESHOOTING:
• Se não conseguir anexar a um processo, verifique privilégios
• Para processos 64-bit, use Python 64-bit
• Alguns antivírus podem detectar como falso positivo

Para mais informações, consulte a documentação ou o código fonte.
    """
    print(help_text)

def run_gui():
    """Executa a interface gráfica"""
    try:
        print("\nInicializando interface gráfica...")
        print("Aguarde enquanto a janela é carregada...")
        
        # Adiciona o diretório atual ao path para resolver imports
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        import ui.gui
        CheatEngineGUI = ui.gui.CheatEngineGUI
        
        # Cria e executa a GUI
        gui = CheatEngineGUI()
        gui.run()
        
    except ImportError as e:
        print(f"\nErro ao importar interface gráfica: {e}")
        print("Verifique se o tkinter está instalado corretamente.")
        if platform.system() == "Linux":
            print("No Ubuntu/Debian: sudo apt-get install python3-tk")
            print("No CentOS/RHEL: sudo yum install tkinter")
    except Exception as e:
        print(f"\nErro na interface gráfica: {e}")
        print("Tente usar a interface de linha de comando (opção 2)")

def run_cli():
    """Executa a interface de linha de comando"""
    try:
        print("\nInicializando interface de linha de comando...")
        
        # Adiciona o diretório atual ao path para resolver imports
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        import ui.cli
        CheatEngineCLI = ui.cli.CheatEngineCLI
        
        # Cria e executa a CLI
        cli = CheatEngineCLI()
        cli.run()
        
    except Exception as e:
        print(f"\nErro na interface CLI: {e}")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    required_modules = ['psutil', 'tkinter']
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'tkinter':
                import tkinter
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nAVISO: Módulos faltando: {', '.join(missing_modules)}")
        print("Instale com: pip install " + " ".join(missing_modules))
        return False
    
    return True

def parse_arguments():
    """Analisa argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='PyCheatEngine - Sistema de Engenharia Reversa e Manipulação de Memória',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py              # Menu interativo
  python main.py --gui        # Interface gráfica direta
  python main.py --cli        # Interface CLI direta
  python main.py --info       # Informações do sistema
        """
    )
    
    parser.add_argument('--gui', action='store_true',
                       help='Executa diretamente a interface gráfica')
    parser.add_argument('--cli', action='store_true',
                       help='Executa diretamente a interface CLI')
    parser.add_argument('--info', action='store_true',
                       help='Mostra informações do sistema e sai')
    parser.add_argument('--no-admin-check', action='store_true',
                       help='Pula verificação de privilégios administrativos')
    parser.add_argument('--version', action='version', version='PyCheatEngine 1.0.0')
    
    return parser.parse_args()

def main():
    """Função principal do programa"""
    try:
        # Analisa argumentos
        args = parse_arguments()
        
        # Mostra banner
        show_banner()
        
        # Verifica dependências
        if not check_dependencies():
            print("\nInstale as dependências necessárias antes de continuar.")
            return 1
        
        # Verifica privilégios administrativos
        if not args.no_admin_check:
            if not check_admin_privileges():
                print("\n⚠️  AVISO: O programa não está sendo executado com privilégios administrativos!")
                print("Algumas funcionalidades podem não funcionar corretamente.")
                print("Para melhor experiência, execute como administrador.")
                
                if platform.system() == "Windows":
                    response = input("\nDeseja tentar executar como administrador? (s/N): ").lower()
                    if response in ['s', 'sim', 'y', 'yes']:
                        request_admin_privileges()
                        return 0
                else:
                    print(f"Execute: sudo python3 {sys.argv[0]}")
                
                response = input("\nContinuar mesmo assim? (s/N): ").lower()
                if response not in ['s', 'sim', 'y', 'yes']:
                    return 0
        
        # Execução baseada em argumentos
        if args.info:
            show_system_info()
            return 0
        elif args.gui:
            run_gui()
            return 0
        elif args.cli:
            run_cli()
            return 0
        
        # Menu principal interativo
        while True:
            choice = show_main_menu()
            
            if choice == '0':
                print("\nObrigado por usar o PyCheatEngine!")
                break
            elif choice == '1':
                run_gui()
            elif choice == '2':
                run_cli()
            elif choice == '3':
                show_system_info()
            elif choice == '4':
                is_admin = check_admin_privileges()
                print(f"\nPrivilégios Administrativos: {'✓ Sim' if is_admin else '✗ Não'}")
                if not is_admin:
                    print("Execute o programa como administrador para melhor funcionalidade.")
            elif choice == '5':
                show_help()
            
            # Pausa antes de mostrar o menu novamente
            if choice != '0':
                input("\nPressione Enter para continuar...")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido pelo usuário.")
        return 1
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        print("Se o problema persistir, verifique a instalação ou contate o suporte.")
        return 1

if __name__ == "__main__":
    # Define o título da janela do console no Windows
    if platform.system() == "Windows":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("PyCheatEngine v1.0.0")
        except:
            pass
    
    # Executa o programa principal
    exit_code = main()
    sys.exit(exit_code)
