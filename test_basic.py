
#!/usr/bin/env python3
"""
Teste básico para verificar se o PyCheatEngine está funcionando
"""

def test_imports():
    """Testa imports básicos"""
    print("Testando imports...")
    
    try:
        import psutil
        print("✓ psutil OK")
    except ImportError:
        print("❌ psutil faltando")
        return False
        
    try:
        from memory import MemoryManager
        print("✓ MemoryManager OK")
    except ImportError as e:
        print(f"❌ MemoryManager erro: {e}")
        return False
        
    try:
        from scanner import MemoryScanner, DataType, ScanType
        print("✓ MemoryScanner OK")
    except ImportError as e:
        print(f"❌ MemoryScanner erro: {e}")
        return False
        
    return True

def test_basic_functionality():
    """Testa funcionalidade básica"""
    print("\nTestando funcionalidade básica...")
    
    try:
        from memory import MemoryManager
        from scanner import MemoryScanner, DataType, ScanType
        
        # Testa criação de objetos
        memory_mgr = MemoryManager()
        scanner = MemoryScanner(memory_mgr)
        
        print("✓ Objetos criados com sucesso")
        
        # Testa lista de processos
        processes = MemoryManager.list_processes()
        print(f"✓ Encontrados {len(processes)} processos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Função principal de teste"""
    print("=== Teste Básico PyCheatEngine ===\n")
    
    if not test_imports():
        print("\n❌ Falha nos imports")
        return False
        
    if not test_basic_functionality():
        print("\n❌ Falha na funcionalidade")
        return False
        
    print("\n✅ Todos os testes passaram!")
    print("PyCheatEngine está funcionando corretamente.")
    return True

if __name__ == "__main__":
    main()
