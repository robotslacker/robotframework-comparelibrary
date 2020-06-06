del /s/q dist\*
del /s/q build\*
python setup.py sdist
python setup.py bdist_wheel --universal

pip uninstall --yes robotframework-comparelibrary
python setup.py install
python -m robot.libdoc .\CompareLibrary doc\CompareLibrary.html
REM twine upload dist/*