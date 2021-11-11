#!/bin/bash
pip install -r requirements.txt -i https://mirror.baidu.com/pypi/simple

rm -rf ./dist
rm -rf ./build
rm -rf ./kaggle_environments.egg-info
# Delete pycache, pyc, and pyo files
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

result=$(echo `python --version 2>&1` | grep "Python 3.9")

if [[ "$result" != "" ]]
then 
    python setup.py sdist
    python setup.py bdist_wheel --universal
    python setup.py install
else
    result=$(echo `python3 --version 2>&1` | grep "Python 3.9")
    if [[ "$result" != "" ]]
    then
        python3 setup.py sdist
        python3 setup.py bdist_wheel --universal
        python3 setup.py install
    else
        echo "Please Install The Correct Python Verison.(3.9)"
    fi
fi