# -*- coding: UTF-8 -*-
import os
import re

from robot.api import logger
import shlex


class DiffException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


class POSIXCompare:
    compare_result = True
    compare_maskEnabled = False

    def __init__(self):
        pass

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

    # 正则表达比较两个字符串
    # p_str1 原字符串
    # p_str2 正则表达式
    def compare_string(self, p_str1, p_str2):
        if p_str1 == p_str2:
            return True
        else:
            if not self.compare_maskEnabled:
                return False
            else:
                try:
                    return re.match(p_str2, p_str1) is not None
                except re.error:
                    # 正则表达式错误，可能是由于这并非是一个正则表达式
                    return False

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

    def compare_text_files(self, file1, file2,
                           skiplines=None, ignoreEmptyLine=False,
                           CompareWithMask=None):
        if not os.path.isfile(file1):
            raise DiffException('ERROR: %s is not a file' % file1)
        if not os.path.isfile(file2):
            raise DiffException('ERROR: %s is not a file' % file2)

        # 是否需要用正则表达是比较
        self.compare_maskEnabled = CompareWithMask

        file1content = open(file1, mode='r', encoding='utf-8').readlines()
        file2content = open(file2, mode='r', encoding='utf-8').readlines()

        # 去除在SkipLine里头的所有内容
        if skiplines is not None:
            m_nPos = 0
            while m_nPos < len(file1content):
                bMatch = False
                for pattern in skiplines:
                    if self.compare_string(file1content[m_nPos], pattern):
                        file1content.pop(m_nPos)
                        bMatch = True
                        break
                if not bMatch:
                    m_nPos = m_nPos + 1

            m_nPos = 0
            while m_nPos < len(file2content):
                bMatch = False
                for pattern in skiplines:
                    if self.compare_string(file2content[m_nPos], pattern):
                        file2content.pop(m_nPos)
                        bMatch = True
                        break
                if not bMatch:
                    m_nPos = m_nPos + 1

        # 去除所有的空行
        if ignoreEmptyLine:
            m_nPos = 0
            while m_nPos < len(file1content):
                if len(file1content[m_nPos].strip()) == 0:
                    file1content.pop(m_nPos)
                else:
                    m_nPos = m_nPos + 1
            m_nPos = 0
            while m_nPos < len(file2content):
                if len(file2content[m_nPos].strip()) == 0:
                    file2content.pop(m_nPos)
                else:
                    m_nPos = m_nPos + 1

        # 开始比较
        m_lcs = self.lcs_len(file1content, file2content)
        m_result = []
        return self.compare(m_lcs, file1content, file2content,
                            len(file1content) - 1, len(file2content) - 1, m_result)


class RunCompare(object):
    __Reference_LogDirLists = None
    __SkipLines = []
    __BreakWithDifference = False             # 是否在遇到比对错误的时候抛出运行例外
    __EnableConsoleOutPut = False             # 是否关闭在Console上的显示，默认是不关闭
    __IgnoreEmptyLine = False                 # 是否在比对的时候忽略空白行
    __CompareWithMask = False                 # 是否在比对的时候利用正则表达式
    __CompareFailedCount = 0                  # Compare已经失败的个次数

    def __init__(self):
        pass

    def Compare_Reset_FailedCount(self):
        """ 清零之前统计的日志比对失败次数  """
        """
        输入参数：
             无
        返回值：
            无
        """
        self.__CompareFailedCount = 0

    def Compare_Check_Result(self):
        """ 检查日志比对的失败次数，如果不是0，即抛出异常  """
        """
        输入参数：
             无
        返回值：
            无
        """
        if self.__CompareFailedCount != 0:
            raise RuntimeError("Total [" + str(self.__CompareFailedCount) + "] difs Found. Please double check.")

    def Compare_Ignore_EmptyLine(self, p_IgnoreEmptyLine):
        """ 设置是否在比对的时候忽略空白行  """
        """
        输入参数：
             p_IgnoreEmptyLine:        是否忽略空白行，默认不忽略
        返回值：
            无

        如果设置为True，则仅仅是空白行的差异不作为文件有差异
        如果设置为False，则需要逐行比对
        """
        if str(p_IgnoreEmptyLine).upper() == 'TRUE':
            self.__IgnoreEmptyLine = True

    def Compare_Enable_ConsoleOutput(self, p_ConsoleOutput):
        """ 设置是否在在屏幕上显示Dif文件的内容  """
        """
        输入参数：
             p_ConsoleOutput:        是否在在屏幕上显示Dif文件的内容， 默认是不显示
        返回值：
            无

        如果设置为True， 则所有Dif会显示在控制台上
        如果设置为False，则所有SQL信息不会显示在控制台上
        对于比对文件较大的场景，不建议将比对结果放在控制台上，会导致报告文件过大，而无法查看
        """
        if str(p_ConsoleOutput).upper() == 'TRUE':
            self.__EnableConsoleOutPut = True
        if str(p_ConsoleOutput).upper() == 'FALSE':
            self.__EnableConsoleOutPut = False

    def Compare_Break_When_Difference(self, p_BreakWithDifference):
        """ 设置是否在遇到错误的时候中断该Case的后续运行  """
        """
        输入参数：
             p_BreakWithDifference:        是否在遇到Dif的时候中断，默认为不中断
        返回值：
            无

        如果设置为True，则Case运行会中断，Case会被判断执行失败
        如果设置为False，则Case运行不会中断，但是在运行目录下会生成一个.dif文件，供参考
        """
        if str(p_BreakWithDifference).upper() == 'TRUE':
            self.__BreakWithDifference = True

    def Compare_Skip(self, p_szSkipLine):
        """ 设置是否在比对的时候忽略某些特殊行  """
        """
         输入参数：
              p_szSkipLine:        特殊行的正则表达式
         返回值：
             无

         可以重复执行来确定所有需要忽略的内容
         """

        if p_szSkipLine not in self.__SkipLines:
            self.__SkipLines.append(p_szSkipLine)

    def Clean_Skip(self):
        """ 清空之前设置的忽略行  """
        """
         输入参数：
             无
         返回值：
             无

         可以重复执行来确定所有需要忽略的内容
         """
        self.__SkipLines = []

    def Compare_Mask(self, p_szCompareWithMask):
        """ 设置是否在比对的时候考虑正则表达式  """
        """
         输入参数：
              p_szCompareWithMask:        在比对的时候是否考虑正则，默认是不考虑
         返回值：
             无

         """
        if str(p_szCompareWithMask).upper() == 'TRUE':
            self.__CompareWithMask = True

    def Compare_Files(self, p_szWorkFile, p_szReferenceFile):
        """ 比较两个文件是否一致  """
        """
        输入参数：
             p_szWorkFile:        需要比对的当前结果文件
             p_szReferenceFile：  需要比对的结果参考文件

        返回值：
            True           比对完成成功
            False          比对中发现了差异

        例外：
            在Compare_Break_With_Difference为True后，若比对发现差异，则抛出例外
        """
        if self.__Reference_LogDirLists is None:
            if "T_LOG" in os.environ:
                T_LOG = os.environ["T_LOG"]
                m_T_LOG_environs = shlex.shlex(T_LOG)
                m_T_LOG_environs.whitespace = ','
                m_T_LOG_environs.quotes = "'"
                m_T_LOG_environs.whitespace_split = True
                self.__Reference_LogDirLists = list(m_T_LOG_environs)

        # 检查work文件是否存在，如果存在，则文件是全路径
        if os.path.exists(p_szWorkFile):
            # 传递的是全路径
            (m_WorkFilePath, m_TempFileName) = os.path.split(p_szWorkFile)
            (m_ShortWorkFileName, m_WorkFileExtension) = os.path.splitext(m_TempFileName)
            # 如果定义了T_WORK，则dif文件生成在T_WORK下, 否则生成在当前目录下
            if "T_WORK" in os.environ:
                m_DifFilePath = os.environ["T_WORK"]
                m_DifFileName = m_ShortWorkFileName + '.dif'
                m_SucFilePath = os.environ["T_WORK"]
                m_SucFileName = m_ShortWorkFileName + '.suc'
            else:
                m_DifFilePath = os.getcwd()
                m_DifFileName = m_ShortWorkFileName + '.dif'
                m_SucFilePath = os.getcwd()
                m_SucFileName = m_ShortWorkFileName + '.suc'
            m_DifFullFileName = os.path.join(m_DifFilePath, m_DifFileName)
            m_SucFullFileName = os.path.join(m_SucFilePath, m_SucFileName)
            m_szWorkFile = p_szWorkFile
        else:
            if "T_WORK" not in os.environ:
                if self.__BreakWithDifference:
                    raise RuntimeError('===============   work log [' + p_szWorkFile + '] does not exist ============')

            # 传递的不是绝对路径，是相对路径
            (m_ShortWorkFileName, m_WorkFileExtension) = os.path.splitext(p_szWorkFile)
            # 如果定义了T_WORK，则dif文件生成在T_WORK下, 否则生成在当前目录下
            m_DifFilePath = os.environ["T_WORK"]
            m_DifFileName = m_ShortWorkFileName + '.dif'
            m_SucFilePath = os.environ["T_WORK"]
            m_SucFileName = m_ShortWorkFileName + '.suc'
            m_DifFullFileName = os.path.join(m_DifFilePath, m_DifFileName)
            m_SucFullFileName = os.path.join(m_SucFilePath, m_SucFileName)
            m_szWorkFile = os.path.join(os.environ['T_WORK'], p_szWorkFile)

        # remove old file first
        if os.path.exists(m_DifFullFileName):
            os.remove(m_DifFullFileName)
        if os.path.exists(m_SucFullFileName):
            os.remove(m_SucFullFileName)

        # check if work file exist
        if not os.path.isfile(m_szWorkFile):
            self.__CompareFailedCount = self.__CompareFailedCount + 1
            if self.__BreakWithDifference:
                raise RuntimeError('===============   work log [' + p_szWorkFile + '] does not exist ============')
            else:
                m_CompareResultFile = open(m_DifFullFileName, 'w')
                m_CompareResultFile.write(
                    '===============   work log [' + p_szWorkFile + '] does not exist ============')
                m_CompareResultFile.close()
                return False

        # search reference log 
        m_ReferenceLog = None
        for m_Reference_LogDir in self.__Reference_LogDirLists:
            m_TempReferenceLog = os.path.join(m_Reference_LogDir, p_szReferenceFile)
            if os.path.isfile(m_TempReferenceLog):
                m_ReferenceLog = m_TempReferenceLog
                break
        if m_ReferenceLog is None:
            m_ReferenceLog = p_szReferenceFile
        if not os.path.isfile(m_ReferenceLog):
            self.__CompareFailedCount = self.__CompareFailedCount + 1
            if self.__BreakWithDifference:
                raise RuntimeError('===============   reference log [' + m_ReferenceLog +
                                   '] does not exist ============')
            else:
                logger.info('===============   reference log [' + m_ReferenceLog +
                            '] does not exist ============')
                m_CompareResultFile = open(m_DifFullFileName, 'w')
                m_CompareResultFile.write('===============   reference log [' + m_ReferenceLog +
                                          '] does not exist ============')
                m_CompareResultFile.close()
                return False

        # compare file
        m_Comparer = POSIXCompare()
        try:
            m_CompareResult = m_Comparer.compare_text_files(m_szWorkFile, m_ReferenceLog,
                                                            self.__SkipLines, self.__IgnoreEmptyLine,
                                                            self.__CompareWithMask)
        except DiffException as de:
            raise RuntimeError('Diff exception::' + de.message)

        if m_CompareResult[0]:
            m_CompareResultFile = open(m_SucFullFileName, 'w')
            m_CompareResultFile.close()
            return True

        if not m_CompareResult[0]:
            self.__CompareFailedCount = self.__CompareFailedCount + 1
            logger.write("======= Diff file [" + m_DifFullFileName + "] >>>>> ")
            m_CompareResultFile = open(m_DifFullFileName, 'w', encoding="utf-8")
            for line in m_CompareResult[1]:
                m_CompareResultFile.write(line)
                if self.__EnableConsoleOutPut:
                    logger.write("    " + line)
            m_CompareResultFile.close()
            logger.write("======= Diff file [" + m_DifFullFileName + "] <<<<<< ")
            if self.__BreakWithDifference:
                raise RuntimeError('Got Difference. Please check [' + m_DifFullFileName + '] for more information.')
            else:
                return False


if __name__ == '__main__':
    pass
