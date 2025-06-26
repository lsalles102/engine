#!/usr/bin/env python3
"""
Gerador de executável simplificado para PyCheatEngine
"""
import os
import sys
import zipfile
import shutil
import subprocess

def criar_executavel_simples():
    """Cria executável usando método básico"""
    print("=== Criando Executável PyCheatEngine ===")

    # Instala PyInstaller se necessário
    try:
        import PyInstaller
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Comando básico
    comando = [
        'pyinstaller',
        '--onefile',
        '--name=PyCheatEngine_Simple',
        'main.py'
    ]

    try:
        print("Compilando...")
        resultado = subprocess.run(comando, check=True)
        print("✓ Executável criado com sucesso!")

        # Verifica se foi criado
        exe_path = "dist/PyCheatEngine_Simple.exe"
        if os.path.exists(exe_path):
            tamanho = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"Arquivo: {exe_path} ({tamanho:.1f} MB)")

        return True

    except subprocess.CalledProcessError:
        print("❌ Erro na compilação")
        return False

def criar_pacote_distribuicao():
    """Cria pacote ZIP para distribuição"""
    print("\n=== Criando Pacote de Distribuição ===")

    nome_zip = "PyCheatEngine_v1.0.0.zip"

    with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Adiciona arquivos principais
        arquivos = [
            'main.py',
            'memory.py',
            'scanner.py',
            'pointer.py',
            'aob_scan.py',
            'README_PT.md'
        ]

        for arquivo in arquivos:
            if os.path.exists(arquivo):
                zipf.write(arquivo)
                print(f"✓ Adicionado: {arquivo}")

        # Adiciona pasta UI
        if os.path.exists('ui'):
            for root, dirs, files in os.walk('ui'):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path)
                    print(f"✓ Adicionado: {file_path}")

    print(f"✓ Pacote criado: {nome_zip}")

def main():
    """Função principal"""
    print("🔧 GERADOR DE EXECUTÁVEL PyCheatEngine")
    print("=" * 40)

    # Cria executável
    if criar_executavel_simples():
        print("\n✅ Executável criado com sucesso!")

        # Cria pacote
        criar_pacote_distribuicao()

        print("\n🎉 PROCESSO CONCLUÍDO!")
        print("Arquivos gerados:")
        print("- dist/PyCheatEngine_Simple.exe")
        print("- PyCheatEngine_v1.0.0.zip")
    else:
        print("\n❌ Falha na criação do executável")

if __name__ == "__main__":
    main()