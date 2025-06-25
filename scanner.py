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

    def _compare_values_for_next_scan(self, previous_value: Any, current_value: Any, 
                                    target_value: Any, scan_type: ScanType) -> bool:
        """
        Compara valores para next_scan baseado no tipo de scan
        """
        try:
            # Validação básica
            if current_value is None or previous_value is None:
                return False

            # Validação de overflow para valores numéricos
            if isinstance(current_value, (int, float)) and abs(current_value) > 1e15:
                return False
            if isinstance(previous_value, (int, float)) and abs(previous_value) > 1e15:
                return False

            if scan_type == ScanType.EXACT:
                if target_value is None:
                    return False
                return current_value == target_value

            elif scan_type == ScanType.INCREASED:
                try:
                    return current_value > previous_value
                except (TypeError, OverflowError):
                    return False

            elif scan_type == ScanType.DECREASED:
                try:
                    return current_value < previous_value
                except (TypeError, OverflowError):
                    return False

            elif scan_type == ScanType.CHANGED:
                try:
                    return current_value != previous_value
                except (TypeError, OverflowError):
                    return False

            elif scan_type == ScanType.UNCHANGED:
                try:
                    return current_value == previous_value
                except (TypeError, OverflowError):
                    return False

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
            print(f"[COMPARE ERROR] Erro na comparação next_scan: {e}")
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

    def next_scan(self, value, scan_type: ScanType) -> List[ScanResult]:
        """
        Realiza próximo scan com base nos resultados anteriores

        Args:
            value: Valor a ser usado na comparação (pode ser None para alguns tipos)
            scan_type: Tipo de scan a ser realizado

        Returns:
            Lista de resultados que correspondem aos critérios
        """
        if not self.scan_results:
            raise ValueError("Nenhum resultado de scan anterior. Execute first_scan primeiro.")

        if not self.memory_manager.is_attached():
            raise ValueError("Processo não anexado")

        self.is_scanning = True
        filtered_results = []

        try:
            print(f"[NEXT_SCAN] Iniciando - Tipo: {scan_type.value}, Valor: {value}")
            print(f"[NEXT_SCAN] Resultados anteriores: {len(self.scan_results)}")

            # PASSO 1: Atualiza TODOS os valores da memória primeiro
            print(f"[NEXT_SCAN] Passo 1: Atualizando valores da memória...")
            for i, result in enumerate(self.scan_results):
                if not self.is_scanning:
                    break

                # Atualiza progresso
                if i % 50 == 0 and self.progress_callback:
                    progress = (i / len(self.scan_results)) * 50  # Primeira metade do progresso
                    self.progress_callback(progress)

                # Lê valor atual da memória
                current_value = self._read_value_at_address(result.address, result.data_type)

                if current_value is not None:
                    print(f"[NEXT_SCAN] Endereço 0x{result.address:X}: anterior={result.value}, atual={current_value}")
                    # Atualiza o valor no resultado
                    result.previous_value = result.value  # Salva valor anterior
                    result.value = current_value  # Atualiza com valor atual

            # PASSO 2: Agora filtra com base nos valores atualizados
            print(f"[NEXT_SCAN] Passo 2: Filtrando resultados...")
            for i, result in enumerate(self.scan_results):
                if not self.is_scanning:
                    break

                # Atualiza progresso (segunda metade)
                if i % 50 == 0 and self.progress_callback:
                    progress = 50 + (i / len(self.scan_results)) * 50
                    self.progress_callback(progress)

                # Verifica se tem valor anterior salvo
                previous_val = result.previous_value if hasattr(result, 'previous_value') and result.previous_value is not None else result.value
                current_val = result.value

                print(f"[NEXT_SCAN] Endereço 0x{result.address:X}: anterior={previous_val}, atual={current_val}, procurado={value}, match={self._compare_values(previous_val, current_val, value, scan_type)}")

                # Aplica filtro baseado no tipo de scan
                match = self._compare_values(previous_val, current_val, value, scan_type)

                if match:
                    filtered_results.append(result)

            # Atualiza lista de resultados
            self.scan_results = filtered_results

            print(f"[NEXT_SCAN] Completado:")
            print(f"  - Processados: {len(self.scan_results)}/{len(self.scan_results)}")
            print(f"  - Correspondências: {len(filtered_results)}")
            print(f"  - Resultados restantes: {len(self.scan_results)}")

        except Exception as e:
            print(f"[NEXT_SCAN] Erro: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.is_scanning = False
            print(f"[NEXT_SCAN] Finalizado - is_scanning = {self.is_scanning}")

            if self.progress_callback:
                self.progress_callback(100)

        return self.scan_results

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

    def update_results(self):
        """Atualiza os valores dos resultados lendo da memória"""
        if not self.memory_manager.is_attached():
            return

        for result in self.scan_results:
            current_value = self._read_value_at_address(result.address, result.data_type)
            if current_value is not None:
                result.update_value(current_value)

    def refresh_all_values(self):
        """
        Força atualização de todos os valores da memória
        Útil antes de fazer next_scan para garantir valores atuais
        """
        if not self.memory_manager.is_attached() or not self.scan_results:
            return

        print(f"[REFRESH] Atualizando {len(self.scan_results)} valores...")
        updated_count = 0

        for result in self.scan_results:
            current_value = self._read_value_at_address(result.address, result.data_type)
            if current_value is not None and current_value != result.value:
                print(f"[REFRESH] 0x{result.address:X}: {result.value} -> {current_value}")
                result.previous_value = result.value
                result.value = current_value
                updated_count += 1

        print(f"[REFRESH] {updated_count} valores foram atualizados")
        return updated_count

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