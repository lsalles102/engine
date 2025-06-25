@echo off
title PyCheatEngine - Compilador Windows
color 0A

echo.
echo ========================================
echo     PyCheatEngine - Compilador Windows
echo ========================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Verificando PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller nao encontrado. Instalando...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERRO: Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo PyInstaller OK!
echo.

echo Limpando builds anteriores...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist __pycache__ rmdir /s /q __pycache__ >nul 2>&1
for %%f in (*.spec) do if not "%%f"=="PyCheatEngine_Demo.spec" del "%%f" >nul 2>&1

echo.
echo Escolha o tipo de compilacao:
echo.
echo [1] GUI - Interface Grafica (Recomendado)
echo [2] CLI - Linha de Comando
echo [3] Standalone - Versao Completa
echo [4] Todas as Versoes
echo [0] Sair
echo.

set /p choice="Digite sua opcao (0-4): "

if "%choice%"=="0" goto :end
if "%choice%"=="1" goto :compile_gui
if "%choice%"=="2" goto :compile_cli
if "%choice%"=="3" goto :compile_standalone
if "%choice%"=="4" goto :compile_all

echo Opcao invalida!
pause
goto :end

:compile_gui
echo.
echo === COMPILANDO VERSAO GUI ===
echo.
pyinstaller --onefile --windowed --name=PyCheatEngine_GUI --add-data="ui;ui" --hidden-import=tkinter --hidden-import=psutil --hidden-import=ctypes --distpath=dist/gui main.py

if errorlevel 1 (
    echo ERRO na compilacao GUI!
) else (
    echo GUI compilada com sucesso!
)
goto :show_results

:compile_cli
echo.
echo === COMPILANDO VERSAO CLI ===
echo.
pyinstaller --onefile --console --name=PyCheatEngine_CLI --add-data="ui;ui" --hidden-import=psutil --hidden-import=ctypes --distpath=dist/cli main.py

if errorlevel 1 (
    echo ERRO na compilacao CLI!
) else (
    echo CLI compilada com sucesso!
)
goto :show_results

:compile_standalone
echo.
echo === COMPILANDO VERSAO STANDALONE ===
echo.
pyinstaller --onefile --console --name=PyCheatEngine_Standalone --add-data="ui;ui" --hidden-import=tkinter --hidden-import=psutil --hidden-import=ctypes --distpath=dist/standalone pycheatengine_standalone.py

if errorlevel 1 (
    echo ERRO na compilacao Standalone!
) else (
    echo Standalone compilada com sucesso!
)
goto :show_results

:compile_all
echo.
echo === COMPILANDO TODAS AS VERSOES ===
echo.

echo Compilando GUI...
pyinstaller --onefile --windowed --name=PyCheatEngine_GUI --add-data="ui;ui" --hidden-import=tkinter --hidden-import=psutil --hidden-import=ctypes --distpath=dist/gui main.py

echo Compilando CLI...
pyinstaller --onefile --console --name=PyCheatEngine_CLI --add-data="ui;ui" --hidden-import=psutil --hidden-import=ctypes --distpath=dist/cli main.py

echo Compilando Standalone...
pyinstaller --onefile --console --name=PyCheatEngine_Standalone --add-data="ui;ui" --hidden-import=tkinter --hidden-import=psutil --hidden-import=ctypes --distpath=dist/standalone pycheatengine_standalone.py

echo.
echo Todas as versoes compiladas!

:show_results
echo.
echo ========================================
echo           RESULTADOS
echo ========================================
echo.

if exist dist (
    echo Executaveis criados em:
    for /r dist %%f in (*.exe) do (
        echo   %%f
    )
    echo.
    echo Para testar, execute os arquivos .exe como Administrador
    echo.
    echo IMPORTANTE: 
    echo - Execute sempre como Administrador
    echo - Alguns antivirus podem detectar como falso positivo
    echo - Use apenas em processos proprios ou autorizados
) else (
    echo Nenhum executavel foi criado!
)

:end
echo.
pause