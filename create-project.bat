@echo off
:: BatchGotAdmin code
::#region
setlocal
if "%1"=="ELEV" (
    shift
    goto main
)
:: Self-elevate using a VBScript hidden window
set "vbs=%temp%\getadmin.vbs"
echo Set UAC = CreateObject^("Shell.Application"^)>"%vbs%"
echo UAC.ShellExecute "%~s0", "ELEV %*", "", "runas", 1 >>"%vbs%"
"%temp%\getadmin.vbs"
del "%temp%\getadmin.vbs"
exit /b

:main
::#endregion

:: Actual script starts here
setlocal EnableDelayedExpansion

:: Inputs
::#region
set /p project_name=Enter project name: 
set /p platform=Enter platform: 
set /p language=Enter language: 
set /p organization=Enter organization: 
::#endregion

:: clear console
cls

set "workspace_path=C:\workspace"

:: Handle project
::#region
set "project_path=%workspace_path%\project\%project_name%"

if not exist "%project_path%" (
    md "%project_path%"

    echo Project directory created.
) else (
    echo Project directory already exists.
)
::#endregion

:: Handle platform
::#region
set "platform_project_path=%workspace_path%\platform\%platform%\%project_name%"

if not exist "%platform_project_path%" (

    set "platform_path=%workspace_path%\platform\%platform%"
    if not exist "!platform_path!" (
        md "!platform_path!"
    )
    
    mklink /D "%platform_project_path%" "%project_path%"

    echo Project linked to platform.
) else (
    echo Project already linked to platform.
)
::#endregion

:: Handle organization
::#region
set "organization_path=%workspace_path%\organization\%organization%"
set "organization_project_path=%organization_path%\%project_name%"

if not exist "%organization_project_path%" (

    if not exist "%organization_path%" (
        md "%organization_path%"
    )

    mklink /D "%organization_project_path%" "%project_path%"

    echo Project linked to organization.
) else (
    echo Project already linked to organization.
)
::#endregion

:: Handle language
::#region

set "language_path=%workspace_path%\language"

:: Appends javascript to language path if the inputted language is a javascript language
for /d %%d in ("%language_path%\javascript\*") do (
    set "folder_name=%%~nd"
    if /i "!folder_name!"=="%language%" (
        set "language_path=!language_path!\javascript\!language!"
        goto :found
    )
)
:found

if "%language_path%" equ "%workspace_path%\language" (
    set "language_path=!language_path!\!language!"
)

set "language_project_path=%language_path%\%project_name%"

if not exist "%language_project_path%" (

    if not exist "%language_path%" (
        md "%language_path%"
    )

    mklink /D "%language_project_path%" "%project_path%"

    echo Project linked to language.
) else (
    echo Project already linked to language.
)

if "%language%"=="php" (
    mklink /D "C:\xampp\htdocs\%project_name%" "%project_path%"
    mklink /D "C:\xampp7.4\htdocs\%project_name%" "%project_path%"
    echo Project linked to xampp.
)
::#endregion

echo "Project setup completed."
pause