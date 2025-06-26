"""
Módulo de Gerenciamento de Memória para PyCheatEngine
Implementa funcionalidades para leitura e escrita na memória de processos
"""

import ctypes
import ctypes.wintypes
import struct
import sys
import platform
from typing import List, Dict, Any, Optional, Tuple
import psutil

# Detecta plataforma
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Windows API
if IS_WINDOWS:
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi

    # Constantes Windows
    PROCESS_ALL_ACCESS = 0x1F0FFF
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_WRITE = 0x0020
    PROCESS_VM_OPERATION = 0x0008
    PROCESS_QUERY_INFORMATION = 0x0400

class MemoryManager:
    """Gerenciador de memória para leitura/escrita em processos"""

    def __init__(self):
        """Inicializa o gerenciador de memória"""
        self.process_id = None
        self.process_handle = None
        self.mem_file = None

    def attach_to_process(self, process_id: int) -> bool:
        """
        Anexa ao processo especificado

        Args:
            process_id: ID do processo

        Returns:
            bool: True se anexou com sucesso
        """
        try:
            if IS_WINDOWS:
                # Windows: usa OpenProcess
                self.process_handle = kernel32.OpenProcess(
                    PROCESS_ALL_ACCESS,
                    False,
                    process_id
                )

                if not self.process_handle:
                    print(f"Erro ao abrir processo {process_id}")
                    return False

            elif IS_LINUX:
                # Linux: abre /proc/PID/mem
                try:
                    self.mem_file = open(f'/proc/{process_id}/mem', 'r+b')
                except PermissionError:
                    print(f"Sem permissão para acessar processo {process_id}")
                    return False
                except FileNotFoundError:
                    print(f"Processo {process_id} não encontrado")
                    return False

            self.process_id = process_id
            print(f"Anexado ao processo {process_id}")
            return True

        except Exception as e:
            print(f"Erro ao anexar ao processo {process_id}: {e}")
            return False

    def is_attached(self) -> bool:
        """Verifica se está anexado a um processo"""
        return self.process_id is not None and (
            (IS_WINDOWS and self.process_handle) or 
            (IS_LINUX and self.mem_file)
        )

    def read_memory(self, address: int, size: int) -> Optional[bytes]:
        """
        Lê dados da memória do processo

        Args:
            address: Endereço de memória
            size: Número de bytes para ler

        Returns:
            bytes: Dados lidos ou None se falhou
        """
        if not self.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")

        # Validação mais rigorosa de endereços
        if not isinstance(address, int) or address < 0:
            return None

        # Limite máximo baseado na arquitetura
        max_address = 0x7FFFFFFF if platform.machine().endswith('32') else 0x7FFFFFFFFFFFFFFF
        if address > max_address:
            return None

        if not isinstance(size, int) or size <= 0 or size > 0x100000:  # Máximo 1MB
            return None

        # Verifica overflow na soma
        try:
            end_address = address + size
            if end_address < address or end_address > max_address:
                return None
        except OverflowError:
            return None

        try:
            if IS_WINDOWS:
                buffer = ctypes.create_string_buffer(size)
                bytes_read = ctypes.c_size_t()

                success = kernel32.ReadProcessMemory(
                    self.process_handle,
                    ctypes.c_void_p(address),
                    buffer,
                    ctypes.c_size_t(size),
                    ctypes.byref(bytes_read)
                )

                if success and bytes_read.value == size:
                    return buffer.raw

            elif IS_LINUX:
                self.mem_file.seek(address)
                data = self.mem_file.read(size)
                return data if len(data) == size else None

            return None

        except Exception as e:
            print(f"Erro ao ler memória no endereço 0x{address:X}: {e}")
            return None

    def write_memory(self, address: int, data: bytes) -> bool:
        """
        Escreve dados na memória do processo

        Args:
            address: Endereço de memória
            data: Dados para escrever

        Returns:
            bool: True se escreveu com sucesso
        """
        if not self.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")

        if address < 0 or address > 0x7FFFFFFFFFFFFFFF:
            return False

        if len(data) <= 0 or len(data) > 0x10000:
            return False

        try:
            if IS_WINDOWS:
                bytes_written = ctypes.c_size_t()

                success = kernel32.WriteProcessMemory(
                    self.process_handle,
                    ctypes.c_void_p(address),
                    data,
                    ctypes.c_size_t(len(data)),
                    ctypes.byref(bytes_written)
                )

                return success and bytes_written.value == len(data)

            elif IS_LINUX:
                self.mem_file.seek(address)
                written = self.mem_file.write(data)
                self.mem_file.flush()
                return written == len(data)

            return False

        except Exception as e:
            print(f"Erro ao escrever memória no endereço 0x{address:X}: {e}")
            return False

    def read_int32(self, address: int) -> Optional[int]:
        """Lê um inteiro de 32 bits"""
        data = self.read_memory(address, 4)
        if data and len(data) == 4:
            try:
                return struct.unpack('<i', data)[0]
            except struct.error:
                return None
        return None

    def write_int32(self, address: int, value: int) -> bool:
        """Escreve um inteiro de 32 bits"""
        try:
            data = struct.pack('<i', value)
            return self.write_memory(address, data)
        except struct.error:
            return False

    def read_int64(self, address: int) -> Optional[int]:
        """Lê um inteiro de 64 bits"""
        data = self.read_memory(address, 8)
        if data and len(data) == 8:
            try:
                return struct.unpack('<q', data)[0]
            except struct.error:
                return None
        return None

    def write_int64(self, address: int, value: int) -> bool:
        """Escreve um inteiro de 64 bits"""
        try:
            data = struct.pack('<q', value)
            return self.write_memory(address, data)
        except struct.error:
            return False

    def read_float(self, address: int) -> Optional[float]:
        """Lê um float de 32 bits"""
        data = self.read_memory(address, 4)
        if data and len(data) == 4:
            try:
                return struct.unpack('<f', data)[0]
            except struct.error:
                return None
        return None

    def write_float(self, address: int, value: float) -> bool:
        """Escreve um float de 32 bits"""
        try:
            data = struct.pack('<f', value)
            return self.write_memory(address, data)
        except struct.error:
            return False

    def read_double(self, address: int) -> Optional[float]:
        """Lê um double de 64 bits"""
        data = self.read_memory(address, 8)
        if data and len(data) == 8:
            try:
                return struct.unpack('<d', data)[0]
            except struct.error:
                return None
        return None

    def write_double(self, address: int, value: float) -> bool:
        """Escreve um double de 64 bits"""
        try:
            data = struct.pack('<d', value)
            return self.write_memory(address, data)
        except struct.error:
            return False

    def read_string(self, address: int, max_length: int = 256, encoding: str = 'utf-8') -> Optional[str]:
        """Lê uma string da memória"""
        data = self.read_memory(address, max_length)
        if data:
            try:
                # Encontra o terminador null
                null_pos = data.find(b'\x00')
                if null_pos != -1:
                    data = data[:null_pos]
                return data.decode(encoding, errors='ignore')
            except UnicodeDecodeError:
                return None
        return None

    def write_string(self, address: int, value: str, encoding: str = 'utf-8') -> bool:
        """Escreve uma string na memória"""
        try:
            data = value.encode(encoding) + b'\x00'
            return self.write_memory(address, data)
        except UnicodeEncodeError:
            return False

    @staticmethod
    def list_processes() -> List[dict]:
        """Lista todos os processos em execução"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Erro ao listar processos: {e}")

        return sorted(processes, key=lambda x: x['name'].lower())

    def get_memory_regions(self) -> List[Dict[str, Any]]:
        """Obtém regiões de memória do processo"""
        regions = []

        if not self.is_attached():
            return regions

        try:
            if IS_WINDOWS:
                # Windows: usa VirtualQueryEx
                address = 0
                while address < 0x7FFFFFFF:
                    mbi = ctypes.wintypes.MEMORY_BASIC_INFORMATION()

                    result = kernel32.VirtualQueryEx(
                        self.process_handle,
                        ctypes.c_void_p(address),
                        ctypes.byref(mbi),
                        ctypes.sizeof(mbi)
                    )

                    if result == 0:
                        break

                    if mbi.State == 0x1000:  # MEM_COMMIT
                        regions.append({
                            'base': mbi.BaseAddress,
                            'size': mbi.RegionSize,
                            'protect': mbi.Protect,
                            'state': mbi.State,
                            'type': mbi.Type
                        })

                    address = mbi.BaseAddress + mbi.RegionSize

            elif IS_LINUX:
                # Linux: lê /proc/PID/maps
                with open(f'/proc/{self.process_id}/maps', 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            addr_range = parts[0].split('-')
                            start = int(addr_range[0], 16)
                            end = int(addr_range[1], 16)

                            regions.append({
                                'base': start,
                                'size': end - start,
                                'permissions': parts[1] if len(parts) > 1 else '',
                                'pathname': parts[-1] if len(parts) > 5 else ''
                            })

        except Exception as e:
            print(f"Erro ao obter regiões de memória: {e}")

        return regions

    def detach_process(self):
        """Desanexa do processo atual"""
        self.close()

    def close(self):
        """Fecha todas as conexões e libera recursos"""
        try:
            if IS_WINDOWS and self.process_handle:
                kernel32.CloseHandle(self.process_handle)
                self.process_handle = None

            elif IS_LINUX and self.mem_file:
                self.mem_file.close()
                self.mem_file = None

            self.process_id = None
            print("Conexões fechadas com sucesso")

        except Exception as e:
            print(f"Erro ao fechar conexões: {e}")

    def get_process_info(self) -> Dict[str, Any]:
        """Retorna informações do processo anexado"""
        if not self.is_attached():
            return {}
        
        info = {
            'process_id': self.process_id,
            'attached': True,
            'platform': platform.system()
        }
        
        # Adiciona nome do processo se disponível
        try:
            import psutil
            process = psutil.Process(self.process_id)
            info['process_name'] = process.name()
            info['memory_usage'] = process.memory_info().rss
            info['cpu_percent'] = process.cpu_percent()
        except:
            info['process_name'] = f"PID_{self.process_id}"
        
        return info
    
    @property
    def process_name(self) -> str:
        """Propriedade para obter nome do processo"""
        info = self.get_process_info()
        return info.get('process_name', f"PID_{self.process_id}")

    def __del__(self):
        """Destrutor para garantir limpeza de recursos"""
        try:
            self.close()
        except:
            pass