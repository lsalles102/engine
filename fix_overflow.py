#!/usr/bin/env python3
"""
PyCheatEngine - Corretor de Problemas de Overflow
Script para diagnosticar e corrigir problemas de overflow no sistema
"""

import sys
import platform
import struct

def test_ctypes_limits():
    """Testa os limites do ctypes no sistema atual"""
    print("Testando limites do ctypes...")
    
    try:
        import ctypes
        
        # Testa valores de endereço
        test_addresses = [
            0x00400000,      # Endereço típico
            0x7FFFFFFF,      # Limite 32-bit
            0x7FFFFFFFFFFFFFFF,  # Limite 64-bit
        ]
        
        for addr in test_addresses:
            try:
                ptr = ctypes.c_void_p(addr)
                print(f"✓ Endereço 0x{addr:X} OK")
            except OverflowError:
                print(f"❌ Endereço 0x{addr:X} causa overflow")
                
        # Testa tamanhos
        test_sizes = [4, 1024, 4096, 65536]
        for size in test_sizes:
            try:
                buffer = ctypes.create_string_buffer(size)
                size_t = ctypes.c_size_t(size)
                print(f"✓ Tamanho {size} bytes OK")
            except OverflowError:
                print(f"❌ Tamanho {size} bytes causa overflow")
                
    except ImportError:
        print("❌ ctypes não disponível")

def test_struct_limits():
    """Testa os limites do módulo struct"""
    print("\nTestando limites do struct...")
    
    # Testa diferentes formatos
    test_values = [
        (100, '<i', 'int32'),
        (123456789012345, '<q', 'int64'),
        (99.5, '<f', 'float'),
        (123.456789, '<d', 'double'),
    ]
    
    for value, fmt, desc in test_values:
        try:
            packed = struct.pack(fmt, value)
            unpacked = struct.unpack(fmt, packed)[0]
            print(f"✓ {desc}: {value} -> {unpacked}")
        except (struct.error, OverflowError) as e:
            print(f"❌ {desc}: {value} -> Erro: {e}")

def get_system_info():
    """Obtém informações do sistema que podem afetar overflow"""
    print("\nInformações do Sistema:")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Machine: {platform.machine()}")
    print(f"Python: {sys.version}")
    print(f"Pointer size: {struct.calcsize('P')} bytes")
    
    # Verifica se é 32-bit ou 64-bit
    is_64bit = struct.calcsize('P') == 8
    print(f"Sistema: {'64-bit' if is_64bit else '32-bit'}")
    
    return is_64bit

def create_safe_limits(is_64bit):
    """Cria constantes seguras baseadas no sistema"""
    if is_64bit:
        max_address = 0x7FFFFFFFFFFFFFFF
        max_pointer = 0xFFFFFFFFFFFFFFFF
    else:
        max_address = 0x7FFFFFFF
        max_pointer = 0xFFFFFFFF
    
    safe_limits = f"""# Limites Seguros para o Sistema
# Gerado automaticamente por fix_overflow.py

import struct
import platform

# Detecta arquitetura
IS_64BIT = struct.calcsize('P') == 8
IS_32BIT = not IS_64BIT

# Limites seguros para endereços
if IS_64BIT:
    MAX_ADDRESS = 0x7FFFFFFFFFFFFFFF
    MAX_POINTER = 0xFFFFFFFFFFFFFFFF
    MIN_ADDRESS = 0x10000
    DEFAULT_END_ADDRESS = 0x7FFFFFFF  # Ainda usa limite 32-bit para compatibilidade
else:
    MAX_ADDRESS = 0x7FFFFFFF
    MAX_POINTER = 0xFFFFFFFF
    MIN_ADDRESS = 0x10000
    DEFAULT_END_ADDRESS = 0x7FFFFFFF

# Limites para operações
MAX_READ_SIZE = 0x10000  # 64KB
MAX_WRITE_SIZE = 0x10000  # 64KB
MAX_SCAN_RESULTS = 10000

def validate_address(address):
    \"\"\"Valida se um endereço está dentro dos limites seguros\"\"\"
    return MIN_ADDRESS <= address <= MAX_ADDRESS

def validate_size(size):
    \"\"\"Valida se um tamanho está dentro dos limites seguros\"\"\"
    return 0 < size <= MAX_READ_SIZE

def safe_address(address):
    \"\"\"Retorna um endereço seguro dentro dos limites\"\"\"
    return max(MIN_ADDRESS, min(MAX_ADDRESS, address))

def safe_size(size):
    \"\"\"Retorna um tamanho seguro dentro dos limites\"\"\"
    return max(1, min(MAX_READ_SIZE, size))
"""
    
    with open('safe_limits.py', 'w') as f:
        f.write(safe_limits)
    
    print(f"\n✓ Arquivo safe_limits.py criado com limites para sistema {'64-bit' if is_64bit else '32-bit'}")

def patch_memory_module():
    """Aplica patch no módulo memory.py para usar limites seguros"""
    print("\nAplicando patch no memory.py...")
    
    try:
        with open('memory.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adiciona import no início
        if 'from safe_limits import' not in content:
            import_line = "from safe_limits import validate_address, validate_size, safe_address, safe_size, MAX_ADDRESS, MAX_READ_SIZE\n"
            
            # Encontra onde inserir o import
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('from typing'):
                    insert_pos = i + 1
                    break
            
            lines.insert(insert_pos, import_line)
            content = '\n'.join(lines)
        
        # Backup do arquivo original
        with open('memory.py.backup', 'w', encoding='utf-8') as f:
            with open('memory.py', 'r', encoding='utf-8') as orig:
                f.write(orig.read())
        
        # Salva versão corrigida
        with open('memory.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ Patch aplicado com sucesso")
        print("✓ Backup criado como memory.py.backup")
        
    except Exception as e:
        print(f"❌ Erro ao aplicar patch: {e}")

def main():
    """Função principal do corretor"""
    print("PyCheatEngine - Corretor de Overflow")
    print("=" * 50)
    
    # Obtém informações do sistema
    is_64bit = get_system_info()
    
    # Testa limites
    test_ctypes_limits()
    test_struct_limits()
    
    # Cria constantes seguras
    create_safe_limits(is_64bit)
    
    # Oferece patch automático
    print("\n" + "=" * 50)
    response = input("Deseja aplicar patch automático no memory.py? (s/N): ")
    if response.lower() in ['s', 'sim', 'y', 'yes']:
        patch_memory_module()
    
    print("\n✅ Diagnóstico completo!")
    print("\nRecomendações:")
    print("1. Use os limites definidos em safe_limits.py")
    print("2. Sempre valide endereços antes de usar")
    print("3. Limite o tamanho de leituras/escritas")
    print("4. Use tratamento de exceção para OverflowError")

if __name__ == "__main__":
    main()