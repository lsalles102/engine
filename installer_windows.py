#!/usr/bin/env python3
"""
PyCheatEngine - Instalador e Configurador para Windows
Instala dependências e configura o ambiente automaticamente
"""

import os
import sys
import subprocess
import platform
import ctypes
from pathlib import Path

def is_admin():
    """Verifica se está executando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Executa o script como administrador"""
    if is_admin():
        return True
    else:
        print("Solicitando privilégios de administrador...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return False

def check_python():
    """Verifica a versão do Python"""
    print("Verificando Python...")
    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} não é suportado")
        print("   Necessário Python 3.8 ou superior")
        return False

    print(f"✓ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def install_dependencies():
    """Instala dependências necessárias"""
    print("\nInstalando dependências...")

    packages = ['psutil', 'pyinstaller']

    for package in packages:
        try:
            print(f"Instalando {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ], stdout=subprocess.DEVNULL)
            print(f"✓ {package} instalado")
        except subprocess.CalledProcessError:
            print(f"❌ Erro ao instalar {package}")
            return False

    return True

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("\nTestando imports...")

    try:
        import psutil
        print("✓ psutil OK")
    except ImportError:
        print("❌ psutil falhou")
        return False

    try:
        import tkinter
        print("✓ tkinter OK")
    except ImportError:
        print("❌ tkinter falhou")
        return False

    return True

def create_shortcuts():
    """Cria atalhos na área de trabalho"""
    print("\nCriando atalhos...")

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")

    # Atalho para versão GUI
    shortcut_content = f'''@echo off
cd /d "{os.getcwd()}"
python main.py --gui
pause'''

    shortcut_path = os.path.join(desktop, "PyCheatEngine_GUI.bat")

    try:
        with open(shortcut_path, 'w') as f:
            f.write(shortcut_content)
        print(f"✓ Atalho criado: {shortcut_path}")
    except Exception as e:
        print(f"❌ Erro ao criar atalho: {e}")

def main():
    """Função principal do instalador"""
    print("=" * 50)
    print("    INSTALADOR PyCheatEngine para Windows")
    print("=" * 50)

    # Verifica privilégios administrativos
    if not is_admin():
        print("⚠️  Executando sem privilégios administrativos")
        print("   Algumas funcionalidades podem não funcionar")
        input("Pressione Enter para continuar...")

    # Verifica Python
    if not check_python():
        input("Pressione Enter para sair...")
        return False

    # Instala dependências
    if not install_dependencies():
        print("\n❌ Falha na instalação de dependências")
        input("Pressione Enter para sair...")
        return False

    # Testa imports
    if not test_imports():
        print("\n❌ Falha nos testes de importação")
        input("Pressione Enter para sair...")
        return False

    # Cria atalhos
    create_shortcuts()

    print("\n" + "=" * 50)
    print("✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 50)
    print("\nComo usar:")
    print("1. Execute: python main.py")
    print("2. Ou use o atalho na área de trabalho")
    print("3. Para GUI: python main.py --gui")
    print("\n⚠️  IMPORTANTE: Execute como administrador para")
    print("   acessar memória de outros processos!")

    input("\nPressione Enter para sair...")
    return True

if __name__ == "__main__":
    main()