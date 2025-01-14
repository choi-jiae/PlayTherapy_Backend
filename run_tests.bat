@echo off
setlocal

set modules=api/auth-api api/contents-api api/script-api api/analyze-api package/core-package package/object-package

for %%G in (%modules%) do (
    cd %%G
    poetry install --sync
    poetry run python -m unittest discover -s tests
    cd ..
    cd ..
)

if %ERRORLEVEL% EQU 0 (
    echo All tests finished successfully
) else (
    echo Error occurred during tests
)

endlocal