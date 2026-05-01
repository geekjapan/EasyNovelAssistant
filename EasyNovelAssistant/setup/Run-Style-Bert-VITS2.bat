@echo off
chcp 65001 > NUL

if not exist %~dp0..\..\Style-Bert-VITS2 (
	echo [Error] Style-Bert-VITS2 がインストールされていません。
	pause & exit /b 1
)

pushd %~dp0..\..\Style-Bert-VITS2

call %~dp0ActivateVirtualEnvironment.bat
if %errorlevel% neq 0 ( popd & exit /b 1 )

set STYLE_BERT_UV_DEPS=--with-requirements requirements.txt --with GPUtil --with torch --with torchvision --with torchaudio --index https://download.pytorch.org/whl/cu118 --index-strategy unsafe-best-match

@REM --cpu
echo "%UV_CMD%" run --python "%PYTHON_CMD%" %STYLE_BERT_UV_DEPS% server_fastapi.py %*
"%UV_CMD%" run --python "%PYTHON_CMD%" %STYLE_BERT_UV_DEPS% server_fastapi.py %*
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )

popd
