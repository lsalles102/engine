#!/usr/bin/env python3
"""
Script para compilar PyCheatEngine para executável
"""

import os
import sys
import subprocess
import shutil

def instalar_pyinstaller():
    """Instala PyInstaller se necessário"""
    try:
        import PyInstaller
        print("✓ PyInstaller já está instalado")
        return True
    except ImportError:
        print("Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller instalado com sucesso")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar PyInstaller: {e}")
            return False

def limpar_build():
    """Remove arquivos de build anteriores"""
    dirs_para_remover = ['build', 'dist']

    for dir_name in dirs_para_remover:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Removido: {dir_name}")

def compilar_demo():
    """Compila a versão demo"""
    print("\n=== Compilando Demo ===")

    comando = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=PyCheatEngine_Demo',
        '--clean',
        'demo_app.py'
    ]

    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Demo compilado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação do demo: {e}")
        return False

def compilar_principal():
    """Compila a versão principal"""
    print("\n=== Compilando Versão Principal ===")

    comando = [
        'pyinstaller',
        '--onefile',
        '--console',
        '--name=PyCheatEngine',
        '--clean',
        'main.py'
    ]

    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Versão principal compilada com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação principal: {e}")
        return False

def verificar_resultados():
    """Verifica os executáveis gerados"""
    print("\n=== Verificando Resultados ===")

    executaveis = [
        'dist/PyCheatEngine_Demo.exe',
        'dist/PyCheatEngine.exe'
    ]

    for exe in executaveis:
        if os.path.exists(exe):
            tamanho = os.path.getsize(exe) / (1024 * 1024)
            print(f"✓ {exe} ({tamanho:.1f} MB)")
        else:
            print(f"❌ {exe} não encontrado")

def main():
    """Função principal"""
    print("=== Build PyCheatEngine ===")

    if not instalar_pyinstaller():
        return False

    limpar_build()

    sucesso_demo = compilar_demo()
    sucesso_principal = compilar_principal()

    if sucesso_demo or sucesso_principal:
        verificar_resultados()
        print("\n✅ Build concluído!")
    else:
        print("\n❌ Falha no build")

    return sucesso_demo or sucesso_principal

if __name__ == "__main__":
    main()