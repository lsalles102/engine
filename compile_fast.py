#!/usr/bin/env python3
"""
Compilador rápido para PyCheatEngine
"""
import subprocess
import sys
import os

def compile_exe():
    """Compila PyCheatEngine usando método otimizado"""
    
    print("=== Compilando PyCheatEngine para EXE ===")
    
    # Comando simplificado e otimizado
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",  # Console para debug
        "--name", "PyCheatEngine_Demo",
        "--distpath", "./",  # Salva no diretório atual
        "--noconfirm",
        "--log-level", "WARN",  # Menos output
        "demo_app.py"
    ]
    
    print("Executando compilação...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Compilação concluída!")
            
            exe_file = "PyCheatEngine_Demo.exe"
            if os.path.exists(exe_file):
                size = os.path.getsize(exe_file) / (1024*1024)
                print(f"✓ Executável criado: {exe_file} ({size:.1f} MB)")
                return True
            else:
                print("✗ Arquivo executável não encontrado")
                
        else:
            print(f"✗ Erro na compilação:\n{result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("✗ Compilação interrompida por timeout")
        
    except Exception as e:
        print(f"✗ Erro: {e}")
    
    return False

if __name__ == "__main__":
    compile_exe()