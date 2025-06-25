@echo off
title PyCheatEngine
echo Iniciando PyCheatEngine...
echo.

python PyCheatEngine.py

if errorlevel 1 (
    echo.
    echo Erro: Python não encontrado ou erro na execução
    echo Certifique-se de que o Python está instalado
    echo.
    pause
)
