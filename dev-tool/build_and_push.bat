@echo off
SETLOCAL EnableDelayedExpansion

REM Get the directory of the current batch script
SET "SCRIPT_DIR=%~dp0"

REM Remove trailing backslash
SET "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Get version from Python script
FOR /F "tokens=*" %%i IN ('python3 -c "import sys; sys.path.insert(0, r'%SCRIPT_DIR%\..\api\%1-api\%1\setting'); from config import Settings; print(Settings.VERSION)"') DO SET VERSION=%%i

IF "!VERSION!"=="" (
    echo can't extract version
    exit /b 1
)

REM Build the Docker image
docker build --build-arg="SOURCE_DIR=api/%1-api" --build-arg="APP_DIR=%1" --platform linux/amd64 -t docker address%1-api:!VERSION! "%SCRIPT_DIR%\.."

IF NOT %ERRORLEVEL% EQU 0 (
    echo docker image build failed
    exit /b 1
)

REM Push the Docker image
docker push docker address%1-api:!VERSION!

IF NOT %ERRORLEVEL% EQU 0 (
    echo docker image push failed
    exit /b 1
)

ENDLOCAL