@echo off
title Instalador - Simonetto Devolucoes
setlocal

set "PADRAO=http://192.168.1.12:8080"
set "DESTINO=%LOCALAPPDATA%\SimonettoDevolucoes"

echo ================================================
echo   Instalador do Simonetto Devolucoes (cliente)
echo ================================================
echo.

if not exist "%~dp0Simonetto-Cliente.exe" (
  echo ERRO: o arquivo Simonetto-Cliente.exe precisa estar
  echo nesta mesma pasta que o Instalar.bat.
  echo.
  pause
  exit /b 1
)

echo Endereco do servidor (PC principal).
echo Pressione ENTER para usar o padrao, ou digite outro.
set /p "SERVIDOR=Endereco [%PADRAO%]: "
if "%SERVIDOR%"=="" set "SERVIDOR=%PADRAO%"

echo.
echo Copiando o programa...
if not exist "%DESTINO%" mkdir "%DESTINO%"
copy /Y "%~dp0Simonetto-Cliente.exe" "%DESTINO%\Simonetto-Cliente.exe" >nul

echo Criando o atalho na area de trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $sc=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Simonetto Devolucoes.lnk'); $sc.TargetPath='%DESTINO%\Simonetto-Cliente.exe'; $sc.Arguments='%SERVIDOR%'; $sc.WorkingDirectory='%DESTINO%'; $sc.IconLocation='%DESTINO%\Simonetto-Cliente.exe,0'; $sc.Description='Gerenciador de Devolucoes'; $sc.Save()"

echo.
echo ================================================
echo   Pronto! Foi criado o icone "Simonetto Devolucoes"
echo   na area de trabalho, apontando para:
echo   %SERVIDOR%
echo.
echo   Pode fechar esta janela e abrir pelo icone.
echo ================================================
echo.
pause
