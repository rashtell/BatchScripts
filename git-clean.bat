@echo off
setlocal enabledelayedexpansion

git fetch -p

for /f "tokens=1" %%i in ('git branch -vv ^| findstr /C:"gone"') do (
    set "branch=%%i"
    if "!branch:~0,1!"=="*" set "branch=!branch:~2!"
    git branch -d "!branch!"
)