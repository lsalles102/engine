
#!/usr/bin/env python3
"""
Teste de Anexação de Processos
Script para testar a funcionalidade de anexação do PyCheatEngine
"""

import os
import sys
import time
from memory import MemoryManager

def test_attachment():
    """Testa anexação a processos"""
    print("=== TESTE DE ANEXAÇÃO DE PROCESSOS ===\n")
    
    # Cria manager
    manager = MemoryManager()
    
    # Lista processos
    print("1. Listando processos disponíveis...")
    processes = manager.list_processes()
    
    if not processes:
        print("❌ Nenhum processo encontrado!")
        return
    
    print(f"✓ Encontrados {len(processes)} processos\n")
    
    # Mostra alguns processos
    print("Primeiros 10 processos:")
    for i, proc in enumerate(processes[:10]):
        print(f"  {i+1}. PID {proc['pid']}: {proc['name']}")
    
    # Testa anexação ao processo atual (Python)
    current_pid = os.getpid()
    print(f"\n2. Testando anexação ao processo atual (PID {current_pid})...")
    
    success = manager.attach_to_process(current_pid)
    
    if success:
        print("✅ Anexação bem-sucedida!")
        print(f"   - Process ID: {manager.process_id}")
        print(f"   - Is attached: {manager.is_attached()}")
        
        # Testa leitura básica
        print("\n3. Testando leitura de memória...")
        try:
            # Tenta ler alguns endereços
            test_addresses = [0x400000, 0x10000000, 0x7FFE0000]
            
            for addr in test_addresses:
                data = manager.read_memory(addr, 4)
                if data:
                    print(f"   ✓ Leitura em 0x{addr:X}: {len(data)} bytes")
                    break
            else:
                print("   ⚠️ Nenhum endereço de teste funcionou (normal)")
                
        except Exception as e:
            print(f"   ❌ Erro na leitura: {e}")
        
        manager.close()
        print("\n✅ Teste concluído com sucesso!")
        
    else:
        print("❌ Falha na anexação!")
        print("\nPossíveis soluções:")
        print("  • Execute como administrador")
        print("  • Verifique se não há antivírus bloqueando")
        print("  • Tente com outro processo")

if __name__ == "__main__":
    try:
        test_attachment()
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
