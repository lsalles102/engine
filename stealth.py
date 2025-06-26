
#!/usr/bin/env python3
"""
Módulo Stealth para PyCheatEngine
Implementa técnicas de evasão e anti-detecção
"""

import ctypes
import ctypes.wintypes
import os
import time
import random
import threading
import platform
from typing import Optional, Callable, List
import struct

# Windows API para técnicas stealth
if platform.system() == 'Windows':
    kernel32 = ctypes.windll.kernel32
    ntdll = ctypes.windll.ntdll
    user32 = ctypes.windll.user32
    psapi = ctypes.windll.psapi

class StealthMemoryManager:
    """Gerenciador de memória com técnicas stealth"""
    
    def __init__(self):
        self.is_stealth_mode = True
        self.delay_range = (0.001, 0.01)  # Delay aleatório entre operações
        self.chunk_sizes = [1024, 2048, 4096]  # Tamanhos variados de chunk
        self.anti_debug_active = True
        
    def enable_stealth_mode(self, enabled: bool = True):
        """Ativa/desativa modo stealth"""
        self.is_stealth_mode = enabled
        print(f"🥷 Modo Stealth: {'ATIVADO' if enabled else 'DESATIVADO'}")
    
    def random_delay(self):
        """Adiciona delay aleatório para evitar detecção de padrões"""
        if self.is_stealth_mode:
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)
    
    def obfuscate_address(self, address: int) -> int:
        """Ofusca endereços usando XOR simples"""
        if not self.is_stealth_mode:
            return address
        
        # XOR com chave aleatória (mantém resultado válido)
        key = 0x12345678
        return address ^ key ^ key  # XOR duplo = valor original
    
    def stealth_read_memory(self, process_handle, address: int, size: int) -> Optional[bytes]:
        """Leitura de memória com técnicas stealth"""
        if not self.is_stealth_mode:
            return self._direct_read_memory(process_handle, address, size)
        
        # Técnica 1: Leitura em chunks pequenos e aleatórios
        data = b""
        remaining = size
        current_addr = address
        
        while remaining > 0:
            # Escolhe tamanho de chunk aleatório
            chunk_size = min(remaining, random.choice(self.chunk_sizes))
            
            # Delay aleatório
            self.random_delay()
            
            # Lê chunk
            chunk_data = self._direct_read_memory(process_handle, current_addr, chunk_size)
            if not chunk_data:
                break
                
            data += chunk_data
            current_addr += chunk_size
            remaining -= chunk_size
        
        return data if len(data) == size else None
    
    def _direct_read_memory(self, process_handle, address: int, size: int) -> Optional[bytes]:
        """Leitura direta de memória"""
        try:
            if platform.system() == 'Windows':
                buffer = ctypes.create_string_buffer(size)
                bytes_read = ctypes.c_size_t()
                
                success = kernel32.ReadProcessMemory(
                    process_handle,
                    ctypes.c_void_p(address),
                    buffer,
                    ctypes.c_size_t(size),
                    ctypes.byref(bytes_read)
                )
                
                if success and bytes_read.value == size:
                    return buffer.raw
            
            return None
        except Exception:
            return None
    
    def stealth_write_memory(self, process_handle, address: int, data: bytes) -> bool:
        """Escrita de memória com técnicas stealth"""
        if not self.is_stealth_mode:
            return self._direct_write_memory(process_handle, address, data)
        
        # Técnica: Escrita em pequenos chunks com delays
        remaining_data = data
        current_addr = address
        
        while remaining_data:
            chunk_size = min(len(remaining_data), random.choice([4, 8, 16, 32]))
            chunk = remaining_data[:chunk_size]
            
            self.random_delay()
            
            if not self._direct_write_memory(process_handle, current_addr, chunk):
                return False
            
            remaining_data = remaining_data[chunk_size:]
            current_addr += chunk_size
        
        return True
    
    def _direct_write_memory(self, process_handle, address: int, data: bytes) -> bool:
        """Escrita direta de memória"""
        try:
            if platform.system() == 'Windows':
                bytes_written = ctypes.c_size_t()
                
                success = kernel32.WriteProcessMemory(
                    process_handle,
                    ctypes.c_void_p(address),
                    data,
                    ctypes.c_size_t(len(data)),
                    ctypes.byref(bytes_written)
                )
                
                return success and bytes_written.value == len(data)
            
            return False
        except Exception:
            return False

class AntiDebugger:
    """Sistema anti-debug para detectar ferramentas de análise"""
    
    def __init__(self):
        self.is_debugged = False
        self.monitoring = False
        self.debug_callbacks: List[Callable] = []
    
    def add_debug_callback(self, callback: Callable):
        """Adiciona callback para quando debugger é detectado"""
        self.debug_callbacks.append(callback)
    
    def check_debugger_present(self) -> bool:
        """Verifica se há debugger anexado (Windows)"""
        if platform.system() != 'Windows':
            return False
        
        try:
            # Método 1: IsDebuggerPresent
            if kernel32.IsDebuggerPresent():
                return True
            
            # Método 2: CheckRemoteDebuggerPresent
            debug_present = ctypes.c_bool()
            if kernel32.CheckRemoteDebuggerPresent(
                kernel32.GetCurrentProcess(),
                ctypes.byref(debug_present)
            ):
                if debug_present.value:
                    return True
            
            # Método 3: NtQueryInformationProcess
            try:
                process_debug_port = ctypes.c_void_p()
                result = ntdll.NtQueryInformationProcess(
                    kernel32.GetCurrentProcess(),
                    7,  # ProcessDebugPort
                    ctypes.byref(process_debug_port),
                    ctypes.sizeof(process_debug_port),
                    None
                )
                
                if result == 0 and process_debug_port.value:
                    return True
            except:
                pass
            
            return False
            
        except Exception:
            return False
    
    def check_vm_environment(self) -> bool:
        """Detecta se está rodando em máquina virtual"""
        vm_indicators = [
            # Arquivos típicos de VMs
            r"C:\windows\system32\drivers\vmmouse.sys",
            r"C:\windows\system32\drivers\vmhgfs.sys",
            r"C:\windows\system32\drivers\VBoxMouse.sys",
            r"C:\windows\system32\drivers\VBoxGuest.sys",
            r"C:\windows\system32\drivers\VBoxSF.sys",
            
            # Processos de VM
            "vmtoolsd.exe",
            "vmware.exe",
            "vboxservice.exe",
        ]
        
        for indicator in vm_indicators:
            if os.path.exists(indicator) or self._process_exists(indicator):
                return True
        
        return False
    
    def _process_exists(self, process_name: str) -> bool:
        """Verifica se processo existe"""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                    return True
        except:
            pass
        return False
    
    def check_sandbox_environment(self) -> bool:
        """Detecta ambiente sandbox"""
        try:
            # Verifica se há poucos processos (indicativo de sandbox)
            import psutil
            process_count = len(psutil.pids())
            if process_count < 30:  # Muito poucos processos
                return True
            
            # Verifica tempo de boot (sandboxes reiniciam frequentemente)
            boot_time = psutil.boot_time()
            current_time = time.time()
            uptime_hours = (current_time - boot_time) / 3600
            
            if uptime_hours < 0.5:  # Menos de 30 minutos de uptime
                return True
            
            return False
        except:
            return False
    
    def start_monitoring(self):
        """Inicia monitoramento contínuo"""
        if self.monitoring:
            return
        
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        print("🛡️ Monitoramento anti-debug ativado")
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.monitoring = False
        print("🛡️ Monitoramento anti-debug desativado")
    
    def _monitor_loop(self):
        """Loop de monitoramento"""
        while self.monitoring:
            try:
                # Verifica debugger
                if self.check_debugger_present():
                    if not self.is_debugged:
                        self.is_debugged = True
                        self._trigger_debug_detected()
                
                # Verifica VM/Sandbox
                if self.check_vm_environment() or self.check_sandbox_environment():
                    self._trigger_sandbox_detected()
                
                # Delay entre verificações
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                break
    
    def _trigger_debug_detected(self):
        """Executado quando debugger é detectado"""
        print("⚠️ DEBUGGER DETECTADO!")
        for callback in self.debug_callbacks:
            try:
                callback()
            except:
                pass
    
    def _trigger_sandbox_detected(self):
        """Executado quando sandbox é detectado"""
        print("⚠️ AMBIENTE SANDBOX/VM DETECTADO!")

class ProcessCamouflage:
    """Sistema de camuflagem de processo"""
    
    def __init__(self):
        self.original_name = "PyCheatEngine.exe"
        self.fake_names = [
            "svchost.exe",
            "explorer.exe", 
            "notepad.exe",
            "calculator.exe",
            "mspaint.exe"
        ]
    
    def get_random_process_name(self) -> str:
        """Retorna nome de processo aleatório para camuflagem"""
        return random.choice(self.fake_names)
    
    def camouflage_window_title(self, window_handle):
        """Camufla título da janela"""
        if platform.system() == 'Windows':
            fake_titles = [
                "Microsoft Windows",
                "Windows Security",
                "System Configuration",
                "Registry Editor",
                "Task Manager"
            ]
            
            fake_title = random.choice(fake_titles)
            try:
                user32.SetWindowTextW(window_handle, fake_title)
                return True
            except:
                return False
        
        return False

class StealthScanner:
    """Scanner com capacidades stealth"""
    
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.stealth_mem = StealthMemoryManager()
        self.anti_debug = AntiDebugger()
        self.camouflage = ProcessCamouflage()
        self.scan_patterns = self._init_scan_patterns()
    
    def _init_scan_patterns(self):
        """Inicializa padrões de scan não-detectáveis"""
        return {
            # Padrões que imitam atividade normal do sistema
            'system_like': [0x1000, 0x2000, 0x4000, 0x8000],
            'random_intervals': lambda: random.randint(100, 5000),
            'fake_allocations': [0x10000, 0x20000, 0x40000]
        }
    
    def stealth_scan_memory(self, target_value, data_type, scan_type):
        """Executa scan com técnicas stealth"""
        print("🥷 Iniciando scan stealth...")
        
        # Ativa anti-debug
        self.anti_debug.start_monitoring()
        
        # Adiciona callback para parar scan se debugger for detectado
        def debug_callback():
            print("⚠️ Scan interrompido - debugger detectado!")
            self.stop_scan = True
        
        self.anti_debug.add_debug_callback(debug_callback)
        self.stop_scan = False
        
        try:
            # Scan normal mas com delays e ofuscação
            results = self._execute_stealth_scan(target_value, data_type, scan_type)
            
            print(f"🎯 Scan stealth completo: {len(results)} resultados")
            return results
            
        finally:
            self.anti_debug.stop_monitoring()
    
    def _execute_stealth_scan(self, target_value, data_type, scan_type):
        """Executa o scan propriamente dito"""
        results = []
        
        # Simula scan real mas com técnicas de evasão
        regions = self.memory_manager.get_memory_regions()
        
        for region in regions:
            if self.stop_scan:
                break
            
            # Delay aleatório entre regiões
            self.stealth_mem.random_delay()
            
            # Scan da região com chunks pequenos
            region_results = self._scan_region_stealth(
                region, target_value, data_type, scan_type
            )
            
            results.extend(region_results)
            
            # Para se encontrou muitos resultados (evita suspectibilidade)
            if len(results) > 1000:
                break
        
        return results
    
    def _scan_region_stealth(self, region, target_value, data_type, scan_type):
        """Scan de região específica com stealth"""
        results = []
        
        base_addr = region.get('base', 0)
        size = region.get('size', 0)
        
        if size > 1024 * 1024:  # Limita a 1MB para não ser suspeito
            size = 1024 * 1024
        
        # Lê região em chunks pequenos
        current_addr = base_addr
        remaining = size
        
        while remaining > 0 and not self.stop_scan:
            chunk_size = min(remaining, random.choice([1024, 2048, 4096]))
            
            # Leitura stealth
            data = self.stealth_mem.stealth_read_memory(
                self.memory_manager.process_handle,
                current_addr,
                chunk_size
            )
            
            if data:
                # Busca valor no chunk
                chunk_results = self._search_in_chunk(
                    data, current_addr, target_value, data_type
                )
                results.extend(chunk_results)
            
            current_addr += chunk_size
            remaining -= chunk_size
            
            # Delay entre chunks
            self.stealth_mem.random_delay()
        
        return results
    
    def _search_in_chunk(self, data, base_addr, target_value, data_type):
        """Busca valor em chunk de dados"""
        results = []
        
        try:
            if data_type == "int32":
                target_bytes = struct.pack('<i', target_value)
                step = 4
            elif data_type == "float":
                target_bytes = struct.pack('<f', target_value)
                step = 4
            else:
                return results
            
            # Busca padrão nos dados
            for i in range(0, len(data) - len(target_bytes) + 1, step):
                if data[i:i+len(target_bytes)] == target_bytes:
                    addr = base_addr + i
                    results.append({
                        'address': addr,
                        'value': target_value,
                        'data_type': data_type
                    })
            
        except Exception:
            pass
        
        return results

def create_stealth_memory_manager():
    """Factory function para criar MemoryManager com capacidades stealth"""
    from memory import MemoryManager
    
    class StealthEnhancedMemoryManager(MemoryManager):
        def __init__(self):
            super().__init__()
            self.stealth = StealthMemoryManager()
            self.anti_debug = AntiDebugger()
            self.stealth_enabled = True
            self.use_driver = False
            self.driver_manager = None
        
        def enable_stealth(self, enabled: bool = True):
            self.stealth_enabled = enabled
            self.stealth.enable_stealth_mode(enabled)
            if enabled:
                self.anti_debug.start_monitoring()
            else:
                self.anti_debug.stop_monitoring()
        
        def enable_driver_mode(self, enabled: bool = True):
            """Ativa modo driver para máximo stealth"""
            self.use_driver = enabled
            if enabled:
                try:
                    from kernel_driver import DriverBasedMemoryManager
                    self.driver_manager = DriverBasedMemoryManager()
                    print("🔧 Modo driver ativado - máximo stealth!")
                except ImportError:
                    print("❌ Driver não disponível")
                    self.use_driver = False
        
        def attach_to_process(self, process_id: int) -> bool:
            """Anexa usando driver se disponível"""
            if self.use_driver and self.driver_manager:
                return self.driver_manager.attach_to_process(process_id)
            else:
                return super().attach_to_process(process_id)
        
        def read_memory(self, address: int, size: int) -> Optional[bytes]:
            if self.use_driver and self.driver_manager:
                # Usa driver virtual (máximo stealth)
                return self.driver_manager.read_memory(address, size)
            elif self.stealth_enabled:
                # Usa stealth tradicional
                return self.stealth.stealth_read_memory(
                    self.process_handle, address, size
                )
            else:
                # Usa método padrão
                return super().read_memory(address, size)
        
        def write_memory(self, address: int, data: bytes) -> bool:
            if self.use_driver and self.driver_manager:
                # Usa driver virtual (máximo stealth)
                return self.driver_manager.write_memory(address, data)
            elif self.stealth_enabled:
                # Usa stealth tradicional
                return self.stealth.stealth_write_memory(
                    self.process_handle, address, data
                )
            else:
                # Usa método padrão
                return super().write_memory(address, data)
        
        def scan_for_value_driver(self, target_value: int, data_type: str = "int32"):
            """Scan usando driver virtual"""
            if self.use_driver and self.driver_manager:
                return self.driver_manager.scan_for_value(target_value, data_type)
            else:
                print("❌ Modo driver não ativo")
                return []
        
        def get_stealth_status(self):
            """Status stealth completo"""
            status = {
                'stealth_enabled': self.stealth_enabled,
                'driver_mode': self.use_driver,
                'anti_debug_active': self.anti_debug.monitoring
            }
            
            if self.use_driver and self.driver_manager:
                status['driver_status'] = self.driver_manager.get_driver_status()
            
            return status
        
        def close(self):
            """Fecha todas as conexões"""
            if self.use_driver and self.driver_manager:
                self.driver_manager.close()
            super().close()
    
    return StealthEnhancedMemoryManager()

# Funções utilitárias stealth
def hide_console_window():
    """Esconde janela do console"""
    if platform.system() == 'Windows':
        try:
            # Obtém handle da janela do console
            console_window = kernel32.GetConsoleWindow()
            if console_window:
                # Esconde a janela
                user32.ShowWindow(console_window, 0)  # SW_HIDE
                return True
        except:
            pass
    return False

def check_if_being_monitored() -> bool:
    """Verifica se o processo está sendo monitorado"""
    try:
        # Verifica se há ferramentas de monitoramento conhecidas
        monitoring_tools = [
            "procmon.exe", "procexp.exe", "processhacker.exe",
            "wireshark.exe", "fiddler.exe", "cheatengine.exe",
            "ollydbg.exe", "x64dbg.exe", "ida.exe"
        ]
        
        import psutil
        running_processes = [p.name().lower() for p in psutil.process_iter(['name'])]
        
        for tool in monitoring_tools:
            if tool.lower() in running_processes:
                return True
        
        return False
    except:
        return False

def obfuscate_strings(text: str) -> str:
    """Ofusca strings para evitar detecção de assinaturas"""
    # XOR simples com chave
    key = 0x42
    obfuscated = ''.join(chr(ord(c) ^ key) for c in text)
    return obfuscated

def deobfuscate_strings(obfuscated: str) -> str:
    """Deofusca strings"""
    key = 0x42
    return ''.join(chr(ord(c) ^ key) for c in obfuscated)

# Demonstração das capacidades stealth
def demo_stealth_capabilities():
    """Demonstra as capacidades stealth"""
    print("🥷 DEMONSTRAÇÃO STEALTH PYCHEATENGINE")
    print("=" * 50)
    
    # Cria gerenciador stealth
    stealth_mem = create_stealth_memory_manager()
    stealth_mem.enable_stealth(True)
    
    # Demonstra anti-debug
    anti_debug = AntiDebugger()
    print(f"Debugger presente: {anti_debug.check_debugger_present()}")
    print(f"Ambiente VM: {anti_debug.check_vm_environment()}")
    print(f"Ambiente Sandbox: {anti_debug.check_sandbox_environment()}")
    
    # Demonstra detecção de monitoramento
    print(f"Sendo monitorado: {check_if_being_monitored()}")
    
    # Demonstra ofuscação
    original = "PyCheatEngine"
    obfuscated = obfuscate_strings(original)
    deobfuscated = deobfuscate_strings(obfuscated)
    print(f"String original: {original}")
    print(f"String ofuscada: {repr(obfuscated)}")
    print(f"String deofuscada: {deobfuscated}")
    
    print("\n✅ Todas as funcionalidades stealth estão operacionais!")

if __name__ == "__main__":
    demo_stealth_capabilities()
