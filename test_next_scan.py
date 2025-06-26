
#!/usr/bin/env python3
"""
Teste específico para verificar se next_scan está funcionando
"""

import time
from memory import MemoryManager
from scanner import MemoryScanner, DataType, ScanType

def test_next_scan():
    """Testa funcionalidade de next_scan"""
    print("=== Teste Next Scan ===\n")
    
    # Lista processos
    processes = MemoryManager.list_processes()
    print("Processos disponíveis:")
    for i, proc in enumerate(processes[:10]):
        print(f"{i+1}. {proc['name']} (PID: {proc['pid']})")
    
    # Solicita PID
    try:
        choice = input("\nEscolha um processo (número ou PID): ").strip()
        
        if choice.isdigit() and int(choice) <= len(processes):
            # Escolha por número
            pid = processes[int(choice)-1]['pid']
        else:
            # PID direto
            pid = int(choice)
        
        # Conecta ao processo
        mem = MemoryManager()
        if not mem.attach_to_process(pid):
            print("Falha ao conectar ao processo")
            return
        
        scanner = MemoryScanner(mem)
        
        # Primeiro scan
        print(f"\n1. Executando first_scan...")
        try:
            value = int(input("Digite um valor para buscar: "))
            results = scanner.first_scan(value, DataType.INT32, ScanType.EXACT)
            print(f"   Encontrados: {len(results)} resultados")
            
            if len(results) == 0:
                print("   Nenhum resultado encontrado. Tente outro valor.")
                return
            
            # Mostra alguns resultados
            print("   Primeiros resultados:")
            for i, result in enumerate(results[:5]):
                print(f"   {i+1}. 0x{result.address:X} = {result.value}")
        
        except ValueError:
            print("Valor inválido")
            return
        
        # Aguarda mudança
        input(f"\n2. Mude o valor no processo e pressione Enter...")
        
        # Próximo scan - teste diferentes tipos
        scan_types = [
            (ScanType.CHANGED, "CHANGED", None),
            (ScanType.INCREASED, "INCREASED", None),
            (ScanType.DECREASED, "DECREASED", None),
            (ScanType.EXACT, "EXACT", None)
        ]
        
        for scan_type, name, test_value in scan_types:
            print(f"\n3. Testando {name} scan...")
            
            if scan_type == ScanType.EXACT:
                try:
                    test_value = int(input(f"   Digite o novo valor: "))
                except ValueError:
                    continue
            
            original_count = len(scanner.scan_results)
            results = scanner.next_scan(test_value, scan_type)
            new_count = len(results)
            
            print(f"   Antes: {original_count} resultados")
            print(f"   Depois: {new_count} resultados")
            print(f"   Filtrados: {original_count - new_count}")
            
            if new_count > 0:
                print("   Resultados restantes:")
                for i, result in enumerate(results[:3]):
                    prev_val = getattr(result, 'previous_value', 'N/A')
                    print(f"   {i+1}. 0x{result.address:X}: {prev_val} -> {result.value}")
            
            if new_count > 0:
                break  # Para no primeiro tipo que funciona
        
        print(f"\nTeste concluído!")
        
    except KeyboardInterrupt:
        print("\nTeste cancelado")
    except Exception as e:
        print(f"Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_next_scan()
