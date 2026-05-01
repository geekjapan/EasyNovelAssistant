@echo off
chcp 65001 > NUL
call %~dp0EasyNovelAssistant\setup\ActivateVirtualEnvironment.bat
if %errorlevel% neq 0 ( exit /b 1 )
echo uv is ready. Use Run-EasyNovelAssistant.bat to start the app.
cmd /k
