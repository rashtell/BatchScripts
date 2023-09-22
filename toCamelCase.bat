@echo off
setlocal enabledelayedexpansion

set /p input=Input sentence: 

:: Run the to-camel-case.bat command and capture its output using a for /f loop
for /f "delims=" %%a in ('to-camel-case.bat %input%') do (
    set "input=%%a"
)

:: Display the captured output
echo Result: %input%

endlocal
