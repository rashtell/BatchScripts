@echo off
:: Elevate the current console window to admin
::#region
setlocal
cd /d "%~dp0"
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if "%errorlevel%" NEQ "0" (
    powershell -Command "Start-Process '%0' -Verb RunAs"
    exit /b
)
endlocal
::#endregion

:: Actual script starts here
setlocal EnableDelayedExpansion

:: Inputs
::#region
:input_project_name
set /p project_name=Enter project name: 
if "%project_name%"=="" (
    echo Project name cannot be empty. Please try again.
    goto :input_project_name
)
:: Convert to camel case and remove spaces
for /f "delims=" %%a in ('to-camel-case.bat %project_name%') do (
    set "project_name=%%a"
)

set /p sub_project_name=Enter sub project name: 
if "%sub_project_name%"=="" (
    set "sub_project_name=!project_name!"
)
:: Convert to camel case and remove spaces
for /f "delims=" %%a in ('to-camel-case.bat %sub_project_name%') do (
    set "sub_project_name=%%a"
)

:input_organization
set /p organization=Enter organization name: 
if "%organization%"=="" (
    echo Organization name cannot be empty. Please try again.
    goto :input_organization
)
:: Convert to camel case and remove spaces
for /f "delims=" %%a in ('to-camel-case.bat %organization%') do (
    set "organization=%%a"
)

:input_platform
set /p platform=Enter platform: 
if "%platform%"=="" (
    echo Platform cannot be empty. Please try again.
    goto :input_platform
)
:: Convert to camel case and remove spaces
for /f "delims=" %%a in ('to-camel-case.bat %platform%') do (
    set "platform=%%a"
)

:input_language
set /p language=Enter language: 
if "%language%"=="" (
    echo Project name cannot be empty. Please try again.
    goto :input_language
)
:: Convert to camel case and remove spaces
for /f "delims=" %%a in ('to-camel-case.bat %language%') do (
    set "language=%%a"
)

set /p framework=Enter framework: 
if "%framework%"=="" (
    set "sub_project_name=unknown"
)
:: Convert to camel case and remove spaces
for /f "delims=" %%a in ('to-camel-case.bat %framework%') do (
    set "framework=%%a"
)
::#endregion

:: clear console
cls

set "workspace_path=C:\workspace"


:: Handle project
::#region
set "project_path=%workspace_path%\projects\!project_name!"
set "sub_project_path=%project_path%\%sub_project_name%"

if not exist "%sub_project_path%" (
    md "%sub_project_path%"

    echo Project directory created.
) else (
    echo Project directory already exists.
)
::#endregion

:: Handle platform
::#region
set "platform_project_path=%workspace_path%\platforms\%platform%\%sub_project_name%"

if not exist "%platform_project_path%" (
    
    set "platform_path=%workspace_path%\platforms\%platform%"

    if not exist "!platform_path!" (
        md "!platform_path!"
    )
    
    mklink /D "%platform_project_path%" "%sub_project_path%"

    echo Sub-project linked to platform.
) else (
    echo Sub-project already linked to platform.
)
::#endregion

:: Handle organization
::#region
set "organization_path=%workspace_path%\organizations\%organization%"
set "organization_project_path=%organization_path%\!project_name!"

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
set "language_path=%workspace_path%\languages\%language%"
set "language_project_path=%language_path%\%sub_project_name%"

if not exist "%language_project_path%" (

    if not exist "%language_path%" (
        md "%language_path%"
    )

    mklink /D "%language_project_path%" "%sub_project_path%"

    echo Sub-project linked to language.
) else (
    echo Sub-project already linked to language.
)

if /i "!language!"=="php" (
    mklink /D "C:\xampp\htdocs\!sub_project_name!" "%sub_project_path%"
    mklink /D "C:\xampp7.4\htdocs\!sub_project_name!" "%sub_project_path%"
    echo Project linked to xampp.
)
::#endregion

:: Handle framework
::#region
set "framework_path=%workspace_path%\frameworks\%framework%"
set "framework_project_path=%framework_path%\%sub_project_name%"

if not exist "%framework_project_path%" (

    if not exist "%framework_path%" (
        md "%framework_path%"
    )

    mklink /D "%framework_project_path%" "%sub_project_path%"

    echo Sub-project linked to framework.
) else (
    echo Sub-project already linked to framework.
)
::#endregion

:: Handle language/framework
::#region
set "lang_frame_path=%workspace_path%\lang-frames\%language%\%framework%"
set "lang_frame_project_path=%lang_frame_path%\%sub_project_name%"

if not exist "%lang_frame_project_path%" (

    if not exist "%lang_frame_path%" (
        md "%lang_frame_path%"
    )

    mklink /D "%lang_frame_project_path%" "%sub_project_path%"

    echo Sub-project linked to lang-frame.
) else (
    echo Sub-project already linked to lang-frame.
)
::#endregion


echo "Project setup completed."
pause