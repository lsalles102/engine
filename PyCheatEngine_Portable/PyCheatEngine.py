#!/usr/bin/env python3
import sys
import os

# Adiciona diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Importa e executa o PyCheatEngine
    from pycheatengine_standalone import main
    main()
except ImportError as e:
    print(f"Erro: {e}")
    print("Certifique-se de que o Python está instalado corretamente.")
    input("Pressione Enter para sair...")
except Exception as e:
    print(f"Erro na execução: {e}")
    input("Pressione Enter para sair...")
