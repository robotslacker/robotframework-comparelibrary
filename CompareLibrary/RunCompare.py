# -*- coding: UTF-8 -*-
import os
import argparse
import re
from robot.api import logger

class DiffException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


class POSIXCompare:
    compare_options = argparse.Namespace()
    compare_result = True

    def __init__(self):
        self.compare_options.isMaskEnabled = False

    def lcs_len(self, x, y):
        """Build a matrix of LCS length.
        This matrix will be used later to backtrack the real LCS.
        """

        # This is our matrix comprised of list of lists.
        # We allocate extra row and column with zeroes for the base case of empty
        # sequence. Extra row and column is appended to the end and exploit
        # Python's ability of negative indices: x[-1] is the last elem.
        c = [[0 for _ in range(len(y) + 1)] for _ in range(len(x) + 1)]

        for i, xi in enumerate(x):
            for j, yj in enumerate(y):
                if self.compare_string(xi, yj):
                    c[i][j] = 1 + c[i - 1][j - 1]
                else:
                    c[i][j] = max(c[i][j - 1], c[i - 1][j])
        return c

    def backtrack(self, c, x, y, i, j):
        """Backtrack the LCS length matrix to get the actual LCS"""
        if i == -1 or j == -1:
            return ""
        elif self.compare_string(x[i], y[j]):
            return self.backtrack(c, x, y, i - 1, j - 1) + x[i]
        elif c[i][j - 1] >= c[i - 1][j]:
            return self.backtrack(c, x, y, i, j - 1)
        elif c[i][j - 1] < c[i - 1][j]:
            return self.backtrack(c, x, y, i - 1, j)

    def lcs(self, x, y):
        """Get the longest common subsequence of x and y"""
        c = self.lcs_len(x, y)
        return self.backtrack(c, x, y, len(x) - 1, len(y) - 1)

    def compare_string(self, p_str1, p_str2):
        if not self.compare_options.isMaskEnabled:
            return p_str1 == p_str2
        if self.compare_options.isMaskEnabled:
            return re.match(p_str2, p_str1) is not None

    def compare(self, c, x, y, i, j, p_result):
        """Print the diff using LCS length matrix by backtracking it"""

        if i < 0 and j < 0:
            return p_result
        elif i < 0:
            self.compare(c, x, y, i, j - 1, p_result)
            self.compare_result = False
            p_result.append("+ " + y[j])
        elif j < 0:
            self.compare(c, x, y, i - 1, j, p_result)
            self.compare_result = False
            p_result.append("- " + x[i])
        elif self.compare_string(x[i], y[j]):
            self.compare(c, x, y, i - 1, j - 1, p_result)
            p_result.append("  " + x[i])
        elif c[i][j - 1] >= c[i - 1][j]:
            self.compare(c, x, y, i, j - 1, p_result)
            self.compare_result = False
            p_result.append("+ " + y[j])
        elif c[i][j - 1] < c[i - 1][j]:
            self.compare(c, x, y, i - 1, j, p_result)
            self.compare_result = False
            p_result.append("- " + x[i])
        return self.compare_result, p_result

    def set_compare_options(self, options):
        self.compare_options = options

    def compare_text_files(self, file1, file2):
        if not os.path.isfile(file1):
            raise DiffException('ERROR: %s is not a file' % file1)
        if not os.path.isfile(file2):
            raise DiffException('ERROR: %s is not a file' % file2)

        file1content = open(file1, mode='r').readlines()
        file2content = open(file2, mode='r').readlines()

        m_lcs = self.lcs_len(file1content, file2content)
        m_result = []
        return self.compare(m_lcs, file1content, file2content,
                            len(file1content) - 1, len(file2content) - 1, m_result)


class RunCompare(object):
    Reference_LogDirLists = []
    BreakWithDifference = False

    def Set_Break_With_Difference(self, p_BreakWithDifference):
        """ 设置是否在遇到错误的时候中断该Case的后续运行
        输入参数：
             p_BreakWithDifference:        是否在遇到Dif的时候中断，默认为不中断
        返回值：
            无

        如果设置为True，则Case运行会中断，Case会被判断执行失败
        如果设置为False，则Case运行不会中断，但是在运行目录下会生成一个.dif文件，供参考
        """
        if str(p_BreakWithDifference).upper() == 'TRUE':
            self.BreakWithDifference = True

    def Set_Reference_LogDir(self, p_szPath):
        """ 设置参考文件的来源目录
          Compare 在比对的时候会按照如下顺序来查找引用文件：
          1： 当前文件运行目录
          2：  p_szPath中指定的目录

        输入参数：
             p_szPath:        用冒号：分开的一个或多个路径信息
        返回值：
            无

        例外：
            无
        """
        self.Reference_LogDirLists = p_szPath.split(':')

    def Compare_Files(self, p_szWorkFile, p_szReferenceFile, *rest):
        """ 比较两个文件是否一致
        输入参数：
             p_szWorkFile:        需要比对的当前结果文件
             p_szReferenceFile：  需要比对的结果参考文件
             *rest:               其他比对选项，支持的选项有：
                  MASK            表示结果参考文件中可以有正则表达式内容

        返回值：
            True           比对完成成功
            False          比对中发现了差异

        例外：
            在Set_Break_With_Difference为True后，若比对发现差异，则抛出例外
        """
        CompareOptions = argparse.Namespace()
        if 'MASK' in rest:
            CompareOptions.isMaskEnabled = True
        else:
            CompareOptions.isMaskEnabled = False

        (m_WorkFilePath, m_TempFileName) = os.path.split(p_szWorkFile)
        (m_ShortWorkFileName, m_WorkFileExtension) = os.path.splitext(m_TempFileName)
        m_DifFilePath = m_WorkFilePath
        m_DifFileName = m_ShortWorkFileName + '.dif'
        m_DifFullFileName = os.path.join(m_DifFilePath, m_DifFileName)
        m_SucFilePath = m_WorkFilePath
        m_SucFileName = m_ShortWorkFileName + '.suc'
        m_SucFullFileName = os.path.join(m_SucFilePath, m_SucFileName)

        # remove old file first
        if os.path.exists(m_DifFullFileName):
            os.remove(m_DifFullFileName)
        if os.path.exists(m_SucFullFileName):
            os.remove(m_SucFullFileName)

        # check if work file exist
        if not os.path.isfile(p_szWorkFile):
            if self.BreakWithDifference:
                raise RuntimeError('===============   work log [' + p_szWorkFile + '] does not exist ============')
            else:
                m_CompareResultFile = open(m_DifFullFileName, 'w')
                m_CompareResultFile.write(
                    '===============   work log [' + p_szWorkFile + '] does not exist ============')
                m_CompareResultFile.close()
                return False

        # search reference log 
        m_ReferenceLog = None
        for m_Reference_LogDir in self.Reference_LogDirLists:
            m_TempReferenceLog = os.path.join(m_Reference_LogDir, p_szReferenceFile)
            if os.path.isfile(m_TempReferenceLog):
                m_ReferenceLog = m_TempReferenceLog
                break
        if m_ReferenceLog is None:
            m_ReferenceLog = p_szReferenceFile
        if not os.path.isfile(m_ReferenceLog):
            if self.BreakWithDifference:
                raise RuntimeError('===============   reference log [' + m_ReferenceLog +
                                   '] does not exist ============')
            else:
                m_CompareResultFile = open(m_DifFullFileName, 'w')
                m_CompareResultFile.write('===============   reference log [' + m_ReferenceLog +
                                          '] does not exist ============')
                m_CompareResultFile.close()
                return False

        # compare file
        m_Comparer = POSIXCompare()
        m_Comparer.set_compare_options(CompareOptions)
        m_CompareResult = m_Comparer.compare_text_files(p_szWorkFile, m_ReferenceLog)

        if m_CompareResult[0]:
            m_CompareResultFile = open(m_SucFullFileName, 'w')
            m_CompareResultFile.close()
            return True

        if not m_CompareResult[0]:
            logger.write("======= Diff file [" + m_DifFullFileName + "] >>>>> ")
            m_CompareResultFile = open(m_DifFullFileName, 'w')
            for line in m_CompareResult[1]:
                m_CompareResultFile.write(line)
                logger.write("    " + line);
            m_CompareResultFile.close()
            logger.write("======= Diff file [" + m_DifFullFileName + "] <<<<<< ")
            if self.BreakWithDifference:
                raise RuntimeError('Got Difference. Please check [' + m_DifFullFileName + '] for more information.')
            else:
                return False


if __name__ == '__main__':
    print("RunSQLCli. Please use this in RobotFramework.")
    m_Handle = RunCompare()
    m_Handle.Compare_Files("test.log", "test.ref", "MASK")
