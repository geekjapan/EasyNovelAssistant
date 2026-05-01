chcp 65001 > NUL
@echo off

pushd %~dp0
call %~dp0..\EasyNovelAssistant\setup\ActivateVirtualEnvironment.bat
if %errorlevel% neq 0 ( popd & exit /b 1 )

set STYLE_BERT_UV_DEPS=--with-requirements requirements.txt --with GPUtil --with torch --with torchvision --with torchaudio --index https://download.pytorch.org/whl/cu118 --index-strategy unsafe-best-match

echo "%UV_CMD%" run --python "%PYTHON_CMD%" %STYLE_BERT_UV_DEPS% server_fastapi.py --cpu
"%UV_CMD%" run --python "%PYTHON_CMD%" %STYLE_BERT_UV_DEPS% server_fastapi.py --cpu

if %errorlevel% neq 0 ( pause & popd & exit /b %errorlevel% )

popd
pause
