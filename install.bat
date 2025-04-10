@echo off
echo Installing Python modules...

REM Ensure pip is available
python -m ensurepip --default-pip

REM Upgrade pip to latest version
python -m pip install --upgrade pip

REM Install the required modules
python -m pip install discord telnetlib3 python-dotenv

echo Done installing modules.
pause