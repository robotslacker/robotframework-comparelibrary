# robotframework-comparelibrary

Compareibrary is a [Robot Framework](https://robotframework.org/) test library that will provide keyword functionality to compare two files together

## Install

Install robotframework-comparelibrary

    pip install -U robotframework-comparelibrary

## Usage

|  |  |  |  |  |  
| :------------------------ | :--------------------------- | :---------------------- | :-------------- | :-------------- |  
| Settings                  |                              |                         |                 |                 |  
| Library                   | CompareLibrary               |                         |                 |                 |  
| Test Cases                |                              |                         |                 |                 |  
| Set ReferenceLogDir       | Set reference log directory  |   LOG_DIR1:LOG_DIR2:... |                 |                 |  
| Compare Files             | Compare Files                |   test.log              |  reference log  |     MASK        |  
|  |  |  |  |  |  

## Set ReferenceLogDir

    # Test will search reference log from current work directory
    default None
    
    # Test will search reference log from /u1/log and /u2/log
    Set ReferenceLogDir  /u1/log:/u2/log

## Compare Files

    test compares the two files for consistency.   
    If they are exactly the same, a .suc file is generated. 
    If they are not completely the same, a .dif file is generated. Differences in files are recorded in the .dif file.  

    if option MASK is used: test will compare files based on regular expressions, that is, the content in the reference log may be a regular expression.  
    
    For Example :  
    Test Log    Reference Log   option   Result
      Hello        He.*o         MASK     True  
      Hello        He.*o         None     False  
