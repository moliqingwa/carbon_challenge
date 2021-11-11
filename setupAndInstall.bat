@echo off 
pip install -r requirements.txt -i https://mirror.baidu.com/pypi/simple

del /s /q .\dist\*.*
rd  /s /q .\dist
del /s /q .\build\*.*
rd  /s /q .\build
del /s /q .\zerosum_env.egg-info\*.*
rd  /s /q .\zerosum_env.egg-info
del *.pyc*
del *.pyo*

python setup.py sdist
python setup.py bdist_wheel --universal
python setup.py install

echo "Installation is complete. Press any key to exit......"
pause

