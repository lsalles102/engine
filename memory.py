"""
Módulo de Leitura e Escrita de Memória
Fornece funcionalidades para ler e escrever diferentes tipos de dados na memória de processos
"""

import struct
import psutil
import platform
import os
from typing import Optional, Union, List

# Detecta plataforma
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

if IS_WINDOWS:
    import ctypes
    import ctypes.wintypes
    
    # Constantes do Windows
    PROCESS_ALL_ACCESS = 0x1F0FFF
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_WRITE = 0x0020
    PROCESS_VM_OPERATION = 0x0008
    PROCESS_QUERY_INFORMATION = 0x0400
    
    # Bibliotecas do Windows
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi

class MemoryManager:
    """Gerenciador de memória para leitura e escrita em processos"""
    
    def __init__(self):
        self.process_handle = None
        self.process_id = None
        self.process_name = None
        self.mem_file = None  # Para Linux
    
    def attach_to_process(self, process_id: int) -> bool:
        """
        Anexa ao processo especificado pelo ID
        
        Args:
            process_id: ID do processo alvo
            
        Returns:
            bool: True se anexou com sucesso, False caso contrário
        """
        try:
            if IS_WINDOWS:
                # Windows: usa APIs nativas
                self.process_handle = kernel32.OpenProcess(
                    PROCESS_ALL_ACCESS,
                    False,
                    process_id
                )
                
                if not self.process_handle:
                    self.process_handle = kernel32.OpenProcess(
                        PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION,
                        False,
                        process_id
                    )
                
                if self.process_handle:
                    self.process_id = process_id
                    try:
                        process = psutil.Process(process_id)
                        self.process_name = process.name()
                    except:
                        self.process_name = f"PID_{process_id}"
                    return True
                
                return False
            
            elif IS_LINUX:
                # Linux: usa /proc/PID/mem
                try:
                    self.mem_file = open(f"/proc/{process_id}/mem", "rb+")
                    self.process_id = process_id
                    try:
                        process = psutil.Process(process_id)
                        self.process_name = process.name()
                    except:
                        self.process_name = f"PID_{process_id}"
                    return True
                except (OSError, PermissionError):
                    print(f"Erro: Sem permissão para acessar processo {process_id}")
                    print("Execute com sudo ou verifique se o processo existe")
                    return False
            
            else:
                print(f"Plataforma {platform.system()} não suportada")
                return False
            
        except Exception as e:
            print(f"Erro ao anexar ao processo {process_id}: {e}")
            return False
    
    def detach_process(self):
        """Desanexa do processo atual"""
        if self.process_handle:
            kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
            self.process_id = None
            self.process_name = None
    
    def is_attached(self) -> bool:
        """Verifica se está anexado a um processo"""
        return self.process_handle is not None
    
    def read_memory(self, address: int, size: int) -> Optional[bytes]:
        """
        Lê dados brutos da memória
        
        Args:
            address: Endereço de memória
            size: Número de bytes para ler
            
        Returns:
            bytes: Dados lidos ou None se falhou
        """
        if not self.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        try:
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()
            
            success = kernel32.ReadProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                buffer,
                size,
                ctypes.byref(bytes_read)
            )
            
            if success and bytes_read.value == size:
                return buffer.raw
            
            return None
            
        except Exception as e:
            print(f"Erro ao ler memória no endereço 0x{address:X}: {e}")
            return None
    
    def write_memory(self, address: int, data: bytes) -> bool:
        """
        Escreve dados na memória
        
        Args:
            address: Endereço de memória
            data: Dados para escrever
            
        Returns:
            bool: True se escreveu com sucesso, False caso contrário
        """
        if not self.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        try:
            if IS_WINDOWS:
                bytes_written = ctypes.c_size_t()
                
                success = kernel32.WriteProcessMemory(
                    self.process_handle,
                    ctypes.c_void_p(address),
                    data,
                    len(data),
                    ctypes.byref(bytes_written)
                )
                
                return success and bytes_written.value == len(data)
            
            elif IS_LINUX:
                # Linux: escreve no arquivo /proc/PID/mem
                self.mem_file.seek(address)
                written = self.mem_file.write(data)
                self.mem_file.flush()
                return written == len(data)
            
            return False
            
        except Exception as e:
            print(f"Erro ao escrever memória no endereço 0x{address:X}: {e}")
            return False
    
    def read_int(self, address: int) -> Optional[int]:
        """Lê um inteiro de 32 bits"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<i', data)[0]
        return None
    
    def read_long(self, address: int) -> Optional[int]:
        """Lê um inteiro de 64 bits"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<q', data)[0]
        return None
    
    def read_float(self, address: int) -> Optional[float]:
        """Lê um float de 32 bits"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<f', data)[0]
        return None
    
    def read_double(self, address: int) -> Optional[float]:
        """Lê um double de 64 bits"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<d', data)[0]
        return None
    
    def read_string(self, address: int, max_length: int = 256) -> Optional[str]:
        """Lê uma string terminada em null"""
        data = self.read_memory(address, max_length)
        if data:
            # Encontra o terminador null
            null_pos = data.find(b'\x00')
            if null_pos != -1:
                data = data[:null_pos]
            try:
                return data.decode('utf-8', errors='ignore')
            except:
                return data.decode('latin-1', errors='ignore')
        return None
    
    def write_int(self, address: int, value: int) -> bool:
        """Escreve um inteiro de 32 bits"""
        data = struct.pack('<i', value)
        return self.write_memory(address, data)
    
    def write_long(self, address: int, value: int) -> bool:
        """Escreve um inteiro de 64 bits"""
        data = struct.pack('<q', value)
        return self.write_memory(address, data)
    
    def write_float(self, address: int, value: float) -> bool:
        """Escreve um float de 32 bits"""
        data = struct.pack('<f', value)
        return self.write_memory(address, data)
    
    def write_double(self, address: int, value: float) -> bool:
        """Escreve um double de 64 bits"""
        data = struct.pack('<d', value)
        return self.write_memory(address, data)
    
    def write_string(self, address: int, value: str) -> bool:
        """Escreve uma string terminada em null"""
        data = value.encode('utf-8') + b'\x00'
        return self.write_memory(address, data)
    
    def get_process_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o processo anexado"""
        if not self.is_attached():
            return {}
        
        try:
            process = psutil.Process(self.process_id)
            return {
                'pid': self.process_id,
                'name': self.process_name,
                'exe': process.exe(),
                'cmdline': ' '.join(process.cmdline()),
                'memory_info': process.memory_info()._asdict(),
                'cpu_percent': process.cpu_percent(),
                'status': process.status(),
                'create_time': process.create_time()
            }
        except:
            return {
                'pid': self.process_id,
                'name': self.process_name
            }
    
    def list_processes(self) -> List[Dict[str, Any]]:
        """Lista todos os processos disponíveis"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info']):
            try:
                info = proc.info
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'] or 'Unknown',
                    'exe': info['exe'] or 'Unknown',
                    'memory_mb': info['memory_info'].rss / (1024*1024) if info['memory_info'] else 0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)
    
    def get_memory_regions(self) -> List[Dict[str, Any]]:
        """Obtém regiões de memória do processo (Windows)"""
        if not self.is_attached() or not IS_WINDOWS:
            return []
        
        regions = []
        try:
            import ctypes.wintypes
            
            class MEMORY_BASIC_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("BaseAddress", ctypes.c_void_p),
                    ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", ctypes.wintypes.DWORD),
                    ("RegionSize", ctypes.c_size_t),
                    ("State", ctypes.wintypes.DWORD),
                    ("Protect", ctypes.wintypes.DWORD),
                    ("Type", ctypes.wintypes.DWORD)
                ]
            
            mbi = MEMORY_BASIC_INFORMATION()
            address = 0
            
            while address < 0x7FFFFFFF:
                if kernel32.VirtualQueryEx(
                    self.process_handle,
                    ctypes.c_void_p(address),
                    ctypes.byref(mbi),
                    ctypes.sizeof(mbi)
                ):
                    if mbi.State == 0x1000:  # MEM_COMMIT
                        regions.append({
                            'base_address': mbi.BaseAddress,
                            'size': mbi.RegionSize,
                            'protect': mbi.Protect,
                            'readable': bool(mbi.Protect & 0x44),  # PAGE_READONLY | PAGE_READWRITE
                            'writable': bool(mbi.Protect & 0x04),  # PAGE_READWRITE
                            'executable': bool(mbi.Protect & 0x20) # PAGE_EXECUTE_READ
                        })
                    
                    address = mbi.BaseAddress + mbi.RegionSize
                else:
                    address += 0x1000
            
        except Exception as e:
            print(f"Erro ao obter regiões de memória: {e}")
        
        return regions
        
        Args:
            address: Endereço de memória
            data: Dados para escrever
            
        Returns:
            bool: True se escreveu com sucesso, False caso contrário
        """
        if not self.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        try:
            if IS_WINDOWS:
                bytes_written = ctypes.c_size_t()
                
                success = kernel32.WriteProcessMemory(
                    self.process_handle,
                    ctypes.c_void_p(address),
                    data,
                    len(data),
                    ctypes.byref(bytes_written)
                )
                
                return success and bytes_written.value == len(data)
            
            elif IS_LINUX:
                self.mem_file.seek(address)
                self.mem_file.write(data)
                self.mem_file.flush()
                return True
            
            return False
            
        except Exception as e:
            print(f"Erro ao escrever memória no endereço 0x{address:X}: {e}")
            return False
    
    def read_int(self, address: int) -> Optional[int]:
        """Lê um inteiro de 32 bits"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<i', data)[0]
        return None
    
    def read_long(self, address: int) -> Optional[int]:
        """Lê um inteiro de 64 bits"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<q', data)[0]
        return None
    
    def read_float(self, address: int) -> Optional[float]:
        """Lê um float de 32 bits"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<f', data)[0]
        return None
    
    def read_double(self, address: int) -> Optional[float]:
        """Lê um double de 64 bits"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<d', data)[0]
        return None
    
    def read_string(self, address: int, max_length: int = 256) -> Optional[str]:
        """Lê uma string terminada em null"""
        data = self.read_memory(address, max_length)
        if data:
            try:
                # Encontra o terminador null
                null_pos = data.find(b'\x00')
                if null_pos >= 0:
                    data = data[:null_pos]
                return data.decode('utf-8', errors='ignore')
            except:
                return None
        return None
    
    def write_int(self, address: int, value: int) -> bool:
        """Escreve um inteiro de 32 bits"""
        data = struct.pack('<i', value)
        return self.write_memory(address, data)
    
    def write_long(self, address: int, value: int) -> bool:
        """Escreve um inteiro de 64 bits"""
        data = struct.pack('<q', value)
        return self.write_memory(address, data)
    
    def write_float(self, address: int, value: float) -> bool:
        """Escreve um float de 32 bits"""
        data = struct.pack('<f', value)
        return self.write_memory(address, data)
    
    def write_double(self, address: int, value: float) -> bool:
        """Escreve um double de 64 bits"""
        data = struct.pack('<d', value)
        return self.write_memory(address, data)
    
    def write_string(self, address: int, value: str) -> bool:
        """Escreve uma string"""
        data = value.encode('utf-8') + b'\x00'
        return self.write_memory(address, data)
    
    def get_process_modules(self) -> List[Dict]:
        """Obtém lista de módulos do processo"""
        if not self.is_attached():
            return []
        
        modules = []
        try:
            process = psutil.Process(self.process_id)
            for module in process.memory_maps():
                modules.append({
                    'name': os.path.basename(module.path),
                    'path': module.path,
                    'base_address': int(module.addr.split('-')[0], 16),
                    'size': module.rss if hasattr(module, 'rss') else 0
                })
        except Exception as e:
            print(f"Erro ao obter módulos: {e}")
        
        return modules
    
    def get_memory_regions(self) -> List[Dict]:
        """Obtém regiões de memória do processo"""
        if not self.is_attached():
            return []
        
        regions = []
        try:
            process = psutil.Process(self.process_id)
            for region in process.memory_maps():
                addr_range = region.addr.split('-')
                start_addr = int(addr_range[0], 16)
                end_addr = int(addr_range[1], 16)
                
                regions.append({
                    'start_address': start_addr,
                    'end_address': end_addr,
                    'size': end_addr - start_addr,
                    'path': region.path,
                    'permissions': getattr(region, 'perms', 'unknown')
                })
        except Exception as e:
            print(f"Erro ao obter regiões de memória: {e}")
        
        return regions
        
        Args:
            address: Endereço de memória
            data: Dados para escrever
            
        Returns:
            bool: True se escreveu com sucesso
        """
        if not self.is_attached():
            raise RuntimeError("Não está anexado a nenhum processo")
        
        try:
            bytes_written = ctypes.c_size_t()
            
            success = kernel32.WriteProcessMemory(
                self.process_handle,
                ctypes.c_void_p(address),
                data,
                len(data),
                ctypes.byref(bytes_written)
            )
            
            return success and bytes_written.value == len(data)
            
        except Exception as e:
            print(f"Erro ao escrever memória no endereço 0x{address:X}: {e}")
            return False
    
    def read_int(self, address: int, signed: bool = True) -> Optional[int]:
        """Lê um valor inteiro de 32 bits"""
        data = self.read_memory(address, 4)
        if data:
            fmt = '<i' if signed else '<I'
            return struct.unpack(fmt, data)[0]
        return None
    
    def write_int(self, address: int, value: int, signed: bool = True) -> bool:
        """Escreve um valor inteiro de 32 bits"""
        fmt = '<i' if signed else '<I'
        data = struct.pack(fmt, value)
        return self.write_memory(address, data)
    
    def read_long(self, address: int, signed: bool = True) -> Optional[int]:
        """Lê um valor inteiro de 64 bits"""
        data = self.read_memory(address, 8)
        if data:
            fmt = '<q' if signed else '<Q'
            return struct.unpack(fmt, data)[0]
        return None
    
    def write_long(self, address: int, value: int, signed: bool = True) -> bool:
        """Escreve um valor inteiro de 64 bits"""
        fmt = '<q' if signed else '<Q'
        data = struct.pack(fmt, value)
        return self.write_memory(address, data)
    
    def read_float(self, address: int) -> Optional[float]:
        """Lê um valor float de 32 bits"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<f', data)[0]
        return None
    
    def write_float(self, address: int, value: float) -> bool:
        """Escreve um valor float de 32 bits"""
        data = struct.pack('<f', value)
        return self.write_memory(address, data)
    
    def read_double(self, address: int) -> Optional[float]:
        """Lê um valor double de 64 bits"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('<d', data)[0]
        return None
    
    def write_double(self, address: int, value: float) -> bool:
        """Escreve um valor double de 64 bits"""
        data = struct.pack('<d', value)
        return self.write_memory(address, data)
    
    def read_string(self, address: int, length: int = 256, encoding: str = 'utf-8') -> Optional[str]:
        """
        Lê uma string da memória
        
        Args:
            address: Endereço da string
            length: Tamanho máximo para ler
            encoding: Codificação da string
            
        Returns:
            str: String lida ou None se falhou
        """
        data = self.read_memory(address, length)
        if data:
            try:
                # Procura pelo terminador null
                null_pos = data.find(b'\x00')
                if null_pos != -1:
                    data = data[:null_pos]
                
                return data.decode(encoding, errors='ignore')
            except:
                return None
        return None
    
    def write_string(self, address: int, value: str, encoding: str = 'utf-8') -> bool:
        """
        Escreve uma string na memória
        
        Args:
            address: Endereço para escrever
            value: String para escrever
            encoding: Codificação da string
            
        Returns:
            bool: True se escreveu com sucesso
        """
        try:
            data = value.encode(encoding) + b'\x00'  # Adiciona terminador null
            return self.write_memory(address, data)
        except:
            return False
    
    def get_module_base_address(self, module_name: str) -> Optional[int]:
        """
        Obtém o endereço base de um módulo
        
        Args:
            module_name: Nome do módulo (ex: "game.exe")
            
        Returns:
            int: Endereço base do módulo ou None se não encontrado
        """
        if not self.is_attached():
            return None
        
        try:
            # Enumera módulos do processo
            modules = (ctypes.wintypes.HMODULE * 1024)()
            cb_needed = ctypes.wintypes.DWORD()
            
            if psapi.EnumProcessModules(
                self.process_handle,
                ctypes.byref(modules),
                ctypes.sizeof(modules),
                ctypes.byref(cb_needed)
            ):
                module_count = cb_needed.value // ctypes.sizeof(ctypes.wintypes.HMODULE)
                
                for i in range(module_count):
                    module_name_buffer = ctypes.create_string_buffer(260)
                    
                    if psapi.GetModuleBaseNameA(
                        self.process_handle,
                        modules[i],
                        module_name_buffer,
                        260
                    ):
                        current_name = module_name_buffer.value.decode('utf-8', errors='ignore')
                        if current_name.lower() == module_name.lower():
                            return modules[i]
            
            return None
            
        except Exception as e:
            print(f"Erro ao obter endereço base do módulo {module_name}: {e}")
            return None
    
    @staticmethod
    def list_processes() -> List[dict]:
        """
        Lista todos os processos em execução
        
        Returns:
            List[dict]: Lista de processos com PID e nome
        """
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
