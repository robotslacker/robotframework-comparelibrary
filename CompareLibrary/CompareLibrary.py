#-*- coding: UTF-8 -*-
import sys
import os
import argparse
import re
import string

class DiffException(Exception):
    def __init__(self,message):
        Exception.__init__(self)
        self.message=message

class POSIXCompare:
    CompareOptions = argparse.Namespace()
    CompareResult = True

    def __init__(self): 
        self.CompareOptions.isMaskEnabled = False

    def lcslen(self, x, y):
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
                if self.CompareString(xi,yj):
                    c[i][j] = 1 + c[i-1][j-1]
                else:
                    c[i][j] = max(c[i][j-1], c[i-1][j])
        return c

    def backtrack(self, c, x, y, i, j):
        """Backtrack the LCS length matrix to get the actual LCS"""
        if i == -1 or j == -1:
            return ""
        elif self.CompareString(x[i],y[j]):
            return backtrack(c, x, y, i-1, j-1) + x[i]
        elif c[i][j-1] >= c[i-1][j]:
            return backtrack(c, x, y, i, j-1)
        elif c[i][j-1] < c[i-1][j]:
            return backtrack(c, x, y, i-1, j)

    def lcs(self, x, y):
        """Get the longest common subsequence of x and y"""
        c = lcslen(x, y)
        return backtrack(c, x, y, len(x)-1, len(y)-1)

    def CompareString(self, p_Str1, p_Str2):
        if self.CompareOptions.isMaskEnabled == False:
            return p_Str1 == p_Str2
        if self.CompareOptions.isMaskEnabled == True:
            return (re.match(p_Str2,p_Str1) != None)

    def Compare(self,c, x, y, i, j,p_ResultList):
        """Print the diff using LCS length matrix by backtracking it"""
        
        if i < 0 and j < 0:
            return p_ResultList
        elif i < 0:
            self.Compare(c, x, y, i, j-1,p_ResultList)
            self.CompareResult = False
            p_ResultList.append("+ " + y[j])
        elif j < 0:
            self.Compare(c, x, y, i-1, j,p_ResultList)
            self.CompareResult = False
            p_ResultList.append("- " + x[i])
        elif self.CompareString(x[i],y[j]):
            self.Compare(c, x, y, i-1, j-1,p_ResultList)
            p_ResultList.append("  " + x[i])
        elif c[i][j-1] >= c[i-1][j]:
            self.Compare(c, x, y, i, j-1,p_ResultList)
            self.CompareResult = False
            p_ResultList.append("+ " + y[j])
        elif c[i][j-1] < c[i-1][j]:
            self.Compare(c, x, y, i-1, j,p_ResultList)
            self.CompareResult = False
            p_ResultList.append("- " + x[i])
        return self.CompareResult,p_ResultList

    def set_compare_options(self, options):
        self.CompareOptions = options
    
    def compare_text_files(self, file1, file2):
        if not os.path.isfile(file1):
            raise DiffException('ERROR: %s is not a file' % (file1))
        if not os.path.isfile(file2):
            raise DiffException('ERROR: %s is not a file' % (file2))

        file1content = open(file1, mode='r').readlines()
        file2content = open(file2, mode='r').readlines()

        m_lcs = self.lcslen(file1content,file2content)
        m_ResultList = []
        return self.Compare(m_lcs, file1content, file2content, \
                        len(file1content)-1, len(file2content)-1, m_ResultList)

class CompareLibrary:
    
    """
    *** Settings ***
    Library   CompareLibrary

    *** Testcases ***
    Set REFLOG DIR
        Set Reference LogDir  Dir1;Dir2;
    Diff test log and reference log
        Compare Files  test.log  testref.log [MASK] [IGNABL] [IGNABS]
    """
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_DOC_FORMAT = 'HTML'
    __version__ = '0.1'

    Reference_LogDirLists = []

    def keyword():
        pass

    def __init__(self):
        pass

    def Set_ReferenceLogDir(self,p_szPath):
        self.Reference_LogDirLists = p_szPath.split(':')

    def Compare_Files(self,p_szWorkFile,p_szReferenceFile,*rest):
        CompareOptions  = argparse.Namespace()
        if 'MASK' in rest:  
            CompareOptions.isMaskEnabled = True
        else:
            CompareOptions.isMaskEnabled = False

        (m_WorkFilePath,m_TempFileName) = os.path.split(p_szWorkFile);
        (m_ShortWorkFileName,m_WorkFileExtension) = os.path.splitext(m_TempFileName);
        m_DifFilePath = m_WorkFilePath
        m_DifFileName = m_ShortWorkFileName + '.dif'
        m_DifFullFileName = os.path.join(m_DifFilePath,m_DifFileName)
        m_SucFilePath = m_WorkFilePath
        m_SucFileName = m_ShortWorkFileName + '.suc'
        m_SucFullFileName = os.path.join(m_SucFilePath,m_SucFileName)

        # remove old file first
        if os.path.exists(m_DifFullFileName):
            os.remove(m_DifFullFileName)
        if os.path.exists(m_SucFullFileName):
            os.remove(m_SucFullFileName)

        # check if work file exist
        if not os.path.isfile(p_szWorkFile):
            m_CompareResultFile = open(m_DifFullFileName,'w')
            m_CompareResultFile.write('===============   work log [' + p_szWorkFile + '] does not exist ============')
            m_CompareResultFile.close()
            return

        # search reference log 
        m_ReferenceLog = None
        for m_Reference_LogDir in self.Reference_LogDirLists:
            m_TempReferenceLog = os.path.join(m_Reference_LogDir, p_szReferenceFile)
            if os.path.isfile(m_TempReferenceLog):
                m_ReferenceLog = m_TempReferenceLog
                break
        if m_ReferenceLog == None:
            m_ReferenceLog = p_szReferenceFile
        if not os.path.isfile(m_ReferenceLog):
            m_CompareResultFile = open(m_DifFullFileName,'w')
            m_CompareResultFile.write('===============   reference log [' + m_ReferenceLog + '] does not exist ============')
            m_CompareResultFile.close()
            return

        # compare file
        m_Comparer = POSIXCompare()
        m_Comparer.set_compare_options(CompareOptions)
        m_CompareResult = m_Comparer.compare_text_files(p_szWorkFile,m_ReferenceLog)

        if (m_CompareResult[0] == True):
            m_CompareResultFile = open(m_SucFullFileName,'w')
            m_CompareResultFile.close()

        if (m_CompareResult[0] == False):
            m_CompareResultFile = open(m_DifFullFileName,'w')
            for line in m_CompareResult[1]:
                m_CompareResultFile.write(line)
            m_CompareResultFile.close()

        return

def main():
    print("Start CompareLibrary Test ...")    

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'arg',
        help='Names of files or directories to compare.',
        nargs=2)
    parser.add_argument(
        '--mask',
        help='The reference log has regex synatx',
        default=False,
        dest="isMaskEnabled",
        action='store_true')
    options = parser.parse_args()

    file1 = options.arg[0]
    file2 = options.arg[1]

    myCompareLibrary = CompareLibrary()
    myCompareLibrary.Set_ReferenceLogDir('/tmp/:/scratch')
    myCompareLibrary.Compare_Files(file1,file2,'MASK' if options.isMaskEnabled else '')

    print("End CompareLibrary Test.")    

if __name__ == '__main__':
    main()
