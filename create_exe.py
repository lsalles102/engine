#!/usr/bin/env python3
"""
Gerador de executável simplificado para PyCheatEngine
"""
import os
import sys
import zipfile
import shutil

def create_portable_exe():
    """Cria versão portável do PyCheatEngine"""
    
    print("=== Criando PyCheatEngine Portável ===")
    
    # Criar diretório de distribuição
    dist_dir = "PyCheatEngine_Portable"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Criar script de inicialização
    launcher_script = f"""#!/usr/bin/env python3
import sys
import os

# Adiciona diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Importa e executa o PyCheatEngine
    from pycheatengine_standalone import main
    main()
except ImportError as e:
    print(f"Erro: {{e}}")
    print("Certifique-se de que o Python está instalado corretamente.")
    input("Pressione Enter para sair...")
except Exception as e:
    print(f"Erro na execução: {{e}}")
    input("Pressione Enter para sair...")
"""
    
    # Salvar launcher
    with open(os.path.join(dist_dir, "PyCheatEngine.py"), "w", encoding="utf-8") as f:
        f.write(launcher_script)
    
    # Copiar arquivo principal
    shutil.copy2("pycheatengine_standalone.py", dist_dir)
    
    # Criar arquivo batch para Windows
    batch_content = """@echo off
title PyCheatEngine
echo Iniciando PyCheatEngine...
echo.

python PyCheatEngine.py

if errorlevel 1 (
    echo.
    echo Erro: Python não encontrado ou erro na execução
    echo Certifique-se de que o Python está instalado
    echo.
    pause
)
"""
    
    with open(os.path.join(dist_dir, "PyCheatEngine.bat"), "w", encoding="utf-8") as f:
        f.write(batch_content)
    
    # Criar README
    readme_content = """PyCheatEngine - Memory Scanner
=============================

COMO USAR:
----------
Windows: Execute PyCheatEngine.bat
Linux/Mac: Execute python PyCheatEngine.py

REQUISITOS:
-----------
- Python 3.7 ou superior
- Tkinter (geralmente incluído com Python)

FUNCIONALIDADES:
----------------
• Scanner de memória em tempo real
• Busca por valores específicos
• Comparações (aumentou, diminuiu, inalterado)
• Modificação de valores na memória
• Interface gráfica intuitiva

DEMONSTRAÇÃO:
-------------
Esta versão simula um processo de jogo com valores que mudam
automaticamente para demonstrar as funcionalidades do scanner.

Valores de exemplo:
- HP: 100 (endereço 0x400000)
- MP: 50 (endereço 0x400004) 
- Score: varia (endereço 0x400008)
- Speed: ~5.5 (endereço 0x40000C)

COMO TESTAR:
------------
1. Digite um valor (ex: 100) e clique "Primeiro Scan"
2. Aguarde alguns segundos para valores mudarem
3. Use "Aumentou", "Diminuiu" ou "Inalterado" para filtrar
4. Selecione um resultado e digite novo valor para modificar

AVISO:
------
Esta é uma versão educacional. Use responsavelmente e apenas
em processos que você possui ou tem autorização para modificar.

Desenvolvido por: PyCheatEngine Team
Versão: 1.0.0
"""
    
    with open(os.path.join(dist_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Criar script shell para Linux/Mac
    shell_content = """#!/bin/bash
echo "Iniciando PyCheatEngine..."
python3 PyCheatEngine.py
"""
    
    shell_file = os.path.join(dist_dir, "PyCheatEngine.sh")
    with open(shell_file, "w", encoding="utf-8") as f:
        f.write(shell_content)
    
    # Tornar executável no Linux/Mac
    try:
        os.chmod(shell_file, 0o755)
    except:
        pass
    
    print(f"✓ Pacote portável criado em: {dist_dir}/")
    print("\nArquivos incluídos:")
    for file in os.listdir(dist_dir):
        print(f"  - {file}")
    
    print(f"\nPara usar:")
    print(f"  Windows: Execute {dist_dir}/PyCheatEngine.bat")
    print(f"  Linux/Mac: Execute {dist_dir}/PyCheatEngine.sh")
    
    # Criar arquivo ZIP para distribuição
    zip_file = "PyCheatEngine_v1.0.0.zip"
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, os.path.dirname(dist_dir))
                zipf.write(file_path, arc_path)
    
    zip_size = os.path.getsize(zip_file) / 1024
    print(f"✓ Arquivo ZIP criado: {zip_file} ({zip_size:.1f} KB)")
    
    return True

if __name__ == "__main__":
    create_portable_exe()