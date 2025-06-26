"""
Interface de Linha de Comando para PyCheatEngine
Implementa uma CLI simples para operações básicas
"""

import sys
import json
from typing import List, Optional

import sys
import os

# Adiciona o diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from memory import MemoryManager
    from scanner import MemoryScanner, ScanType, DataType
    from pointer import PointerResolver
    from aob_scan import AOBScanner
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)

class PyCheatEngineCLI:
    """Interface de linha de comando para PyCheatEngine"""
    
    def __init__(self, memory_manager=None):
        if memory_manager:
            self.memory_manager = memory_manager
        else:
            self.memory_manager = MemoryManager()
        self.memory_manager = MemoryManager()
        self.scanner = MemoryScanner(self.memory_manager)
        self.pointer_resolver = PointerResolver(self.memory_manager)
        self.aob_scanner = AOBScanner(self.memory_manager)
        
        self.current_process = None
        self.commands = {
            'help': self.show_help,
            'list': self.list_processes,
            'attach': self.attach_process,
            'detach': self.detach_process,
            'scan': self.perform_scan,
            'next': self.next_scan,
            'results': self.show_results,
            'write': self.write_value,
            'pointer': self.add_pointer,
            'aob': self.aob_scan,
            'save': self.save_session,
            'load': self.load_session,
            'clear': self.clear_results,
            'quit': self.quit_program,
            'exit': self.quit_program
        }
    
    def run(self):
        """Executa a interface CLI"""
        print("=== PyCheatEngine CLI ===")
        print("Digite 'help' para ver os comandos disponíveis")
        print()
        
        while True:
            try:
                command = input("PyCheatEngine> ").strip().lower()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                if cmd in self.commands:
                    try:
                        self.commands[cmd](args)
                    except Exception as e:
                        print(f"Erro ao executar comando: {e}")
                else:
                    print(f"Comando desconhecido: {cmd}")
                    print("Digite 'help' para ver os comandos disponíveis")
                
            except KeyboardInterrupt:
                print("\nSaindo...")
                break
            except EOFError:
                break
    
    def show_help(self, args):
        """Mostra ajuda dos comandos"""
        help_text = """
Comandos disponíveis:

Gerenciamento de Processos:
  list                    - Lista processos em execução
  attach <pid>           - Anexa ao processo com PID especificado
  detach                 - Desanexa do processo atual

Scanner de Memória:
  scan <tipo> <valor>    - Primeiro scan (tipos: int32, int64, float, double, string)
  next <tipo> [valor]    - Próximo scan (tipos: exact, increased, decreased, changed, unchanged)
  results [count]        - Mostra resultados (opcionalmente limita quantidade)
  write <index> <valor>  - Escreve valor no resultado pelo índice
  clear                  - Limpa resultados

Ponteiros:
  pointer <base> <offsets> [desc] - Adiciona ponteiro (ex: pointer 0x400000 0x10,0x20 "HP")

AOB Scanner:
  aob <pattern> [desc]   - Busca padrão de bytes (ex: aob "48 8B ?? ?? 89")

Sessões:
  save <arquivo>         - Salva sessão atual
  load <arquivo>         - Carrega sessão

Outros:
  help                   - Mostra esta ajuda
  quit/exit             - Sai do programa

Exemplos:
  attach 1234
  scan int32 100
  next decreased
  write 0 150
  pointer 0x400000 0x10,0x20 "Player HP"
  aob "48 8B 05 ?? ?? ?? ??"
        """
        print(help_text)
    
    def list_processes(self, args):
        """Lista processos em execução"""
        try:
            processes = MemoryManager.list_processes()
            
            print("\nProcessos em execução:")
            print("-" * 50)
            print(f"{'PID':<8} {'Nome'}")
            print("-" * 50)
            
            for proc in processes[:50]:  # Limita a 50 processos
                print(f"{proc['pid']:<8} {proc['name']}")
            
            if len(processes) > 50:
                print(f"... e mais {len(processes) - 50} processos")
            
            print(f"\nTotal: {len(processes)} processos")
            
        except Exception as e:
            print(f"Erro ao listar processos: {e}")
    
    def attach_process(self, args):
        """Anexa a um processo"""
        if not args:
            print("Uso: attach <pid>")
            return
        
        try:
            pid = int(args[0])
            
            if self.memory_manager.attach_to_process(pid):
                self.current_process = pid
                print(f"Anexado ao processo PID {pid} ({self.memory_manager.process_name})")
            else:
                print(f"Falha ao anexar ao processo PID {pid}")
                
        except ValueError:
            print("PID deve ser um número")
        except Exception as e:
            print(f"Erro ao anexar ao processo: {e}")
    
    def detach_process(self, args):
        """Desanexa do processo atual"""
        if not self.memory_manager.is_attached():
            print("Nenhum processo anexado")
            return
        
        process_name = self.memory_manager.process_name
        self.memory_manager.detach_process()
        self.scanner.clear_results()
        self.current_process = None
        
        print(f"Desanexado do processo {process_name}")
    
    def perform_scan(self, args):
        """Realiza primeiro scan"""
        if not self.memory_manager.is_attached():
            print("Anexe a um processo primeiro (use 'attach <pid>')")
            return
        
        if len(args) < 2:
            print("Uso: scan <tipo> <valor>")
            print("Tipos: int32, int64, float, double, string")
            return
        
        try:
            data_type_str = args[0].lower()
            value_str = args[1]
            
            # Valida tipo de dado
            if data_type_str not in ['int32', 'int64', 'float', 'double', 'string']:
                print("Tipo inválido. Use: int32, int64, float, double, string")
                return
            
            data_type = DataType(data_type_str)
            
            # Converte valor
            if data_type in [DataType.INT32, DataType.INT64]:
                value = int(value_str)
            elif data_type in [DataType.FLOAT, DataType.DOUBLE]:
                value = float(value_str)
            else:
                value = value_str
            
            print(f"Iniciando scan para {data_type_str}: {value}")
            
            # Configura callback de progresso
            def progress_callback(progress):
                if progress % 10 == 0:  # Mostra a cada 10%
                    print(f"Progresso: {progress}%")
            
            self.scanner.set_progress_callback(progress_callback)
            
            # Executa scan
            results = self.scanner.first_scan(value, data_type, ScanType.EXACT)
            
            print(f"\nScan completado: {len(results)} resultados encontrados")
            
            if len(results) > 0:
                print("Use 'results' para ver os resultados ou 'next' para próximo scan")
            
        except ValueError as e:
            print(f"Valor inválido: {e}")
        except Exception as e:
            print(f"Erro durante scan: {e}")
    
    def next_scan(self, args):
        """Realiza próximo scan"""
        if not self.memory_manager.is_attached():
            print("Anexe a um processo primeiro")
            return
        
        if not self.scanner.scan_results:
            print("Execute um primeiro scan antes")
            return
        
        if not args:
            print("Uso: next <tipo> [valor]")
            print("Tipos: exact, increased, decreased, changed, unchanged, greater_than, less_than")
            return
        
        try:
            scan_type_str = args[0].lower()
            
            # Valida tipo de scan
            valid_types = ['exact', 'increased', 'decreased', 'changed', 'unchanged', 'greater_than', 'less_than']
            if scan_type_str not in valid_types:
                print(f"Tipo inválido. Use: {', '.join(valid_types)}")
                return
            
            scan_type = ScanType(scan_type_str)
            
            # Obtém valor se necessário
            value = None
            if scan_type in [ScanType.EXACT, ScanType.GREATER_THAN, ScanType.LESS_THAN]:
                if len(args) < 2:
                    print(f"Tipo '{scan_type_str}' requer um valor")
                    return
                
                value_str = args[1]
                
                # Determina tipo de dado dos resultados existentes
                if self.scanner.scan_results:
                    data_type = self.scanner.scan_results[0].data_type
                    
                    if data_type in [DataType.INT32, DataType.INT64]:
                        value = int(value_str)
                    elif data_type in [DataType.FLOAT, DataType.DOUBLE]:
                        value = float(value_str)
                    else:
                        value = value_str
            
            print(f"Iniciando próximo scan: {scan_type_str}")
            
            # Configura callback de progresso
            def progress_callback(progress):
                if progress % 20 == 0:  # Mostra a cada 20%
                    print(f"Progresso: {progress}%")
            
            self.scanner.set_progress_callback(progress_callback)
            
            # Executa scan
            results = self.scanner.next_scan(value, scan_type)
            
            print(f"\nNext scan completado: {len(results)} resultados restantes")
            
        except ValueError as e:
            print(f"Valor inválido: {e}")
        except Exception as e:
            print(f"Erro durante next scan: {e}")
    
    def show_results(self, args):
        """Mostra resultados do scan"""
        if not self.scanner.scan_results:
            print("Nenhum resultado de scan disponível")
            return
        
        # Determina quantos resultados mostrar
        max_results = 20
        if args:
            try:
                max_results = int(args[0])
            except ValueError:
                print("Número inválido para quantidade de resultados")
                return
        
        results = self.scanner.scan_results[:max_results]
        total = len(self.scanner.scan_results)
        
        print(f"\nResultados do scan (mostrando {len(results)} de {total}):")
        print("-" * 60)
        print(f"{'#':<3} {'Endereço':<12} {'Valor':<15} {'Tipo'}")
        print("-" * 60)
        
        for i, result in enumerate(results):
            print(f"{i:<3} 0x{result.address:08X}  {str(result.value):<15} {result.data_type.value}")
        
        if total > max_results:
            print(f"\n... e mais {total - max_results} resultados")
            print("Use 'results <número>' para ver mais resultados")
    
    def write_value(self, args):
        """Escreve valor em um resultado"""
        if not self.scanner.scan_results:
            print("Nenhum resultado disponível")
            return
        
        if len(args) < 2:
            print("Uso: write <índice> <valor>")
            return
        
        try:
            index = int(args[0])
            new_value = args[1]
            
            if index < 0 or index >= len(self.scanner.scan_results):
                print(f"Índice inválido. Use 0-{len(self.scanner.scan_results)-1}")
                return
            
            result = self.scanner.scan_results[index]
            
            # Converte valor baseado no tipo
            if result.data_type in [DataType.INT32, DataType.INT64]:
                new_value = int(new_value)
            elif result.data_type in [DataType.FLOAT, DataType.DOUBLE]:
                new_value = float(new_value)
            
            if self.scanner.write_value_to_address(result.address, new_value, result.data_type):
                print(f"Valor escrito com sucesso no endereço 0x{result.address:08X}")
                
                # Atualiza o valor no resultado
                result.update_value(new_value)
            else:
                print("Falha ao escrever valor")
                
        except ValueError as e:
            print(f"Valor inválido: {e}")
        except Exception as e:
            print(f"Erro ao escrever valor: {e}")
    
    def add_pointer(self, args):
        """Adiciona uma cadeia de ponteiros"""
        if not self.memory_manager.is_attached():
            print("Anexe a um processo primeiro")
            return
        
        if len(args) < 2:
            print("Uso: pointer <base> <offsets> [descrição]")
            print("Exemplo: pointer 0x400000 0x10,0x20,0x30 'Player HP'")
            return
        
        try:
            # Endereço base
            base_str = args[0]
            if base_str.startswith('0x'):
                base_addr = int(base_str, 16)
            else:
                base_addr = int(base_str)
            
            # Offsets
            offsets_str = args[1]
            offsets = []
            for offset_str in offsets_str.split(','):
                offset_str = offset_str.strip()
                if offset_str.startswith('0x'):
                    offsets.append(int(offset_str, 16))
                else:
                    offsets.append(int(offset_str))
            
            # Descrição
            description = args[2] if len(args) > 2 else f"Pointer_{len(self.pointer_resolver.pointer_chains)}"
            
            # Adiciona ponteiro
            chain = self.pointer_resolver.add_pointer_chain(base_addr, offsets, description)
            
            if chain.is_valid:
                # Lê valor
                value = self.pointer_resolver.get_value_from_chain(chain)
                print(f"Ponteiro adicionado com sucesso:")
                print(f"  Descrição: {description}")
                print(f"  Base: 0x{base_addr:X}")
                print(f"  Offsets: {', '.join(f'0x{off:X}' for off in offsets)}")
                print(f"  Endereço final: 0x{chain.final_address:X}")
                print(f"  Valor atual: {value}")
            else:
                print("Ponteiro inválido - não foi possível resolver a cadeia")
                
        except ValueError as e:
            print(f"Valor inválido: {e}")
        except Exception as e:
            print(f"Erro ao adicionar ponteiro: {e}")
    
    def aob_scan(self, args):
        """Realiza scan AOB"""
        if not self.memory_manager.is_attached():
            print("Anexe a um processo primeiro")
            return
        
        if not args:
            print("Uso: aob <pattern> [descrição]")
            print("Exemplo: aob '48 8B 05 ?? ?? ?? ??' 'Call pattern'")
            return
        
        try:
            pattern = args[0]
            description = args[1] if len(args) > 1 else "AOB Pattern"
            
            print(f"Iniciando AOB scan para padrão: {pattern}")
            
            # Configura callback de progresso
            def progress_callback(progress):
                if progress % 20 == 0:  # Mostra a cada 20%
                    print(f"Progresso: {progress}%")
            
            self.aob_scanner.set_progress_callback(progress_callback)
            
            # Executa scan
            results = self.aob_scanner.scan_aob(pattern, description, max_results=20)
            
            print(f"\nAOB scan completado: {len(results)} resultados encontrados")
            
            if results:
                print("\nResultados:")
                print("-" * 70)
                print(f"{'Endereço':<12} {'Padrão':<30} {'Bytes Encontrados'}")
                print("-" * 70)
                
                for result in results[:10]:  # Mostra apenas os primeiros 10
                    print(f"0x{result.address:08X}  {result.pattern.original_pattern:<30} {result.matched_bytes.hex().upper()}")
                
                if len(results) > 10:
                    print(f"... e mais {len(results) - 10} resultados")
            
        except Exception as e:
            print(f"Erro durante AOB scan: {e}")
    
    def save_session(self, args):
        """Salva sessão atual"""
        if not args:
            print("Uso: save <arquivo>")
            return
        
        try:
            filename = args[0]
            if not filename.endswith('.json'):
                filename += '.json'
            
            session_data = {
                'process_id': self.current_process,
                'scan_results': [
                    {
                        'address': result.address,
                        'value': result.value,
                        'data_type': result.data_type.value,
                        'previous_value': result.previous_value
                    }
                    for result in self.scanner.scan_results
                ],
                'pointer_chains': [chain.to_dict() for chain in self.pointer_resolver.pointer_chains],
                'aob_results': [result.to_dict() for result in self.aob_scanner.scan_results]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            print(f"Sessão salva em: {filename}")
            
        except Exception as e:
            print(f"Erro ao salvar sessão: {e}")
    
    def load_session(self, args):
        """Carrega sessão salva"""
        if not args:
            print("Uso: load <arquivo>")
            return
        
        try:
            filename = args[0]
            if not filename.endswith('.json'):
                filename += '.json'
            
            with open(filename, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Carrega ponteiros
            self.pointer_resolver.pointer_chains.clear()
            for chain_data in session_data.get('pointer_chains', []):
                from ..pointer import PointerChain
                chain = PointerChain.from_dict(chain_data)
                self.pointer_resolver.pointer_chains.append(chain)
            
            print(f"Sessão carregada de: {filename}")
            print(f"  Ponteiros carregados: {len(self.pointer_resolver.pointer_chains)}")
            
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {filename}")
        except Exception as e:
            print(f"Erro ao carregar sessão: {e}")
    
    def clear_results(self, args):
        """Limpa todos os resultados"""
        self.scanner.clear_results()
        self.aob_scanner.clear_results()
        print("Resultados limpos")
    
    def quit_program(self, args):
        """Sai do programa"""
        if self.memory_manager.is_attached():
            self.memory_manager.detach_process()
        
        print("Saindo do PyCheatEngine...")
        sys.exit(0)

def main():
    """Função principal da CLI"""
    cli = PyCheatEngineCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\nSaindo...")
    finally:
        if cli.memory_manager.is_attached():
            cli.memory_manager.detach_process()

if __name__ == "__main__":
    main()
