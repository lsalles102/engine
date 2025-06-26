
"""
Módulo de Captura de ViewMatrix para PyCheatEngine
Implementa funcionalidades para encontrar e ler a ViewMatrix de jogos 3D
"""

import struct
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from memory import MemoryManager
from scanner import MemoryScanner, DataType, ScanType

class ViewMatrix:
    """Representa uma ViewMatrix 4x4"""
    
    def __init__(self, matrix_data: np.ndarray = None):
        if matrix_data is not None:
            self.matrix = matrix_data.reshape(4, 4)
        else:
            self.matrix = np.eye(4, dtype=np.float32)
    
    def world_to_screen(self, world_pos: Tuple[float, float, float], 
                       screen_width: int, screen_height: int) -> Optional[Tuple[int, int]]:
        """
        Converte coordenadas do mundo 3D para coordenadas de tela 2D
        
        Args:
            world_pos: Posição no mundo (x, y, z)
            screen_width: Largura da tela
            screen_height: Altura da tela
            
        Returns:
            Coordenadas de tela (x, y) ou None se atrás da câmera
        """
        try:
            # Converte para coordenadas homogêneas
            world_vec = np.array([world_pos[0], world_pos[1], world_pos[2], 1.0], dtype=np.float32)
            
            # Aplica transformação da ViewMatrix
            clip_coords = np.dot(self.matrix, world_vec)
            
            # Verifica se está atrás da câmera
            if clip_coords[3] <= 0.001:
                return None
                
            # Normaliza coordenadas
            ndc_x = clip_coords[0] / clip_coords[3]
            ndc_y = clip_coords[1] / clip_coords[3]
            
            # Converte para coordenadas de tela
            screen_x = int((ndc_x + 1.0) * screen_width / 2.0)
            screen_y = int((1.0 - ndc_y) * screen_height / 2.0)
            
            # Verifica se está dentro da tela
            if 0 <= screen_x <= screen_width and 0 <= screen_y <= screen_height:
                return (screen_x, screen_y)
            
            return None
            
        except Exception as e:
            print(f"Erro na conversão world_to_screen: {e}")
            return None
    
    def get_camera_position(self) -> Tuple[float, float, float]:
        """Extrai a posição da câmera da ViewMatrix"""
        try:
            # A posição da câmera está na transformação inversa
            inv_matrix = np.linalg.inv(self.matrix)
            return (inv_matrix[0, 3], inv_matrix[1, 3], inv_matrix[2, 3])
        except:
            return (0.0, 0.0, 0.0)
    
    def is_valid(self) -> bool:
        """Verifica se a ViewMatrix é válida"""
        try:
            # Verifica se não é uma matriz zero
            if np.allclose(self.matrix, 0):
                return False
                
            # Verifica se tem valores razoáveis
            if np.any(np.abs(self.matrix) > 1e6):
                return False
                
            # Verifica se o determinante não é zero
            det = np.linalg.det(self.matrix[:3, :3])
            if abs(det) < 1e-6:
                return False
                
            return True
        except:
            return False

class ViewMatrixScanner:
    """Scanner especializado para encontrar ViewMatrix"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.scanner = MemoryScanner(memory_manager)
        self.known_patterns = self._get_known_patterns()
        self.found_addresses: List[int] = []
        
    def _get_known_patterns(self) -> Dict[str, Dict]:
        """Padrões conhecidos de ViewMatrix para diferentes engines"""
        return {
            "unity": {
                "description": "Unity Engine ViewMatrix",
                "signatures": [
                    b"\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",  # Identity matrix pattern
                ],
                "offsets": [0x0, 0x10, 0x20, 0x30]
            },
            "unreal": {
                "description": "Unreal Engine ViewMatrix", 
                "signatures": [
                    b"\x00\x00\x00\x00\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00",
                ],
                "offsets": [0x0, 0x40, 0x80]
            },
            "source": {
                "description": "Source Engine ViewMatrix",
                "signatures": [
                    b"\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00",
                ],
                "offsets": [0x0, 0x4, 0x8, 0xC]
            }
        }
    
    def scan_for_viewmatrix(self, scan_range: Tuple[int, int] = None) -> List[int]:
        """
        Procura por ViewMatrix na memória usando múltiplas técnicas
        
        Args:
            scan_range: Range de endereços para scan (start, end)
            
        Returns:
            Lista de endereços onde ViewMatrix pode estar
        """
        if not self.memory_manager.is_attached():
            raise RuntimeError("Processo não anexado")
            
        self.found_addresses.clear()
        print("[VIEWMATRIX] Iniciando busca por ViewMatrix...")
        
        if scan_range:
            self.scanner.set_scan_range(scan_range[0], scan_range[1])
        
        # Técnica 1: Busca por padrões de identidade matrix
        self._scan_identity_patterns()
        
        # Técnica 2: Busca por valores típicos de ViewMatrix
        self._scan_typical_values()
        
        # Técnica 3: Busca por assinaturas conhecidas
        self._scan_known_signatures()
        
        # Técnica 4: Validação matemática
        self._validate_candidates()
        
        print(f"[VIEWMATRIX] Encontrados {len(self.found_addresses)} candidatos")
        return self.found_addresses
    
    def _scan_identity_patterns(self):
        """Busca por padrões de matriz identidade"""
        print("[VIEWMATRIX] Buscando padrões de matriz identidade...")
        
        # Padrão: 1.0f em posições diagonais
        identity_value = struct.pack('<f', 1.0)  # 0x3F800000
        
        try:
            # Busca por valores 1.0
            results = self.scanner.first_scan(1.0, DataType.FLOAT, ScanType.EXACT)
            
            for result in results:
                address = result.address
                
                # Verifica se pode ser início de ViewMatrix 4x4
                if self._check_matrix_pattern(address):
                    if address not in self.found_addresses:
                        self.found_addresses.append(address)
                        print(f"[VIEWMATRIX] Candidato encontrado: 0x{address:X}")
                        
        except Exception as e:
            print(f"[VIEWMATRIX] Erro na busca por identidade: {e}")
    
    def _scan_typical_values(self):
        """Busca por valores típicos encontrados em ViewMatrix"""
        print("[VIEWMATRIX] Buscando valores típicos...")
        
        typical_values = [0.0, 1.0, -1.0]
        
        for value in typical_values:
            try:
                results = self.scanner.first_scan(value, DataType.FLOAT, ScanType.EXACT)
                
                for result in results[:100]:  # Limita para não sobrecarregar
                    base_addr = result.address & ~0xF  # Alinha para 16 bytes
                    
                    if self._is_potential_viewmatrix(base_addr):
                        if base_addr not in self.found_addresses:
                            self.found_addresses.append(base_addr)
                            
            except Exception as e:
                print(f"[VIEWMATRIX] Erro buscando valor {value}: {e}")
    
    def _scan_known_signatures(self):
        """Busca por assinaturas conhecidas de engines"""
        print("[VIEWMATRIX] Buscando assinaturas conhecidas...")
        
        for engine_name, pattern_info in self.known_patterns.items():
            print(f"[VIEWMATRIX] Testando padrões do {engine_name}...")
            
            for signature in pattern_info["signatures"]:
                try:
                    # Busca por padrão de bytes
                    addresses = self._scan_byte_pattern(signature)
                    
                    for addr in addresses:
                        for offset in pattern_info["offsets"]:
                            candidate_addr = addr + offset
                            
                            if self._is_potential_viewmatrix(candidate_addr):
                                if candidate_addr not in self.found_addresses:
                                    self.found_addresses.append(candidate_addr)
                                    print(f"[VIEWMATRIX] {engine_name} candidato: 0x{candidate_addr:X}")
                                    
                except Exception as e:
                    print(f"[VIEWMATRIX] Erro em {engine_name}: {e}")
    
    def _scan_byte_pattern(self, pattern: bytes) -> List[int]:
        """Busca por padrão de bytes na memória"""
        addresses = []
        
        try:
            # Implementação simplificada de busca por padrão
            regions = self.memory_manager.get_memory_regions()
            
            for region in regions[:10]:  # Limita regiões para performance
                try:
                    base = region['base']
                    size = min(region['size'], 0x100000)  # Max 1MB por região
                    
                    data = self.memory_manager.read_memory(base, size)
                    if data:
                        pos = 0
                        while pos < len(data) - len(pattern):
                            pos = data.find(pattern, pos)
                            if pos == -1:
                                break
                            addresses.append(base + pos)
                            pos += 1
                            
                except:
                    continue
                    
        except Exception as e:
            print(f"[VIEWMATRIX] Erro na busca por padrão: {e}")
            
        return addresses
    
    def _check_matrix_pattern(self, address: int) -> bool:
        """Verifica se endereço pode ser uma ViewMatrix válida"""
        try:
            # Lê 64 bytes (4x4 matrix de floats)
            data = self.memory_manager.read_memory(address, 64)
            if not data or len(data) < 64:
                return False
                
            # Converte para matriz de floats
            floats = struct.unpack('<16f', data)
            
            # Verifica padrões típicos de ViewMatrix
            # 1. Valores na diagonal devem ser não-zero (geralmente ±1)
            if abs(floats[0]) < 0.001 or abs(floats[5]) < 0.001:
                return False
                
            # 2. Não deve ter valores muito grandes
            if any(abs(f) > 1000000 for f in floats):
                return False
                
            # 3. Última linha geralmente é [0,0,0,1] ou [0,0,0,w]
            if abs(floats[15]) < 0.001:
                return False
                
            return True
            
        except:
            return False
    
    def _is_potential_viewmatrix(self, address: int) -> bool:
        """Validação rápida se endereço pode conter ViewMatrix"""
        try:
            # Alinhamento: ViewMatrix geralmente está alinhada
            if address % 16 != 0:
                return False
                
            # Lê e valida matriz
            matrix = self.read_viewmatrix(address)
            return matrix is not None and matrix.is_valid()
            
        except:
            return False
    
    def _validate_candidates(self):
        """Valida candidatos usando critérios matemáticos"""
        print("[VIEWMATRIX] Validando candidatos...")
        
        valid_addresses = []
        
        for address in self.found_addresses:
            try:
                matrix = self.read_viewmatrix(address)
                if matrix and matrix.is_valid():
                    valid_addresses.append(address)
                    print(f"[VIEWMATRIX] Candidato válido: 0x{address:X}")
                    
            except:
                continue
                
        self.found_addresses = valid_addresses
    
    def read_viewmatrix(self, address: int) -> Optional[ViewMatrix]:
        """
        Lê ViewMatrix do endereço especificado
        
        Args:
            address: Endereço da ViewMatrix
            
        Returns:
            ViewMatrix object ou None se inválida
        """
        try:
            # Lê 64 bytes (4x4 matrix de floats)
            data = self.memory_manager.read_memory(address, 64)
            if not data or len(data) < 64:
                return None
                
            # Converte para array numpy
            floats = struct.unpack('<16f', data)
            matrix_data = np.array(floats, dtype=np.float32)
            
            return ViewMatrix(matrix_data)
            
        except Exception as e:
            print(f"Erro ao ler ViewMatrix em 0x{address:X}: {e}")
            return None
    
    def monitor_viewmatrix(self, address: int, callback=None) -> bool:
        """
        Monitora mudanças na ViewMatrix
        
        Args:
            address: Endereço da ViewMatrix
            callback: Função chamada quando ViewMatrix muda
            
        Returns:
            True se monitoramento iniciou com sucesso
        """
        try:
            import threading
            import time
            
            def monitor_worker():
                last_matrix = None
                
                while True:
                    try:
                        current_matrix = self.read_viewmatrix(address)
                        
                        if current_matrix and current_matrix.is_valid():
                            if last_matrix is None or not np.allclose(current_matrix.matrix, last_matrix.matrix, atol=1e-6):
                                if callback:
                                    callback(current_matrix)
                                last_matrix = current_matrix
                                
                        time.sleep(0.016)  # ~60 FPS
                        
                    except Exception as e:
                        print(f"Erro no monitoramento: {e}")
                        time.sleep(1)
            
            thread = threading.Thread(target=monitor_worker, daemon=True)
            thread.start()
            
            print(f"[VIEWMATRIX] Monitoramento iniciado para 0x{address:X}")
            return True
            
        except Exception as e:
            print(f"Erro ao iniciar monitoramento: {e}")
            return False
    
    def get_best_candidate(self) -> Optional[int]:
        """Retorna o melhor candidato para ViewMatrix"""
        if not self.found_addresses:
            return None
            
        best_addr = None
        best_score = -1
        
        for address in self.found_addresses:
            try:
                matrix = self.read_viewmatrix(address)
                if not matrix or not matrix.is_valid():
                    continue
                    
                # Sistema de pontuação
                score = 0
                
                # Pontos por alinhamento
                if address % 16 == 0:
                    score += 10
                    
                # Pontos por valores típicos
                if abs(matrix.matrix[3, 3] - 1.0) < 0.001:  # w component = 1
                    score += 20
                    
                # Pontos por posição da câmera razoável
                cam_pos = matrix.get_camera_position()
                if all(abs(pos) < 10000 for pos in cam_pos):
                    score += 15
                    
                if score > best_score:
                    best_score = score
                    best_addr = address
                    
            except:
                continue
                
        return best_addr
    
    def export_viewmatrix_info(self, filename: str) -> bool:
        """Exporta informações das ViewMatrix encontradas"""
        try:
            import json
            import time
            
            info = {
                'timestamp': time.time(),
                'process_id': self.memory_manager.process_id,
                'candidates': []
            }
            
            for address in self.found_addresses:
                try:
                    matrix = self.read_viewmatrix(address)
                    if matrix:
                        cam_pos = matrix.get_camera_position()
                        
                        info['candidates'].append({
                            'address': hex(address),
                            'is_valid': matrix.is_valid(),
                            'camera_position': cam_pos,
                            'matrix': matrix.matrix.tolist()
                        })
                        
                except:
                    info['candidates'].append({
                        'address': hex(address),
                        'is_valid': False,
                        'error': 'Failed to read matrix'
                    })
            
            with open(filename, 'w') as f:
                json.dump(info, f, indent=2)
                
            print(f"[VIEWMATRIX] Informações exportadas para {filename}")
            return True
            
        except Exception as e:
            print(f"Erro ao exportar: {e}")
            return False
