"""
Módulo de Resolução de Ponteiros
Implementa funcionalidades para resolver cadeias de ponteiros (pointer chains)
"""

from typing import List, Optional, Dict, Any
from memory import MemoryManager

class PointerChain:
    """Representa uma cadeia de ponteiros"""
    
    def __init__(self, base_address: int, offsets: List[int], description: str = ""):
        self.base_address = base_address
        self.offsets = offsets
        self.description = description
        self.final_address: Optional[int] = None
        self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização"""
        return {
            'base_address': self.base_address,
            'offsets': self.offsets,
            'description': self.description,
            'final_address': self.final_address,
            'is_valid': self.is_valid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PointerChain':
        """Cria uma instância a partir de um dicionário"""
        chain = cls(data['base_address'], data['offsets'], data.get('description', ''))
        chain.final_address = data.get('final_address')
        chain.is_valid = data.get('is_valid', False)
        return chain

class PointerResolver:
    """Resolvedor de cadeias de ponteiros"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.pointer_chains: List[PointerChain] = []
        self.is_64bit = True  # Assume 64-bit por padrão
    
    def set_architecture(self, is_64bit: bool):
        """Define se o processo alvo é 64-bit ou 32-bit"""
        self.is_64bit = is_64bit
    
    def resolve_pointer_chain(self, base_address: int, offsets: List[int]) -> Optional[int]:
        """
        Resolve uma cadeia de ponteiros
        
        Args:
            base_address: Endereço base (pode ser um módulo + offset)
            offsets: Lista de offsets para seguir
            
        Returns:
            int: Endereço final ou None se falhou
        """
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        try:
            current_address = base_address
            
            # Navega através dos ponteiros
            for i, offset in enumerate(offsets):
                # Lê o ponteiro no endereço atual
                if self.is_64bit:
                    pointer_value = self.memory_manager.read_long(current_address, signed=False)
                else:
                    pointer_value = self.memory_manager.read_int(current_address, signed=False)
                
                if pointer_value is None or pointer_value == 0:
                    return None
                
                # Se não é o último offset, adiciona o offset e continua
                if i < len(offsets) - 1:
                    current_address = pointer_value + offset
                else:
                    # No último offset, retorna o endereço final
                    current_address = pointer_value + offset
            
            return current_address
            
        except Exception as e:
            print(f"Erro ao resolver cadeia de ponteiros: {e}")
            return None
    
    def create_pointer_chain(self, base_address: int, offsets: List[int], 
                           description: str = "") -> PointerChain:
        """
        Cria uma nova cadeia de ponteiros
        
        Args:
            base_address: Endereço base
            offsets: Lista de offsets
            description: Descrição da cadeia
            
        Returns:
            PointerChain: Nova cadeia de ponteiros
        """
        chain = PointerChain(base_address, offsets, description)
        
        # Tenta resolver imediatamente para validar
        final_address = self.resolve_pointer_chain(base_address, offsets)
        if final_address:
            chain.final_address = final_address
            chain.is_valid = True
        
        return chain
    
    def add_pointer_chain(self, base_address: int, offsets: List[int], 
                         description: str = "") -> PointerChain:
        """Adiciona uma nova cadeia de ponteiros à lista"""
        chain = self.create_pointer_chain(base_address, offsets, description)
        self.pointer_chains.append(chain)
        return chain
    
    def remove_pointer_chain(self, index: int) -> bool:
        """Remove uma cadeia de ponteiros pelo índice"""
        try:
            if 0 <= index < len(self.pointer_chains):
                del self.pointer_chains[index]
                return True
            return False
        except:
            return False
    
    def update_all_chains(self) -> List[PointerChain]:
        """Atualiza todas as cadeias de ponteiros"""
        for chain in self.pointer_chains:
            final_address = self.resolve_pointer_chain(chain.base_address, chain.offsets)
            if final_address:
                chain.final_address = final_address
                chain.is_valid = True
            else:
                chain.is_valid = False
        
        return self.pointer_chains
    
    def get_value_from_chain(self, chain: PointerChain, data_type: str = "int32") -> Any:
        """
        Obtém o valor apontado por uma cadeia de ponteiros
        
        Args:
            chain: Cadeia de ponteiros
            data_type: Tipo de dado para ler
            
        Returns:
            Any: Valor lido ou None se falhou
        """
        if not chain.is_valid or not chain.final_address:
            # Tenta resolver novamente
            final_address = self.resolve_pointer_chain(chain.base_address, chain.offsets)
            if not final_address:
                return None
            chain.final_address = final_address
            chain.is_valid = True
        
        try:
            if data_type == "int32":
                return self.memory_manager.read_int(chain.final_address)
            elif data_type == "int64":
                return self.memory_manager.read_long(chain.final_address)
            elif data_type == "float":
                return self.memory_manager.read_float(chain.final_address)
            elif data_type == "double":
                return self.memory_manager.read_double(chain.final_address)
            elif data_type == "string":
                return self.memory_manager.read_string(chain.final_address)
            else:
                return self.memory_manager.read_memory(chain.final_address, 4)
                
        except Exception as e:
            print(f"Erro ao ler valor da cadeia de ponteiros: {e}")
            return None
    
    def set_value_from_chain(self, chain: PointerChain, value: Any, 
                           data_type: str = "int32") -> bool:
        """
        Define o valor apontado por uma cadeia de ponteiros
        
        Args:
            chain: Cadeia de ponteiros
            value: Valor para escrever
            data_type: Tipo de dado para escrever
            
        Returns:
            bool: True se escreveu com sucesso
        """
        if not chain.is_valid or not chain.final_address:
            # Tenta resolver novamente
            final_address = self.resolve_pointer_chain(chain.base_address, chain.offsets)
            if not final_address:
                return False
            chain.final_address = final_address
            chain.is_valid = True
        
        try:
            if data_type == "int32":
                return self.memory_manager.write_int(chain.final_address, int(value))
            elif data_type == "int64":
                return self.memory_manager.write_long(chain.final_address, int(value))
            elif data_type == "float":
                return self.memory_manager.write_float(chain.final_address, float(value))
            elif data_type == "double":
                return self.memory_manager.write_double(chain.final_address, float(value))
            elif data_type == "string":
                return self.memory_manager.write_string(chain.final_address, str(value))
            else:
                if isinstance(value, str):
                    value = bytes.fromhex(value.replace(' ', ''))
                return self.memory_manager.write_memory(chain.final_address, value)
                
        except Exception as e:
            print(f"Erro ao escrever valor na cadeia de ponteiros: {e}")
            return False
    
    def find_pointer_chains(self, target_address: int, max_depth: int = 5, 
                          max_offset: int = 0x1000) -> List[PointerChain]:
        """
        Tenta encontrar cadeias de ponteiros que apontam para um endereço alvo
        
        Args:
            target_address: Endereço alvo
            max_depth: Profundidade máxima da busca
            max_offset: Offset máximo para considerar
            
        Returns:
            List[PointerChain]: Lista de cadeias encontradas
        """
        if not self.memory_manager.is_attached():
            return []
        
        found_chains = []
        
        # Esta é uma implementação simplificada
        # Em uma implementação completa, isso seria muito mais complexo
        # e envolveria varrer grandes regiões de memória
        
        try:
            # Busca ponteiros diretos (profundidade 1)
            for base in range(0x400000, 0x800000, 0x1000):  # Range típico de módulos
                try:
                    if self.is_64bit:
                        value = self.memory_manager.read_long(base, signed=False)
                    else:
                        value = self.memory_manager.read_int(base, signed=False)
                    
                    if value:
                        # Verifica se aponta próximo ao endereço alvo
                        diff = abs(value - target_address)
                        if diff <= max_offset:
                            offset = target_address - value
                            chain = self.create_pointer_chain(base, [offset], 
                                                            f"Direct pointer (offset: {offset})")
                            if chain.is_valid:
                                found_chains.append(chain)
                
                except:
                    continue
        
        except Exception as e:
            print(f"Erro ao procurar cadeias de ponteiros: {e}")
        
        return found_chains
    
    def validate_chain(self, chain: PointerChain) -> bool:
        """Valida se uma cadeia de ponteiros ainda é válida"""
        final_address = self.resolve_pointer_chain(chain.base_address, chain.offsets)
        chain.is_valid = final_address is not None
        if final_address:
            chain.final_address = final_address
        return chain.is_valid
    
    def get_chains_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das cadeias de ponteiros"""
        valid_chains = sum(1 for chain in self.pointer_chains if chain.is_valid)
        return {
            'total_chains': len(self.pointer_chains),
            'valid_chains': valid_chains,
            'invalid_chains': len(self.pointer_chains) - valid_chains
        }
