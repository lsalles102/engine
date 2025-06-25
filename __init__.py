"""
PyCheatEngine - Sistema de Engenharia Reversa e Manipulação de Memória
Similar ao Cheat Engine, mas implementado em Python

Autor: PyCheatEngine Team
Versão: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "PyCheatEngine Team"
__description__ = "Sistema de Engenharia Reversa e Manipulação de Memória em Python"

# Importações principais
from .memory import MemoryManager
from .scanner import MemoryScanner
from .pointer import PointerResolver
from .aob_scan import AOBScanner

__all__ = [
    'MemoryManager',
    'MemoryScanner', 
    'PointerResolver',
    'AOBScanner'
]
