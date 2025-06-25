"""
Módulo Scanner de Array of Bytes (AOB)
Implementa funcionalidades para busca de padrões de bytes na memória com suporte a wildcards
"""

import re
from typing import List, Optional, Dict, Any, Callable
from memory import MemoryManager

class AOBPattern:
    """Representa um padrão de bytes para busca"""
    
    def __init__(self, pattern: str, description: str = ""):
        self.original_pattern = pattern
        self.description = description
        self.compiled_pattern = self._compile_pattern(pattern)
        self.size = len(self._pattern_to_bytes(pattern))
    
    def _compile_pattern(self, pattern: str) -> bytes:
        """Compila o padrão de string para regex de bytes"""
        # Remove espaços e normaliza
        pattern = pattern.replace(' ', '').upper()
        
        # Valida o padrão
        if not re.match(r'^[0-9A-F?]+$', pattern):
            raise ValueError("Padrão inválido. Use apenas caracteres hexadecimais (0-9, A-F) e wildcards (?)")
        
        if len(pattern) % 2 != 0:
            raise ValueError("Padrão deve ter número par de caracteres")
        
        return self._pattern_to_bytes(pattern)
    
    def _pattern_to_bytes(self, pattern: str) -> bytes:
        """Converte padrão de string para bytes"""
        result = []
        for i in range(0, len(pattern), 2):
            byte_str = pattern[i:i+2]
            if byte_str == '??':
                result.append(None)  # Wildcard
            else:
                result.append(int(byte_str, 16))
        return result
    
    def matches(self, data: bytes, offset: int = 0) -> bool:
        """Verifica se o padrão corresponde aos dados no offset especificado"""
        if offset + len(self.compiled_pattern) > len(data):
            return False
        
        for i, pattern_byte in enumerate(self.compiled_pattern):
            if pattern_byte is not None:  # Não é wildcard
                if data[offset + i] != pattern_byte:
                    return False
        
        return True

class AOBResult:
    """Representa um resultado de busca AOB"""
    
    def __init__(self, address: int, pattern: AOBPattern, matched_bytes: bytes):
        self.address = address
        self.pattern = pattern
        self.matched_bytes = matched_bytes
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização"""
        return {
            'address': self.address,
            'pattern': self.pattern.original_pattern,
            'pattern_description': self.pattern.description,
            'matched_bytes': self.matched_bytes.hex().upper()
        }

class AOBScanner:
    """Scanner de Array of Bytes (AOB) com suporte a wildcards"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.scan_results: List[AOBResult] = []
        self.is_scanning = False
        self.scan_progress = 0
        self.progress_callback: Optional[Callable] = None
        
        # Configurações de scan
        self.start_address = 0x10000
        self.end_address = 0x7FFFFFFF
        self.chunk_size = 8192  # Tamanho do chunk para leitura
    
    def set_progress_callback(self, callback: Callable):
        """Define callback para progresso do scan"""
        self.progress_callback = callback
    
    def set_scan_range(self, start_address: int, end_address: int):
        """Define o intervalo de endereços para scan"""
        self.start_address = start_address
        self.end_address = end_address
    
    def scan_aob(self, pattern: str, description: str = "", 
                 max_results: int = 1000) -> List[AOBResult]:
        """
        Realiza busca por padrão de bytes na memória
        
        Args:
            pattern: Padrão de bytes (ex: "48 8B 05 ?? ?? ?? ?? 48 89")
            description: Descrição do padrão
            max_results: Número máximo de resultados
            
        Returns:
            List[AOBResult]: Lista de resultados encontrados
        """
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        try:
            aob_pattern = AOBPattern(pattern, description)
        except ValueError as e:
            raise ValueError(f"Erro no padrão: {e}")
        
        self.scan_results.clear()
        self.is_scanning = True
        self.scan_progress = 0
        
        try:
            total_range = self.end_address - self.start_address
            current_address = self.start_address
            overlap_size = aob_pattern.size - 1
            
            while current_address < self.end_address and self.is_scanning:
                # Atualiza progresso
                progress = int(((current_address - self.start_address) / total_range) * 100)
                if progress != self.scan_progress:
                    self.scan_progress = progress
                    if self.progress_callback:
                        self.progress_callback(progress)
                
                # Para se atingiu o limite de resultados
                if len(self.scan_results) >= max_results:
                    break
                
                # Lê chunk de memória
                chunk_data = self.memory_manager.read_memory(current_address, self.chunk_size)
                if not chunk_data:
                    current_address += self.chunk_size
                    continue
                
                # Busca padrão no chunk
                for offset in range(len(chunk_data) - aob_pattern.size + 1):
                    if aob_pattern.matches(chunk_data, offset):
                        result_address = current_address + offset
                        matched_bytes = chunk_data[offset:offset + aob_pattern.size]
                        
                        result = AOBResult(result_address, aob_pattern, matched_bytes)
                        self.scan_results.append(result)
                        
                        if len(self.scan_results) >= max_results:
                            break
                
                # Move para próximo chunk com overlap para não perder padrões nas bordas
                current_address += self.chunk_size - overlap_size
            
            self.is_scanning = False
            self.scan_progress = 100
            if self.progress_callback:
                self.progress_callback(100)
            
            return self.scan_results
            
        except Exception as e:
            self.is_scanning = False
            print(f"Erro durante scan AOB: {e}")
            return []
    
    def scan_aob_in_module(self, pattern: str, module_name: str, 
                          description: str = "", max_results: int = 1000) -> List[AOBResult]:
        """
        Realiza busca por padrão de bytes em um módulo específico
        
        Args:
            pattern: Padrão de bytes
            module_name: Nome do módulo (ex: "game.exe")
            description: Descrição do padrão
            max_results: Número máximo de resultados
            
        Returns:
            List[AOBResult]: Lista de resultados encontrados
        """
        module_base = self.memory_manager.get_module_base_address(module_name)
        if not module_base:
            raise RuntimeError(f"Módulo '{module_name}' não encontrado")
        
        # Estima tamanho do módulo (implementação simplificada)
        # Em uma implementação completa, seria necessário obter o tamanho real do módulo
        module_size = 0x1000000  # 16MB por padrão
        
        # Define range para o módulo
        original_start = self.start_address
        original_end = self.end_address
        
        self.set_scan_range(module_base, module_base + module_size)
        
        try:
            results = self.scan_aob(pattern, f"{description} (Module: {module_name})", max_results)
        finally:
            # Restaura range original
            self.set_scan_range(original_start, original_end)
        
        return results
    
    def scan_multiple_patterns(self, patterns: List[Dict[str, str]], 
                             max_results_per_pattern: int = 100) -> Dict[str, List[AOBResult]]:
        """
        Realiza busca por múltiplos padrões
        
        Args:
            patterns: Lista de dicionários com 'pattern' e 'description'
            max_results_per_pattern: Máximo de resultados por padrão
            
        Returns:
            Dict: Resultados organizados por padrão
        """
        all_results = {}
        
        for pattern_info in patterns:
            if not self.is_scanning:
                break
            
            pattern = pattern_info['pattern']
            description = pattern_info.get('description', '')
            
            try:
                results = self.scan_aob(pattern, description, max_results_per_pattern)
                all_results[pattern] = results
            except Exception as e:
                print(f"Erro ao buscar padrão '{pattern}': {e}")
                all_results[pattern] = []
        
        return all_results
    
    def verify_pattern_at_address(self, address: int, pattern: str) -> bool:
        """
        Verifica se um padrão existe em um endereço específico
        
        Args:
            address: Endereço para verificar
            pattern: Padrão de bytes
            
        Returns:
            bool: True se o padrão corresponde
        """
        try:
            aob_pattern = AOBPattern(pattern)
            data = self.memory_manager.read_memory(address, aob_pattern.size)
            
            if data and len(data) >= aob_pattern.size:
                return aob_pattern.matches(data, 0)
            
            return False
            
        except Exception as e:
            print(f"Erro ao verificar padrão no endereço 0x{address:X}: {e}")
            return False
    
    def get_bytes_at_address(self, address: int, size: int) -> Optional[str]:
        """
        Obtém bytes em um endereço como string hexadecimal
        
        Args:
            address: Endereço de memória
            size: Número de bytes para ler
            
        Returns:
            str: Bytes em formato hexadecimal ou None se falhou
        """
        try:
            data = self.memory_manager.read_memory(address, size)
            if data:
                return ' '.join(f'{b:02X}' for b in data)
            return None
        except:
            return None
    
    def create_pattern_from_address(self, address: int, size: int, 
                                  wildcard_positions: List[int] = None) -> str:
        """
        Cria um padrão AOB a partir de um endereço de memória
        
        Args:
            address: Endereço base
            size: Tamanho em bytes
            wildcard_positions: Posições para colocar wildcards
            
        Returns:
            str: Padrão AOB gerado
        """
        try:
            data = self.memory_manager.read_memory(address, size)
            if not data:
                return ""
            
            pattern_parts = []
            wildcard_positions = wildcard_positions or []
            
            for i, byte in enumerate(data):
                if i in wildcard_positions:
                    pattern_parts.append('??')
                else:
                    pattern_parts.append(f'{byte:02X}')
            
            return ' '.join(pattern_parts)
            
        except Exception as e:
            print(f"Erro ao criar padrão do endereço 0x{address:X}: {e}")
            return ""
    
    def cancel_scan(self):
        """Cancela o scan em andamento"""
        self.is_scanning = False
    
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
            'patterns_found': len(set(result.pattern.original_pattern for result in self.scan_results))
        }
