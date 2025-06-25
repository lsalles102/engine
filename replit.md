# PyCheatEngine - Sistema de Engenharia Reversa e Manipulação de Memória

## Overview

PyCheatEngine is a comprehensive memory manipulation and reverse engineering tool implemented in Python, similar to Cheat Engine but designed with modularity and efficiency in mind. The system provides capabilities for process memory reading/writing, value scanning, pointer chain resolution, and Array of Bytes (AOB) pattern scanning.

## System Architecture

### Core Architecture Pattern
The application follows a modular architecture pattern with clear separation of concerns:

- **Memory Management Layer**: Handles low-level memory operations with Windows API integration
- **Scanning Engine**: Provides various scanning algorithms for value detection and comparison
- **Pointer Resolution**: Manages complex pointer chain traversal and resolution
- **Pattern Matching**: Implements AOB scanning with wildcard support
- **User Interface Layer**: Dual interface approach with both GUI (Tkinter) and CLI implementations

### Platform Dependencies
- **Primary Platform**: Windows (uses Windows API through ctypes)
- **Privilege Requirements**: Requires administrator privileges for memory access
- **Architecture Support**: Both 32-bit and 64-bit process support

## Key Components

### 1. Memory Manager (`memory.py`)
**Purpose**: Core memory access functionality
- **Windows API Integration**: Uses kernel32 and psapi for process manipulation
- **Process Attachment**: Manages connection to target processes with appropriate privileges
- **Data Type Support**: Handles multiple data types (int32, int64, float, double, strings, bytes)
- **Safety Features**: Includes privilege checking and error handling

### 2. Memory Scanner (`scanner.py`)
**Purpose**: Value scanning and comparison operations
- **Scan Types**: Supports exact, increased, decreased, changed, unchanged, greater than, less than, and between comparisons
- **Multi-threaded**: Implements threading for non-blocking scan operations
- **Result Management**: Maintains scan results with history tracking
- **Progress Callbacks**: Provides real-time progress updates during scanning

### 3. Pointer Resolver (`pointer.py`)
**Purpose**: Pointer chain navigation and resolution
- **Chain Management**: Handles complex multi-level pointer chains
- **Architecture Awareness**: Supports both 32-bit and 64-bit pointer resolution
- **Serialization**: Provides JSON serialization for saving/loading pointer configurations
- **Validation**: Includes pointer chain validation and verification

### 4. AOB Scanner (`aob_scan.py`)
**Purpose**: Array of Bytes pattern matching
- **Wildcard Support**: Implements ?? wildcards for flexible pattern matching
- **Pattern Compilation**: Converts string patterns to searchable byte sequences
- **Validation**: Includes pattern syntax validation and error checking

### 5. User Interfaces (`ui/`)
**Purpose**: User interaction layers

#### GUI Interface (`ui/gui.py`)
- **Framework**: Tkinter-based graphical interface
- **Features**: Process selection, real-time scanning, result management, auto-update functionality
- **Layout**: Organized with menus, tabs, and progress indicators

#### CLI Interface (`ui/cli.py`)
- **Command System**: Command-based interface with help system
- **Session Management**: Save/load functionality for scan sessions
- **Interactive**: Real-time command processing with feedback

## Data Flow

### 1. Process Attachment Flow
```
User Selection → Process ID → Memory Manager → Windows API → Process Handle
```

### 2. Memory Scanning Flow
```
Scan Request → Memory Scanner → Memory Manager → Target Process → Results → UI Update
```

### 3. Pointer Resolution Flow
```
Base Address + Offsets → Pointer Resolver → Memory Manager → Final Address → Value Retrieval
```

### 4. AOB Scanning Flow
```
Pattern Input → Pattern Compilation → Memory Scanning → Pattern Matching → Results
```

## External Dependencies

### Required Libraries
- **psutil (>=7.0.0)**: Process and system utilities for cross-platform process management
- **ctypes**: Built-in library for Windows API access
- **tkinter**: Built-in GUI framework (for graphical interface)

### System Dependencies
- **Windows API**: kernel32.dll and psapi.dll for memory operations
- **Administrator Privileges**: Required for memory access to other processes

## Deployment Strategy

### Environment Setup
- **Python Version**: Requires Python 3.11+
- **Platform**: Windows-focused with potential for cross-platform expansion
- **Privilege Management**: Automatic privilege elevation request for Windows

### Execution Modes
1. **GUI Mode**: `python main.py --gui` (default)
2. **CLI Mode**: `python main.py --cli`
3. **Interactive Mode**: Direct module importing for custom implementations

### Project Structure
```
PyCheatEngine/
├── main.py              # Entry point with privilege management
├── memory.py            # Core memory operations
├── scanner.py           # Memory scanning functionality
├── pointer.py           # Pointer chain resolution
├── aob_scan.py         # Array of Bytes scanning
├── ui/
│   ├── gui.py          # Tkinter-based GUI
│   └── cli.py          # Command-line interface
└── pyproject.toml      # Project configuration
```

## User Preferences

Preferred communication style: Portuguese language, complete and functional implementations.

## Recent Changes

- ✓ Implementado PyCheatEngine completo com arquitetura modular
- ✓ Criada demonstração funcional com interface gráfica Tkinter
- ✓ Adicionado suporte multiplataforma (Windows/Linux)
- ✓ Configurado PyInstaller para compilação de executáveis
- ✓ Documentação completa de compilação criada
- ✓ Migração completa para ambiente Replit
- ✓ Corrigidos módulos memory.py e scanner.py
- ✓ Criado compilador automático funcional
- ✓ Adicionado demo web interativo
- ✓ Sistema completo de requirements e compilação para exe

## Deployment Strategy

### Compilação para Executável
- **PyInstaller**: Ferramenta principal para criar .exe
- **auto-py-to-exe**: Interface gráfica alternativa
- **Configurações**: --onefile --windowed para GUI, --console para CLI
- **Distribuição**: Executáveis independentes, não requerem Python instalado

## Changelog

- June 25, 2025: Implementação completa do PyCheatEngine
- June 25, 2025: Adicionada funcionalidade de compilação para executável