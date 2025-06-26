"""
Módulo de Resolução de Ponteiros para PyCheatEngine
Implementa funcionalidades para resolver cadeias de ponteiros
"""

from typing import List, Optional, Any, Dict, Union
from dataclasses import dataclass

class PointerChain:
    """Representa uma cadeia de ponteiros"""

    def __init__(self, base_address: int, offsets: List[int], description: str = ""):
        self.base_address = base_address
        self.offsets = offsets
        self.description = description
        self.final_address: Optional[int] = None
        self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'base_address': self.base_address,
            'offsets': self.offsets,
            'description': self.description,
            'final_address': self.final_address,
            'is_valid': self.is_valid
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PointerChain':
        """Cria instância a partir de dicionário"""
        chain = cls(data['base_address'], data['offsets'], data.get('description', ''))
        chain.final_address = data.get('final_address')
        chain.is_valid = data.get('is_valid', False)
        return chain

class PointerResolver:
    """Resolvedor de cadeias de ponteiros"""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.pointer_chains: List[PointerChain] = []
        self.is_64bit = True  # Assume 64-bit por padrão

    def set_architecture(self, is_64bit: bool):
        """Define se o processo alvo é 64-bit ou 32-bit"""
        self.is_64bit = is_64bit

    def add_pointer_chain(self, base_address: int, offsets: List[int], description: str = "") -> PointerChain:
        """Adiciona nova cadeia de ponteiros"""
        chain = PointerChain(base_address, offsets, description)
        self.update_chain(chain)
        self.pointer_chains.append(chain)
        return chain

    def resolve_pointer_chain(self, base_address: int, offsets: List[int]) -> Optional[int]:
        """Resolve uma cadeia de ponteiros"""
        if not self.memory_manager.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        try:
            current_address = base_address

            # Segue cada offset na cadeia
            for i, offset in enumerate(offsets[:-1]):  # Todos exceto o último
                # Lê endereço atual como ponteiro
                if self.is_64bit:
                    pointer_value = self.memory_manager.read_long(current_address + offset, signed=False)
                else:
                    pointer_value = self.memory_manager.read_int(current_address + offset, signed=False)
                if pointer_value is None:
                    return None
                current_address = pointer_value

            # Aplica offset final
            if offsets:
                final_address = current_address + offsets[-1]
            else:
                final_address = current_address

            return final_address

        except Exception:
            return None

    def update_chain(self, chain: PointerChain):
        """Atualiza uma cadeia de ponteiros"""
        final_addr = self.resolve_pointer_chain(chain.base_address, chain.offsets)
        chain.final_address = final_addr
        chain.is_valid = final_addr is not None

    def update_all_chains(self):
        """Atualiza todas as cadeias"""
        for chain in self.pointer_chains:
            self.update_chain(chain)

    def get_value_from_chain(self, chain: PointerChain, data_type: str = "int32") -> Any:
        """Obtém valor de uma cadeia de ponteiros"""
        if not chain.is_valid or chain.final_address is None:
            return None

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

    def remove_pointer_chain(self, index: int) -> bool:
        """Remove cadeia de ponteiros por índice"""
        try:
            if 0 <= index < len(self.pointer_chains):
                del self.pointer_chains[index]
                return True
        except:
            pass
        return False