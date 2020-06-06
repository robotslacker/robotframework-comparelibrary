# -*- coding: utf-8 -*-

from CompareLibrary.RunCompare import RunCompare


class CompareLibrary(RunCompare):
    """ RobotFrameWork 扩展库

    `CompareLibrary` 是RobotFrameWork的一个扩展库，通过这个扩展库，我们可以在Robot中比对程序运行结果和参考文件的差异

    以下是在Robot中调用该扩展库的例子：
    ========================================================
    *** Settings ***
    Library           CompareLibrary

    *** Test Cases ***
    E101Test
        Set Break With Difference      True
        Set Reference LogDir           Dir1;Dir2;
        Compare Files                  test.log  testref.log [MASK]
    ========================================================

    如何利用Robot来执行上述文件：
    $>  robot [test file]
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_DOC_FORMAT = 'TEXT'
    ROBOT_LIBRARY_VERSION = '0.0.11'
