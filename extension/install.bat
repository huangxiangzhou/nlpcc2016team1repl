setlocal
cd /d %~dp0
Path=%PATH%;%~dp0
python setup.py install
pause
endlocal