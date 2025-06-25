#!/usr/bin/env python3
"""
Script para compilar PyCheatEngine para executável
"""

import os
import sys
import subprocess
import shutil

def build_executable():
    """Compila o PyCheatEngine para executável usando PyInstaller"""
    
    print("=== Compilador PyCheatEngine para EXE ===")
    print("Preparando para criar executável...")
    
    # Verifica se PyInstaller está instalado
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} encontrado")
    except ImportError:
        print("Erro: PyInstaller não está instalado")
        print("Execute: pip install pyinstaller")
        return False
    
    # Define opções de compilação
    main_script = "main.py"
    app_name = "PyCheatEngine"
    
    # Comando PyInstaller com opções otimizadas
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",           # Arquivo único
        "--windowed",          # Sem console (GUI)
        "--name", app_name,    # Nome do executável
        "--icon=icon.ico",     # Ícone (se existir)
        "--add-data", "ui;ui", # Inclui pasta UI
        "--hidden-import", "tkinter",
        "--hidden-import", "psutil",
        "--hidden-import", "struct",
        "--hidden-import", "threading",
        "--clean",             # Limpa cache
        main_script
    ]
    
    # Remove --icon se não existir
    if not os.path.exists("icon.ico"):
        pyinstaller_cmd.remove("--icon=icon.ico")
    
    print(f"Comando: {' '.join(pyinstaller_cmd)}")
    print("Compilando... (isso pode levar alguns minutos)")
    
    try:
        # Executa PyInstaller
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Compilação concluída com sucesso!")
            
            # Verifica se o executável foi criado
            exe_path = os.path.join("dist", f"{app_name}.exe")
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"✓ Executável criado: {exe_path}")
                print(f"✓ Tamanho: {size_mb:.1f} MB")
                
                # Cria pasta de distribuição limpa
                dist_folder = "PyCheatEngine_Portable"
                if os.path.exists(dist_folder):
                    shutil.rmtree(dist_folder)
                os.makedirs(dist_folder)
                
                # Copia executável
                shutil.copy2(exe_path, os.path.join(dist_folder, f"{app_name}.exe"))
                
                # Cria arquivos de documentação
                create_documentation(dist_folder)
                
                print(f"✓ Pacote criado em: {dist_folder}/")
                print("\nArquivos incluídos:")
                for file in os.listdir(dist_folder):
                    print(f"  - {file}")
                
                return True
            else:
                print("✗ Erro: Executável não foi criado")
                return False
        else:
            print("✗ Erro na compilação:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def create_documentation(dist_folder):
    """Cria documentação para o pacote distribuível"""
    
    # README.txt
    readme_content = """PyCheatEngine v1.0.0
====================

Sistema de Engenharia Reversa e Manipulação de Memória em Python

FUNCIONALIDADES:
• Scanner de memória com múltiplos tipos de dados
• Comparações avançadas (exato, aumentou, diminuiu, inalterado)
• Resolução de cadeias de ponteiros
• Scanner AOB (Array of Bytes) com wildcards
• Interface gráfica intuitiva
• Sistema de sessões para salvar/carregar estado

COMO USAR:
1. Execute PyCheatEngine.exe como Administrador
2. Selecione um processo na lista
3. Use as abas para diferentes funcionalidades:
   - Scanner: Busca valores na memória
   - Ponteiros: Resolve cadeias de ponteiros
   - AOB: Busca padrões de bytes

REQUISITOS:
• Windows 7/8/10/11
• Privilégios de Administrador (para acessar memória de outros processos)

AVISO LEGAL:
Este software é destinado apenas para fins educacionais e de pesquisa.
Use apenas em processos que você possui ou tem autorização para modificar.
O uso indevido pode violar termos de serviço ou leis locais.

DESENVOLVIDO POR: PyCheatEngine Team
VERSÃO: 1.0.0
"""
    
    with open(os.path.join(dist_folder, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # CHANGELOG.txt
    changelog_content = """CHANGELOG - PyCheatEngine
========================

v1.0.0 (2025-06-25)
-------------------
• Lançamento inicial
• Scanner de memória completo
• Suporte a múltiplos tipos de dados (int32, int64, float, string)
• Sistema de ponteiros com resolução automática
• Scanner AOB com wildcards (??)
• Interface gráfica com Tkinter
• Sistema de sessões (salvar/carregar)
• Calculadora hexadecimal integrada
• Conversor de tipos de dados
• Suporte multiplataforma (Windows/Linux)
• Demonstração funcional incluída
"""
    
    with open(os.path.join(dist_folder, "CHANGELOG.txt"), "w", encoding="utf-8") as f:
        f.write(changelog_content)

def build_demo_exe():
    """Compila versão de demonstração"""
    
    print("\n=== Compilando Versão de Demonstração ===")
    
    demo_cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "PyCheatEngine_Demo",
        "--hidden-import", "tkinter",
        "--clean",
        "demo_app.py"
    ]
    
    try:
        result = subprocess.run(demo_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Demo compilado com sucesso!")
            
            demo_exe = os.path.join("dist", "PyCheatEngine_Demo.exe")
            if os.path.exists(demo_exe):
                size_mb = os.path.getsize(demo_exe) / (1024 * 1024)
                print(f"✓ Demo criado: {demo_exe}")
                print(f"✓ Tamanho: {size_mb:.1f} MB")
                return True
        else:
            print("✗ Erro na compilação do demo:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def main():
    """Função principal"""
    print("Escolha uma opção:")
    print("1. Compilar PyCheatEngine completo")
    print("2. Compilar apenas demonstração")
    print("3. Compilar ambos")
    
    choice = input("Opção (1-3): ").strip()
    
    success = False
    
    if choice == "1":
        success = build_executable()
    elif choice == "2":
        success = build_demo_exe()
    elif choice == "3":
        success1 = build_executable()
        success2 = build_demo_exe()
        success = success1 and success2
    else:
        print("Opção inválida")
        return
    
    if success:
        print("\n✓ Compilação concluída!")
        print("\nOs executáveis estão na pasta 'dist/'")
        print("Para distribuir, use os arquivos da pasta 'PyCheatEngine_Portable/'")
    else:
        print("\n✗ Falha na compilação")

if __name__ == "__main__":
    main()