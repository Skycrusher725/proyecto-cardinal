@echo off
cd /d "%~dp0"
echo Buscando entorno virtual y arrancando Cardinal...

:: Busca python localmente dentro de carpetas comunes de entornos
if exist ".venv\Scripts\python.exe" (
    echo Usando .venv...
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else if exist "venv\Scripts\python.exe" (
    echo Usando venv...
    "venv\Scripts\python.exe" -m streamlit run app.py
) else (
    echo No se encontro entorno virtual local. Usando python global...
    python -m streamlit run app.py
)

pause