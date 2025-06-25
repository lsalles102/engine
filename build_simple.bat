@echo off
echo === Compilador PyCheatEngine para EXE ===
echo.

:: Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Erro: Python não está instalado ou não está no PATH
    pause
    exit /b 1
)

:: Instala PyInstaller se necessário
echo Verificando PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

:: Compila PyCheatEngine principal
echo.
echo Compilando PyCheatEngine...
pyinstaller --onefile --windowed --name PyCheatEngine --clean main.py

:: Compila demonstração
echo.
echo Compilando demonstração...
pyinstaller --onefile --windowed --name PyCheatEngine_Demo --clean demo_app.py

:: Verifica resultados
if exist "dist\PyCheatEngine.exe" (
    echo.
    echo ✓ PyCheatEngine.exe compilado com sucesso!
    for %%F in ("dist\PyCheatEngine.exe") do echo   Tamanho: %%~zF bytes
)

if exist "dist\PyCheatEngine_Demo.exe" (
    echo ✓ PyCheatEngine_Demo.exe compilado com sucesso!
    for %%F in ("dist\PyCheatEngine_Demo.exe") do echo   Tamanho: %%~zF bytes
)

echo.
echo Arquivos criados na pasta 'dist\'
echo.
pause