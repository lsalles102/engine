"""
Módulo Scanner de Memória
Implementa funcionalidades de scan de valores na memória com comparações
"""

import struct
import time
import threading
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from memory import MemoryManager

class ScanType(Enum):
    """Tipos de scan disponíveis"""
    EXACT = "exact"
    INCREASED = "increased"
    DECREASED = "decreased"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"

class DataType(Enum):
    """Tipos de dados suportados"""
    INT32 = "int32"
    INT64 = "int64"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "string"
    BYTES = "bytes"

class ScanResult:
    """Representa um resultado de scan"""

    def __init__(self, address: int, value: Any, data_type: DataType):
        self.address = address
        self.value = value
        self.data_type = data_type
        self.previous_value = None

    def update_value(self, new_value: Any):
        """Atualiza o valor, mantendo o anterior"""
        self.previous_value = self.value
        self.value = new_value

class MemoryScanner:
    """Scanner de memória para busca e comparação de valores"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.scan_results: List[ScanResult] = []
        self.is_scanning = False
        self.scan_progress = 0
        self.progress_callback: Optional[Callable] = None

        # Configurações de scan
        self.start_address = 0x10000
        self.end_address = 0x7FFFFFFF
        self.alignment = 4  # Alinhamento de memória

    def set_progress_callback(self, callback: Callable):
        """Define callback para progresso do scan"""
        self.progress_callback = callback

    def set_scan_range(self, start_address: int, end_address: int):
        """Define o intervalo de endereços para scan"""
        # Validação mais rigorosa para evitar overflow
        try:
            # Converte para int se necessário e valida
            start_address = int(start_address) if start_address is not None else 0x10000
            end_address = int(end_address) if end_address is not None else 0x7FFFFFFF
            
            # Limites seguros
            min_address = 0x10000
            max_address = 0x7FFFFFFF
            
            if start_address < min_address:
                start_address = min_address
            if start_address > max_address:
                start_address = min_address
                
            if end_address < min_address or end_address > max_address:
                end_address = max_address
            if end_address <= start_address:
                end_address = start_address + 0x1000000  # 16MB por padrão
                if end_address > max_address:
                    end_address = max_address

            self.start_address = start_address
            self.end_address = end_address
            
        except (ValueError, TypeError, OverflowError):
            # Define valores padrão seguros em caso de erro
            self.start_address = 0x10000
            self.end_address = 0x7FFFFFFF

    def _get_data_size(self, data_type: DataType) -> int:
        """Retorna o tamanho em bytes do tipo de dado"""
        sizes = {
            DataType.INT32: 4,
            DataType.INT64: 8,
            DataType.FLOAT: 4,
            DataType.DOUBLE: 8,
            DataType.STRING: 1,  # Será determinado dinamicamente
            DataType.BYTES: 1    # Será determinado dinamicamente
        }
        return sizes.get(data_type, 4)

    def _read_value_at_address(self, address: int, data_type: DataType) -> Any:
        """Lê um valor específico no endereço dado"""
        try:
            # Validação do endereço
            if address < 0 or address > 0x7FFFFFFFFFFFFFFF:
                return None
                
            if data_type == DataType.INT32:
                value = self.memory_manager.read_int32(address)
                # Validação do valor INT32
                if value is not None and (value < -2147483648 or value > 2147483647):
                    return None
                return value
            elif data_type == DataType.INT64:
                value = self.memory_manager.read_int64(address)
                # Validação do valor INT64
                if value is not None and (value < -9223372036854775808 or value > 9223372036854775807):
                    return None
                return value
            elif data_type == DataType.FLOAT:
                value = self.memory_manager.read_float(address)
                # Validação do valor FLOAT
                if value is not None and (abs(value) > 3.4e38 or (value != 0 and abs(value) < 1.2e-38)):
                    return None
                return value
            elif data_type == DataType.DOUBLE:
                value = self.memory_manager.read_double(address)
                # Validação do valor DOUBLE
                if value is not None and abs(value) > 1.7e308:
                    return None
                return value
            elif data_type == DataType.STRING:
                return self.memory_manager.read_string(address, 64)
            elif data_type == DataType.BYTES:
                return self.memory_manager.read_memory(address, 4)

            return None
        except (OverflowError, ValueError, struct.error, TypeError, OSError):
            return None

    def _compare_values(self, current_value: Any, target_value: Any, 
                       scan_type: ScanType, previous_value: Any = None) -> bool:
        """
        Compara valores baseado no tipo de scan
        Esta função é usada apenas no first_scan para comparações simples
        """
        try:
            # Validação básica
            if current_value is None:
                return False

            # Validação de overflow para valores numéricos
            if isinstance(current_value, (int, float)):
                if abs(current_value) > 1e15:
                    return False
                if target_value is not None and isinstance(target_value, (int, float)) and abs(target_value) > 1e15:
                    return False

            # Para first_scan, normalmente só usamos EXACT
            if scan_type == ScanType.EXACT:
                if target_value is None:
                    return False
                return current_value == target_value

            elif scan_type == ScanType.GREATER_THAN:
                if target_value is None:
                    return False
                try:
                    return current_value > target_value
                except (TypeError, OverflowError):
                    return False

            elif scan_type == ScanType.LESS_THAN:
                if target_value is None:
                    return False
                try:
                    return current_value < target_value
                except (TypeError, OverflowError):
                    return False

            elif scan_type == ScanType.BETWEEN:
                if not isinstance(target_value, (list, tuple)) or len(target_value) != 2:
                    return False
                try:
                    return target_value[0] <= current_value <= target_value[1]
                except (TypeError, OverflowError):
                    return False

            return False

        except Exception as e:
            print(f"[COMPARE ERROR] Erro na comparação: {e}")
            return False

    def first_scan(self, value: Any, data_type: DataType, 
                   scan_type: ScanType = ScanType.EXACT) -> List[ScanResult]:
        """
        Realiza o primeiro scan por um valor

        Args:
            value: Valor a procurar
            data_type: Tipo de dado
            scan_type: Tipo de comparação

        Returns:
            List[ScanResult]: Lista de resultados encontrados
        """
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")

        self.scan_results.clear()
        self.is_scanning = True
        self.scan_progress = 0

        try:
            # Configura thread de scan
            scan_thread = threading.Thread(
                target=self._scan_worker,
                args=(value, data_type, scan_type, None)
            )
            scan_thread.daemon = True
            scan_thread.start()
            scan_thread.join()

            return self.scan_results.copy()

        finally:
            self.is_scanning = False

    def next_scan(self, value: Any, scan_type: ScanType) -> List[ScanResult]:
        """
        Realiza scan subsequente baseado nos resultados anteriores
        Funciona como o Cheat Engine tradicional - compara valor atual com o valor fornecido

        Args:
            value: Valor a procurar (pode ser None para alguns tipos de scan)
            scan_type: Tipo de comparação

        Returns:
            List[ScanResult]: Lista de resultados filtrados
        """
        print(f"[NEXT_SCAN] Iniciando - Tipo: {scan_type.value}, Valor: {value}")
        print(f"[NEXT_SCAN] Resultados anteriores: {len(self.scan_results)}")
        
        # Validação básica
        if not self.scan_results:
            error_msg = "Nenhum scan anterior encontrado. Execute first_scan primeiro."
            print(f"[NEXT_SCAN ERROR] {error_msg}")
            raise RuntimeError(error_msg)

        if not self.memory_manager.is_attached():
            error_msg = "Não está anexado a nenhum processo"
            print(f"[NEXT_SCAN ERROR] {error_msg}")
            raise RuntimeError(error_msg)

        # Validação específica por tipo de scan
        needs_value = scan_type in [ScanType.EXACT, ScanType.GREATER_THAN, ScanType.LESS_THAN, ScanType.BETWEEN]
        if needs_value and value is None:
            error_msg = f"Tipo de scan '{scan_type.value}' requer um valor"
            print(f"[NEXT_SCAN ERROR] {error_msg}")
            raise ValueError(error_msg)

        self.is_scanning = True
        self.scan_progress = 0
        processed_count = 0
        matched_count = 0

        try:
            # PRIMEIRO: Atualiza todos os valores lendo da memória atual
            print(f"[NEXT_SCAN] Passo 1: Atualizando valores da memória...")
            total_results = len(self.scan_results)
            
            for i, result in enumerate(self.scan_results):
                if not self.is_scanning:
                    break
                    
                # Atualiza progresso da leitura (0-50%)
                progress = int((i / total_results) * 50) if total_results > 0 else 0
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        try:
                            self.progress_callback(progress)
                        except Exception as e:
                            print(f"[NEXT_SCAN WARNING] Erro no callback de progresso: {e}")
                
                # Lê valor atual da memória e atualiza o resultado
                try:
                    current_value = self._read_value_at_address(result.address, result.data_type)
                    if current_value is not None:
                        # Salva o valor anterior antes de atualizar
                        result.previous_value = result.value
                        result.value = current_value  # Atualiza com valor atual da memória
                        
                        if i < 3:  # Log apenas dos primeiros 3
                            print(f"[NEXT_SCAN] Endereço 0x{result.address:X}: anterior={result.previous_value}, atual={current_value}")
                    else:
                        # Remove resultados que não podem ser lidos
                        result.value = None
                except Exception as e:
                    if i < 5:  # Log apenas para os primeiros erros
                        print(f"[NEXT_SCAN WARNING] Erro ao ler endereço 0x{result.address:X}: {e}")
                    result.value = None

            # SEGUNDO: Agora filtra baseado na comparação
            print(f"[NEXT_SCAN] Passo 2: Filtrando resultados...")
            new_results = []

            for i, result in enumerate(self.scan_results):
                if not self.is_scanning:
                    print("[NEXT_SCAN] Scan cancelado pelo usuário")
                    break

                processed_count += 1

                # Atualiza progresso da filtragem (50-100%)
                progress = 50 + int((i / total_results) * 50) if total_results > 0 else 100
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        try:
                            self.progress_callback(progress)
                        except Exception as e:
                            print(f"[NEXT_SCAN WARNING] Erro no callback de progresso: {e}")

                # Pula se não conseguiu ler o valor
                if result.value is None:
                    continue

                # Compara valores usando lógica correta do Cheat Engine
                try:
                    match = False
                    current_value = result.value  # Valor atual já atualizado
                    previous_value = result.previous_value  # Valor anterior
                    
                    if scan_type == ScanType.EXACT:
                        # Compara valor atual com o valor digitado pelo usuário
                        match = (current_value == value)
                        
                    elif scan_type == ScanType.INCREASED:
                        # Verifica se valor atual é maior que o valor anterior
                        if previous_value is not None:
                            match = (current_value > previous_value)
                        
                    elif scan_type == ScanType.DECREASED:
                        # Verifica se valor atual é menor que o valor anterior
                        if previous_value is not None:
                            match = (current_value < previous_value)
                        
                    elif scan_type == ScanType.CHANGED:
                        # Verifica se valor atual é diferente do valor anterior
                        if previous_value is not None:
                            match = (current_value != previous_value)
                        
                    elif scan_type == ScanType.UNCHANGED:
                        # Verifica se valor atual é igual ao valor anterior
                        if previous_value is not None:
                            match = (current_value == previous_value)
                        
                    elif scan_type == ScanType.GREATER_THAN:
                        # Compara valor atual com o valor digitado
                        match = (current_value > value)
                        
                    elif scan_type == ScanType.LESS_THAN:
                        # Compara valor atual com o valor digitado
                        match = (current_value < value)
                        
                    elif scan_type == ScanType.BETWEEN:
                        # Verifica se valor atual está entre os valores fornecidos
                        if isinstance(value, (list, tuple)) and len(value) == 2:
                            match = (value[0] <= current_value <= value[1])
                    
                    if i < 3:  # Log detalhado para debug dos primeiros 3
                        print(f"[NEXT_SCAN] Endereço 0x{result.address:X}: anterior={previous_value}, atual={current_value}, procurado={value}, match={match}")
                    
                    if match:
                        new_results.append(result)
                        matched_count += 1
                        
                except Exception as comp_error:
                    print(f"[NEXT_SCAN ERROR] Erro na comparação para endereço 0x{result.address:X}: {comp_error}")
                    continue

            # Atualiza resultados
            self.scan_results = new_results
            self.scan_progress = 100
            
            print(f"[NEXT_SCAN] Completado:")
            print(f"  - Processados: {processed_count}/{total_results}")
            print(f"  - Correspondências: {matched_count}")
            print(f"  - Resultados restantes: {len(new_results)}")
            
            # Callback final
            if self.progress_callback:
                try:
                    self.progress_callback(100)
                except Exception as e:
                    print(f"[NEXT_SCAN WARNING] Erro no callback final: {e}")

            return self.scan_results.copy()

        except Exception as e:
            print(f"[NEXT_SCAN ERROR] Erro crítico durante scan: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self.is_scanning = False
            print(f"[NEXT_SCAN] Finalizado - is_scanning = {self.is_scanning}")

    def _scan_worker(self, value: Any, data_type: DataType, scan_type: ScanType, previous_results: Optional[List[ScanResult]]):
        """Worker thread para realizar o scan"""
        try:
            data_size = self._get_data_size(data_type)
            
            # Validação mais rigorosa dos endereços
            if self.start_address < 0:
                self.start_address = 0x10000
            if self.end_address < 0 or self.end_address > 0x7FFFFFFF:
                self.end_address = 0x7FFFFFFF
            if self.start_address >= self.end_address:
                print("Intervalo de scan inválido")
                return
                
            current_address = self.start_address
            total_range = self.end_address - self.start_address
            chunk_size = 4096  # 4KB chunks

            # Validação adicional para evitar overflow
            if total_range <= 0 or total_range > 0x7FFFFFFF:
                print("Intervalo de scan inválido")
                return

            while current_address < self.end_address and self.is_scanning:
                # Verifica se endereço está dentro dos limites
                if current_address < 0 or current_address > 0x7FFFFFFF:
                    break  # Para o loop em vez de continuar infinitamente
                
                # Proteção adicional contra overflow
                if current_address + chunk_size < current_address:
                    break

                # Atualiza progresso com proteção contra divisão por zero
                if total_range > 0:
                    progress = int(((current_address - self.start_address) / total_range) * 100)
                    progress = max(0, min(100, progress))  # Garante que está entre 0-100
                    if progress != self.scan_progress:
                        self.scan_progress = progress
                        if self.progress_callback:
                            try:
                                self.progress_callback(progress)
                            except:
                                pass  # Ignora erros no callback

                # Lê chunk de memória com tratamento de erro
                try:
                    chunk_data = self.memory_manager.read_memory(current_address, chunk_size)
                    if not chunk_data:
                        current_address += chunk_size
                        continue
                except (OverflowError, OSError):
                    current_address += chunk_size
                    continue

                # Processa cada posição possível no chunk
                max_offset = max(0, len(chunk_data) - data_size + 1)
                for offset in range(0, max_offset, self.alignment):
                    if not self.is_scanning:
                        break

                    address = current_address + offset

                    # Validação do endereço final
                    if address < 0 or address > 0x7FFFFFFF:
                        continue

                    try:
                        current_value = self._read_value_at_address(address, data_type)

                        if current_value is not None:
                            # Validação adicional para valores numéricos
                            if data_type in [DataType.INT32, DataType.INT64, DataType.FLOAT, DataType.DOUBLE]:
                                # Verifica se o valor está dentro de limites seguros
                                if isinstance(current_value, (int, float)):
                                    if data_type == DataType.INT32 and (current_value < -2147483648 or current_value > 2147483647):
                                        continue
                                    elif data_type == DataType.INT64 and (current_value < -9223372036854775808 or current_value > 9223372036854775807):
                                        continue
                                    elif data_type in [DataType.FLOAT, DataType.DOUBLE] and abs(current_value) > 1e308:
                                        continue
                            
                            if self._compare_values(current_value, value, scan_type):
                                result = ScanResult(address, current_value, data_type)
                                self.scan_results.append(result)

                                # Limita resultados para evitar sobrecarga
                                if len(self.scan_results) >= 10000:
                                    self.is_scanning = False
                                    break
                    except (OverflowError, ValueError, struct.error, TypeError):
                        continue  # Ignora valores que causam overflow ou erros

                current_address += chunk_size

            self.scan_progress = 100
            if self.progress_callback:
                try:
                    self.progress_callback(100)
                except:
                    pass

        except Exception as e:
            print(f"Erro durante scan: {e}")
        finally:
            self.is_scanning = False

    def cancel_scan(self):
        """Cancela o scan atual"""
        self.is_scanning = False

    def update_results(self) -> int:
        """
        Atualiza os valores de todos os resultados

        Returns:
            int: Número de resultados ainda válidos
        """
        if not self.scan_results:
            return 0

        valid_results = []

        for result in self.scan_results:
            current_value = self._read_value_at_address(result.address, result.data_type)
            if current_value is not None:
                result.update_value(current_value)
                valid_results.append(result)

        self.scan_results = valid_results
        return len(self.scan_results)

    def get_scan_summary(self) -> Dict[str, Any]:
        """Retorna resumo do scan atual"""
        return {
            'total_results': len(self.scan_results),
            'is_scanning': self.is_scanning,
            'progress': self.scan_progress,
            'scan_range': {
                'start': hex(self.start_address),
                'end': hex(self.end_address)
            },
            'alignment': self.alignment
        }

    def export_results(self, filename: str) -> bool:
        """
        Exporta resultados para arquivo JSON

        Args:
            filename: Nome do arquivo

        Returns:
            bool: True se exportou com sucesso
        """
        try:
            import json

            data = {
                'timestamp': time.time(),
                'process_info': self.memory_manager.get_process_info(),
                'scan_summary': self.get_scan_summary(),
                'results': []
            }

            for result in self.scan_results:
                data['results'].append({
                    'address': hex(result.address),
                    'value': result.value,
                    'previous_value': result.previous_value,
                    'data_type': result.data_type.value
                })

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            print(f"Erro ao exportar resultados: {e}")
            return False

    def import_results(self, filename: str) -> bool:
        """
        Importa resultados de arquivo JSON

        Args:
            filename: Nome do arquivo

        Returns:
            bool: True se importou com sucesso
        """
        try:
            import json

            with open(filename, 'r') as f:
                data = json.load(f)

            self.scan_results.clear()

            for result_data in data.get('results', []):
                address = int(result_data['address'], 16)
                value = result_data['value']
                data_type = DataType(result_data['data_type'])

                result = ScanResult(address, value, data_type)
                result.previous_value = result_data.get('previous_value')
                self.scan_results.append(result)

            return True

        except Exception as e:
            print(f"Erro ao importar resultados: {e}")
            return False

    def get_results_summary(self) -> Dict[str, Any]:
        """Retorna um resumo dos resultados"""
        return {
            'count': len(self.scan_results),
            'is_scanning': self.is_scanning,
            'progress': self.scan_progress,
            'attached_process': self.memory_manager.process_id if self.memory_manager.is_attached() else None
        }

    def clear_results(self):
        """Limpa todos os resultados"""
        self.scan_results.clear()

    def get_scan_progress(self) -> int:
        """Retorna o progresso atual do scan (0-100)"""
        return self.scan_progress

    def is_scan_running(self) -> bool:
        """Verifica se um scan está em execução"""
        return self.is_scanning

    def get_result_count(self) -> int:
        """Retorna o número de resultados do scan"""
        return len(self.scan_results)

    def write_value_to_address(self, address: int, value: Any, data_type: DataType) -> bool:
        """
        Escreve um valor no endereço especificado
        
        Args:
            address: Endereço de memória
            value: Valor a ser escrito
            data_type: Tipo do dado
            
        Returns:
            bool: True se escreveu com sucesso
        """
        try:
            if data_type == DataType.INT32:
                return self.memory_manager.write_int32(address, int(value))
            elif data_type == DataType.INT64:
                return self.memory_manager.write_int64(address, int(value))
            elif data_type == DataType.FLOAT:
                return self.memory_manager.write_float(address, float(value))
            elif data_type == DataType.DOUBLE:
                return self.memory_manager.write_double(address, float(value))
            elif data_type == DataType.STRING:
                return self.memory_manager.write_string(address, str(value))
            elif data_type == DataType.BYTES:
                if isinstance(value, str):
                    value = bytes.fromhex(value.replace(' ', ''))
                return self.memory_manager.write_memory(address, value)
            
            return False
        except Exception as e:
            print(f"Erro ao escrever valor: {e}")
            return False

    def get_process_info(self) -> Dict[str, Any]:
        """Retorna informações do processo anexado"""
        if not self.memory_manager.is_attached():
            return {}
        
        return {
            'process_id': self.memory_manager.process_id,
            'attached': True
        }