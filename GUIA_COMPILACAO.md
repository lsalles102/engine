# Como Compilar PyCheatEngine para Executável (.exe)

## Métodos Disponíveis

### Método 1: Script Automático (Recomendado)
```bash
python build_exe.py
```

### Método 2: Batch Script (Windows)
```bash
build_simple.bat
```

### Método 3: Manual com PyInstaller
```bash
# Instalar PyInstaller
pip install pyinstaller

# Compilar PyCheatEngine principal
pyinstaller --onefile --windowed --name PyCheatEngine --clean main.py

# Compilar demonstração
pyinstaller --onefile --windowed --name PyCheatEngine_Demo --clean demo_app.py
```

### Método 4: Interface Gráfica com auto-py-to-exe
```bash
# Instalar auto-py-to-exe
pip install auto-py-to-exe

# Abrir interface gráfica
auto-py-to-exe
```

## Configurações Recomendadas

### Para PyInstaller:
- `--onefile`: Cria um único arquivo executável
- `--windowed`: Remove janela do console (para GUI)
- `--name`: Define nome do executável
- `--clean`: Limpa cache antes de compilar
- `--icon`: Adiciona ícone (opcional)

### Para auto-py-to-exe:
1. **Script Location**: Selecione `main.py` ou `demo_app.py`
2. **Onefile**: Marque "One File"
3. **Console Window**: Desmarque (Window Based)
4. **Icon**: Adicione ícone se desejar
5. **Additional Files**: Adicione pasta `ui/` se necessário

## Resultado da Compilação

Após a compilação, você terá:
- `dist/PyCheatEngine.exe` (versão completa)
- `dist/PyCheatEngine_Demo.exe` (demonstração)
- `PyCheatEngine_Portable/` (pasta com documentação)

## Tamanhos Esperados
- PyCheatEngine completo: ~15-25 MB
- Demonstração: ~12-20 MB

## Problemas Comuns

### 1. Erro "Module not found"
```bash
# Adicione imports explícitos
pyinstaller --hidden-import=tkinter --hidden-import=psutil main.py
```

### 2. Arquivos não incluídos
```bash
# Adicione arquivos/pastas extras
pyinstaller --add-data "ui;ui" main.py
```

### 3. Muito lento para iniciar
```bash
# Use --exclude-module para remover módulos desnecessários
pyinstaller --exclude-module matplotlib main.py
```

## Distribuição

Para distribuir o PyCheatEngine:

1. **Arquivo único**: Envie apenas o `.exe`
2. **Pacote completo**: Use a pasta `PyCheatEngine_Portable/`
3. **Requisitos**: Windows 7+ (não precisa Python instalado)
4. **Privilégios**: Execute como Administrador

## Comandos Úteis

```bash
# Verificar dependências
pip list

# Limpar builds anteriores
rmdir /s dist build
del *.spec

# Teste rápido
pyinstaller --onefile --console demo_app.py
```

## Configuração Avançada

Para customizações avançadas, edite o arquivo `.spec` gerado:

```python
# PyCheatEngine.spec
a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[('ui', 'ui')],
             hiddenimports=['tkinter', 'psutil'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='PyCheatEngine',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='icon.ico')
```

Depois execute:
```bash
pyinstaller PyCheatEngine.spec
```

## Otimizações

### Reduzir tamanho:
```bash
pip install upx
pyinstaller --upx-dir=/path/to/upx --onefile main.py
```

### Melhorar velocidade:
```bash
pyinstaller --onedir main.py  # Em vez de --onefile
```