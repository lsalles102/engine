#!/usr/bin/env python3
"""
Script para compilar PyCheatEngine para executável .exe
Automatiza o processo de criação de executáveis usando PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def verificar_pyinstaller():
    """Verifica se PyInstaller está instalado"""
    try:
        import PyInstaller
        print("✓ PyInstaller encontrado")
        return True
    except ImportError:
        print("❌ PyInstaller não encontrado")
        print("Instale com: pip install pyinstaller")
        return False

def limpar_builds():
    """Remove diretórios de build anteriores"""
    dirs_para_remover = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_para_remover:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Removido diretório: {dir_name}")
    
    # Remove arquivos .spec antigos
    for spec_file in Path('.').glob('*.spec'):
        if spec_file.name != 'PyCheatEngine_Demo.spec':
            spec_file.unlink()
            print(f"✓ Removido arquivo: {spec_file}")

def compilar_gui():
    """Compila a versão GUI para executável"""
    print("\n=== COMPILANDO VERSÃO GUI ===")
    
    comando = [
        'pyinstaller',
        '--onefile',           # Um único arquivo executável
        '--windowed',          # Sem console (apenas para GUI)
        '--name=PyCheatEngine_GUI',
        '--icon=icon.ico',     # Ícone (se existir)
        '--add-data=ui;ui',    # Inclui diretório ui
        '--hidden-import=tkinter',
        '--hidden-import=psutil',
        '--hidden-import=ctypes',
        '--distpath=dist/gui',
        'main.py'
    ]
    
    # Remove --icon se não existir
    if not os.path.exists('icon.ico'):
        comando.remove('--icon=icon.ico')
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Compilação GUI concluída com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação GUI: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def compilar_cli():
    """Compila a versão CLI para executável"""
    print("\n=== COMPILANDO VERSÃO CLI ===")
    
    comando = [
        'pyinstaller',
        '--onefile',           # Um único arquivo executável
        '--console',           # Com console (para CLI)
        '--name=PyCheatEngine_CLI',
        '--icon=icon.ico',     # Ícone (se existir)
        '--add-data=ui;ui',    # Inclui diretório ui
        '--hidden-import=psutil',
        '--hidden-import=ctypes',
        '--distpath=dist/cli',
        'main.py'
    ]
    
    # Remove --icon se não existir
    if not os.path.exists('icon.ico'):
        comando.remove('--icon=icon.ico')
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Compilação CLI concluída com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação CLI: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def compilar_standalone():
    """Compila versão standalone (sem dependências externas)"""
    print("\n=== COMPILANDO VERSÃO STANDALONE ===")
    
    comando = [
        'pyinstaller',
        '--onefile',
        '--console',
        '--name=PyCheatEngine_Standalone',
        '--icon=icon.ico',
        '--add-data=ui;ui',
        '--hidden-import=tkinter',
        '--hidden-import=psutil',
        '--hidden-import=ctypes',
        '--distpath=dist/standalone',
        'pycheatengine_standalone.py'
    ]
    
    # Remove --icon se não existir
    if not os.path.exists('icon.ico'):
        comando.remove('--icon=icon.ico')
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Compilação Standalone concluída com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação Standalone: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def criar_spec_personalizado():
    """Cria arquivo .spec personalizado para controle avançado"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui', 'ui')],
    hiddenimports=['tkinter', 'psutil', 'ctypes', 'struct', 'threading'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyCheatEngine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('PyCheatEngine_Custom.spec', 'w') as f:
        f.write(spec_content)
    
    print("✓ Arquivo .spec personalizado criado")

def compilar_com_spec():
    """Compila usando arquivo .spec personalizado"""
    print("\n=== COMPILANDO COM SPEC PERSONALIZADO ===")
    
    comando = ['pyinstaller', 'PyCheatEngine_Custom.spec', '--distpath=dist/custom']
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Compilação com spec personalizado concluída!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação com spec: {e}")
        return False

def criar_batch_compilacao():
    """Cria arquivo batch para compilação rápida no Windows"""
    batch_content = '''@echo off
echo Compilando PyCheatEngine...
echo.

echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo Compilando versao GUI...
pyinstaller --onefile --windowed --name=PyCheatEngine_GUI --add-data=ui;ui main.py

echo.
echo Compilando versao CLI...
pyinstaller --onefile --console --name=PyCheatEngine_CLI --add-data=ui;ui main.py

echo.
echo Compilacao concluida!
echo Executaveis disponiveis em: dist/
pause
'''
    
    with open('compilar.bat', 'w') as f:
        f.write(batch_content)
    
    print("✓ Arquivo compilar.bat criado")

def mostrar_resultados():
    """Mostra informações sobre os executáveis criados"""
    print("\n" + "="*60)
    print("RESULTADOS DA COMPILAÇÃO")
    print("="*60)
    
    if os.path.exists('dist'):
        for root, dirs, files in os.walk('dist'):
            for file in files:
                if file.endswith('.exe'):
                    filepath = os.path.join(root, file)
                    size = os.path.getsize(filepath) / (1024*1024)  # MB
                    print(f"✓ {file} - {size:.1f} MB")
                    print(f"  Localização: {filepath}")
        
        print(f"\n📁 Todos os executáveis estão na pasta: {os.path.abspath('dist')}")
    else:
        print("❌ Nenhum executável foi criado")

def main():
    """Função principal do compilador"""
    print("PyCheatEngine - Compilador para Executável")
    print("="*50)
    
    if not verificar_pyinstaller():
        return
    
    print("\nOpções de compilação:")
    print("1. Compilar versão GUI (interface gráfica)")
    print("2. Compilar versão CLI (linha de comando)")
    print("3. Compilar versão Standalone (independente)")
    print("4. Compilar com spec personalizado")
    print("5. Compilar todas as versões")
    print("6. Apenas criar arquivos de configuração")
    print("0. Sair")
    
    while True:
        try:
            opcao = input("\nEscolha uma opção (0-6): ").strip()
            
            if opcao == '0':
                print("Saindo...")
                break
            elif opcao == '1':
                limpar_builds()
                compilar_gui()
                mostrar_resultados()
                break
            elif opcao == '2':
                limpar_builds()
                compilar_cli()
                mostrar_resultados()
                break
            elif opcao == '3':
                limpar_builds()
                compilar_standalone()
                mostrar_resultados()
                break
            elif opcao == '4':
                limpar_builds()
                criar_spec_personalizado()
                compilar_com_spec()
                mostrar_resultados()
                break
            elif opcao == '5':
                limpar_builds()
                print("Compilando todas as versões...")
                
                sucesso_gui = compilar_gui()
                sucesso_cli = compilar_cli()
                sucesso_standalone = compilar_standalone()
                
                criar_spec_personalizado()
                sucesso_spec = compilar_com_spec()
                
                print(f"\nResultados:")
                print(f"GUI: {'✓' if sucesso_gui else '❌'}")
                print(f"CLI: {'✓' if sucesso_cli else '❌'}")
                print(f"Standalone: {'✓' if sucesso_standalone else '❌'}")
                print(f"Spec personalizado: {'✓' if sucesso_spec else '❌'}")
                
                mostrar_resultados()
                break
            elif opcao == '6':
                criar_spec_personalizado()
                criar_batch_compilacao()
                print("✓ Arquivos de configuração criados")
                break
            else:
                print("Opção inválida. Digite um número entre 0 e 6.")
                
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário.")
            break

if __name__ == "__main__":
    main()