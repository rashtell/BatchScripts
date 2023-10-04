@echo off
setlocal enabledelayedexpansion

:: Set the path to your projects directory
set "directory="
set "prompt=Enter the project index or name: "

:: Gets the flag arguments
:GETOPTS
 if /I %~1 == --dir set directory=%2& shift
 if /I %~1 == --prompt set prompt=%2& shift
 shift
if not (%1)==() goto GETOPTS

if not exist %directory% (
    set "directory=C:\workspace\projects"
)

:: Remove double quotation marks from the beginning and end of the string
set "first_char=!prompt:~0,1!"
set "last_char=!prompt:~-1,1!"

if !first_char!==^" (
    set prompt=!prompt:~1!
)
if !last_char!==^" (
    set prompt=!prompt:~0,-1!
)

:: Add column and space to the end prompt 
echo !prompt! | find ": " > nul
if errorlevel 1 (
    set "prompt=!prompt!: "
) 


:: Initialize variables
set "selected_project="
set "project="

:: Display existing project names with numbered indices
echo Existing Projects:
set "index=0"
for /d %%i in ("%directory%\*") do (
    set /a "index+=1"
    echo !index!. %%~nxi
    set "project[!index!]=%%~nxi"
)

:: Prompt for project index or name input
:input_loop
set /p "input=%prompt%"

:: Check if the input is a valid number
for /l %%i in (1, 1, !index!) do (
    if "!input!"=="%%i" (
        set "selected_project=!project[%%i]!"
    )
)

:: Check if the variable contains only digits
set "isNumber=true"
for /f "delims=0123456789" %%a in ("!input!") do (
    set "isNumber=false"
)


if "!selected_project!"=="" (
    if !isNumber!==true (
        echo Invalid input. Please enter a valid project index or name.
        goto :input_loop
    ) else if  "%input%"=="" (
        echo Invalid input. Please enter a valid project index or name.
        goto :input_loop
    ) else (
        set "selected_project=%input%"
    )
)

echo !selected_project!
