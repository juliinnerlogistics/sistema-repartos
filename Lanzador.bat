@echo off
title Lanzador Sistema de Reparto
echo ---------------------------------------------------
echo Iniciando aplicacion...
echo Si es la primera vez, puede tardar unos segundos.
echo ---------------------------------------------------
echo.

:: Ejecuta Streamlit usando el modulo de Python
python -m streamlit run app.py

echo.
echo ---------------------------------------------------
echo EL PROGRAMA SE DETUVO.
echo Si ves un error arriba, por favor copialo.
echo ---------------------------------------------------
pause