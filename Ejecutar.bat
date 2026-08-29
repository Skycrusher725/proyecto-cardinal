@echo off
title Proyecto Cardinal - Torre de Control
cd /d "C:\Users\Usuario\Desktop\Proyecto_Cardinal"

echo Iniciando Proyecto Cardinal (Sistema Unificado)...
start "" python -m streamlit run app.py --server.port=8501 --server.headless=true

:: Esperar a que levante el servidor y abrir el navegador
timeout /t 3 >nul
start http://localhost:8501

echo.
echo ¡El sistema esta en ejecucion!
echo - Pestaña normal (o principal): Ingresa como admin
echo - Pestaña de incognito: Ingresa como erika.aguirre
echo.
pause