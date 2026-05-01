@echo off
chcp 65001 > NUL
pushd %~dp0
call EasyNovelAssistant\setup\ActivateVirtualEnvironment.bat
if %errorlevel% neq 0 ( popd & exit /b 1 )

"%UV_CMD%" run --python %PYTHON_CMD% EasyNovelAssistant\setup\run_easy_novel_assistant.py
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
