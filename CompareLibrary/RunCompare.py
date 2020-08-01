# -*- coding: UTF-8 -*-
import os
import re
from robot.api import logger
from robot.errors import ExecutionFailed
import shlex


class DiffException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


class POSIXCompare:
    CompiledRegexPattern = {}

    def __init__(self):
        pass

    # 正则表达比较两个字符串
    # p_str1                  原字符串
    # p_str2                  正则表达式
    # p_compare_maskEnabled   是否按照正则表达式来判断是否相等
    # p_compare_ignorecase    是否忽略匹配中的大小写
    def compare_string(self, p_str1, p_str2,
                       p_compare_maskEnabled=False,
                       p_compare_ignorecase=False):
        # 如果两个字符串完全相等，直接返回
        if p_str1 == p_str2:
            return True

        # 如果忽略大小写的情况下，两个字符串的大写相同，则直接返回
        if p_compare_ignorecase:
            if p_str1.upper() == p_str2.upper():
                return True

        # 如果没有启用正则，则直接返回不相等
        if not p_compare_maskEnabled:
            return False

        # 用正则判断表达式是否相等
        try:
            if p_str2 in self.CompiledRegexPattern:
                m_CompiledPattern = self.CompiledRegexPattern[p_str2]
            else:
                m_CompiledPattern = re.compile(p_str2)
                self.CompiledRegexPattern[p_str2] = m_CompiledPattern
            if p_compare_ignorecase:
                matchObj = re.match(m_CompiledPattern, p_str1, re.IGNORECASE)
            else:
                matchObj = re.match(m_CompiledPattern, p_str1)
            if matchObj is None:
                return False
            elif str(matchObj.group()) != p_str1:
                return False
            else:
                return True
        except re.error:
            # 正则表达式错误，可能是由于这并非是一个正则表达式
            return False

    def compare(self,
                x,
                y,
                linenox,
                linenoy,
                p_compare_maskEnabled=False,
                p_compare_ignorecase=False):
        # LCS问题就是求两个字符串最长公共子串的问题。
        # 解法就是用一个矩阵来记录两个字符串中所有位置的两个字符之间的匹配情况，若是匹配则为1，否则为0。
        # 然后求出对角线最长的1序列，其对应的位置就是最长匹配子串的位置。

        # c           LCS数组
        # x           源数据
        # y           目的数据
        # linenox     源数据行数信息
        # linenoy     目的数据行数信息
        # i           源数据长度
        # j           目的数据长度
        # p_result    比对结果
        next_x = x
        next_y = y
        next_i = len(x) - 1
        next_j = len(y) - 1

        # This is our matrix comprised of list of lists.
        # We allocate extra row and column with zeroes for the base case of empty
        # sequence. Extra row and column is appended to the end and exploit
        # Python's ability of negative indices: x[-1] is the last elem.
        # 构建LCS数组
        c = [[0 for _ in range(len(y) + 1)] for _ in range(len(x) + 1)]
        for i, xi in enumerate(x):
            for j, yj in enumerate(y):
                if self.compare_string(xi, yj,
                                       p_compare_maskEnabled, p_compare_ignorecase):
                    c[i][j] = 1 + c[i - 1][j - 1]
                else:
                    c[i][j] = max(c[i][j - 1], c[i - 1][j])

        # 开始比较
        compare_result = True
        m_CompareDiffResult = []
        while True:
            if next_i < 0 and next_j < 0:
                break
            elif next_i < 0:
                compare_result = False
                m_CompareDiffResult.append("+{:>{}} ".format(linenoy[next_j], 6) + next_y[next_j])
                next_x = next_x
                next_y = next_y
                next_i = next_i
                next_j = next_j - 1
            elif next_j < 0:
                compare_result = False
                m_CompareDiffResult.append("-{:>{}} ".format(linenox[next_i], 6) + next_x[next_i])
                next_x = next_x
                next_y = next_y
                next_i = next_i - 1
                next_j = next_j
            elif self.compare_string(next_x[next_i], next_y[next_j],
                                     p_compare_maskEnabled, p_compare_ignorecase):
                m_CompareDiffResult.append(" {:>{}} ".format(linenox[next_i], 6) + next_x[next_i])
                next_x = next_x
                next_y = next_y
                next_i = next_i - 1
                next_j = next_j - 1
            elif c[next_i][next_j - 1] >= c[next_i - 1][next_j]:
                compare_result = False
                m_CompareDiffResult.append("+{:>{}} ".format(linenoy[next_j], 6) + next_y[next_j])
                next_x = next_x
                next_y = next_y
                next_i = next_i
                next_j = next_j - 1
            elif c[next_i][next_j - 1] < c[next_i - 1][next_j]:
                compare_result = False
                m_CompareDiffResult.append("-{:>{}} ".format(linenox[next_i], 6) + next_x[next_i])
                next_x = next_x
                next_y = next_y
                next_i = next_i - 1
                next_j = next_j
        return compare_result, m_CompareDiffResult

    def compare_text_files(self, file1, file2,
                           skiplines=None,
                           ignoreEmptyLine=False,
                           CompareWithMask=None,
                           CompareIgnoreCase=False,
                           CompareIgnoreTailOrHeadBlank=False):
        if not os.path.isfile(file1):
            raise DiffException('ERROR: %s is not a file' % file1)
        if not os.path.isfile(file2):
            raise DiffException('ERROR: %s is not a file' % file2)

        # 将比较文件加载到数组
        file1rawcontent = open(file1, mode='r', encoding='utf-8').readlines()

        file1content = open(file1, mode='r', encoding='utf-8').readlines()
        file2content = open(file2, mode='r', encoding='utf-8').readlines()

        lineno1 = []
        lineno2 = []
        for m_nPos in range(0, len(file1content)):
            lineno1.append(m_nPos + 1)
        for m_nPos in range(0, len(file2content)):
            lineno2.append(m_nPos + 1)

        # 去掉filecontent中的回车换行
        for m_nPos in range(0, len(file1content)):
            if file1content[m_nPos].endswith('\n'):
                file1content[m_nPos] = file1content[m_nPos][:-1]
        for m_nPos in range(0, len(file2content)):
            if file2content[m_nPos].endswith('\n'):
                file2content[m_nPos] = file2content[m_nPos][:-1]

        # 去掉fileconent中的首尾空格
        if CompareIgnoreTailOrHeadBlank:
            for m_nPos in range(0, len(file1content)):
                file1content[m_nPos] = file1content[m_nPos].lstrip().rstrip()
            for m_nPos in range(0, len(file2content)):
                file2content[m_nPos] = file2content[m_nPos].lstrip().rstrip()

        # 去除在SkipLine里头的所有内容
        if skiplines is not None:
            m_nPos = 0
            while m_nPos < len(file1content):
                bMatch = False
                for pattern in skiplines:
                    if self.compare_string(file1content[m_nPos], pattern, p_compare_maskEnabled=True):
                        file1content.pop(m_nPos)
                        lineno1.pop(m_nPos)
                        bMatch = True
                        break
                if not bMatch:
                    m_nPos = m_nPos + 1

            m_nPos = 0
            while m_nPos < len(file2content):
                bMatch = False
                for pattern in skiplines:
                    if self.compare_string(file2content[m_nPos], pattern, p_compare_maskEnabled=True):
                        file2content.pop(m_nPos)
                        lineno2.pop(m_nPos)
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
                    lineno1.pop(m_nPos)
                else:
                    m_nPos = m_nPos + 1
            m_nPos = 0
            while m_nPos < len(file2content):
                if len(file2content[m_nPos].strip()) == 0:
                    file2content.pop(m_nPos)
                    lineno2.pop(m_nPos)
                else:
                    m_nPos = m_nPos + 1

        # 输出两个信息
        # 1：  Compare的结果是否存在dif，True/False
        # 2:   Compare的Dif列表，注意：这里是一个翻转的列表
        (m_CompareResult, m_CompareResultList) = self.compare(file1content, file2content, lineno1, lineno2,
                                                              p_compare_maskEnabled=CompareWithMask,
                                                              p_compare_ignorecase=CompareIgnoreCase)
        # 首先翻转数组
        # 随后从数组中补充进入被Skip掉的内容
        m_nLastPos = 0
        m_NewCompareResultList = []
        for row in m_CompareResultList[::-1]:
            if row.startswith('+'):
                # 当前日志没有，Log中有的，忽略不计
                m_NewCompareResultList.append(row)
                continue
            elif row.startswith('-'):
                # 记录当前行号
                m_LineNo = int(row[1:7])
            elif row.startswith(' '):
                # 记录当前行号
                m_LineNo = int(row[0:7])
            else:
                raise ExecutionFailed("Missed line number. Bad compare result. [" + row + "]", continue_on_failure=True)
            if m_LineNo > (m_nLastPos + 1):
                for m_nPos in range(m_nLastPos + 1, m_LineNo):
                    m_NewCompareResultList.append("S{:>{}} ".format(m_nPos, 6) + file1rawcontent[m_nPos - 1])
                m_NewCompareResultList.append(row)
                m_nLastPos = m_LineNo
            else:
                m_NewCompareResultList.append(row)
                m_nLastPos = m_LineNo
        return m_CompareResult, m_NewCompareResultList


class RunCompare(object):
    # TEST SUITE 在suite中引用，只会实例化一次
    # 也就是说多test case都引用了这个类的方法，但是只有第一个test case调用的时候实例化
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    __Reference_LogDirLists = None
    __SkipLines = []
    __BreakWithDifference = False             # 是否在遇到比对错误的时候抛出运行例外
    __EnableConsoleOutPut = False             # 是否关闭在Console上的显示，默认是不关闭
    __IgnoreEmptyLine = False                 # 是否在比对的时候忽略空白行
    __CompareWithMask = False                 # 是否在比对的时候利用正则表达式
    __CompareIgnoreCase = False               # 是否再比对的时候忽略大小写
    __CompareIgnoreTailOrHeadBlank = False    # 是否忽略对比的前后空格

    def __init__(self):
        pass

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
        if str(p_BreakWithDifference).upper() == 'FALSE':
            self.__BreakWithDifference = False

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
        if str(p_szCompareWithMask).upper() == 'FALSE':
            self.__CompareWithMask = False

    def Compare_IgnoreCase(self, p_szIgnoreCase):
        """ 设置是否在比对的时候忽略大小写  """
        """
         输入参数：
              p_szIgnoreCase:        在比对的时候是否忽略大小写，默认是不忽略
         返回值：
             无

         """
        if str(p_szIgnoreCase).upper() == 'TRUE':
            self.__CompareIgnoreCase = True
        if str(p_szIgnoreCase).upper() == 'FALSE':
            self.__CompareIgnoreCase = False

    def Compare_IgnoreTailOrHeadBlank(self, p_szIgnoreTailOrHeadBlank):
        """ 设置是否在比对的时候忽略行首和行末的空格  """
        """
         输入参数：
              p_szIgnoreTailOrHeadBlank:        在比对的时候是否忽略行首和行末的空格，默认是不忽略
         返回值：
             无

         """
        if str(p_szIgnoreTailOrHeadBlank).upper() == 'TRUE':
            self.__CompareIgnoreTailOrHeadBlank = True
        if str(p_szIgnoreTailOrHeadBlank).upper() == 'FALSE':
            self.__CompareIgnoreTailOrHeadBlank = False

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
                logger.info('===============   work log [' + p_szWorkFile + '] does not exist. ' +
                            ' T_WORK env does not exist too ============')
                if self.__BreakWithDifference:
                    raise ExecutionFailed(
                        message=('===============   work log [' + p_szWorkFile + '] does not exist. ' +
                                 ' T_WORK env does not exist too ============'),
                        continue_on_failure=True
                    )
                return False

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
            m_CompareResultFile = open(m_DifFullFileName, 'w')
            m_CompareResultFile.write(
                '===============   work log [' + p_szWorkFile + '] does not exist ============')
            m_CompareResultFile.close()
            if self.__BreakWithDifference:
                raise ExecutionFailed(
                    message=('===============   work log [' + p_szWorkFile + '] does not exist ============'),
                    continue_on_failure=True
                )
            return False

        # search reference log
        m_ReferenceLog = None
        if self.__Reference_LogDirLists is not None:
            for m_Reference_LogDir in self.__Reference_LogDirLists:
                m_TempReferenceLog = os.path.join(m_Reference_LogDir, p_szReferenceFile)
                if os.path.isfile(m_TempReferenceLog):
                    m_ReferenceLog = m_TempReferenceLog
                    break
        if m_ReferenceLog is None:
            m_ReferenceLog = p_szReferenceFile
        if not os.path.isfile(m_ReferenceLog):
            logger.info('===============   reference log [' + m_ReferenceLog +
                        '] does not exist ============')
            m_CompareResultFile = open(m_DifFullFileName, 'w')
            m_CompareResultFile.write('===============   reference log [' + m_ReferenceLog +
                                      '] does not exist ============')
            m_CompareResultFile.close()
            if self.__BreakWithDifference:
                raise ExecutionFailed(
                    message=('===============   reference log [' + m_ReferenceLog + '] does not exist ============'),
                    continue_on_failure=True
                )
            return False

        # compare file
        m_Comparer = POSIXCompare()
        try:
            # 这里的CompareResultList是一个被翻转了的列表，在输出的时候，需要翻转回来
            (m_CompareResult, m_CompareResultList) = m_Comparer.compare_text_files(
                m_szWorkFile, m_ReferenceLog,
                self.__SkipLines,
                self.__IgnoreEmptyLine,
                self.__CompareWithMask,
                self.__CompareIgnoreCase,
                self.__CompareIgnoreTailOrHeadBlank)
        except DiffException as de:
            logger.info('Fatal Diff Exception:: ' + de.message)
            if self.__BreakWithDifference:
                raise ExecutionFailed(
                    message=('Fatal Diff Exception:: ' + de.message),
                    continue_on_failure=True
                )
            return False

        if m_CompareResult:
            m_CompareResultFile = open(m_SucFullFileName, 'w')
            m_CompareResultFile.close()
            logger.write("======= Succ file       [" + m_SucFullFileName + "] >>>>> ")
            logger.write("  ===== Work file       [" + os.path.abspath(m_szWorkFile) + "]")
            logger.write("  ===== Ref  file       [" + os.path.abspath(m_ReferenceLog) + "]")
            logger.write("  ===== Mask flag       [" + str(self.__CompareWithMask) + "]")
            logger.write("  ===== BlankSpace flag [" + str(self.__CompareIgnoreTailOrHeadBlank) + "]")
            logger.write("  ===== Case flag       [" + str(self.__CompareIgnoreCase) + "]")
            logger.write("  ===== Empty line flag [" + str(self.__IgnoreEmptyLine) + "]")
            for row in self.__SkipLines:
                logger.write("  ===== Skip line       [" + str(row) + "]")
            return True
        else:
            logger.write("======= Diff file       [" + m_DifFullFileName + "] >>>>> ")
            logger.write("  ===== Work file       [" + os.path.abspath(m_szWorkFile) + "]")
            logger.write("  ===== Ref  file       [" + os.path.abspath(m_ReferenceLog) + "]")
            logger.write("  ===== Mask flag       [" + str(self.__CompareWithMask) + "]")
            logger.write("  ===== BlankSpace flag [" + str(self.__CompareIgnoreTailOrHeadBlank) + "]")
            logger.write("  ===== Case flag       [" + str(self.__CompareIgnoreCase) + "]")
            logger.write("  ===== Empty line flag [" + str(self.__IgnoreEmptyLine) + "]")
            for row in self.__SkipLines:
                logger.write("  ===== Skip line       [" + str(row) + "]")

            m_CompareResultFile = open(m_DifFullFileName, 'w', encoding="utf-8")
            for line in m_CompareResultList:
                print(line, file=m_CompareResultFile)
                if self.__EnableConsoleOutPut:
                    if line.startswith('-'):
                        logger.write('<font style="color:Black;background-color:#E0E0E0">' + line[0:7] + '</font>' +
                                     '<font style="color:white;background-color:Red">' + line[7:] + '</font>',
                                     html=True)
                    elif line.startswith('+'):
                        logger.write('<font style="color:Black;background-color:#E0E0E0">' + line[0:7] + '</font>' +
                                     '<font style="color:white;background-color:Green">' + line[7:] + '</font>',
                                     html=True)
                    elif line.startswith('S'):
                        logger.write('<font style="color:Black;background-color:#E0E0E0">' + line + '</font>',
                                     html=True)
                    else:
                        logger.write('<font style="color:Black;background-color:#E0E0E0">' + line[0:7] + '</font>' +
                                     '<font style="color:Black;background-color:white">' + line[7:] + '</font>',
                                     html=True)
            m_CompareResultFile.close()
            logger.write("======= Diff file [" + m_DifFullFileName + "] <<<<< ")
            if self.__BreakWithDifference:
                raise ExecutionFailed(
                    message=('Got Difference. Please check [' + m_DifFullFileName + '] for more information.'),
                    continue_on_failure=self.__BreakWithDifference
                )
            return False


if __name__ == '__main__':
    pass
    myCompare = RunCompare()
    # myCompare.Compare_IgnoreCase("TRUE")
    myCompare.Compare_Files("C:\\Work\\linkoop\\robotframework-comparelibrary\\localtest\\join_number.log",
                            "C:\\Work\\linkoop\\robotframework-comparelibrary\\localtest\\join_number.ref",
                            )
