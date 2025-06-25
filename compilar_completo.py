#!/usr/bin/env python3
"""
Compilador Completo e Automático para PyCheatEngine
Versão simplificada e funcional para criar executáveis
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def instalar_dependencias():
    """Instala PyInstaller se não estiver disponível"""
    try:
        import PyInstaller
        print("✓ PyInstaller já instalado")
        return True
    except ImportError:
        print("Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller instalado com sucesso")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erro ao instalar PyInstaller")
            return False

def limpar_arquivos():
    """Remove arquivos de build anteriores"""
    dirs_para_remover = ['build', 'dist', '__pycache__']
    arquivos_spec = list(Path('.').glob('*.spec'))
    
    for dir_name in dirs_para_remover:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Removido: {dir_name}")
    
    for spec_file in arquivos_spec:
        spec_file.unlink()
        print(f"✓ Removido: {spec_file}")

def compilar_executavel():
    """Compila o executável principal"""
    print("\n=== COMPILANDO PyCheatEngine.exe ===")
    
    # Comando básico que funciona na maioria dos casos
    comando = [
        'pyinstaller',
        '--onefile',                    # Arquivo único
        '--name=PyCheatEngine',         # Nome do executável
        '--console',                    # Mantém console para debug
        '--add-data=ui;ui',            # Inclui pasta ui
        '--hidden-import=tkinter',      # Import explícito do tkinter
        '--hidden-import=psutil',       # Import explícito do psutil
        '--hidden-import=ctypes',       # Import explícito do ctypes
        '--hidden-import=struct',       # Import explícito do struct
        '--hidden-import=threading',    # Import explícito do threading
        'main.py'                      # Arquivo principal
    ]
    
    try:
        print("Executando PyInstaller...")
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Compilação concluída com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na compilação:")
        print(f"Comando: {' '.join(comando)}")
        if e.stdout:
            print(f"Saída: {e.stdout}")
        if e.stderr:
            print(f"Erro: {e.stderr}")
        return False

def compilar_web_demo():
    """Compila também o web demo"""
    print("\n=== COMPILANDO PyCheatEngine_WebDemo.exe ===")
    
    comando = [
        'pyinstaller',
        '--onefile',
        '--name=PyCheatEngine_WebDemo',
        '--console',
        '--hidden-import=flask',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--add-data=templates;templates',
        'web_demo.py'
    ]
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print("✓ Web demo compilado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao compilar web demo: {e}")
        return False

def mostrar_resultados():
    """Mostra os arquivos gerados"""
    print("\n" + "="*50)
    print("ARQUIVOS GERADOS")
    print("="*50)
    
    if os.path.exists('dist'):
        executaveis = []
        for arquivo in os.listdir('dist'):
            if arquivo.endswith('.exe'):
                caminho_completo = os.path.join('dist', arquivo)
                tamanho = os.path.getsize(caminho_completo) / (1024*1024)
                executaveis.append((arquivo, tamanho))
                print(f"✓ {arquivo} ({tamanho:.1f} MB)")
        
        if executaveis:
            print(f"\n📁 Localização: {os.path.abspath('dist')}")
            print("\nPara usar:")
            for nome, _ in executaveis:
                print(f"   .\\dist\\{nome}")
        else:
            print("❌ Nenhum executável encontrado")
    else:
        print("❌ Pasta dist não foi criada")

def criar_arquivo_lancamento():
    """Cria arquivo .bat para lançamento rápido"""
    bat_content = '''@echo off
title PyCheatEngine
echo Iniciando PyCheatEngine...
echo.
.\\dist\\PyCheatEngine.exe
pause
'''
    
    with open('executar.bat', 'w') as f:
        f.write(bat_content)
    
    print("✓ Arquivo executar.bat criado")

def main():
    """Função principal"""
    print("PyCheatEngine - Compilador Automático")
    print("="*40)
    
    # Verifica e instala dependências
    if not instalar_dependencias():
        return
    
    # Limpa arquivos anteriores
    print("\nLimpando arquivos anteriores...")
    limpar_arquivos()
    
    # Compila executável principal
    sucesso_principal = compilar_executavel()
    
    # Compila web demo se o principal funcionou
    sucesso_web = False
    if sucesso_principal and os.path.exists('web_demo.py'):
        sucesso_web = compilar_web_demo()
    
    # Cria arquivo de lançamento
    if sucesso_principal:
        criar_arquivo_lancamento()
    
    # Mostra resultados
    mostrar_resultados()
    
    # Resumo final
    print(f"\nResumo:")
    print(f"PyCheatEngine principal: {'✓ Sucesso' if sucesso_principal else '❌ Falhou'}")
    if os.path.exists('web_demo.py'):
        print(f"Web Demo: {'✓ Sucesso' if sucesso_web else '❌ Falhou'}")
    
    if sucesso_principal:
        print(f"\n🎉 Compilação concluída! Execute: .\\dist\\PyCheatEngine.exe")
    else:
        print(f"\n❌ Falha na compilação. Verifique os erros acima.")

if __name__ == "__main__":
    main()