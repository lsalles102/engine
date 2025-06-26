
#!/usr/bin/env python3
"""
Script simplificado para compilar PyCheatEngine
"""
import subprocess
import os
import sys

def compile_pycheatengine():
    """Compila PyCheatEngine para executáveis"""
    
    print("=== Compilando PyCheatEngine para EXE ===\n")
    
    # Verifica se PyInstaller está instalado
    try:
        import PyInstaller
        print("✓ PyInstaller encontrado")
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 1. Compila demonstração (GUI)
    print("1. Compilando PyCheatEngine_Demo.exe...")
    demo_cmd = [
        "pyinstaller", 
        "--onefile", 
        "--windowed", 
        "--name", "PyCheatEngine_Demo",
        "--clean",
        "demo_app.py"
    ]
    
    result1 = subprocess.run(demo_cmd, capture_output=True, text=True)
    if result1.returncode == 0:
        print("✓ Demo compilado com sucesso!")
    else:
        print(f"✗ Erro no demo: {result1.stderr}")
    
    # 2. Compila versão principal (console)
    print("\n2. Compilando PyCheatEngine.exe...")
    main_cmd = [
        "pyinstaller",
        "--onefile",
        "--console", 
        "--name", "PyCheatEngine",
        "--clean",
        "main.py"
    ]
    
    result2 = subprocess.run(main_cmd, capture_output=True, text=True)
    if result2.returncode == 0:
        print("✓ Versão principal compilada!")
    else:
        print(f"✗ Erro na compilação: {result2.stderr}")
    
    # 3. Verifica resultados
    print("\n=== Resultados ===")
    
    demo_exe = "dist/PyCheatEngine_Demo.exe"
    main_exe = "dist/PyCheatEngine.exe"
    
    if os.path.exists(demo_exe):
        size = os.path.getsize(demo_exe) / (1024*1024)
        print(f"✓ {demo_exe} ({size:.1f} MB)")
    
    if os.path.exists(main_exe):
        size = os.path.getsize(main_exe) / (1024*1024)
        print(f"✓ {main_exe} ({size:.1f} MB)")

if __name__ == "__main__":
    compile_pycheatengine()
