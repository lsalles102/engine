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
        self.start_address = start_address
        self.end_address = end_address
    
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
            if data_type == DataType.INT32:
                return self.memory_manager.read_int(address)
            elif data_type == DataType.INT64:
                return self.memory_manager.read_long(address)
            elif data_type == DataType.FLOAT:
                return self.memory_manager.read_float(address)
            elif data_type == DataType.DOUBLE:
                return self.memory_manager.read_double(address)
            elif data_type == DataType.STRING:
                return self.memory_manager.read_string(address, 64)
            elif data_type == DataType.BYTES:
                return self.memory_manager.read_memory(address, 4)
            
            return None
        except:
            return None
    
    def _compare_values(self, current_value: Any, target_value: Any, 
                       scan_type: ScanType, previous_value: Any = None) -> bool:
        """Compara valores baseado no tipo de scan"""
        try:
            if current_value is None:
                return False
            
            if scan_type == ScanType.EXACT:
                return current_value == target_value
            
            elif scan_type == ScanType.INCREASED:
                return previous_value is not None and current_value > previous_value
            
            elif scan_type == ScanType.DECREASED:
                return previous_value is not None and current_value < previous_value
            
            elif scan_type == ScanType.CHANGED:
                return previous_value is not None and current_value != previous_value
            
            elif scan_type == ScanType.UNCHANGED:
                return previous_value is not None and current_value == previous_value
            
            elif scan_type == ScanType.GREATER_THAN:
                return current_value > target_value
            
            elif scan_type == ScanType.LESS_THAN:
                return current_value < target_value
            
            elif scan_type == ScanType.BETWEEN:
                if isinstance(target_value, (list, tuple)) and len(target_value) == 2:
                    return target_value[0] <= current_value <= target_value[1]
            
            return False
            
        except:
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
        
        Args:
            value: Valor a procurar
            scan_type: Tipo de comparação
            
        Returns:
            List[ScanResult]: Lista de resultados filtrados
        """
        if not self.scan_results:
            raise RuntimeError("Nenhum scan anterior encontrado. Execute first_scan primeiro.")
        
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        self.is_scanning = True
        self.scan_progress = 0
        
        try:
            new_results = []
            total_results = len(self.scan_results)
            
            for i, result in enumerate(self.scan_results):
                if not self.is_scanning:
                    break
                
                # Atualiza progresso
                progress = int((i / total_results) * 100)
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        self.progress_callback(progress)
                
                # Lê valor atual
                current_value = self._read_value_at_address(result.address, result.data_type)
                
                # Compara valores
                if self._compare_values(current_value, value, scan_type, result.value):
                    result.update_value(current_value)
                    new_results.append(result)
            
            self.scan_results = new_results
            self.scan_progress = 100
            if self.progress_callback:
                self.progress_callback(100)
            
            return self.scan_results.copy()
            
        finally:
            self.is_scanning = False
    
    def _scan_worker(self, value: Any, data_type: DataType, scan_type: ScanType, previous_results: Optional[List[ScanResult]]):
        """Worker thread para realizar o scan"""
        try:
            data_size = self._get_data_size(data_type)
            current_address = self.start_address
            total_range = self.end_address - self.start_address
            chunk_size = 4096  # 4KB chunks
            
            while current_address < self.end_address and self.is_scanning:
                # Atualiza progresso
                progress = int(((current_address - self.start_address) / total_range) * 100)
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        self.progress_callback(progress)
                
                # Lê chunk de memória
                chunk_data = self.memory_manager.read_memory(current_address, chunk_size)
                if not chunk_data:
                    current_address += chunk_size
                    continue
                
                # Processa cada posição possível no chunk
                for offset in range(0, len(chunk_data) - data_size + 1, self.alignment):
                    if not self.is_scanning:
                        break
                    
                    address = current_address + offset
                    current_value = self._read_value_at_address(address, data_type)
                    
                    if current_value is not None:
                        if self._compare_values(current_value, value, scan_type):
                            result = ScanResult(address, current_value, data_type)
                            self.scan_results.append(result)
                            
                            # Limita resultados para evitar sobrecarga
                            if len(self.scan_results) >= 10000:
                                self.is_scanning = False
                                break
                
                current_address += chunk_size
            
            self.scan_progress = 100
            if self.progress_callback:
                self.progress_callback(100)
                
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
        Returns:
            List[ScanResult]: Lista de resultados encontrados
        """
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        self.scan_results.clear()
        self.is_scanning = True
        self.scan_progress = 0
        
        try:
            step_size = self._get_data_size(data_type)
            total_addresses = (self.end_address - self.start_address) // step_size
            checked_addresses = 0
            
            current_address = self.start_address
            while current_address < self.end_address and self.is_scanning:
                # Atualiza progresso
                progress = int((checked_addresses / total_addresses) * 100)
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        self.progress_callback(progress)
                
                # Lê valor no endereço atual
                current_value = self._read_value_at_address(current_address, data_type)
                
                # Compara valor
                if self._compare_values(current_value, value, scan_type):
                    result = ScanResult(current_address, current_value, data_type)
                    self.scan_results.append(result)
                
                current_address += step_size
                checked_addresses += 1
                
                # Limite de resultados para evitar sobrecarga
                if len(self.scan_results) > 10000:
                    break
            
            self.is_scanning = False
            self.scan_progress = 100
            if self.progress_callback:
                self.progress_callback(100)
            
            return self.scan_results
            
        except Exception as e:
            self.is_scanning = False
            print(f"Erro durante first_scan: {e}")
            return []
    
    def next_scan(self, value: Any, scan_type: ScanType) -> List[ScanResult]:
        """
        Realiza scan subsequente nos resultados existentes
        
        Args:
            value: Valor a procurar
            scan_type: Tipo de comparação
            
        Returns:
            List[ScanResult]: Lista de resultados filtrados
        """
        if not self.scan_results:
            raise RuntimeError("Nenhum resultado de scan anterior")
        
        new_results = []
        self.is_scanning = True
        self.scan_progress = 0
        
        try:
            total_results = len(self.scan_results)
            
            for i, result in enumerate(self.scan_results):
                if not self.is_scanning:
                    break
                
                # Atualiza progresso
                progress = int((i / total_results) * 100)
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        self.progress_callback(progress)
                
                # Lê valor atual
                current_value = self._read_value_at_address(result.address, result.data_type)
                
                # Compara valor
                if self._compare_values(current_value, value, scan_type, result.value):
                    result.update_value(current_value)
                    new_results.append(result)
            
            self.scan_results = new_results
            self.is_scanning = False
            self.scan_progress = 100
            if self.progress_callback:
                self.progress_callback(100)
            
            return self.scan_results
            
        except Exception as e:
            self.is_scanning = False
            print(f"Erro durante next_scan: {e}")
            return []
    
    def update_results(self):
        """Atualiza valores de todos os resultados"""
        for result in self.scan_results:
            current_value = self._read_value_at_address(result.address, result.data_type)
            if current_value is not None:
                result.update_value(current_value)
    
    def cancel_scan(self):
        """Cancela o scan atual"""
        self.is_scanning = False
    
    def clear_results(self):
        """Limpa todos os resultados"""
        self.scan_results.clear()
    
    def get_scan_progress(self) -> int:
        """Retorna o progresso atual do scan (0-100)"""
        return self.scan_progress
    
    def is_scan_running(self) -> bool:
        """Verifica se um scan está em execução"""
        return self.is_scanning
        Returns:
            List[ScanResult]: Lista de resultados encontrados
        """
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        self.scan_results.clear()
        self.is_scanning = True
        self.scan_progress = 0
        
        try:
            data_size = self._get_data_size(data_type)
            chunk_size = 4096  # Lê em chunks de 4KB
            
            current_address = self.start_address
            total_range = self.end_address - self.start_address
            
            while current_address < self.end_address and self.is_scanning:
                # Atualiza progresso
                progress = int(((current_address - self.start_address) / total_range) * 100)
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        self.progress_callback(progress)
                
                # Lê chunk de memória
                chunk_data = self.memory_manager.read_memory(current_address, chunk_size)
                if not chunk_data:
                    current_address += chunk_size
                    continue
                
                # Procura valores no chunk
                for offset in range(0, len(chunk_data) - data_size + 1, self.alignment):
                    address = current_address + offset
                    
                    try:
                        current_value = self._read_value_at_address(address, data_type)
                        
                        if self._compare_values(current_value, value, scan_type):
                            result = ScanResult(address, current_value, data_type)
                            self.scan_results.append(result)
                    
                    except:
                        continue
                
                current_address += chunk_size
            
            self.is_scanning = False
            self.scan_progress = 100
            if self.progress_callback:
                self.progress_callback(100)
            
            return self.scan_results
            
        except Exception as e:
            self.is_scanning = False
            print(f"Erro durante o primeiro scan: {e}")
            return []
    
    def next_scan(self, value: Any = None, scan_type: ScanType = ScanType.UNCHANGED) -> List[ScanResult]:
        """
        Realiza um novo scan baseado nos resultados anteriores
        
        Args:
            value: Valor para comparação (opcional, dependendo do tipo)
            scan_type: Tipo de comparação
            
        Returns:
            List[ScanResult]: Lista de resultados filtrados
        """
        if not self.scan_results:
            raise RuntimeError("Nenhum resultado de scan anterior encontrado")
        
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        self.is_scanning = True
        self.scan_progress = 0
        
        try:
            filtered_results = []
            total_results = len(self.scan_results)
            
            for i, result in enumerate(self.scan_results):
                if not self.is_scanning:
                    break
                
                # Atualiza progresso
                progress = int((i / total_results) * 100)
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        self.progress_callback(progress)
                
                # Lê valor atual
                current_value = self._read_value_at_address(result.address, result.data_type)
                
                if current_value is not None:
                    # Compara baseado no tipo de scan
                    if self._compare_values(current_value, value, scan_type, result.value):
                        result.update_value(current_value)
                        filtered_results.append(result)
            
            self.scan_results = filtered_results
            self.is_scanning = False
            self.scan_progress = 100
            if self.progress_callback:
                self.progress_callback(100)
            
            return self.scan_results
            
        except Exception as e:
            self.is_scanning = False
            print(f"Erro durante o next scan: {e}")
            return []
    
    def cancel_scan(self):
        """Cancela o scan em andamento"""
        self.is_scanning = False
    
    def update_results(self) -> List[ScanResult]:
        """Atualiza os valores de todos os resultados"""
        if not self.memory_manager.is_attached():
            return []
        
        for result in self.scan_results:
            current_value = self._read_value_at_address(result.address, result.data_type)
            if current_value is not None:
                result.update_value(current_value)
        
        return self.scan_results
    
    def write_value_to_address(self, address: int, value: Any, data_type: DataType) -> bool:
        """
        Escreve um valor em um endereço específico
        
        Args:
            address: Endereço de memória
            value: Valor para escrever
            data_type: Tipo de dado
            
        Returns:
            bool: True se escreveu com sucesso
        """
        try:
            if data_type == DataType.INT32:
                return self.memory_manager.write_int(address, int(value))
            elif data_type == DataType.INT64:
                return self.memory_manager.write_long(address, int(value))
            elif data_type == DataType.FLOAT:
                return self.memory_manager.write_float(address, float(value))
            elif data_type == DataType.DOUBLE:
                return self.memory_manager.write_double(address, float(value))
            elif data_type == DataType.STRING:
                return self.memory_manager.write_string(address, str(value))
            elif data_type == DataType.BYTES:
                if isinstance(value, str):
                    # Converte string hex para bytes
                    value = bytes.fromhex(value.replace(' ', ''))
                return self.memory_manager.write_memory(address, value)
            
            return False
        except:
            return False
    
    def clear_results(self):
        """Limpa todos os resultados de scan"""
        self.scan_results.clear()
    
    def get_result_count(self) -> int:
        """Retorna o número de resultados encontrados"""
        return len(self.scan_results)
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Retorna um resumo dos resultados"""
        return {
            'count': len(self.scan_results),
            'is_scanning': self.is_scanning,
            'progress': self.scan_progress,
            'attached_process': self.memory_manager.process_name if self.memory_manager.is_attached() else None
        }
