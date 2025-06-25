# PyCheatEngine - Sistema de Engenharia Reversa para Windows

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Sobre o Projeto

PyCheatEngine é um sistema completo de engenharia reversa e manipulação de memória desenvolvido em Python, similar ao Cheat Engine mas com arquitetura modular e funcionalidades avançadas.

### 🎯 Principais Funcionalidades

- **Scanner de Memória**: Busca valores na memória de processos em tempo real
- **Scanner AOB**: Busca padrões de bytes com suporte a wildcards
- **Resolução de Ponteiros**: Navega cadeias de ponteiros complexas
- **Interface Dupla**: GUI (Tkinter) e CLI completas
- **Compilação para EXE**: Cria executáveis independentes
- **Suporte Multiplataforma**: Windows (principal) e Linux

## 🚀 Instalação Rápida

### Método 1: Instalador Automático (Recomendado)
```bash
python installer_windows.py
```

### Método 2: Manual
```bash
# Clone ou baixe o projeto
# Instale as dependências
pip install -r requirements_custom.txt
```

## 📦 Dependências

- Python 3.8 ou superior
- psutil >= 7.0.0
- pyinstaller >= 6.14.1 (para compilação)
- auto-py-to-exe >= 2.46.0 (opcional)
- tkinter (interface gráfica)

## 🔧 Como Usar

### Interface Gráfica (Recomendado)
```bash
python main.py --gui
# ou execute: PyCheatEngine_GUI.bat
```

### Linha de Comando
```bash
python main.py --cli
# ou execute: PyCheatEngine_CLI.bat
```

### Compilar para Executável
```bash
python compilar_exe.py
# ou execute: Compilar_EXE.bat
# ou execute: compilar_windows.bat
```

## 🎮 Funcionalidades Detalhadas

### Scanner de Memória
- **Tipos de Dados**: int32, int64, float, double, string, bytes
- **Tipos de Scan**: Exato, Maior que, Menor que, Alterado, Inalterado, Entre valores
- **Scan Progressivo**: Refina resultados em múltiplas passadas
- **Limitação de Resultados**: Evita sobrecarga com muitos resultados

### Scanner AOB (Array of Bytes)
```
Exemplo de padrão: 48 8B 05 ?? ?? ?? 78
- ?? = wildcard (qualquer byte)
- Busca padrões específicos no código
- Útil para encontrar funções e dados
```

### Sistema de Ponteiros
- Resolução de cadeias multi-nível
- Validação automática de ponteiros
- Serialização em JSON para save/load
- Suporte a 32-bit e 64-bit

### Interfaces Disponíveis

#### GUI (Interface Gráfica)
- Menu completo com atalhos
- Abas organizadas por funcionalidade
- Progresso em tempo real
- Atualização automática de valores
- Save/Load de sessões

#### CLI (Linha de Comando)
- Sistema de comandos intuitivo
- Help integrado
- Automação via scripts
- Saída formatada

## ⚙️ Compilação para Executável

### Opções Disponíveis
1. **GUI**: Interface gráfica sem console
2. **CLI**: Linha de comando com console
3. **Standalone**: Versão completa independente
4. **Todas**: Compila todas as versões

### Comando de Compilação
```bash
# Usando o script Python
python compilar_exe.py

# Usando batch do Windows
compilar_windows.bat

# Manual com PyInstaller
pyinstaller --onefile --windowed main.py
```

## 🔒 Segurança e Avisos

### ⚠️ IMPORTANTE
- **Execute sempre como Administrador** para acesso completo à memória
- Use apenas em processos próprios ou autorizados
- Não utilize para trapacear em jogos online
- Alguns antivírus podem detectar como falso positivo

### Configuração do Windows Defender
O instalador automático adiciona exclusões necessárias no Windows Defender.

## 📁 Estrutura do Projeto

```
PyCheatEngine/
├── main.py                 # Ponto de entrada principal
├── memory.py               # Gerenciamento de memória
├── scanner.py              # Scanner de valores
├── pointer.py              # Resolução de ponteiros
├── aob_scan.py            # Scanner AOB
├── ui/
│   ├── gui.py             # Interface gráfica
│   └── cli.py             # Interface CLI
├── compilar_exe.py        # Compilador Python
├── installer_windows.py   # Instalador automático
├── compilar_windows.bat   # Compilador batch
└── requirements_custom.txt # Dependências
```

## 🖥️ Requisitos do Sistema

### Windows (Principal)
- Windows 7/8/10/11 (32-bit ou 64-bit)
- Python 3.8+ instalado
- Privilégios de administrador
- 2GB RAM livres (recomendado)

### Linux (Limitado)
- Kernel com /proc/PID/mem
- Python 3.8+
- Permissões root (sudo)

## 🚨 Solução de Problemas

### Erro: "Sem privilégios administrativos"
```bash
# Execute como administrador
# Clique direito > "Executar como administrador"
```

### Erro: "Processo não encontrado"
```bash
# Verifique se o processo está executando
# Use Task Manager para confirmar PID
```

### Erro: "Falha ao ler memória"
```bash
# Processo pode ter proteção anti-debug
# Tente com processo mais simples (notepad, calculadora)
```

### Antivírus detectando como vírus
```bash
# Adicione exclusão na pasta do projeto
# Configure Windows Defender com installer_windows.py
```

## 📖 Exemplos de Uso

### Exemplo 1: Scanner Básico
```python
from memory import MemoryManager
from scanner import MemoryScanner, DataType, ScanType

# Anexa ao processo
mem = MemoryManager()
mem.attach_to_process(1234)  # PID do processo

# Configura scanner
scanner = MemoryScanner(mem)

# Busca valor 100
results = scanner.first_scan(100, DataType.INT32, ScanType.EXACT)
print(f"Encontrados {len(results)} resultados")

# Refina busca
results = scanner.next_scan(150, ScanType.EXACT)
print(f"Restaram {len(results)} resultados")
```

### Exemplo 2: Scanner AOB
```python
from aob_scan import AOBScanner

aob = AOBScanner(mem)
pattern = "48 8B 05 ?? ?? ?? 78"
results = aob.scan_aob(pattern, "Exemplo de busca")

for result in results:
    print(f"Encontrado em: {hex(result.address)}")
```

### Exemplo 3: Ponteiros
```python
from pointer import PointerResolver, PointerChain

resolver = PointerResolver(mem)
chain = PointerChain(0x00400000, [0x10, 0x20, 0x4])

value = resolver.resolve_pointer_chain(chain)
print(f"Valor final: {value}")
```

## 🤝 Contribuição

1. Faça fork do projeto
2. Crie sua branch de feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 🔗 Links Úteis

- [Python Downloads](https://www.python.org/downloads/)
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [Cheat Engine Official](https://www.cheatengine.org/)

## 📞 Suporte

Para reportar bugs ou solicitar funcionalidades, abra uma issue no repositório.

---

**⚡ PyCheatEngine - Engenharia Reversa Simplificada**