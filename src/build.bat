:: ---------------------------------------------------------------------------
:: Datei:  build.bat - Windows MS-DOS Batch file
:: Author: Jens Kallup - paule32
::
:: Rechte: (c) 2024 by kallup non-profit software
::         all rights reserved
::
:: only for education, and for non-profit usage !!!
:: commercial use ist not allowed.
:: ---------------------------------------------------------------------------
@echo off
set APP=chmfilter

:: ---------------------------------------------------------------------------
:: the USERPROFILE directory contains the standard default installation of
:: Python 3.1.0 - there should be a Tools directory which comes with the
:: official installation files.
:: ---------------------------------------------------------------------------
set PY=%USERPROFILE%\AppData\Local\Programs\Python\Python310
set PO=%PY%\Tools\i18n\msgfmt.py
set EX=python -X nofaulthandler

set BASEDIR=%cd%
echo create directories...  [

:: ---------------------------------------------------------------------------
:: for default, the neccassary localization directories, and file are already
:: exists. But I add a "mkdir" command, and return value check for future use
:: new languages can be add into the for range block.
:: ---------------------------------------------------------------------------
:: en => English
:: de => German
:: ---------------------------------------------------------------------------
for %%A in (en, de) do (
    dir /A:D %BASEDIR%\locales  >nul 2>&1
    if errorlevel 0 (
        mkdir %BASEDIR%\locales >nul 2>&1
        dir /A:D %BASEDIR%\locales\%%A  >nul 2>&1
        if errorlevel 0 (
            echo|set /p="%%A => "
            mkdir %BASEDIR%\locales\%%A >nul 2>&1
            dir /A:D locales\%%A\LC_MESSAGES >nul 2>&1
            if errorlevel 0 (
                echo|set /p="ok, "
                mkdir locales\%%A\LC_MESSAGES >nul 2>&1
                cd %BASEDIR%\locales\%%A\LC_MESSAGES
                echo|set /p="locales compiled => "
                %EX% "%PO%" -o %APP%.mo %APP%.po
                if errorlevel 0 (
                    echo [ ok   ]
                )   else (
                    echo [ fail ],
                )
            )
        )
    )
)
:: ---------------------------------------------------------------------------
:: Python can produce byte-code, and executable files to speed up the loading
:: and for information hidding ...
:: ---------------------------------------------------------------------------
cd %BASEDIR%
echo|set /p="create Byte-Code...           ["
python -m compileall %BASEDIR%\filter.py >nul 2>&1
if errorlevel 1 ( goto error_bytecode )
echo  ok   ]

:: ---------------------------------------------------------------------------
:: to create Windows executables, you have to install pyinstaller seperatly.
:: after pyinstaller success the executable resides in ./dist folder.
:: ---------------------------------------------------------------------------
echo|set /p="create ExEcutable...          ["
pyinstaller %BASEDIR%\filter.spec >nul 2>&1
if errorlevel 1 (
    echo  fail ]
    goto error_executable
)   else (
    echo  ok   ]
    goto skc
    echo|set /p="create Certificate...       ["
    :: -----------------------------------------------------------------------
    :: finally, try to sign the executable with a certificate, that we will
    :: create with powershell, and the MS-SDK signtool.
    :: this reqauire, that you have powershell access on modern Windows.
    :: -----------------------------------------------------------------------
    powershell.exe -executionpolicy remotesigned -File %BASEDIR%\gencert.cmd
    if errorlevel 1 (
        echo  ok   ]
    )   else (
        echo  fail ]
    )
)
:skc

:: ---------------------------------------------------------------------------
:: no errors was detected - normal exit.
:: ---------------------------------------------------------------------------
:TheEnd
echo,
echo exit without error's, done.
goto skipper

:: ---------------------------------------------------------------------------
:: all other cases that produce errors - inform the user with nice messages:
:: ---------------------------------------------------------------------------
:error_bytecode
echo.
echo Error: can't create Byte-Code
goto error

:error_executable
echo.
echo Error: could not create executable.
goto error

:error_lc_messages
echo.
echo Error occured: LC_MESSAGES
goto error

:error
echo.
echo "process, fail"
goto skipper

:skipper

:: ---------------------------------------------------------------------------
:: E - O - F   End of File
:: ---------------------------------------------------------------------------
