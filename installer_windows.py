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

def install_requirements():
    """Instala as dependências necessárias"""
    requirements = [
        'psutil>=7.0.0',
        'pyinstaller>=6.14.1',
        'auto-py-to-exe>=2.46.0'
    ]
    
    print("\nInstalando dependências...")
    
    for req in requirements:
        print(f"Instalando {req}...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', req
            ], capture_output=True, text=True, check=True)
            print(f"✓ {req} instalado com sucesso")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {req}: {e}")
            print(f"Saída: {e.stdout}")
            print(f"Erro: {e.stderr}")
            return False
    
    return True

def create_desktop_shortcut():
    """Cria atalho na área de trabalho"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "PyCheatEngine.lnk")
        target = os.path.join(os.getcwd(), "main.py")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}" --gui'
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        print("✓ Atalho criado na área de trabalho")
        return True
        
    except ImportError:
        print("! winshell não disponível, pulando criação de atalho")
        return True
    except Exception as e:
        print(f"! Erro ao criar atalho: {e}")
        return True

def configure_windows_defender():
    """Configura exclusões no Windows Defender"""
    try:
        current_dir = os.getcwd()
        
        # Comando para adicionar exclusão de pasta
        cmd = [
            'powershell', '-Command',
            f'Add-MpPreference -ExclusionPath "{current_dir}"'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Exclusão adicionada ao Windows Defender")
        else:
            print("! Não foi possível configurar Windows Defender automaticamente")
            print(f"  Adicione manualmente a pasta: {current_dir}")
        
    except Exception as e:
        print(f"! Erro ao configurar Windows Defender: {e}")

def create_batch_files():
    """Cria arquivos batch para execução fácil"""
    
    # Batch para GUI
    gui_batch = """@echo off
title PyCheatEngine - Interface Grafica
cd /d "%~dp0"
python main.py --gui
pause"""
    
    with open("PyCheatEngine_GUI.bat", "w") as f:
        f.write(gui_batch)
    
    # Batch para CLI
    cli_batch = """@echo off
title PyCheatEngine - Linha de Comando
cd /d "%~dp0"
python main.py --cli
pause"""
    
    with open("PyCheatEngine_CLI.bat", "w") as f:
        f.write(cli_batch)
    
    # Batch para compilação
    compile_batch = """@echo off
title PyCheatEngine - Compilador
cd /d "%~dp0"
python compilar_exe.py
pause"""
    
    with open("Compilar_EXE.bat", "w") as f:
        f.write(compile_batch)
    
    print("✓ Arquivos batch criados")

def setup_project_structure():
    """Configura a estrutura do projeto"""
    dirs_to_create = [
        "build",
        "dist",
        "temp_build"
    ]
    
    for dir_name in dirs_to_create:
        os.makedirs(dir_name, exist_ok=True)
    
    print("✓ Estrutura do projeto configurada")

def test_installation():
    """Testa se a instalação está funcionando"""
    print("\nTestando instalação...")
    
    try:
        # Testa import dos módulos principais
        import psutil
        print("✓ psutil funcionando")
        
        import tkinter
        print("✓ tkinter funcionando")
        
        # Testa módulos do projeto
        sys.path.insert(0, os.getcwd())
        from memory import MemoryManager
        print("✓ MemoryManager funcionando")
        
        from scanner import MemoryScanner
        print("✓ MemoryScanner funcionando")
        
        # Testa criação de objetos
        mem_manager = MemoryManager()
        print("✓ MemoryManager inicializado")
        
        processes = mem_manager.list_processes()
        print(f"✓ Encontrados {len(processes)} processos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal do instalador"""
    print("=" * 60)
    print("     PyCheatEngine - Instalador para Windows")
    print("=" * 60)
    print()
    
    # Verifica se é Windows
    if platform.system() != "Windows":
        print("❌ Este instalador é apenas para Windows")
        return 1
    
    # Verifica privilégios de admin
    if not is_admin():
        print("⚠️  Privilégios de administrador recomendados")
        response = input("Continuar sem privilégios de admin? (s/N): ")
        if response.lower() not in ['s', 'sim', 'y', 'yes']:
            if not run_as_admin():
                return 1
    
    print("🔧 Iniciando instalação...")
    
    # Verifica Python
    if not check_python():
        print("\n❌ Instalação falhou - Python inadequado")
        input("Pressione Enter para sair...")
        return 1
    
    # Instala dependências
    if not install_requirements():
        print("\n❌ Instalação falhou - Erro nas dependências")
        input("Pressione Enter para sair...")
        return 1
    
    # Configura projeto
    setup_project_structure()
    create_batch_files()
    
    # Configurações opcionais
    if is_admin():
        configure_windows_defender()
        create_desktop_shortcut()
    
    # Testa instalação
    if not test_installation():
        print("\n⚠️  Instalação concluída com avisos")
        input("Pressione Enter para continuar...")
    else:
        print("\n✅ Instalação concluída com sucesso!")
    
    print("\n" + "=" * 60)
    print("INSTRUÇÕES DE USO:")
    print("=" * 60)
    print("1. Execute 'PyCheatEngine_GUI.bat' para interface gráfica")
    print("2. Execute 'PyCheatEngine_CLI.bat' para linha de comando")
    print("3. Execute 'Compilar_EXE.bat' para criar executáveis")
    print("4. SEMPRE execute como Administrador para melhor funcionamento")
    print("=" * 60)
    
    input("\nPressione Enter para sair...")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInstalação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)