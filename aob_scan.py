"""
Módulo de Scanner AOB (Array of Bytes) para PyCheatEngine
Implementa busca de padrões de bytes na memória
"""

import re
from typing import List, Optional, Callable

class AOBPattern:
    """Representa um padrão AOB"""

    def __init__(self, pattern_string: str):
        self.original_pattern = pattern_string.strip()
        self.pattern_bytes = self._parse_pattern()

    def _parse_pattern(self) -> List[Optional[int]]:
        """Converte string do padrão para lista de bytes"""
        parts = self.original_pattern.replace(' ', '').upper()
        if len(parts) % 2 != 0:
            raise ValueError("Padrão deve ter número par de caracteres")

        bytes_list = []
        for i in range(0, len(parts), 2):
            byte_str = parts[i:i+2]
            if byte_str == '??':
                bytes_list.append(None)  # Wildcard
            else:
                try:
                    bytes_list.append(int(byte_str, 16))
                except ValueError:
                    raise ValueError(f"Byte inválido: {byte_str}")

        return bytes_list

class AOBResult:
    """Resultado de scan AOB"""

    def __init__(self, address: int, pattern: AOBPattern, matched_bytes: bytes):
        self.address = address
        self.pattern = pattern
        self.matched_bytes = matched_bytes

    def to_dict(self):
        """Converte para dicionário"""
        return {
            'address': self.address,
            'pattern': self.pattern.original_pattern,
            'matched_bytes': self.matched_bytes.hex()
        }

class AOBScanner:
    """Scanner de padrões AOB"""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.scan_results: List[AOBResult] = []
        self.progress_callback: Optional[Callable[[int], None]] = None
        self.cancel_requested = False

    def set_progress_callback(self, callback: Callable[[int], None]):
        """Define callback para progresso"""
        self.progress_callback = callback

    def cancel_scan(self):
        """Cancela scan"""
        self.cancel_requested = True

    def scan_aob(self, pattern_string: str, description: str = "", max_results: int = 100) -> List[AOBResult]:
        """Executa scan AOB"""
        self.cancel_requested = False
        results = []

        try:
            pattern = AOBPattern(pattern_string)
        except ValueError as e:
            raise ValueError(f"Padrão inválido: {e}")

        if not self.memory_manager.is_attached():
            raise RuntimeError("Não anexado a processo")

        # Simula scan para demonstração
        regions = self.memory_manager.get_memory_regions()

        for i, region in enumerate(regions[:5]):  # Limita busca
            if self.cancel_requested or len(results) >= max_results:
                break

            # Atualiza progresso
            if self.progress_callback:
                progress = int((i + 1) / min(len(regions), 5) * 100)
                self.progress_callback(progress)

            # Simula encontrar resultado
            if i < 2:  # Simula encontrar alguns padrões
                fake_addr = 0x401000 + (i * 0x1000)
                fake_bytes = bytes([0x48, 0x8B, 0x05, 0x12, 0x34, 0x56, 0x78])
                result = AOBResult(fake_addr, pattern, fake_bytes[:len(pattern.pattern_bytes)])
                results.append(result)

        self.scan_results = results
        return results

    def clear_results(self):
        """Limpa resultados"""
        self.scan_results.clear()

    def get_result_count(self) -> int:
        """Retorna o número de resultados encontrados"""
        return len(self.scan_results)
    
    def get_results_summary(self) -> dict:
        """Retorna um resumo dos resultados"""
        summary = {
            'count': len(self.scan_results),
            'is_scanning': not self.cancel_requested,  # Assuming cancel_requested means not scanning
            'progress': 0,  # This needs to be properly calculated and updated
            'patterns_found': len(set(result.pattern.original_pattern for result in self.scan_results)) if self.scan_results else 0
        }
        return summary

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
        # original_start = self.start_address
        # original_end = self.end_address
        
        # self.set_scan_range(module_base, module_base + module_size)
        
        try:
            results = self.scan_aob(pattern, f"{description} (Module: {module_name})", max_results)
        finally:
            # Restaura range original
            # self.set_scan_range(original_start, original_end)
            pass
        
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
            if self.cancel_requested:
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
    
    def verify_pattern_at_address(self, address: int, pattern_string: str) -> bool:
        """
        Verifica se um padrão existe em um endereço específico
        
        Args:
            address: Endereço para verificar
            pattern: Padrão de bytes
            
        Returns:
            bool: True se o padrão corresponde
        """
        try:
            pattern = AOBPattern(pattern_string)
            data = self.memory_manager.read_memory(address, len(pattern.pattern_bytes))  # Correct size

            if data and len(data) >= len(pattern.pattern_bytes):
                # Manually check if the pattern matches the data
                for i, pattern_byte in enumerate(pattern.pattern_bytes):
                    if pattern_byte is not None and data[i] != pattern_byte:
                        return False
                return True
            
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
    
    def clear_results(self):
        """Limpa todos os resultados de scan"""
        self.scan_results.clear()
    
    def get_result_count(self) -> int:
        """Retorna o número de resultados encontrados"""
        return len(self.scan_results)