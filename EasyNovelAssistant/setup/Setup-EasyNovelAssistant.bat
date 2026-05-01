@echo off
chcp 65001 > NUL
pushd %~dp0..\..
set PS_CMD=PowerShell -Version 5.1 -ExecutionPolicy Bypass

echo copy /Y %~dp0Install-EasyNovelAssistant.bat Update-EasyNovelAssistant.bat > NUL
copy /Y %~dp0Install-EasyNovelAssistant.bat Update-EasyNovelAssistant.bat > NUL
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )

call %~dp0ActivateVirtualEnvironment.bat
if %errorlevel% neq 0 ( popd & exit /b 1 )

echo %PYTHON_CMD% -c "import tkinter" > NUL 2>&1
%PYTHON_CMD% -c "import tkinter" > NUL 2>&1
if %errorlevel% neq 0 (
	cd > NUL
	echo %PS_CMD% Expand-Archive -Path %~dp0res\tkinter-PythonSoftwareFoundationLicense.zip -DestinationPath %PYTHON_DIR% -Force
	%PS_CMD% Expand-Archive -Path %~dp0res\tkinter-PythonSoftwareFoundationLicense.zip -DestinationPath %PYTHON_DIR% -Force
)

echo %UV_CMD% run --python %PYTHON_CMD% %~dp0setup_easy_novel_assistant.py
"%UV_CMD%" run --python %PYTHON_CMD% %~dp0setup_easy_novel_assistant.py
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
