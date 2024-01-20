# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Datei:  filter.py
# Author: Jens Kallup - paule32
#
# Rechte: (c) 2024 by kallup non-profit software
#         all rights reserved
#
# only for education, and for non-profit usage !!!
# commercial use ist not allowed.
#
# To give doxygen a little bit "faked" intelligence, I have created this
# script, which I use for post-processing. It will start the doxygen app as a
# sub process, and after all is done, the script is used, to delete not needed
# stuff like:
# - html comments
# - whitespaces (\n\r\t)
# - !doctype
# - xmlns
# - html header stuff like meta data's
# - content header navigation html elements.
#
# The performed action's that are used in this script helps, to shrink down
# the CHM project file size - because the data information's described above
# will be delete in all found html files, in all found directories in the
# given OUTPUT_DIRECTORY folder.
#
# When action is gone, the resulting content will be write back to the
# original file name.
#
# To run this script, you have to add some environment variables to your
# current system process domain:
#
# DOXYGEN_PATH = <path\to\doxygen.exe>
# DOXYHHC_PATH = <path\to\hhc.exe>
#
# ATTENTION:
# -----------
# This is not an offical script for the offical doxygen reprosity !
# It is created mainly for using to my personal usage.
# So, I give no warantees for anything.
#
# I have insert some TODO marks, which means that modifications must be done
# before working well.
#
# !!! YOU USE IT AT YOUR OWN RISK !!!
# ----------------------------------------------------------------------------

global EXIT_SUCCESS; EXIT_SUCCESS = 0
global EXIT_FAILURE; EXIT_FAILURE = 1

global paule32_debug
global basedir
global tr

try:
    import os            # operating system stuff
    import sys           # system specifies
    import time          # thread count
    import re            # regular expression handling
    import glob          # directory search
    import subprocess    # start sub processes
    import platform      # Windows ?
    import keyboard
    import shutil        # shell utils
    import pkgutil       # attached binary data utils
    
    import gettext       # localization
    import locale        # internal system locale
    
    import configparser  # .ini files
    import traceback     # stack exception trace back
    
    # ------------------------------------------------------------------------
    # html parser modules
    # ------------------------------------------------------------------------
    from bs4             import BeautifulSoup, Doctype
    from bs4.element     import Comment
    
    # ------------------------------------------------------------------------
    # Qt5 gui framework
    # ------------------------------------------------------------------------
    from PyQt5.QtWidgets import *         # Qt5 widgets
    from PyQt5.QtGui     import *         # Qt5 gui
    from PyQt5.QtCore    import *         # Qt5 core
    
    from functools       import partial   # callback functions

    if getattr(sys, 'frozen', False):
        import pyi_splash
    
    basedir = os.path.dirname(__file__)

    # ------------------------------------------------------------------------
    # branding water marks ...
    # ------------------------------------------------------------------------
    __version__ = "Version 0.0.1"
    __authors__ = "paule32"

    __date__    = "2024-01-04"
    
    # ------------------------------------------------------------------------
    # when the user start the application script under Windows 7 and higher:
    # ------------------------------------------------------------------------
    try:
        from ctypes import windll  # Only exists on Windows.
        myappid = 'kallup-nonprofit.doxygen.chmfilter.1'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass
    
    # ------------------------------------------------------------------------
    # constants, and varibales that are used multiple times ...
    # ------------------------------------------------------------------------
    __copy__ = ""                               \
        + "doxygen 1.10.0 HTML Filter 0.0.1\n"  \
        + "(c) 2024 by paule32\n"               \
        + "all rights reserved.\n"
    
    __error__os__error = "" \
        + "can not determine operating system.\n" \
        + "start aborted."
    
    __error__locales_error = "" \
        + "no locales file for this application.\n" \
        + "use default: english"
    
    # ------------------------------------------------------------------------
    # global used locales constants ...
    # ------------------------------------------------------------------------
    __locale__    = "locales"
    __locale__enu = "en_us"
    __locale__deu = "de_de"
    
    # ------------------------------------------------------------------------
    # global used application stuff ...
    # ------------------------------------------------------------------------
    __app__name        = "chmfilter"
    __app__config_ini  = "chmfilter.ini"
    
    __app__framework   = "PyQt5.QtWidgets.QApplication"
    __app__exec_name   = sys.executable
    
    __app__error_level = "0"
    
    # ------------------------------------------------------------------------
    # paule developer settings to save time ,,,
    # ------------------------------------------------------------------------
    paule32_debug = True
    
    # ------------------------------------------------------------------------
    # worker thread for the progress bar ...
    # ------------------------------------------------------------------------
    class WorkerThread(QThread):
        progress_changed = pyqtSignal(int)
        def run(self):
            for i in range(101):
                time.sleep(0.1)
                self.progress_changed.emit(i)
    
    # ------------------------------------------------------------------------
    # get the locale, based on the system locale settings ...
    # ------------------------------------------------------------------------
    def handle_language(lang):
        try:
            system_lang, _ = locale.getdefaultlocale()
            if   system_lang.lower() == __locale__enu:
                 if lang.lower() == __locale__enu[:2]:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__enu[:2]])  # english
                 if lang.lower() == __locale__deu[:2]:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__deu[:2]])  # german
            elif system_lang.lower() == __locale__deu:
                 if lang.lower() == __locale__enu[:2]:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__enu[:2]])  # english
                 if lang.lower() == __locale__deu[:2]:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__deu[:2]])  # german
            else:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__enu[:2]])  # fallback - english
            
            tr.install()
            return tr
        except Exception as ex:
            return
            
    # ------------------------------------------------------------------------
    # get current time, and date measured on "now" ...
    # ------------------------------------------------------------------------
    def get_current_time():
        return datetime.datetime.now().strftime("%H_%M")
    def get_current_date():
        return datetime.datetime.now().strftime("%Y_%m_%d")
    
    # ------------------------------------------------------------------------
    # pythonw.exe is for gui application's
    # python .exe is for text application's
    # ------------------------------------------------------------------------
    def isPythonWindows():
        if "pythonw" in __app__exec_name:
            return True
        elif "python" in __app__exec_name:
            return False
    
    # ------------------------------------------------------------------------
    # check, if the gui application is initialized by an instance of app ...
    # ------------------------------------------------------------------------
    def isApplicationInit():
        app_instance = QApplication.instance()
        return app_instance is not None
    
    # ------------------------------------------------------------------------
    # methode to show information about this application script ...
    # ------------------------------------------------------------------------
    def showInfo(text):
        infoWindow = QMessageBox()
        infoWindow.setIcon(QMessageBox.Information)
        infoWindow.setWindowTitle("Information")
        infoWindow.setText(text)
        infoWindow.exec_()
    
    def showApplicationInformation(text):
        if isPythonWindows() == True:
            if isApplicationInit() == False:
                app = QApplication(sys.argv)
            showInfo(text)
        else:
            print(text)
    
    # ------------------------------------------------------------------------
    # methode to show error about this application script ...
    # ------------------------------------------------------------------------
    def showError(text):
        infoWindow = QMessageBox()
        infoWindow.setIcon(QMessageBox.Critical)
        infoWindow.setWindowTitle("Error")
        infoWindow.setText(text)
        infoWindow.show()
        infoWindow.exec_()
    
    def showApplicationError(text):
        if isPythonWindows() == True:
            if isApplicationInit() == False:
                app = QApplication(sys.argv)
            showError(text)
        else:
            print(text)
    
    # ------------------------------------------------------------------------
    # convert the os path seperator depend ond the os system ...
    # ------------------------------------------------------------------------
    def convertPath(text):
        if os_type == os_type_windows:
            result = text.replace("/", "\\")
        elif os_type == os_type_linux:
            result = text.replace("\\", "/")
        else:
            showApplicationError(__error__os__error)
            sys.exit(EXIT_FAILURE)
        return result
    
    # ---------------------------------------------------------
    # here, we try to open doxygen. The path to the executable
    # must be in the PATH variable of your system...
    # ---------------------------------------------------------
    def convertFiles(htm_file):
        # ---------------------------------------------------------
        # open the html files where to remove the not neccassary
        # data from "read" content.
        # ---------------------------------------------------------
        with open(htm_file, "r", encoding="utf-8") as input_file:
            soup = BeautifulSoup(input_file, "html.parser")
            divs = soup.find_all("div")
            
            # ---------------------------------------------------------
            # remove the header bar stuff from the html file ...
            # ---------------------------------------------------------
            counter = 1
            for div in divs:
                idname = "navrow" + str(counter)
                if div.get("id") == f"{idname}":
                    div.extract()
                    counter = counter + 1
            
            # ---------------------------------------------------------
            # renove meta data for IE - Internet Explorer, because the
            # IE is very old, and out of date.
            # ---------------------------------------------------------
            #meta = soup.find("meta", {"http-equiv": "X-UA-Compatible"})
            #if meta:
            #    meta.decompose()
            
            # ---------------------------------------------------------
            # NOTE: Pleas be fair, and make a comment of the following
            # three lines, if you would hold on CODEOFCONDUCT.
            # They are only for meassure usage...
            # THANK YOU !!!
            # ---------------------------------------------------------
            meta = soup.find("meta", {"name": "generator"})
            if meta:
                meta.decompose()
            
            meta = soup.find("a", {"href": "doxygen_crawl.html"})
            if meta:
                meta.decompose()
            
            # ---------------------------------------------------------
            # remove the "not" neccassary html comments from the input:
            # ---------------------------------------------------------
            rems = soup.find_all(string=lambda string: isinstance(string, Comment))
            for comment in rems:
                comment.extract()
            
            html_tag = soup.find("html")
            if html_tag and 'xmlns' in html_tag.attrs:
                del html_tag["xmlns"]
            
            # ---------------------------------------------------------
            # remove whitespaces ...
            # ---------------------------------------------------------
            try:
                modh = str(soup)
                modh = modh.split('\n', 1)[1]     # extract first line with
                modh = re.sub(r"\s+", " ", modh)  # <!DOCTYPE ...
            except Exception as ex:
                foo = 1
                #print(f"warning: " + f"{ex}")
            
            # ---------------------------------------------------------
            # close old file, to avoid cross over's. Then write the
            # modified content back to the original file...
            # ---------------------------------------------------------
            input_file.close()
            
            with open(htm_file, "w", encoding="utf-8") as output_file:            
                output_file.write(modh)
                output_file.close()
    
    # ------------------------------------------------------------------------
    # custom widget for QListWidgetItem element's ...
    # ------------------------------------------------------------------------
    class customQListWidgetItem(QListWidgetItem):
        def __init__(self, name, parent):
            super().__init__()
            
            font = QFont("Arial", 10)
            
            self.name = name
            self.parent = parent
            
            element = QListWidgetItem(name, parent)
            self.setSizeHint(element.sizeHint())
            self.setFont(font)
            self.setData(0, self.name)
    
    # ------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------
    class myLineEdit(QLineEdit):
        def __init__(self, name=""):
            super().__init__()
            self.name = name
            self.init_ui()
        
        def init_ui(self):
            self.setText(self.name)
            self.cssColor = "QLineEdit{background-color:white;}QLineEdit:hover{background-color:yellow;}"
            self.setStyleSheet(self.cssColor)
        
    # ------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------
    class myTextEdit(QTextEdit):
        def __init__(self, name=""):
            super().__init__()
            self.name = name
            self.cssColor = "QTextEdit{background-color:#bdbfbf;}QTextEdit:hover{background-color:yellow;}"
            self.setStyleSheet(self.cssColor)
            self.setText(self.name)
    
    class myCustomLabel(QLabel):
        def __init__(self, text, helpID, helpText):
            super().__init__(text)
            
            self.helpID   = helpID
            self.helpText = helpText
        
        def enterEvent(self, event):
            sv_help.setText(self.helpText)
    
    # ------------------------------------------------------------------------
    # create a scroll view for the mode tab on left side of application ...
    # ------------------------------------------------------------------------
    class myCustomScrollArea(QScrollArea):
        def __init__(self, name):
            super().__init__()
            
            self.name = name
            self.font = QFont("Arial")
            self.font.setPointSize(10)
            
            self.type_label        = 1
            self.type_edit         = 2
            self.type_spin         = 3
            self.type_combo_box    = 4
            self.type_check_box    = 5
            self.type_push_button  = 6
            self.type_radio_button = 7
            
            font_primary   = "Consolas"
            font_secondary = "Courier New"
            
            self.font_a = QFont("Consolas"); self.font_a.setPointSize(11)
            self.font_b = QFont("Arial");    self.font_a.setPointSize(10)
            
            self.font_a.setFamily(font_primary)
            font_id = QFontDatabase.addApplicationFont(self.font_a.family())
            if font_id != -1:
                self.font_a.setFamily(font_primary)
                self.font_a.setPointSize(11)
            else:
                self.font_a.setFamily(font_secondary)
                self.font_a.setPointSize(11)
            
            
            self.content_widget = QWidget(self)
            self.content_widget.setMinimumHeight(self.height()-150)
            self.content_widget.setMinimumWidth (self.width()-50)
            self.content_widget.setFont(self.font)
            
            self.layout = QVBoxLayout(self.content_widget)
            self.layout.setAlignment(Qt.AlignTop)
            self.label_1 = QLabel(self.name)
            
            self.layout.addWidget(self.label_1)
            self.content_widget.setLayout(self.layout)
            
            self.setWidgetResizable(False)
            self.setWidget(self.content_widget)
        
        def setName(self, name):
            self.name = name
            self.label_1.setText(self.name)
        
        def setElementBold(self, w):
            self.font.setBold(True); w.setFont(self.font)
            self.font.setBold(False)
            
        def addPushButton(self, text, l = None):
            w = QPushButton(text)
            w.setFont(self.font_a)
            w.font().setPointSize(14)
            w.font().setBold(True)
            w.setMinimumWidth(32)
            w.setMinimumHeight(32)
            if not l == None:
                l.addWidget(w)
            else:
                self.layout.addWidget(w)
            return w
        
        def addCheckBox(self, text, bold=False):
            w = QCheckBox(text)
            if bold == True:
                self.setElementBold(w)
            else:
                w.setFont(self.font)
            self.layout.addWidget(w)
            return w
        
        def addRadioButton(self, text):
            w = QRadioButton(text)
            w.setFont(self.font)
            self.layout.addWidget(w)
            return w
        
        def addFrame(self, lh = None):
            w = QFrame()
            w.setFrameShape (QFrame.HLine)
            w.setFrameShadow(QFrame.Sunken)
            if not lh == None:
                lh.addWidget(w)
            else:
                self.layout.addWidget(w)
            return w
        
        def addHelpLabel(self, text, helpID, helpText, lh=None):
            w = myCustomLabel( text, helpID, helpText)
            if not lh == None:
                w.setFont(self.font_a)
                lh.addWidget(w)
            else:
                self.layout.addWidget(w)
            return w
        
        def addLabel(self, text, bold=False, lh=None):
            w = QLabel(text)
            if bold == True:
                self.setElementBold(w)
            else:
                w.setFont(self.font)
            if not lh == None:
                w.setFont(self.font_a)
                lh.addWidget(w)
            else:
                self.layout.addWidget(w)
            return w
        
        def addLineEdit(self, text = "", lh = None):
            w = myLineEdit(text)
            w.setMinimumHeight(21)
            w.setFont(self.font_a)
            if not lh == None:
                lh.addWidget(w)
            else:
                self.layout.addWidget(w)
            return w
    
    # ------------------------------------------------------------------------
    # create a scroll view for the project tab on left side of application ...
    # ------------------------------------------------------------------------
    class customScrollView_1(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            
            self.__button_style_css = tr("__button_style_css")
            self.name = name
            
            self.init_ui()
        
        def init_ui(self):
            content_widget = QWidget(self)
            layout = QVBoxLayout(content_widget)
            layout.setAlignment(Qt.AlignLeft)
            
            font = QFont("Arial")
            font.setPointSize(10)
            
            w_layout_0 = QHBoxLayout()
            w_layout_0.setAlignment(Qt.AlignLeft)
            widget_1_label_1 = self.addLabel("Provide some informations about the Project you are documenting", True)
            widget_1_label_1.setMinimumWidth(250)
            widget_1_label_1.setMaximumWidth(500)
            w_layout_0.addWidget(widget_1_label_1)
            layout.addLayout(w_layout_0)
            
            items = [
                "Project name:",
                "Project author:",
                "Project version or id:"
            ]
            
            for i in range(0, len(items)):
                w_layout = QHBoxLayout()
                w_layout.setAlignment(Qt.AlignLeft)
                #
                w_label  = self.addLabel(items[i], False, w_layout)
                w_label.setMinimumWidth(160)
                w_label.setFont(font)
                #
                w_edit = self.addLineEdit("",w_layout)
                w_edit.setMinimumWidth(300)
                w_edit.setFont(font)
                #
                w_layout.addWidget(w_label)
                w_layout.addWidget(w_edit)
                layout.addLayout(w_layout)
            
            layout_4 = QHBoxLayout()
            layout_4.setAlignment(Qt.AlignLeft)
            widget_4_label_1 = self.addLabel("Project logo:", False, layout_4)
            widget_4_label_1.setFont(font)
            widget_4_label_1.setMaximumWidth(160)
            layout_4.addWidget(widget_4_label_1)
            #
            widget_4_pushb_1 = self.addPushButton("Select", layout_4)
            widget_4_pushb_1.setMinimumHeight(32)
            widget_4_pushb_1.setMinimumWidth(84)
            widget_4_pushb_1.setMaximumWidth(84)  ; font.setBold(True)
            widget_4_pushb_1.setFont(font)        ; font.setBold(False)
            #
            widget_4_licon_1 = self.addLabel("", False, layout_4)
            widget_4_licon_1.setPixmap(QIcon(os.path.join(basedir,"img","floppy-disk.png")).pixmap(42,42))
            #
            layout.addLayout(layout_4)
            
            layout_5 = QHBoxLayout()
            layout_5.setAlignment(Qt.AlignLeft)
            frame_5 = self.addFrame(layout_5)
            frame_5.setMinimumWidth(560)
            frame_5.setMaximumWidth(560)
            layout_5.addWidget(frame_5)
            #
            layout.addLayout(layout_5)
            
            
            layout_6 = QHBoxLayout()
            layout_6.setAlignment(Qt.AlignLeft)
            widget_6_label_1 = self.addLabel("Source dir:", False, layout_6)
            widget_6_label_1.setMinimumWidth(160)
            widget_6_label_1.setMaximumWidth(160)
            widget_6_label_1.setFont(font)
            #
            widget_6_edit_1  = self.addLineEdit("E:\\temp\\src", layout_6)
            widget_6_edit_1.setMinimumWidth(300)
            widget_6_edit_1.setMaximumWidth(300)
            widget_6_edit_1.setFont(font)
            #
            widget_6_pushb_1 = self.addPushButton("Select", layout_6)
            widget_6_pushb_1.setMinimumHeight(40)
            widget_6_pushb_1.setMaximumHeight(40)
            widget_6_pushb_1.setMinimumWidth(84)
            widget_6_pushb_1.setMaximumWidth(84) ; font.setBold(True)
            widget_6_pushb_1.setFont(font)       ; font.setBold(False)
            #
            layout_6.addWidget(widget_6_label_1)
            layout_6.addWidget(widget_6_edit_1)
            layout_6.addWidget(widget_6_pushb_1)
            #
            layout.addLayout(layout_6)
            
            
            layout_7 = QHBoxLayout()
            layout_7.setAlignment(Qt.AlignLeft)
            widget_7_label_1 = self.addLabel("Destination dir:", False, layout_7)
            widget_7_label_1.setMinimumWidth(160)
            widget_7_label_1.setMaximumWidth(160)
            widget_7_label_1.setFont(font)
            #
            widget_7_edit_1  = self.addLineEdit("E:\\temp\\src\\html", layout_7)
            widget_7_edit_1.setMinimumWidth(300)
            widget_7_edit_1.setMaximumWidth(300)
            widget_7_edit_1.setFont(font)
            #
            widget_7_pushb_1 = self.addPushButton("Select", layout_7)
            widget_7_pushb_1.setMinimumHeight(40)
            widget_7_pushb_1.setMaximumHeight(40)
            widget_7_pushb_1.setMinimumWidth(84)
            widget_7_pushb_1.setMaximumWidth(84) ; font.setBold(True)
            widget_7_pushb_1.setFont(font)       ; font.setBold(False)
            #
            layout_7.addWidget(widget_7_label_1)
            layout_7.addWidget(widget_7_pushb_1)
            #
            layout.addLayout(layout_7)
            
            
            layout_61 = QHBoxLayout()
            layout_61.setAlignment(Qt.AlignLeft)
            frame_61 = self.addFrame(layout_61)
            frame_61.setMinimumWidth(560)
            frame_61.setMaximumWidth(560)
            layout_61.addWidget(frame_61)
            #
            layout.addLayout(layout_61)
            
            
            layout_9 = QHBoxLayout()
            layout_9.setAlignment(Qt.AlignLeft)
            widget_9_checkbutton_1 = self.addCheckBox("Scan recursive")
            widget_9_checkbutton_1.setMaximumWidth(300)
            widget_9_checkbutton_1.setFont(font)
            layout_9.addWidget(widget_9_checkbutton_1)
            layout.addLayout(layout_9)
            
            self.setWidgetResizable(False)
            self.setWidget(content_widget)
        
        def btn_clicked_3(self):
            print("HelpNDoc")
        
        def btn_clicked_2(self):
            # ---------------------------------------------------------
            # all files are write, then create the CHM file ...
            # ---------------------------------------------------------
            dir_old = os.getcwd()
            dir_new = html_out + "/html"
            
            if os_type == os_type_windows:
                dir_old = dir_old.replace("/", "\\")
                dir_new = dir_new.replace("/", "\\")
                
                os.chdir(dir_new)
                result = subprocess.run([f"{hhc__path}" + "hhc.exe", ".\\index.hhp"])
                exit_code = result.returncode
                
                # -----------------------------------------------------
                # when error level, then do nothing anyelse - exit ...
                # -----------------------------------------------------
                if exit_code != 1:
                    print(""                               \
                    + "error: hhc.exe aborted with code: " \
                    + f"{exit_code}")
                    sys.exit(EXIT_FAILURE)
                
                os.chdir(dir_old)
            else:
                print("error: this script is for Windows hhc.exe")
                sys.exit(EXIT_FAILURE)
        
        def btn_clicked_1(self):
            print("converting all files can take a while...\n")
            
            result = subprocess.run([f"{doxy_path}",f"{doxyfile}"])
            exit_code = result.returncode
            
            # -----------------------------------------------------
            # when error level, then do nothing anyelse - exit ...
            # -----------------------------------------------------
            if exit_code > 0:
                print(""                               \
                + "error: doxygen aborted with code: " \
                + f"{exit_code}")
                sys.exit(EXIT_FAILURE)
            
            # ---------------------------------------------------------
            # get all .html files, in all directories based on root ./
            # ---------------------------------------------------------
            html_directory = './**/*.html'
            
            if os_type == os_type_windows:
                html_directory  =  html_directory.replace("/", "\\")
            
            self.html_files = glob.glob(html_directory,recursive = True)
            self.file_names = []
            
            # ---------------------------------------------------------
            # start thread ...
            # ---------------------------------------------------------
            self.thread = WorkerThread()
            self.thread.progress_changed.connect(self.update_progress)
            self.thread.start()  # start
        
        def update_progress(self, value):
            for file_name in self.html_files:
                if os_type == os_type_windows:
                    file_name = file_name.replace("/", "\\")
                #self.file_names.append(file_name)
                self.progress_bar.setValue(value)
                convertFiles(file_name)
    
    class customScrollView_2(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            
            label_2 = self.addLabel("Select a desired extraction mode:", True)
            label_2.setMinimumHeight(30)
            label_2.setMinimumWidth(200)
            
            self.addRadioButton("Documentet entries only")
            self.addRadioButton("All entries")
            self.addCheckBox("Include cross referenced source code in the output:")
            
            self.addFrame()
            
            self.addLabel("Select programming language to optimize the results for:", True)
            
            self.addRadioButton("Optimize for C++ output")
            self.addRadioButton("Optimize for C++ / CLI output")
            self.addRadioButton("Optimize for Java or C-Sharp / C# output")
            self.addRadioButton("Optimize for C or PHP output")
            self.addRadioButton("Optimize for Fortran output")
            self.addRadioButton("Optimize for VHCL output")
            self.addRadioButton("Optimize for SLICE output")
    
    # ------------------------------------------------------------------------
    # create a scroll view for the output tab on left side of application ...
    # ------------------------------------------------------------------------
    class customScrollView_3(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            
            self.addLabel("Select the output format(s) to generate:", True)
            
            # HTML
            self.addCheckBox("HTML", True)
            #
            self.addRadioButton("plain HTML")
            self.addRadioButton("with navigation Panel")
            self.addRadioButton("prepare for compressed HTML .chm")
            self.addCheckBox("with search function")
            
            self.addFrame()
            
            # LaTeX
            self.addCheckBox("LaTeX", True)
            #
            self.addRadioButton("an intermediate format for hypter-linked PDF")
            self.addRadioButton("an intermediate format for PDF")
            self.addRadioButton("an intermediate format for PostScript")
            
            self.addFrame()
            
            # misc
            self.addCheckBox("Man pages")
            self.addCheckBox("Rich Text Format - RTF")
            self.addCheckBox("XML")
            self.addCheckBox("DocBook")
    
    # ------------------------------------------------------------------------
    # create a scroll view for the diagrams tab on left side of application ...
    # ------------------------------------------------------------------------
    class customScrollView_4(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            
            self.addLabel("Diagrams to generate:", True)
            
            self.addRadioButton("No diagrams")
            self.addRadioButton("Text only")
            self.addRadioButton("Use built-in diagram generator")
            self.addRadioButton("Use Dot-Tool from the GrappVz package")
            
            self.addFrame()
            
            self.addLabel("Dot graphs to generate:", True)
            
            self.addCheckBox("Class graph")
            self.addCheckBox("Colaboration diagram")
            self.addCheckBox("Overall Class hiearchy")
            self.addCheckBox("Include dependcy graphs")
            self.addCheckBox("Included by dependcy graphs")
            self.addCheckBox("Call graphs")
            self.addCheckBox("Called-by graphs")
            
    
    class customScrollView_5(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(2000)
            
            label_1_elements = [
                # <text>,                  <type 1>,             <help>, <type 2>,  <list 1>
                ["DOXYFILE_ENCODING",      self.type_edit,       100, 0],
                ["PROJECT_NAME",           self.type_edit,       101, 0],
                ["PROJECT_NUMBER",         self.type_edit,       102, 0],
                ["PROJECT_BRUEF",          self.type_edit,       103, 0],
                ["PROJECT_LOGO",           self.type_edit,       104, 1],
                ["PROJECT_ICON",           self.type_edit,       105, 1],
                ["OUTPUT_DIRECTORY",       self.type_edit,       106, 1],
                ["CREATE_SUBDIRS",         self.type_check_box,  107, 0],
                ["CREATE_SUBDIRS_LEVEL",   self.type_spin,       108, 0],
                ["ALLOW_UNICODE_NAMES",    self.type_check_box,  109, 0],
                ["OUTPUT_LANGUAGE",        self.type_combo_box,  110, 4, ["English","German","French","Spanish"]],
                ["BRIEF_MEMBER_DESC",      self.type_check_box,  111, 0],
                ["REPEAT_BRIEF",           self.type_check_box,  112, 0],
                ["ABBREVIATE_BRIEF",       self.type_edit,       113, 3],
                ["ALWAYS_DETAILED_SEC",    self.type_check_box,  114, 0],
                ["INLINE_INHERITED_MEMB",  self.type_check_box,  115, 0],
                ["FULL_PATH_NAMES",        self.type_check_box,  116, 0],
                ["STRIP_FROM_PATH",        self.type_edit,       117, 3],
                ["STRIP_FROM_INC_PATH",    self.type_edit,       118, 3],
                ["SORT_NAMES",             self.type_check_box,  119, 0],
                ["JAVADOC_AUTOBRIEF",      self.type_check_box,  120, 0],
                ["JAVADOC_BANNER",         self.type_check_box,  121, 0],
                ["QT_AUTOBRIEF",           self.type_check_box,  122, 0],
                ["MULTILINE_CPP_IS_BRIEF", self.type_check_box,  123, 0],
                ["PYTHON_DOCSTRING",       self.type_check_box,  124, 0],
                ["INHERITED_DOCS",         self.type_check_box,  125, 0],
                ["SEPERATE_MEMBER_PAGES",  self.type_check_box,  126, 0],
                ["TAB_SIZE",               self.type_spin,       127, 0],
                ["ALIASES",                self.type_edit,       128, 3],
                ["OPTIMIZE_OUTPUT_FOR_C",  self.type_check_box,  129, 0],
                ["OPTIMIZE_OUTPUT_JAVA",   self.type_check_box,  130, 0],
                ["OPTIMIZE_FOR_FORTRAN",   self.type_check_box,  131, 0],
                ["OPTIMIZE_OUTPUT_VHCL",   self.type_check_box,  132, 0],
                ["OPTIMIZE_OUTPUT_SLICE",  self.type_check_box,  133, 0],
                ["EXTERNAL_MAPPING",       self.type_edit,       134, 3],
                ["MARKDOWN_SUPPORT",       self.type_check_box,  135, 0],
                ["MARKDOWN_ID_STYLE",      self.type_combo_box,  136, 2, ["DOXYGEN", "CIT"]],
                ["TOC_INCLUDE_HEADINGS",   self.type_spin,       137, 0],
                ["AUTOLINK_SUPPORT",       self.type_check_box,  138, 0],
                ["BUILTIN_STL_SUPPORT",    self.type_check_box,  139, 0],
                ["CPP_CLI_SUPPORT",        self.type_check_box,  140, 0],
                ["SIP_SUPPORT",            self.type_check_box,  141, 0],
                ["IDL_PROPERTY_SUPPORT",   self.type_check_box,  142, 0],
                ["DESTRIBUTE_GROUP_DOC",   self.type_check_box,  143, 0],
                ["GROUP_NESTED_COMPOUNDS", self.type_check_box,  144, 0],
                ["SUBGROUPING",            self.type_check_box,  145, 0],
                ["INLINE_GROUPED_CLASSES", self.type_check_box,  146, 0],
                ["INLINE_SIMPLE_STRUCTS",  self.type_check_box,  147, 0],
                ["TYPEDEF_HIDES_STRUCT",   self.type_check_box,  148, 0],
                ["LOOKUP_CACHE_SIZE",      self.type_spin,       149, 0],
                ["NUM_PROC_THREADS",       self.type_spin,       150, 0],
                ["TIMESTAMP",              self.type_combo_box,  151, 2, ["NO","YES"]]
            ]
            
            for i in range(0, len(label_1_elements)):
                lv_0 = QVBoxLayout()
                lh_0 = QHBoxLayout()
                
                # -----------------------------------------
                # the help string for a doxygen tag ...
                # -----------------------------------------
                helpID   = 256 + i + 1
                
                s = int.to_bytes(helpID,2,"little")
                s = s.decode("utf-8")
                
                helpText = tr("h" + s)
                vw_1 = self.addHelpLabel(   \
                    label_1_elements[i][0], \
                    helpID,                 \
                    helpText,               \
                    lh_0)
                vw_1.setMinimumHeight(14)
                vw_1.setMinimumWidth(200)
                
                if label_1_elements[i][1] == self.type_edit:
                    self.addLineEdit("",lh_0)
                                        
                    if label_1_elements[i][3] == 1:
                        self.addPushButton("+",lh_0)
                        
                    elif label_1_elements[i][3] == 3:
                        self.addPushButton("+",lh_0)
                        self.addPushButton("-",lh_0)
                        self.addPushButton("R",lh_0)
                        
                        vw_3 = myTextEdit()
                        vw_3.setFont(self.font_a)
                        vw_3.setMinimumHeight(52)
                        lv_0.addWidget(vw_3)
                        
                elif label_1_elements[i][1] == self.type_check_box:
                    vw_2 = QCheckBox()
                    vw_2.setMinimumHeight(21)
                    vw_2.setFont(self.font_a)
                    lh_0.addWidget(vw_2)
                    
                elif label_1_elements[i][1] == self.type_combo_box:
                    vw_2 = QComboBox()
                    vw_2.setMinimumHeight(26)
                    vw_2.setFont(self.font)
                    vw_2.font().setPointSize(14)
                    lh_0.addWidget(vw_2)
                    
                    if label_1_elements[i][3] == 4:
                        for j in range(0, len(label_1_elements[i][4])):
                            img = "flag_"               \
                            + label_1_elements[i][4][j] \
                            + ".png".lower()
                            vw_2.insertItem(0, label_1_elements[i][4][j])
                            vw_2.setItemIcon(0, QIcon(os.path.join(basedir,"img",img)))
                    
                    elif label_1_elements[i][3] == 2:
                        for j in range(0, len(label_1_elements[i][4])):
                            vw_2.addItem(label_1_elements[i][4][j])
                
                elif label_1_elements[i][1] == self.type_spin:
                    vw_2 = QSpinBox()
                    vw_2.setFont(self.font_a)
                    vw_2.setMinimumHeight(21)
                    lh_0.addWidget(vw_2)
                
                lv_0.addLayout(lh_0)
                self.layout.addLayout(lv_0)
        
        # ----------------------------------------------
        # show help text when mouse move over the label
        # ----------------------------------------------
        def label_enter_event(self, text):
            sv_help.setText(text)
    
    class customScrollView_6(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            
            label_1_elements = [
                "EXTRACT_ALL","EXTRACT_PRIVATE","EXTRACT_PRIV_VIRTUAL"
            ]
    
    class customScrollView_7(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_8(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_9(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_10(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_11(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_12(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_13(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_14(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_15(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_16(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_17(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_18(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_19(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_20(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_21(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_22(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_23(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_24(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
    class customScrollView_help(QTextEdit):
        def __init__(self):
            super().__init__()
            
            font = QFont("Arial")
            font.setPointSize(11)
            
            self.setFont(font)
            self.setMinimumHeight(100)
            self.setMaximumHeight(100)
    
    class MyCustomClass():
        def __init__(self, name, number):
            super().__init__()
            
            if number == 1:
                customScrollView_5()
    
    # ------------------------------------------------------------------------
    # after main was process, create the main application gui window ...
    # ------------------------------------------------------------------------
    class mainWindow(QDialog):
        def __init__(self):
            super().__init__()
            
            self.minimumWidth = 880
            self.controlFont = "font-size:10pt;font-weight:bold;border-width:5px;"
            
            self.__error__internal_widget_error_1 = "" \
                + "internal error:\n"                  \
                + "itemWidget could not found."
            self.__error__internal_widget_error_2 = "" \
                + "internal error:\n"                  \
                + "item label could not found."
            
            self.__css__widget_item = tr("__css__widget_item")
            self.__button_style_css = tr("__button_style_css")
            
            self.init_ui()
        
        def init_ui(self):
            font = QFont("Arial", 10)
            self.setFont(font)
            self.setContentsMargins(0,0,0,0)
            self.setStyleSheet("padding:0px;margin:0px;")
            
            container = QVBoxLayout(self)
            container.setContentsMargins(0,0,0,0)
            container.setAlignment(Qt.AlignTop)
            
            # ----------------------------------------
            # color for the menu items ...
            # ----------------------------------------
            menu_item_style = tr("menu_item_style")
            
            # ----------------------------------------
            # create a new fresh menubar ...
            # ----------------------------------------
            menubar = QMenuBar()
            menubar.setStyleSheet(_(menu_item_style))
            
            menu_file = menubar.addMenu("File")
            menu_edit = menubar.addMenu("Edit")
            menu_help = menubar.addMenu("Help")
            
            menu_font = menu_file.font()
            menu_font.setPointSize(11)
            
            menu_file.setFont(menu_font)
            menu_edit.setFont(menu_font)
            menu_help.setFont(menu_font)
            
            # ----------------------------------------
            # file menu action's ...
            # ----------------------------------------
            menu_file_new    = QWidgetAction(menu_file)
            menu_file.addSeparator()
            menu_file_open   = QWidgetAction(menu_file)
            menu_file_save   = QWidgetAction(menu_file)
            menu_file_saveas = QWidgetAction(menu_file)
            menu_file.addSeparator()
            menu_file_exit   = QWidgetAction(menu_file)
            menu_file.setStyleSheet("color:white;font-weight:normal;font-style:italic")
            
            menu_label_style = tr("menu_label_style")
            
            menu_icon_1 = QIcon("")
            menu_icon_2 = QIcon("")
            menu_icon_3 = QIcon("")
            
            menu_widget_1 = QWidget()
            menu_layout_1 = QHBoxLayout(menu_widget_1)
            menu_layout_1.setContentsMargins(0,0,0,0)
            #
            menu_icon_widget_1 = QWidget()
            menu_icon_widget_1.setFixedWidth(26)
            menu_icon_widget_1.setContentsMargins(0,0,0,0)
            #
            menu_label_1 = QLabel("New ...")
            menu_label_1.setStyleSheet(menu_label_style)
            menu_label_1.setMinimumWidth(160)
            menu_label_1_shortcut = QLabel("Ctrl-N")
            #
            menu_layout_1.addWidget(menu_icon_widget_1)
            menu_layout_1.addWidget(menu_label_1)
            menu_layout_1.addWidget(menu_label_1_shortcut)
            #
            menu_widget_1.setLayout(menu_layout_1)
            
            
            menu_widget_2 = QWidget()
            menu_layout_2 = QHBoxLayout(menu_widget_2)
            menu_layout_2.setContentsMargins(0,0,0,0)
            #
            menu_icon_widget_2 = QWidget()
            menu_icon_widget_2.setFixedWidth(26)
            menu_icon_widget_2.setContentsMargins(0,0,0,0)
            #
            menu_label_2 = QLabel("Open");
            menu_label_2.setStyleSheet(menu_label_style)
            menu_label_2.setMinimumWidth(160)
            menu_label_2_shortcut = QLabel("Ctrl-O")
            #
            menu_layout_2.addWidget(menu_icon_widget_2)
            menu_layout_2.addWidget(menu_label_2)
            menu_layout_2.addWidget(menu_label_2_shortcut)
            #
            menu_widget_2.setLayout(menu_layout_2)
            
            
            menu_widget_3 = QWidget()
            menu_layout_3 = QHBoxLayout(menu_widget_3)
            menu_layout_3.setContentsMargins(0,0,0,0)
            #
            menu_icon_widget_3 = QWidget()
            menu_icon_widget_3.setFixedWidth(26)
            menu_icon_widget_3.setContentsMargins(0,0,0,0)
            #
            menu_label_3 = QLabel("Save");
            menu_label_3.setStyleSheet(menu_label_style)
            menu_label_3.setMinimumWidth(160)
            menu_label_3_shortcut = QLabel("Ctrl-S")
            #
            menu_layout_3.addWidget(menu_icon_widget_3)
            menu_layout_3.addWidget(menu_label_3)
            menu_layout_3.addWidget(menu_label_3_shortcut)
            #
            menu_widget_3.setLayout(menu_layout_3)
            
            
            menu_widget_4 = QWidget()
            menu_layout_4 = QHBoxLayout(menu_widget_4)
            menu_layout_4.setContentsMargins(0,0,0,0)
            #
            menu_icon_widget_4 = QWidget()
            menu_icon_widget_4.setFixedWidth(26)
            menu_icon_widget_4.setContentsMargins(0,0,0,0)
            #
            menu_label_4 = QLabel("Save As ...");
            menu_label_4.setStyleSheet(menu_label_style)
            menu_label_4.setMinimumWidth(160)
            menu_label_4_shortcut = QLabel("")
            #
            menu_layout_4.addWidget(menu_icon_widget_4)
            menu_layout_4.addWidget(menu_label_4)
            menu_layout_4.addWidget(menu_label_4_shortcut)
            #
            menu_widget_4.setLayout(menu_layout_4)
            
            
            menu_widget_5 = QWidget()
            menu_layout_5 = QHBoxLayout(menu_widget_5)
            menu_layout_5.setContentsMargins(0,0,0,0)
            #
            menu_icon_widget_5 = QWidget()
            menu_icon_widget_5.setFixedWidth(26)
            menu_icon_widget_5.setContentsMargins(0,0,0,0)
            #
            menu_label_5 = QLabel("Exit");
            menu_label_5.setStyleSheet(menu_label_style)
            menu_label_5.setMinimumWidth(160)
            menu_label_5_shortcut = QLabel("")
            #
            menu_layout_5.addWidget(menu_icon_widget_5)
            menu_layout_5.addWidget(menu_label_5)
            menu_layout_5.addWidget(menu_label_5_shortcut)
            #
            menu_widget_5.setLayout(menu_layout_5)
            
            
            menu_file_new   .setDefaultWidget(menu_widget_1)
            menu_file_open  .setDefaultWidget(menu_widget_2)
            menu_file_save  .setDefaultWidget(menu_widget_3)
            menu_file_saveas.setDefaultWidget(menu_widget_4)
            menu_file_exit  .setDefaultWidget(menu_widget_5)
            
            # ----------------------------------------
            # menu action event's (mouse click):
            # ----------------------------------------
            menu_file_new   .triggered.connect(self.menu_file_clicked_new)
            menu_file_open  .triggered.connect(self.menu_file_clicked_open)
            menu_file_save  .triggered.connect(self.menu_file_clicked_save)
            menu_file_saveas.triggered.connect(self.menu_file_clicked_saveas)
            menu_file_exit  .triggered.connect(self.menu_file_clicked_exit)
            
            menu_file.addAction(menu_file_new)
            menu_file.addAction(menu_file_open)
            menu_file.addAction(menu_file_save)
            menu_file.addAction(menu_file_saveas)
            menu_file.addAction(menu_file_exit)
            
            # ----------------------------------------
            # add toolbar under the main menu ...
            # ----------------------------------------
            toolbar = QToolBar("main-toolbar")
            toolbar.setContentsMargins(0,0,0,0)
            toolbar.setStyleSheet("background-color:gray;font-size:11pt;height:38px;")
            
            toolbar_action_new  = QAction(QIcon(os.path.join(basedir,"img","new-document.png")),tr("New Config."), self)
            toolbar_action_open = QAction(QIcon(os.path.join(basedir,"img","open-folder.png" )),tr("Open existing Config."), self)
            toolbar_action_save = QAction(QIcon(os.path.join(basedir,"img","floppy-disk.png" )),tr("Save current session."), self)
            
            toolbar_action_new .triggered.connect(self.menu_file_clicked_new)
            toolbar_action_open.triggered.connect(self.menu_file_clicked_open)
            toolbar_action_open.triggered.connect(self.menu_file_clicked_open)
            
            toolbar.addAction(toolbar_action_new )
            toolbar.addAction(toolbar_action_open)
            toolbar.addAction(toolbar_action_save)
            
            
            # ----------------------------------------
            # select working directory widget ...
            # ----------------------------------------
            widget_font = QFont("Arial", 10)
            
            text_layout_widget_1 = QWidget()
            text_layout_widget_1.setStyleSheet(self.controlFont)
            text_layout_widget_1.setContentsMargins(0,0,0,0)
            #
            text_layout_1 = QHBoxLayout()
            text_layout_1.setContentsMargins(10,0,0,0)
            #
            text_label_1 = QLabel("Working directory")
            text_label_1.setFont(widget_font)
            text_label_1.setFixedWidth(150)
            #
            self.text_label_palette_1 = QPalette()
            self.text_label_palette_1.setColor(QPalette.Base, QColor("yellow"))
            
            self.text_label_1_editfield_1 = QLineEdit()
            self.text_label_1_editfield_1.setStyleSheet(self.controlFont)
            self.text_label_1_editfield_1.setFixedWidth(520)
            self.text_label_1_editfield_1.setText(os.getcwd())
            self.text_label_1_editfield_1.setPalette(self.text_label_palette_1)
            #
            text_label_1_button_1 = QPushButton("Select")
            text_label_1_button_1.setStyleSheet(self.__button_style_css)
            text_label_1_button_1.clicked.connect(self.show_directory_dialog)
            
            text_label_1_button_1.setMinimumWidth(100)
            text_label_1_button_1.setMaximumWidth(100)
            text_label_1_button_1.setMinimumHeight(32)
            
            # ----------------------------------------
            # add working dir widgets to layout ...
            # ----------------------------------------
            text_layout_1.addWidget(text_label_1)
            text_layout_1.addWidget(self.text_label_1_editfield_1)
            text_layout_1.addWidget(text_label_1_button_1)
            #
            text_layout_1.setAlignment(text_label_1, Qt.AlignLeft)
            text_layout_1.setAlignment(self.text_label_1_editfield_1, Qt.AlignLeft)
            text_layout_1.setAlignment(text_label_1_button_1, Qt.AlignLeft)
            
            spacer_1 = QSpacerItem(440, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
            text_layout_1.addItem(spacer_1)
            
            # ----------------------------------------
            # left card panel on main screen:
            # ----------------------------------------
            container_widget_2 = QWidget()
            container_layout_2 = QHBoxLayout(container_widget_2)
            container_layout_2.setContentsMargins(5,0,0,0)
            container_layout_2.setAlignment(Qt.AlignTop)
            
            
            # ----------------------------------------
            # left register card ...
            # ----------------------------------------
            self.tab_widget_1 = QTabWidget()
            self.tab_widget_1.setFont(widget_font)
            self.tab_widget_1.setMinimumHeight(380)
            
            self.tab_widget_1.setStyleSheet(tr("tab_widget_1"))
            
            tab_1 = QWidget()
            tab_2 = QWidget()
            tab_3 = QWidget()
            
            tab_1.setFont(widget_font)
            tab_2.setFont(widget_font)
            tab_3.setFont(widget_font)
            
            self.tab_widget_1.addTab(tab_1, "Wizard")
            self.tab_widget_1.addTab(tab_2, "Expert")
            self.tab_widget_1.addTab(tab_3, "Run")
            
            font = QFont("Arial", 10)
            font.setBold(True)
            #
            list_layout_1 = QHBoxLayout(tab_1)
            list_widget_1 = QListWidget()
            
            list_widget_1.setFont(font)
            list_widget_1.setFocusPolicy(Qt.NoFocus)
            list_widget_1.setStyleSheet(self.__css__widget_item)
            list_widget_1.setMinimumHeight(300)
            list_widget_1.setMaximumWidth(200)
            self.list_widget_1_elements = ["Project", "Mode", "Output", "Diagrams" ]
            #
            #
            list_layout_2 = QHBoxLayout(tab_2)
            list_widget_2 = QListWidget()
            
            list_widget_2.setFont(font)
            list_widget_2.setFocusPolicy(Qt.NoFocus)
            list_widget_2.setStyleSheet(self.__css__widget_item)
            list_widget_2.setMinimumHeight(300)
            list_widget_2.setMaximumWidth(200)
            self.list_widget_2_elements = [                                     \
                "Project", "Build", "Messages", "Input", "Source Browser",      \
                "Index", "HTML", "LaTeX", "RTF", "Man", "XML", "DocBook",       \
                "AutoGen", "SQLite3", "PerlMod", "Preprocessor", "External",    \
                "Dot" ]
            
            self.list_widget_3 = QListWidget(tab_3)
            self.list_widget_3.setMinimumHeight(300)
            self.list_widget_3_elements = []
            
            for element in self.list_widget_1_elements:
                list_item = customQListWidgetItem(element, list_widget_1)
                list_item.setFont(widget_font)
            #
            for element in self.list_widget_2_elements:
                list_item = customQListWidgetItem(element, list_widget_2)
                list_item.setFont(widget_font)
            
            list_widget_1.setCurrentRow(0)
            list_widget_1.itemClicked.connect(self.handle_item_click)
            list_layout_1.addWidget(list_widget_1)
            
            list_widget_2.setCurrentRow(0)
            list_widget_2.itemClicked.connect(self.handle_item_click)
            list_layout_2.addWidget(list_widget_2)
            
            
            # tab: 0
            self.sv_1_1 = customScrollView_1("Project")
            self.sv_1_2 = customScrollView_2("Mode");     self.sv_1_2.hide()
            self.sv_1_3 = customScrollView_3("Output");   self.sv_1_3.hide()
            self.sv_1_4 = customScrollView_4("Diagrams"); self.sv_1_4.hide()
            
            #tab: 1
            tab1_classes = [ \
                customScrollView_5 , customScrollView_6 , customScrollView_7 , customScrollView_8 , \
                customScrollView_9 , customScrollView_10, customScrollView_11, customScrollView_12, \
                customScrollView_13, customScrollView_14, customScrollView_15, customScrollView_16, \
                customScrollView_17, customScrollView_18, customScrollView_19, customScrollView_20, \
                customScrollView_21, customScrollView_22  ]
            
            tab1_class_objs = [ cls("name") for cls in tab1_classes ]
            
            for i in range(0, len(tab1_classes)):
                s = "sv_2_" + str(i+1)
                v1 = tab1_class_objs[i]
                v1.setName(self.list_widget_2_elements[i])
                setattr(self, s, v1)
                list_layout_2.addWidget(getattr(self, f"{s}"))
                v1.hide()
            
            self.sv_2_1.show()
            
            # tab: 0
            for i in range(1, 5):
                s = "sv_1_" + str(i)
                list_layout_1.addWidget(getattr(self, f"{s}"))
            
            # ----------------------------------------
            # middle area ...
            # ----------------------------------------
            container_layout_2.addWidget(self.tab_widget_1)
            
            # ----------------------------------------
            # the status bar is the last widget ...
            # ----------------------------------------
            status_bar = QStatusBar()
            status_bar.setStyleSheet("background-color:gray;color:white;font-size:9pt;")
            status_bar.showMessage("Welcome")
            
            # ----------------------------------------
            # the main container for all widget's ...
            # ----------------------------------------
            container.setMenuBar(menubar)
            container.addWidget(toolbar)
            
            container.addLayout(text_layout_1)
            container.addItem(spacer_1)
            
            container.addWidget(container_widget_2)
            container.addWidget(sv_help)
            container.addWidget(status_bar)
            
            self.setLayout(container)
            
            # ----------------------------------------
            # add windows specified informations ...
            # ----------------------------------------
            self.setWindowFlags(
            self.windowFlags()
                | Qt.WindowMinimizeButtonHint
                | Qt.WindowMaximizeButtonHint)
            
            self.setWindowTitle("doxygen CHM filter (c) 2024 by paule32")
            self.setGeometry(100, 100, 400, 300)
            self.setMinimumWidth(self.minimumWidth)
            self.setModal(True)
            self.show()
        
        # ------------------------------------------------------------------------
        # customized actions on user application exit ...
        # ------------------------------------------------------------------------
        def closeEvent(self, event):
            print("close application.")
            event.accept()
            sys.exit(EXIT_SUCCESS)
        
        # ------------------------------------------------------------------------
        # class member to get the widget item from list_widget_1 or list_widget_2.
        # The application script will stop, if an internal error occur ...
        # ------------------------------------------------------------------------
        def handle_item_click(self, item):
            tab_index = self.tab_widget_1.currentIndex()
            if tab_index == 1:
                for i in range(0, len(self.list_widget_2_elements)):
                    if item.data(0) == self.list_widget_2_elements[i]:
                        print("t: " + str(i) + ": " + self.list_widget_2_elements[i])
                        self.hideTabItems_2(i)
                        s = "sv_2_" + str(i+1)
                        w = getattr(self, f"{s}")
                        w.show()
                        break
            elif tab_index == 0:
                for i in range(0, len(self.list_widget_1_elements)):
                    if item.data(0) == self.list_widget_1_elements[i]:
                        self.hideTabItems_1(i)
                        s = "sv_1_" + str(i+1)
                        w = getattr(self, f"{s}")
                        w.show()
                        return
        
        def hideTabItems_1(self, it):
            for i in range(0, len(self.list_widget_1_elements)):
                s = "sv_1_" + str(i+1)
                w = getattr(self, f"{s}")
                w.hide()
                if i == it:
                    w.show()
        
        def hideTabItems_2(self, it):
            for i in range(0, len(self.list_widget_2_elements)):
                s = "sv_2_" + str(i+1)
                w = getattr(self, f"{s}")
                w.hide()
                if i == it:
                    w.show()
        
        # ------------------------------------------------------------------------
        # select the work space directory where the Doxyfile resides, and let the
        # directory to be the root directory, if it not overwrite by config.ini
        # settings,
        # ------------------------------------------------------------------------
        def show_directory_dialog(self):
            options = QFileDialog.Options()
            options |= QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
            
            font = QFont("Arial")
            font.setPointSize(11)
            
            file_dialog = QFileDialog(self, "Select directory:", options=options)
            file_dialog.setFont(font)
            
            directory = file_dialog.getExistingDirectory(self)
            if directory:
                directory = convertPath(directory)
                self.text_label_1_editfield_1.setText(directory)
                print(doxyfile)
        
        def menu_file_clicked_new(self):
            return
        
        def menu_file_clicked_open(self):
            return
        
        def menu_file_clicked_save(self):
            return
        
        def menu_file_clicked_saveas(self):
            return
        
        def menu_file_clicked_exit(self):
            sys.exit(EXIT_SUCCESS)
            return
        
    
    # ------------------------------------------------------------------------
    # inform the user about the rules/license of this application script ...
    # ------------------------------------------------------------------------
    class licenseWindow(QDialog):
        def __init__(self):
            super().__init__()
            
            self.returnCode = 0
            
            self.setWindowTitle("LICENSE - Please read, before you start.")
            self.setMinimumWidth(820)
        
            font = QFont("Courier New", 10)
            self.setFont(font)
            
            layout = QVBoxLayout()
            
            button1 = QPushButton("Accept")
            button2 = QPushButton("Decline")
            
            button1.clicked.connect(self.button1_clicked)
            button2.clicked.connect(self.button2_clicked)
            
            textfield = QTextEdit(self)
            textfield.setReadOnly(True)
            
            layout.addWidget(textfield)
            layout.addWidget(button1)
            layout.addWidget(button2)
            
            self.setLayout(layout)
            
            # ---------------------------------------------------------
            # get license to front, before the start shot ...
            # ---------------------------------------------------------
            file_lic = os.getcwd() + "/LICENSE"
            if not os.path.exists(file_lic):
                showApplicationError("no license - aborted.")
                sys.exit(EXIT_FAILURE)
            
            with open(file_lic, 'r') as file:
                content = file.read()
                file.close()
                textfield.setPlainText(content)
        
        def button1_clicked(self):
            self.returnCode = 0
            self.close()
        
        def button2_clicked(self):
            self.returnCode = 1
            self.close()
    
    # ------------------------------------------------------------------------
    # this is our "main" entry point, where the application will start, if you
    # type the name of the script into the console, or by mouse click at the
    # file explorer under a GUI system (Windows) ...
    # ------------------------------------------------------------------------
    if __name__ == "__main__":
        
        # ---------------------------------------------------------
        # scoped global stuff ...
        # ---------------------------------------------------------
        global doxyfile, hhc__path
        
        pcount     = len(sys.argv) - 1
        
        doxy_env   = "DOXYGEN_PATH"  # doxygen.exe
        doxy_hhc   = "DOXYHHC_PATH"  # hhc.exe
        
        doxy_path  = "./"
        hhc__path  = ""
        
        doxyfile   = "Doxyfile"
        
        # ---------------------------------------------------------
        # first, we check the operating system platform:
        # 0 - unknown
        # 1 - Windows
        # 2 - Linux
        # ---------------------------------------------------------
        global os_type, os_type_windows, os_type_linux
        
        os_type_unknown = 0
        os_type_windows = 1
        os_type_linux   = 2
        
        os_type         = os_type_unknown
        # ---------------------------------------------------------
        if platform.system() == "Windows":
            os_type = os_type_windows
        elif platform.system() == "Linux":
            os_type = os_type_linux
        else:
            os_type = os_type_unknown
            if isPythonWindows():
                if not isApplicationInit():
                    app = QApplication(sys.argv)
                showApplicationError(__error__os__error)
            elif "python" in __app__exec_name:
                print(__error__os_error)
            sys.exit(EXIT_FAILURE)
        
        # ---------------------------------------------------------
        # print a nice banner on the display device ...
        # ---------------------------------------------------------
        if isPythonWindows() == False:
            print(__copy__)
        
        # ---------------------------------------------------------
        # when config.ini does not exists, then create a small one:
        # ---------------------------------------------------------
        if not os.path.exists(__app__config_ini):
            with open(__app__config_ini, "w", encoding="utf-8") as output_file:
                content = ""   \
                + "[common]\n" \
                + "language = en\n"
                output_file.write(content)
                output_file.close()
                ini_lang = "en" # default is english; en
        else:
            config = configparser.ConfigParser()
            config.read(__app__config_ini)
            ini_lang = config.get("common", "language")
        
        tr = handle_language(ini_lang)
        if not tr == None:
            tr  = tr.gettext
        
        # ---------------------------------------------------------
        # combine the puzzle names, and folders ...
        # ---------------------------------------------------------
        po_file_name = "./locales/"    \
            + f"{ini_lang}"    + "/LC_MESSAGES/" \
            + f"{__app__name}" + ".po"
        
        if not os.path.exists(convertPath(po_file_name)):
            if isPythonWindows() == True:
                showApplicationInformation(__error__locales_error)
            else:
                print(__error__locales_error)
        
        if os_type == os_type_windows or isPythonWindows() == True:
            # -----------------------------------------------------
            # show a license window, when readed, and user give a
            # okay, to accept it, then start the application ...
            # -----------------------------------------------------
            if isApplicationInit() == False:
                app = QApplication(sys.argv)
            
            license_window = licenseWindow()
            license_window.show()
            
            if getattr(sys, 'frozen', False):
                pyi_splash.close()
            
            license_window.exec_()
            
            if license_window.returnCode == 1:
                del license_window
                sys.exit(EXIT_SUCCESS)
            
            del license_window  # free memory
        
        # ---------------------------------------------------------
        # doxygen.exe directory path ...
        # ---------------------------------------------------------
        if not doxy_env in os.environ:
            if isPythonWindows() == False:
                if paule32_debug == True:
                    os.environ["DOXYGEN_PATH"] = "E:\\doxygen\\bin"
                else:
                    print("error: " + f"{doxy_env}" \
                    + " is not set in your system settings.")
                    sys.exit(EXIT_FAILURE)
            else:
                if paule32_debug == True:
                    os.environ["DOXYGEN_PATH"] = "E:\\doxygen\\bin"
                else:
                    if not isApplicationInit():
                        app = QApplication(sys.argv)
                    showApplicationError(""     \
                    + "error: " + f"{doxy_env}" \
                    + " is not set in your system settings.")
                    sys.exit(EXIT_FAILURE)
        else:
            doxy_path = os.environ[doxy_env]
        
        
        # ---------------------------------------------------------
        # Microsoft Help Workshop path ...
        # ---------------------------------------------------------
        if not doxy_hhc in os.environ:
            if isPythonWindows() == False:
                if paule32_debug == True:
                    os.environ["DOXYHHC_PATH"] = "E:\\doxygen\\hhc"
                else:
                    print(""                    \
                    + "error: " + f"{doxy_hhc}" \
                    + " is not set in your system settings.")
                    sys.exit(EXIT_FAILURE)
            else:
                if paule32_debug == True:
                    os.environ["DOXYGEN_PATH"] = "E:\\doxygen\\hhc"
                else:
                    if not isApplicationInit():
                        app = QApplication(sys.argv)
                    showApplicationError(""     \
                    + "error: " + f"{doxy_hhc}" \
                    + " is not set in your system settings.")
                    sys.exit(EXIT_FAILURE)
        else:
            hhc__path = os.environ[doxy_hhc]
        
        # ---------------------------------------------------------
        # depend on the platform system, check if doxygen exec name
        # was set into DOXYGEN_PATH. If no such entry exists, then
        # add doxygen executable name to "doxy_path" ...
        # ---------------------------------------------------------
        if os_type == os_type_windows:
            doxy_path = convertPath(doxy_path)
            if isPythonWindows() == True:
                if doxy_path[-1] == "\\":
                    if not "doxygen.exe" in doxy_path.lower():
                        doxy_path += "doxygen.exe"
                else:
                    if not "doxygen.exe" in doxy_path.lower():
                        doxy_path += "\\doxygen.exe"
            else:
                if doxy_path[-1] == "/":
                    if not "doxygen" in doxy_path.lower():
                        doxy_path += "doxygen"
                else:
                    if not "doxygen" in doxy_path.lower():
                        doxy_path += "/doxygen"
            
            # -----------------------------------------------------
            # Microsoft Help Workshop Compiler path ...
            # -----------------------------------------------------
            hhc__path = convertPath(hhc__path)
            if isPythonWindows() == True:
                if doxy_path[-1] == "\\":
                    if not "hhc.exe" in hhc__path.lower():
                        hhc__path += "hhc.exe"
                else:
                    if not "hhc.exe" in hhc__path.lower():
                        hhc__path += "\\hhc.exe"
            else:
                if doxy_path[-1] == "/":
                    if not "hhc" in hhc__path.lower():
                        hhc__path += "/hhc"
        
        # ---------------------------------------------------------
        # this is for Linux user's ,,,
        # ---------------------------------------------------------
        elif os_type == os_type_linux:
            if doxy_path[-1] == "/":
                if not "doxygen" in doxy_path:
                    doxy_path += "doxygen"
            else:
                if not "doxygen" in doxy_path:
                    doxy_path += "/doxygen"
        
        # ---------------------------------------------------------
        # at startup, check parameters for a given Doxyfile config
        # file. Is none given, the name for the config will be on
        # "Doxyfile" as default.
        # ---------------------------------------------------------
        if pcount < 1:
            if isPythonWindows() == True:
                if not isApplicationInit():
                    app = QApplication(sys.argv)
                showApplicationInformation( ""    \
                + "info: no parameter given. "    \
                + "use default: 'Doxyfile' config.")
            else:
                print(""                          \
                + "info: no parameter given. "    \
                + "use default: 'Doxyfile' config.")
        elif pcount > 1:
            if isPythonWindows() == True:
                if not isApplicationInit():
                    app = QApplication(sys.argv)
                showApplicationInformation( ""    \
                + "error: to many parameters. "   \
                + "use first parameter as config.")
            else:
                print(""                          \
                + "error: to many parameters. "   \
                + "use first parameter as config.")
                doxyfile = sys.argv[1]
        else:
            doxyfile = sys.argv[1]
        
        
        if os_type == os_type_windows:
            doxyfile = doxyfile.replace("/", "\\")
        
        # ---------------------------------------------------------
        # when config file not exists, then spite a info message,
        # and create a default template for doxygen 1.10.0
        # ---------------------------------------------------------
        if not os.path.exists(doxyfile):
            print("info: config: '" \
            + f"{doxyfile}" + "' does not exists. I will fix this by create a default file.")
            
            file_content = [
                ["PROJECT_NAME", "Project name"],
                ["PROJECT_NUMBER", "1.0.0" ],
                ["PROJECT_LOGO", "" ],
                ["",""],
                ["DOXYFILE_ENCODING", "UTF-8"],
                ["INPUT_ECODING", "UTF-8"],
                ["INPUT_FILE_ENCODING", "UTF-8"],
                ["",""],
                ["ALLOW_UNICODE_NAMES", "YES"],
                ["",""],
                ["ENABLED_SECTIONS", "english"],
                ["OUTPUT_LANGUAGE", "English"],
                ["OUTPUT_DIRECTORY", "./dox/enu/dark"],
                ["",""],
                ["CHM_FILE", "project.chm"],
                ["HHC_LOCATION", ""],
                ["",""],
                ["GENERATE_HTML", "YES"],
                ["GENERATE_HTMLHELP", "YES"],
                ["GENERATE_TREEVIEW", "NO"],
                ["GENERATE_LATEX", "NO"],
                ["GENERATE_CHI", "NO"],
                ["",""],
                ["HTML_OUTPUT", "html"],
                ["HTML_COLORSTYLE", "DARK"],
                ["",""],
                ["BINARY_TOC", "NO"],
                ["TOC_EXPAND", "NO"],
                ["",""],
                ["DISABLE_INDEX", "NO"],
                ["FULL_SIDEBAR", "NO"],
                ["",""],
                ["INPUT", ""],
                ["",""],
                ["BRIEF_MEMBER_DESC", "YES"],
                ["REPEAT_BRIEF", "YES"],
                ["",""],
                ["FILE_PATTERNS", "*.c *.cc *.cxx *.cpp *.c++ *.h *.hh *.hxx *.hpp *.h++"],
                ["ALIASES", ""],
                ["",""],
                ["CREATE_SUBDIRS", "YES"],
                ["CREATE_SUBDIRS_LEVEL", "8"],
                ["",""],
                ["ALWAYS_DETAILED_SEC", "YES"],
                ["INLINE_INHERITED_MEMB", "YES"],
                ["",""],
                ["FULL_PATH_NAMES", "NO"],
                ["SHORT_NAMES", "NO"],
                ["",""],
                ["STRIP_FROM_PATH", "YES"],
                ["STRIP_FROM_INC_PATH", "YES"],
                ["",""],
                ["MULTILINE_CPP_IS_BRIEF", "NO"],
                ["INHERITED_DOCS", "YES"],
                ["SEPERATE_MEMBER_PAGES", "NO"],
                ["",""],
                ["TAB_SIZE", "8"],
                ["",""],
                ["OPTIMIZE_OUTPUT_FOR_C", "YES"],
                ["OPTIMIZE_OUTPUT_JAVA", "NO"],
                ["OPTIMIZE_FOR_FORTRAN", "NO"],
                ["",""],
                ["EXTERNAL_MAPPING", ""],
                ["",""],
                ["TOC_INCLUDE_HEADINGS", "5"],
                ["AUTOLINK_SUPPORT", "YES"],
                ["",""],
                ["BUILTIN_STL_SUPPORT", "NO"],
                ["CPP_CLI_SUPPORT", "YES"],
                ["",""],
                ["SIP_SUPPORT", "NO"],
                ["IDL_PROPERTY_SUPPORT", "YES"],
                ["",""],
                ["DISTRIBUTE_GROUP_DOC", "NO"],
                ["GROUP_NESTED_COMPOUNDS", "NO"],
                ["SUBGROUPING", "YES"],
                ["",""],
                ["INLINE_GROUPED_CLASSES", "NO"],
                ["INLINE_SIMPLE_STRUCTS", "NO"],
                ["",""],
                ["TYPEDEF_HIDES_STRUCT", "NO"],
                ["",""],
                ["LOOKUP_CACHE_SIZE", "0"],
                ["NUM_PROC_THREADS", "1"],
                ["CASE_SENSE_NAMES", "YES"],
                ["",""],
                ["EXTRACT_ALL", "YES"],
                ["EXTRACT_PRIVATE", "NO"],
                ["EXTRAVT_PRIV_VIRTUAL", "NO"],
                ["EXTRACT_PACKAGE", "NO"],
                ["EXTRACT_STATIC", "YES"],
                ["EXTRACT_LOCAL_CLASSES", "YES"],
                ["EXTRACT_LOCAL_METHODS", "YES"],
                ["EXTRACT_ANON_NSPACES", "YES"],
                ["",""],
                ["RESOLVE_UNUSED_PARAMS", "YES"],
                ["",""],
                ["HIDE_UNDOC_MEMBERS", "NO"],
                ["HIDE_UNDOC_CLASSES", "NO"],
                ["HIDE_UNDOC_RELATIONS", "NO"],
                ["",""],
                ["HIDE_FRIEND_COMPOUNDS", "NO"],
                ["HIDE_IN_BODY_DOCS", "NO"],
                ["HIDE_SCOPE_NAMES", "NO"],
                ["HIDE_COMPOUND_REFERENCE", "NO"],
                ["",""],
                ["INTERNAL_DOCS", "YES"],
                ["",""],
                ["SHOW_HEADERFILE", "NO"],
                ["SHOW_INCLUDE_FILES", "NO"],
                ["SHOW_GROUPED_MEMB_INC", "NO"],
                ["",""],
                ["FORCE_LOCAL_INCLUDES", "NO"],
                ["",""],
                ["INLINE_INFO", "NO"],
                ["",""],
                ["SORT_MEMBER_DOCS", "YES"],
                ["SORT_BRIEF_DOCS", "YES"],
                ["SORT_MEMBERS_CTORS_IST", "NO"],
                ["SORT_GROUP_NAMES", "NO"],
                ["SORT_BY_SCOPE_NAME", "YES"],
                ["",""],
                ["STRICT_PROTO_MATCHING", "NO"],
                ["",""],
                ["GENERATE_TODO_LIST", "YES"],
                ["GENERATE_TESTLIST", "YES"],
                ["GENERATE_BUGLIST", "YES"],
                ["GENERATE_DEPRECATEDLIST", "YES"],
                ["",""],
                ["MAX_INITIALIZER_LINES", "30"],
                ["",""],
                ["SHOW_FILES", "NO"],
                ["SHOW_USED_FILES", "NO"],
                ["SHOW_NAMESPACES", "YES"],
                ["",""],
                ["FILE_VERSION_FILTER", ""],
                ["CITE_BIB_FILES", ""],
                ["",""],
                ["RECURSIVE", "NO"],
                ["",""],
                ["EXCLUDE", ""],
                ["EXCLUDE_SYMLINKS", "NO"],
                ["EXCLUDE_PATTERNS", ""],
                ["EXCLUDE_SYMBOLS", ""],
                ["",""],
                ["EXAMPLE_PATH", "./src/doc"],
                ["EXAMPLE_PATTERNS", "*"],
                ["EXAMPLE_RECURSIVE", "NO"],
                ["",""],
                ["IMAGE_PATH", ""],
                ["INPUT_FILTER", ""],
                ["",""],
                ["FILTER_PATTERNS", ""],
                ["FILTER_SOURCE_FILES", "NO"],
                ["FILTER_SOURCE_PATTERNS", ""],
                ["",""],
                ["USE_MDFILE_AS_MAINPAGE", ""],
                ["",""],
                ["SOURCE_BROWSER", "NO"],
                ["INLINE_SOURCES", "NO"],
                ["",""],
                ["STRIP_CODE_COMMENTS", "YES"],
                ["",""],
                ["REFERENCES_RELATION", "YES"],
                ["REFERENCES_LINK_SOURCE", "NO"],
                ["",""],
                ["SOURCE_TOOLTIPS", "NO"],
                ["USE_HTAGS", "NO"],
                ["VERBATIM_HEADERS", "NO"],
                ["",""],
                ["ALPHABETICAL_INDEX", "YES"],
                ["",""],
                ["IGNORE_PREFIX", ""],
                ["",""],
                ["ENUM_VALUES_PER_LINE", "4"],
                ["",""],
                ["HTML_FILE_EXTENSION", ".html"],
                ["HTML_CODE_FOLDING", "NO"],
                ["HTML_COPY_CLIPBOARD", "NO"],
                ["",""],
                ["HTML_HEADER", ""],
                ["HTML_FOOTER", "./src/doc/empty.html"],
                ["HTML_STYLESHEET", ""],
                ["",""],
                ["HTML_EXTRA_STYLESHEET", "./doxyfile.css"],
                ["HTML_EXTRA_FILES", ""],
                ["",""],
                ["HTML_COLORSTYLE_HUE", "220"],
                ["HTML_COLORSTYLE_SAT", "100"],
                ["HTML_COLORSTYLE_GAMMA", "80"],
                ["",""],
                ["HTML_DYNAMIC_MENUS", "NO"],
                ["HTML_DYNAMIC_SECTIONS", "NO"],
                ["",""],
                ["HTML_INDEX_NUM_ENTRIES", "100"],
                ["",""],
                ["TREEVIEW_WIDTH", "210"],
                ["",""],
                ["EXT_LINKS_IN_WINDOW", "NO"],
                ["OBFUSCATE_EMAILS", "YES"],
                ["",""],
                ["HAVE_DOT", "NO"],
                ["DOT_PATH", ""],
                ["DIA_PATH", ""],
                ["",""],
                ["DOT_COMMON_ATTR", "\"fontname=FreeSans,fontsize=10\""],
                ["DOT_EDGE_ATTR", "\"labelfontname=FreeSans,labelfontsize=10\""],
                ["DOT_NODE_ATTR", "\"shabe=box,height=0.2,width=0.4\""],
                ["DOT_FONTPATH", ""],
                ["",""],
                ["USE_MATHJAX", "NO"],
                ["",""],
                ["MATHJAX_VERSION", "MathJax_2"],
                ["MATHJAX_FORMAT", "HTML-CSS"],
                ["MATHJAX_RELPATH", ""],
                ["MATHJAX_EXTENSIONS", ""],
                ["MATHJAX_CODEFILE", ""],
                ["",""],
                ["HTML_FORMULA_FORMAT", "png"],
                ["",""],
                ["FORMULA_FONTSIZE", "10"],
                ["FORMULA_MACROFILE", ""],
                ["",""],
                ["SEARCH_ENGINE", "NO"],
                ["SERVER_BASED_SEARCH", "NO"],
                ["",""],
                ["EXTERNAL_SEARCH", "NO"],
                ["EXTERNAL_SEARCH_ID", "NO"],
                ["",""],
                ["EXTERNAL_GROUPS", "YES"],
                ["EXTERNAL_PAGES", "YES"],
                ["",""],
                ["GENERATE_AUTOGEN_DEF", "NO"],
                ["",""],
                ["ENABLE_PREPROCESSING", "YES"],
                ["MACRO_EXPANSION", "YES"],
                ["EXPAND_ONLY_PREDEF", "NO"],
                ["",""],
                ["SEARCH_INCLUDES", "NO"],
                ["",""],
                ["INCLUDE_PATH", ""],
                ["INCLUDE_FILE_PATTERNS", ""],
                ["",""],
                ["PREDEFINED", ""],
                ["EXPAND_AS_DEFINED", ""],
                ["SKIP_FUNCTION_MACROS", "YES"],
                ["",""],
                ["TAGFILES", ""],
                ["GENERATE_TAGFILE", ""],
                ["ALLEXTERNALS", "NO"],
                ["",""],
                ["CLASS_GRAPH", "YES"],
                ["COLLABORATION_GRAPH", "YES"],
                ["GROUP_GRAPHS", "YES"],
                ["",""],
                ["UML_LOOK", "NO"],
                ["UML_LIMIT_NUM_FIELDS", "10"],
                ["",""],
                ["DOT_UML_DETAILS", "NO"],
                ["DOT_WRAP_THRESHOLD", "17"],
                ["DOT_CLEANUP", "YES"],
                ["",""],
                ["TEMPLATE_RELATIONS", "YES"],
                ["",""],
                ["INCLUDE_GRAPH", "YES"],
                ["INCLUDED_BY_GRAPH", "YES"],
                ["",""],
                ["CALL_GRAPH", "NO"],
                ["CALLER_GRAPH", "NO"],
                ["",""],
                ["GRAPHICAL_HIERARCHY", "YES"],
                ["DIRECTORY_GRAPH", "YES"],
                ["DIR_GRAPH_MAX_DEPTH", "5"],
                ["",""],
                ["DOT_IMAGE_FORMAT", "png"],
                ["",""],
                ["DOT_GRAPH_MAX_NODES", "50"],
                ["MAX_DOT_GRAPH_DEPTH", "1000"],
                ["",""],
                ["GENERATE_LEGEND", "YES"]
            ]
            file_content_warn = [
                ["QUIET", "YES"],
                ["WARNINGS", "YES"],
                ["",""],
                ["WARN_IF_UNDOCUMENTED", "NO"],
                ["WARN_IF_UNDOC_ENUM_VAL", "NO"],
                ["WARN_IF_DOC_ERROR", "YES"],
                ["WARN_IF_INCOMPLETE_DOC", "YES"],
                ["WARN_AS_ERROR", "NO"],
                ["WARN_FORMAT", "\"$file:$line: $text\""],
                ["WARN_LINE_FORMAT", "\"at line $line of file $file\""],
                ["WARN_LOGFILE", "warnings.log"]
            ]
            with open(doxyfile, 'w') as file:
                file.write("# " + ("-" * 76) + "\n")
                file.write("# File: Doxyfile\n")
                file.write("# Author: (c) 2024 Jens Kallup - paule32 non-profit software\n")
                file.write("#"  + (" " *  9) + "all rights reserved.\n")
                file.write("#\n")
                file.write("# optimized for: # Doxyfile 1.10.1\n")
                file.write("# " + ("-" * 76) + "\n")
                
                for i in range(0, len(file_content)):
                    if len(file_content[i][0]) > 1:
                        file.write("{0:<32} = {1:s}\n".format( \
                        file_content[i][0],\
                        file_content[i][1]))
                    else:
                        file.write("\n")
                
                file.write("# " + ("-" * 76)   + "\n")
                file.write("# warning settings ...\n")
                file.write("# " + ("-" * 76)   + "\n")
                
                for i in range(0, len(file_content_warn)):
                    if len(file_content_warn[i][0]) > 1:
                        file.write("{0:<32} = {1:s}\n".format( \
                        file_content_warn[i][0],\
                        file_content_warn[i][1]))
                    else:
                        file.write("\n")
                
                file.close()
        
        # ---------------------------------------------------------
        # - open config file
        # - get the string from OUTPUT_DIRECTORY
        # - extract path
        # - convert seperator if under Windows
        # ---------------------------------------------------------
        html_out = os.path.join("./", "html")
        
        with open(doxyfile, 'r') as config_file:
            for line in config_file:
                if "OUTPUT_DIRECTORY" in line:
                    rows = line.split()
                    html_out = rows[2]
                    break
        
        if os_type == os_type_windows:
            html_out = html_out.replace("/", "\\")
        
        # ---------------------------------------------------------
        # !!! CAUTION !!!: data can be lost there.
        # ---------------------------------------------------------
        if os.path.exists(html_out):
            shutil.rmtree(html_out)
        
        os.makedirs(html_out, exist_ok = True)
        
        # ---------------------------------------------------------
        # now, we are ready to start our user interface ...
        # ---------------------------------------------------------
        if isApplicationInit() == False:
            app = QApplication(sys.argv)
        
        sv_help = customScrollView_help()
                
        appWindow = mainWindow()
        appWindow.show()
        result = appWindow.exec_()
        
        del appWindow  # free memory
        
        #result = app.exec_()
        sys.exit(result)
        
        # ---------------------------------------------------------
        # when all is gone, stop the running script ...
        # ---------------------------------------------------------
        print("Done.")
        sys.exit(EXIT_SUCCESS)

except ImportError as ex:
    print("error: import module missing: " + f"{ex}")
    sys.exit(EXIT_FAILURE)

# ----------------------------------------------------------------------------
# E O F  -  End - Of - File
# ----------------------------------------------------------------------------
