# Como Compilar PyCheatEngine para Executável (.exe)

## Método Rápido (Recomendado)

### 1. Instalar PyInstaller
```bash
pip install pyinstaller
```

### 2. Compilar Demonstração
```bash
pyinstaller --onefile --windowed --name PyCheatEngine_Demo demo_app.py
```

### 3. Compilar Versão Completa
```bash
pyinstaller --onefile --console --name PyCheatEngine main.py
```

## Comandos Específicos

### Para Interface Gráfica (sem console)
```bash
# Demo com interface gráfica
pyinstaller --onefile --windowed --clean demo_app.py

# Versão principal com GUI
pyinstaller --onefile --windowed --clean ui/gui.py
```

### Para Interface de Console
```bash
# Versão completa com console
pyinstaller --onefile --console --clean main.py
```

## Opções Avançadas

### Compilação Otimizada
```bash
pyinstaller --onefile --windowed --optimize=2 --clean demo_app.py
```

### Com Ícone Personalizado
```bash
pyinstaller --onefile --windowed --icon=icon.ico demo_app.py
```

### Excluindo Módulos Desnecessários
```bash
pyinstaller --onefile --exclude-module matplotlib --exclude-module numpy demo_app.py
```

## Usando auto-py-to-exe (Interface Gráfica)

### 1. Instalar
```bash
pip install auto-py-to-exe
```

### 2. Abrir Interface
```bash
auto-py-to-exe
```

### 3. Configurações Recomendadas
- **Script Location**: `demo_app.py` ou `main.py`
- **Onefile**: ✓ One File
- **Console Window**: ✗ Window Based (GUI) ou ✓ Console Based
- **Icon**: Opcional
- **Advanced**: 
  - **--clean**: ✓
  - **--optimize**: 2

## Resultados Esperados

Após compilação bem-sucedida:
```
dist/
├── PyCheatEngine_Demo.exe    (15-25 MB)
├── PyCheatEngine.exe         (12-20 MB)
└── ...
```

## Para Distribuição

### Arquivo Único
- Copie apenas o `.exe` da pasta `dist/`
- Não precisa Python instalado no PC de destino
- Execute como Administrador (para acessar memória de outros processos)

### Pacote Completo
Crie uma pasta com:
```
PyCheatEngine_Portable/
├── PyCheatEngine_Demo.exe
├── PyCheatEngine.exe
├── README.txt
└── CHANGELOG.txt
```

## Solução de Problemas

### Erro "Failed to execute script"
```bash
# Compile com console para ver erros
pyinstaller --onefile --console demo_app.py
```

### Executável muito grande
```bash
# Exclua módulos não usados
pyinstaller --onefile --exclude-module PIL --exclude-module matplotlib demo_app.py
```

### Demora para iniciar
```bash
# Use --onedir em vez de --onefile
pyinstaller --onedir --windowed demo_app.py
```

### Falta de permissões
- Execute o .exe como Administrador
- No Windows: Clique direito → "Executar como administrador"

## Teste Rápido

Para testar se funcionou:
```bash
# Após compilação
cd dist
./PyCheatEngine_Demo.exe  # ou duplo-clique no Windows
```

## Comandos Úteis

```bash
# Limpar builds anteriores
rm -rf build dist *.spec

# Ver dependências
pip show pyinstaller

# Versão do PyInstaller
pyinstaller --version

# Ajuda completa
pyinstaller --help
```

## Exemplo Completo

```bash
# 1. Preparar ambiente
pip install pyinstaller psutil

# 2. Compilar demonstração
pyinstaller --onefile --windowed --name PyCheatEngine_Demo --clean demo_app.py

# 3. Compilar versão principal  
pyinstaller --onefile --console --name PyCheatEngine --clean main.py

# 4. Testar
cd dist
ls -la *.exe

# 5. Executar
./PyCheatEngine_Demo.exe
```

## Automatização com Script

Salve como `build.py`:
```python
import subprocess
import os

def build():
    # Demo GUI
    subprocess.run([
        "pyinstaller", "--onefile", "--windowed", 
        "--name", "PyCheatEngine_Demo", "--clean", "demo_app.py"
    ])
    
    # Main Console
    subprocess.run([
        "pyinstaller", "--onefile", "--console",
        "--name", "PyCheatEngine", "--clean", "main.py" 
    ])
    
    print("Compilação concluída! Verifique a pasta dist/")

if __name__ == "__main__":
    build()
```

Execute: `python build.py`