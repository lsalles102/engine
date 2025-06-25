
#!/usr/bin/env python3
"""
Sistema de logging para debug do PyCheatEngine
"""

import logging
import os
from datetime import datetime

class PyCheatEngineLogger:
    """Logger personalizado para PyCheatEngine"""
    
    def __init__(self, name="PyCheatEngine", level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove handlers existentes
        self.logger.handlers.clear()
        
        # Configura formatador
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para arquivo (opcional)
        if self._should_log_to_file():
            file_handler = logging.FileHandler('pycheatengine_debug.log')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _should_log_to_file(self):
        """Determina se deve logar para arquivo"""
        return os.environ.get('PYCHEAT_DEBUG_FILE', 'false').lower() == 'true'
    
    def debug(self, message):
        """Log debug"""
        self.logger.debug(f"[DEBUG] {message}")
    
    def info(self, message):
        """Log info"""
        self.logger.info(f"[INFO] {message}")
    
    def warning(self, message):
        """Log warning"""
        self.logger.warning(f"[WARNING] {message}")
    
    def error(self, message):
        """Log error"""
        self.logger.error(f"[ERROR] {message}")
    
    def scan_event(self, event_type, message):
        """Log eventos de scan específicos"""
        self.logger.info(f"[SCAN_{event_type.upper()}] {message}")

# Instância global do logger
debug_logger = PyCheatEngineLogger()
