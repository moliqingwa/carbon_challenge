@echo off 
set MODULES=flask gym ipython jsonschema numpy requests wheel
(for %%m in (%MODULES%) do ( 
    pip install %%m
))

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

