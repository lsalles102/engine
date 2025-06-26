
#!/usr/bin/env python3
"""
Configurações para funcionalidades stealth do PyCheatEngine
"""

import json
import os
from typing import Dict, Any, List

class StealthConfig:
    """Gerenciador de configurações stealth"""
    
    def __init__(self, config_file: str = "stealth_config.json"):
        self.config_file = config_file
        self.default_config = {
            "stealth_level": 0,
            "anti_debug": {
                "enabled": True,
                "check_interval": 2.0,
                "detection_methods": [
                    "IsDebuggerPresent",
                    "CheckRemoteDebuggerPresent", 
                    "NtQueryInformationProcess",
                    "VM_Detection",
                    "Sandbox_Detection"
                ]
            },
            "memory_operations": {
                "use_random_delays": True,
                "delay_range": [0.001, 0.01],
                "chunk_sizes": [1024, 2048, 4096],
                "max_chunk_size": 8192,
                "obfuscate_addresses": True
            },
            "process_camouflage": {
                "enabled": True,
                "fake_process_names": [
                    "svchost.exe",
                    "explorer.exe",
                    "notepad.exe", 
                    "calculator.exe",
                    "mspaint.exe"
                ],
                "fake_window_titles": [
                    "Microsoft Windows",
                    "Windows Security",
                    "System Configuration",
                    "Registry Editor",
                    "Task Manager"
                ]
            },
            "api_evasion": {
                "detect_hooks": True,
                "bypass_hooks": False,  # Perigoso - apenas para testes avançados
                "monitored_apis": [
                    "ReadProcessMemory",
                    "WriteProcessMemory", 
                    "VirtualAllocEx",
                    "CreateRemoteThread",
                    "OpenProcess"
                ]
            },
            "network_evasion": {
                "generate_fake_traffic": False,
                "fake_traffic_duration": 30,
                "decoy_targets": [
                    "8.8.8.8:53",
                    "1.1.1.1:53", 
                    "208.67.222.222:53"
                ]
            },
            "encryption": {
                "encrypt_memory_regions": True,
                "encryption_algorithm": "XOR",
                "key_derivation": "system_based",
                "auto_decrypt": True
            },
            "obfuscation": {
                "obfuscate_strings": True,
                "obfuscate_addresses": True,
                "encoding_method": "base64_xor",
                "dynamic_keys": True
            },
            "scanning": {
                "stealth_scan_enabled": True,
                "max_results_limit": 1000,
                "scan_timeout": 30,
                "random_scan_order": True,
                "hide_scan_progress": False
            },
            "logging": {
                "log_stealth_operations": False,  # Pode ser detectável
                "log_file": "stealth_debug.log",
                "log_level": "WARNING"
            },
            "safety": {
                "educational_mode": True,
                "require_confirmation": True,
                "disable_dangerous_features": True,
                "max_stealth_level": 3  # Limita nível máximo por segurança
            }
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Mescla com configuração padrão
                config = self.default_config.copy()
                self._deep_update(config, loaded_config)
                return config
                
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
                return self.default_config.copy()
        
        return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Salva configuração no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
            return False
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Atualiza dicionário recursivamente"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key_path: str, default=None):
        """Obtém valor usando path com pontos (ex: 'anti_debug.enabled')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value):
        """Define valor usando path com pontos"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_stealth_level(self) -> int:
        """Obtém nível stealth atual"""
        return self.get('stealth_level', 0)
    
    def set_stealth_level(self, level: int):
        """Define nível stealth com validação"""
        max_level = self.get('safety.max_stealth_level', 3)
        
        if level > max_level:
            print(f"⚠️ Nível limitado a {max_level} por configuração de segurança")
            level = max_level
        
        self.set('stealth_level', level)
        self.save_config()
    
    def is_feature_enabled(self, feature_path: str) -> bool:
        """Verifica se uma funcionalidade está habilitada"""
        return self.get(f'{feature_path}.enabled', False)
    
    def get_safety_mode(self) -> bool:
        """Verifica se está em modo educacional/seguro"""
        return self.get('safety.educational_mode', True)
    
    def require_confirmation(self) -> bool:
        """Verifica se requer confirmação para operações perigosas"""
        return self.get('safety.require_confirmation', True)
    
    def get_monitored_apis(self) -> List[str]:
        """Obtém lista de APIs para monitorar"""
        return self.get('api_evasion.monitored_apis', [])
    
    def get_delay_range(self) -> tuple:
        """Obtém range de delays para operações stealth"""
        delay_range = self.get('memory_operations.delay_range', [0.001, 0.01])
        return tuple(delay_range)
    
    def get_chunk_sizes(self) -> List[int]:
        """Obtém tamanhos de chunk para leitura de memória"""
        return self.get('memory_operations.chunk_sizes', [1024, 2048, 4096])
    
    def export_config(self, filename: str) -> bool:
        """Exporta configuração para arquivo específico"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuração exportada para: {filename}")
            return True
        except Exception as e:
            print(f"❌ Erro ao exportar: {e}")
            return False
    
    def import_config(self, filename: str) -> bool:
        """Importa configuração de arquivo"""
        if not os.path.exists(filename):
            print(f"❌ Arquivo não encontrado: {filename}")
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Valida configuração
            if self._validate_config(imported_config):
                self.config = imported_config
                self.save_config()
                print(f"✅ Configuração importada de: {filename}")
                return True
            else:
                print("❌ Configuração inválida")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao importar: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração importada"""
        required_sections = ['anti_debug', 'memory_operations', 'safety']
        
        for section in required_sections:
            if section not in config:
                print(f"Seção obrigatória ausente: {section}")
                return False
        
        # Valida nível stealth
        stealth_level = config.get('stealth_level', 0)
        if not isinstance(stealth_level, int) or not 0 <= stealth_level <= 5:
            print("stealth_level deve ser inteiro entre 0 e 5")
            return False
        
        return True
    
    def reset_to_defaults(self):
        """Reseta configuração para padrões"""
        self.config = self.default_config.copy()
        self.save_config()
        print("✅ Configuração resetada para padrões")
    
    def print_current_config(self):
        """Exibe configuração atual de forma organizada"""
        print("\n🔧 CONFIGURAÇÃO STEALTH ATUAL")
        print("=" * 50)
        
        print(f"Nível Stealth: {self.get_stealth_level()}")
        print(f"Modo Educacional: {'SIM' if self.get_safety_mode() else 'NÃO'}")
        print(f"Requer Confirmação: {'SIM' if self.require_confirmation() else 'NÃO'}")
        
        print(f"\nAnti-Debug: {'ATIVO' if self.is_feature_enabled('anti_debug') else 'INATIVO'}")
        print(f"Camuflagem: {'ATIVO' if self.is_feature_enabled('process_camouflage') else 'INATIVO'}")
        print(f"Evasão de API: {'ATIVO' if self.is_feature_enabled('api_evasion') else 'INATIVO'}")
        print(f"Criptografia: {'ATIVO' if self.is_feature_enabled('encryption') else 'INATIVO'}")
        
        print(f"\nDelay Range: {self.get_delay_range()}")
        print(f"Chunk Sizes: {self.get_chunk_sizes()}")
        print(f"APIs Monitoradas: {len(self.get_monitored_apis())}")

# Configuração global padrão
stealth_config = StealthConfig()

def get_stealth_config() -> StealthConfig:
    """Retorna instância global da configuração stealth"""
    return stealth_config

# Presets de configuração
STEALTH_PRESETS = {
    "educational": {
        "stealth_level": 1,
        "safety": {
            "educational_mode": True,
            "require_confirmation": True,
            "disable_dangerous_features": True,
            "max_stealth_level": 2
        },
        "api_evasion": {
            "bypass_hooks": False
        },
        "network_evasion": {
            "generate_fake_traffic": False
        }
    },
    
    "testing": {
        "stealth_level": 2,
        "safety": {
            "educational_mode": True,
            "require_confirmation": True,
            "disable_dangerous_features": False,
            "max_stealth_level": 3
        },
        "api_evasion": {
            "bypass_hooks": False
        },
        "network_evasion": {
            "generate_fake_traffic": True
        }
    },
    
    "advanced": {
        "stealth_level": 3,
        "safety": {
            "educational_mode": False,
            "require_confirmation": True,
            "disable_dangerous_features": False,
            "max_stealth_level": 4
        },
        "api_evasion": {
            "bypass_hooks": True
        },
        "network_evasion": {
            "generate_fake_traffic": True
        }
    },
    
    "maximum": {
        "stealth_level": 5,
        "safety": {
            "educational_mode": False,
            "require_confirmation": False,
            "disable_dangerous_features": False,
            "max_stealth_level": 5
        },
        "api_evasion": {
            "bypass_hooks": True
        },
        "network_evasion": {
            "generate_fake_traffic": True
        }
    }
}

def apply_preset(preset_name: str) -> bool:
    """Aplica preset de configuração"""
    if preset_name not in STEALTH_PRESETS:
        print(f"❌ Preset '{preset_name}' não encontrado")
        return False
    
    config = get_stealth_config()
    preset = STEALTH_PRESETS[preset_name]
    
    # Aplica configurações do preset
    for key, value in preset.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                config.set(f"{key}.{subkey}", subvalue)
        else:
            config.set(key, value)
    
    config.save_config()
    print(f"✅ Preset '{preset_name}' aplicado com sucesso")
    return True

if __name__ == "__main__":
    # Teste da configuração
    config = StealthConfig()
    config.print_current_config()
    
    print("\n📋 Presets disponíveis:")
    for preset_name in STEALTH_PRESETS.keys():
        print(f"  • {preset_name}")
