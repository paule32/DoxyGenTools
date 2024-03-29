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
    import json          # json lists
    
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
        + "no locales file for this application."
    
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
            if system_lang.lower() == __locale__enu:
                if lang.lower() == __locale__enu:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__enu])  # english
                elif lang.lower() == __locale__deu:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__deu])  # german
            elif system_lang.lower() == __locale__deu:
                if lang.lower() == __locale__deu:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__deu])  # english
                elif lang.lower() == __locale__enu:
                    tr = gettext.translation(
                    __app__name,
                    localedir=__locale__,
                    languages=[__locale__enu])  # german
            else:
                print("ennnn")
                tr = gettext.translation(
                __app__name,
                localedir=__locale__,
                languages=[__locale__enu])  # fallback - english
            
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
        
        def mousePressEvent(self, event):
            self.anchor = self.anchorAt(event.pos())
            if self.anchor:
                QApplication.setOverrideCursor(Qt.PointingHandCursor)
        
        def mouseReleaseEvent(self, event):
            if self.anchor:
                QDesktopServices.openUrl(QUrl(self.anchor))
                QApplication.setOverrideCursor(Qt.ArrowCursor)
                self.anchor = None
    
    class myCustomLabel(QLabel):
        def __init__(self, text, helpID, helpText):
            super().__init__(text)
            
            self.helpID   = helpID
            self.helpText = helpText
        
        def enterEvent(self, event):
            sv_help.setText(self.helpText)
        
        def mousePressEvent(self, event):
            self.anchor = self.anchorAt(event.pos())
            if self.anchor:
                QApplication.setOverrideCursor(Qt.PointingHandCursor)
        
        def mouseReleaseEvent(self, event):
            if self.anchor:
                QDesktopServices.openUrl(QUrl(self.anchor))
                QApplication.setOverrideCursor(Qt.ArrowCursor)
                self.anchor = None
    
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
            
            
            self.supported_langs= tr("supported_langs")
            
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
        
        def addElements(self, elements, hid):
            for i in range(0, len(elements)):
                lv_0 = QVBoxLayout()
                lh_0 = QHBoxLayout()
                
                # -----------------------------------------
                # the help string for a doxygen tag ...
                # -----------------------------------------
                helpID   = hid + i + 1
                helpText = tr(f"h{helpID:04X}")
                
                vw_1 = self.addHelpLabel(   \
                    elements[i][0], \
                    helpID,         \
                    helpText,       \
                    lh_0)
                vw_1.setMinimumHeight(14)
                vw_1.setMinimumWidth(200)
                
                if elements[i][1] == self.type_edit:
                    self.addLineEdit("",lh_0)
                                        
                    if elements[i][3] == 1:
                        self.addPushButton("+",lh_0)
                        
                    elif elements[i][3] == 3:
                        self.addPushButton("+",lh_0)
                        self.addPushButton("-",lh_0)
                        self.addPushButton("R",lh_0)
                        
                        vw_3 = myTextEdit()
                        vw_3.setFont(self.font_a)
                        vw_3.setMinimumHeight(96)
                        vw_3.setMaximumHeight(96)
                        lv_0.addWidget(vw_3)
                        
                elif elements[i][1] == self.type_check_box:
                    vw_2 = QCheckBox()
                    vw_2.setMinimumHeight(21)
                    vw_2.setFont(self.font_a)
                    vw_2.setChecked(elements[i][4])
                    lh_0.addWidget(vw_2)
                    
                elif elements[i][1] == self.type_combo_box:
                    vw_2 = QComboBox()
                    vw_2.setMinimumHeight(26)
                    vw_2.setFont(self.font)
                    vw_2.font().setPointSize(14)
                    lh_0.addWidget(vw_2)
                    
                    if elements[i][3] == 4:
                        data = json.loads(self.supported_langs)
                        elements[i][4] = data
                        for j in range(0, len(data)):
                            img = "flag_"       \
                            + elements[i][4][j] \
                            + ".png".lower()
                            vw_2.insertItem(0, elements[i][4][j])
                            vw_2.setItemIcon(0, QIcon(os.path.join(basedir,"img",img)))
                    
                    elif elements[i][3] == 2:
                        for j in range(0, len(elements[i][4])):
                            vw_2.addItem(elements[i][4][j])
                
                elif elements[i][1] == self.type_spin:
                    vw_2 = QSpinBox()
                    vw_2.setFont(self.font_a)
                    vw_2.setMinimumHeight(21)
                    lh_0.addWidget(vw_2)
                
                lv_0.addLayout(lh_0)
                self.layout.addLayout(lv_0)
    
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
                
                ["PROJECT_NAME",           self.type_edit,       101, 0, "My Project"],
                ["PROJECT_NUMBER",         self.type_edit,       102, 0],
                ["PROJECT_BRIEF",          self.type_edit,       103, 0],
                ["PROJECT_LOGO",           self.type_edit,       104, 1],
                ["PROJECT_ICON",           self.type_edit,       105, 1],
                
                ["OUTPUT_DIRECTORY",       self.type_edit,       106, 1],
                ["CREATE_SUBDIRS",         self.type_check_box,  107, 0, True],
                ["CREATE_SUBDIRS_LEVEL",   self.type_spin,       108, 0],
                
                ["ALLOW_UNICODE_NAMES",    self.type_check_box,  109, 0, False],
                ["OUTPUT_LANGUAGE",        self.type_combo_box,  110, 4, [] ],
                
                ["BRIEF_MEMBER_DESC",      self.type_check_box,  111, 0, True],
                ["REPEAT_BRIEF",           self.type_check_box,  112, 0, True],
                ["ABBREVIATE_BRIEF",       self.type_edit,       113, 3],
                ["ALWAYS_DETAILED_SEC",    self.type_check_box,  114, 0, True],
                ["INLINE_INHERITED_MEMB",  self.type_check_box,  115, 0, True],
                
                ["FULL_PATH_NAMES",        self.type_check_box,  116, 0, True],
                ["STRIP_FROM_PATH",        self.type_edit,       117, 3],
                ["STRIP_FROM_INC_PATH",    self.type_edit,       118, 3],
                
                ["SHORT_NAMES",            self.type_check_box,  119, 0, False],
                
                ["JAVADOC_AUTOBRIEF",      self.type_check_box,  120, 0, True ],
                ["JAVADOC_BANNER",         self.type_check_box,  121, 0, False],
                
                ["QT_AUTOBRIEF",           self.type_check_box,  122, 0, False],
                
                ["MULTILINE_CPP_IS_BRIEF", self.type_check_box,  123, 0, False],
                ["PYTHON_DOCSTRING",       self.type_check_box,  124, 0, True ],
                ["INHERITED_DOCS",         self.type_check_box,  125, 0, True ],
                ["SEPERATE_MEMBER_PAGES",  self.type_check_box,  126, 0, False],
                
                ["TAB_SIZE",               self.type_spin,       127, 0],
                ["ALIASES",                self.type_edit,       128, 3],
                
                ["OPTIMIZE_OUTPUT_FOR_C",  self.type_check_box,  129, 0, True ],
                ["OPTIMIZE_OUTPUT_JAVA",   self.type_check_box,  130, 0, False],
                ["OPTIMIZE_FOR_FORTRAN",   self.type_check_box,  131, 0, False],
                ["OPTIMIZE_OUTPUT_VHCL",   self.type_check_box,  132, 0, False],
                ["OPTIMIZE_OUTPUT_SLICE",  self.type_check_box,  133, 0, False],
                
                ["EXTERNAL_MAPPING",       self.type_edit,       134, 3],
                
                ["MARKDOWN_SUPPORT",       self.type_check_box,  135, 0, True ],
                ["MARKDOWN_ID_STYLE",      self.type_combo_box,  136, 2, ["DOXYGEN", "CIT"]],
                
                ["TOC_INCLUDE_HEADINGS",   self.type_spin,       137, 0],
                ["AUTOLINK_SUPPORT",       self.type_check_box,  138, 0, True ],
                
                ["BUILTIN_STL_SUPPORT",    self.type_check_box,  139, 0, True ],
                ["CPP_CLI_SUPPORT",        self.type_check_box,  140, 0, True ],
                ["SIP_SUPPORT",            self.type_check_box,  141, 0, False],
                ["IDL_PROPERTY_SUPPORT",   self.type_check_box,  142, 0, True ],
                
                ["DESTRIBUTE_GROUP_DOC",   self.type_check_box,  143, 0, False],
                ["GROUP_NESTED_COMPOUNDS", self.type_check_box,  144, 0, False],
                ["SUBGROUPING",            self.type_check_box,  145, 0, True ],
                
                ["INLINE_GROUPED_CLASSES", self.type_check_box,  146, 0, False],
                ["INLINE_SIMPLE_STRUCTS",  self.type_check_box,  147, 0, False],
                ["TYPEDEF_HIDES_STRUCT",   self.type_check_box,  148, 0, False],
                
                ["LOOKUP_CACHE_SIZE",      self.type_spin,       149, 0],
                ["NUM_PROC_THREADS",       self.type_spin,       150, 0],
                
                ["TIMESTAMP",              self.type_combo_box,  151, 2, ["NO","YES"]]
            ]
            self.addElements(label_1_elements, 0x100)
        
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
            self.content_widget.setMinimumHeight(1400)
            
            label_1_elements = [
                ["EXTRACT_ALL",              self.type_check_box, 0x200, 0, False ],
                ["EXTRACT_PRIVATE",          self.type_check_box, 0x201, 0, False ],
                ["EXTRACT_PRIV_VIRTUAL",     self.type_check_box, 0x202, 0, False ],
                ["EXTRACT_PACKAGE",          self.type_check_box, 0x203, 0, False ],
                ["EXTRACT_STATIC",           self.type_check_box, 0x204, 0, True  ],
                ["EXTRACT_LOCAL_CLASSES",    self.type_check_box, 0x205, 0, True  ],
                ["EXTRACT_LOCAL_METHODS",    self.type_check_box, 0x206, 0, True  ],
                ["EXTRACT_ANON_NSPACES",     self.type_check_box, 0x207, 0, True  ],
                ["RECURSIVE_UNNAMED_PARAMS", self.type_check_box, 0x208, 0, True  ],
                ["HIDE_UNDOC_MEMBERS",       self.type_check_box, 0x209, 0, False ],
                ["HIDE_UNDOC_CLASSES",       self.type_check_box, 0x20A, 0, False ],
                ["HIDE_FRIEND_COMPOUNDS",    self.type_check_box, 0x20B, 0, False ],
                ["HIDE_IN_BODY_DOCS",        self.type_check_box, 0x20C, 0, False ],
                ["INTERNAL_DOCS",            self.type_check_box, 0x20D, 0, True  ],
                
                ["CASE_SENSE_NAMES",         self.type_combo_box, 0x20E, 2, ["SYSTEM", "NO", "YES"] ],
                
                ["HIDE_SCOPE_NAMES",         self.type_check_box, 0x20E, 0, False ],
                ["HIDE_COMPOUND_REFERENCE",  self.type_check_box, 0x20F, 0, False ],
                
                ["SHOW_HEADERFILE",          self.type_check_box, 0x210, 0, True  ],
                ["SHOW_INCLUDE_FILES",       self.type_check_box, 0x210, 0, True  ],
                
                ["SHOW_GROUPED_MEMB_INC",    self.type_check_box, 0x210, 0, False ],
                ["FORCE_LOCAL_INCLUDES",     self.type_check_box, 0x210, 0, False ],
                ["INLINE_INFO",              self.type_check_box, 0x210, 0, False ],
                ["SORT_MEMBER_DOCS",         self.type_check_box, 0x210, 0, False ],
                ["SORT_BRIEF_DOCS",          self.type_check_box, 0x210, 0, False ],
                ["SORT_MEMBERS_CTORS_1ST",   self.type_check_box, 0x210, 0, False ],
                
                ["SORT_GROUP_NAMES",         self.type_check_box, 0x210, 0, False ],
                ["SORT_BY_SCOPE_NAME",       self.type_check_box, 0x210, 0, False ],
                ["STRICT_PROTO_MATCHING",    self.type_check_box, 0x210, 0, False ],
                
                ["GENERATE_TODOLIST",        self.type_check_box, 0x210, 0, False ],
                ["GENERATE_TESTLIST",        self.type_check_box, 0x210, 0, False ],
                ["GENERATE_BUGLIST",         self.type_check_box, 0x210, 0, False ],
                ["GENERATE_DEPRECATEDLIST",  self.type_check_box, 0x210, 0, False ],
                
                ["ENABLED_SECTIONS",         self.type_edit,      0x210, 3 ],
                ["MAX_INITIALIZER_LINES",    self.type_spin,      0x210, 0 ],
                
                ["SHOW_USED_FILES",          self.type_check_box, 0x210, 0, True  ],
                ["SHOW_FILES",               self.type_check_box, 0x210, 0, True  ],
                ["SHOW_NAMESPACES",          self.type_check_box, 0x210, 0, True  ],
                
                ["FILE_VERSION_FILTER",      self.type_edit,      0x210, 1 ],
                ["LAYOUT_FILE",              self.type_edit,      0x210, 1 ],
                ["CITE_BIB_FILES",           self.type_edit,      0x210, 3 ]
            ]
            self.addElements(label_1_elements, 0x200)
    
    class customScrollView_7(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["QUIET",                    self.type_check_box, 0x300, 0, True  ],
                ["WARNINGS",                 self.type_check_box, 0x200, 0, True  ],
                
                ["WARN_IF_UNDOCUMENTED",     self.type_check_box, 0x200, 0, False ],
                ["WARN_IF_DOC_ERROR",        self.type_check_box, 0x200, 0, True  ],
                ["WARN_IF_INCOMPLETE_DOC",   self.type_check_box, 0x200, 0, True  ],
                
                ["WARN_NO_PARAMDOC",         self.type_check_box, 0x200, 0, False ],
                ["WARN_IF_UNDOC_ENUM_VAL",   self.type_check_box, 0x200, 0, False ],
                
                ["WARN_AS_ERROR",            self.type_spin,      0x200, 0 ],
                
                ["WARN_FORMAT",              self.type_edit,      0x200, 0 ],
                ["WARN_LINE_FORMAT",         self.type_edit,      0x200, 0 ],
                ["WARN_LOGFILE",             self.type_edit,      0x200, 1 ]
            ]
            self.addElements(label_1_elements, 0x0300)
    
    class customScrollView_8(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(1700)
            
            label_1_elements = [
                ["INPUT",                  self.type_edit,      0x400, 3],
                ["INPUT_ENCODING",         self.type_edit,      0x400, 0],
                ["INPUT_FILE_ENCODING",    self.type_edit,      0x400, 1],
                ["FILE_PATTERNS",          self.type_edit,      0x400, 3],
                ["RECURSIVE",              self.type_check_box, 0x400, 0, True  ],
                ["EXCLUDE",                self.type_edit,      0x400, 3],
                ["EXCLUDE_SYMLINKS",       self.type_check_box, 0x400, 0, False ],
                ["EXCLUDE_PATTERNS",       self.type_edit,      0x400, 3],
                ["EXCLUDE_SYMBOLS",        self.type_edit,      0x400, 3],
                ["EXAMPLE_PATH",           self.type_edit,      0x400, 3],
                ["EXAMPLE_PATTERNS",       self.type_edit,      0x400, 3],
                ["EXAMPLE_RECURSIVE",      self.type_edit,      0x400, 0, False ],
                ["IMAGE_PATH",             self.type_edit,      0x400, 3],
                ["INPUT_FILTER",           self.type_edit,      0x400, 1],
                ["FILTER_PATTERNS",        self.type_edit,      0x400, 3],
                ["FILTER_SOURCE_FILES",    self.type_check_box, 0x400, 0, False ],
                ["FILTER_SOURCE_PATTERNS", self.type_edit,      0x400, 3],
                ["USE_MDFILE_AS_MAINPAGE", self.type_edit,      0x400, 0],
                ["FORTRAN_COMMENT_AFTER",  self.type_spin,      0x400, 0]
            ]
            self.addElements(label_1_elements, 0x0400)
    
    class customScrollView_9(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(560)
            
            label_1_elements = [
                ["SOURCE_BROWSER",          self.type_check_box, 0x500, 0, True  ],
                ["INLINE_SOURCES",          self.type_check_box, 0x200, 0, False ],
                ["STRIP_CODE_COMMENTS",     self.type_check_box, 0x200, 0, False ],
                
                ["REFERENCED_BY_RELATION",  self.type_check_box, 0x200, 0, True  ],
                ["REFERENCES_RELATION",     self.type_check_box, 0x200, 0, True  ],
                ["REFERENCES_LINK_SOURCE",  self.type_check_box, 0x200, 0, True  ],
                
                ["SOURCE_TOOLTIPS",         self.type_check_box, 0x200, 0, True  ],
                ["USE_HTAGS",               self.type_check_box, 0x200, 0, False ],
                ["VERBATIM_HEADERS",        self.type_check_box, 0x200, 0, True  ],
                
                ["CLANG_ASSISTED_PARSING",  self.type_check_box, 0x200, 0, False ],
                ["CLANG_ADD_INC_PATHS",     self.type_check_box, 0x200, 0, False ],
                ["CLANG_OPTIONS",           self.type_edit     , 0x200, 3 ],
                ["CLANG_DATABASE_PATH",     self.type_edit     , 0x200, 1 ]
            ]
            self.addElements(label_1_elements, 0x0500)
    
    class customScrollView_10(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["ALPHABETICAL_INDEX", self.type_check_box, 0x600, 0, True ],
                ["IGNORE_PREFIX",      self.type_edit,      0x601, 3 ]
            ]
            self.addElements(label_1_elements, 0x0600)
    
    class customScrollView_11(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(2380)
            
            label_1_elements = [
                ["GENERATE_HTML",          self.type_check_box, 0x200, 0, True  ],
                ["HTML_OUTPUT",            self.type_edit,      0x200, 1 ],
                ["HTML_FILE_EXTENSION",    self.type_edit,      0x200, 0 ],
                
                ["HTML_HEADER",            self.type_edit,      0x200, 1 ],
                ["HTML_FOOTER",            self.type_edit,      0x200, 1 ],
                
                ["HTML_STYLESHEET",        self.type_edit,      0x200, 1 ],
                ["HTML_EXTRA_STYLESHEET",  self.type_edit,      0x200, 3 ],
                ["HTML_EXTRA_FILES",       self.type_edit,      0x200, 3 ],
                
                ["HTML_COLORSTYLE",        self.type_combo_box, 0x200, 2, [ "LIGHT", "DARK", "AUTO_LIGHT", "AUTO_DARK", "TOOGLE" ] ],
                ["HTML_COLORSTYLE_HUE",    self.type_spin,      0x200, 0 ],
                ["HTML_COLORSTYLE_SAT",    self.type_spin,      0x200, 0 ],
                ["HTML_COLORSTYLE_GAMMA",  self.type_spin,      0x200, 0 ],
                ["HTML_DYNAMIC_MENUS",     self.type_check_box, 0x200, 0, True  ],
                ["HTML_DYNAMIC_SECTIONS",  self.type_check_box, 0x200, 0, False ],
                
                ["HTML_CODE_FOLDING",      self.type_check_box, 0x200, 0, True  ],
                ["HTML_COPY_CLIPBOARD",    self.type_check_box, 0x200, 0, True  ],
                ["HTML_PROJECT_COOKIE",    self.type_edit,      0x200, 0 ],
                ["HTML_INDEX_NUM_ENTRIES", self.type_spin,      0x200, 0 ],
                
                ["GENERATE_DOCSET",        self.type_check_box, 0x200, 0, False ],
                ["DOCSET_FEEDNAME",        self.type_edit,      0x200, 0 ],
                ["DOCSET_FEEDURL",         self.type_edit,      0x200, 0 ],
                ["DOCSET_BUNDLE_ID",       self.type_edit,      0x200, 0 ],
                ["DOCSET_PUBLISHER_ID",    self.type_edit,      0x200, 0 ],
                ["DOCSET_PUBLISHER_NAME",  self.type_edit,      0x200, 0 ],
                
                ["GENERATE_HTMLHELP",      self.type_check_box, 0x200, 0, True  ],
                ["CHM_FILE",               self.type_edit,      0x200, 1 ],
                ["HHC_LOCATION",           self.type_edit,      0x200, 1 ],
                ["GENERATE_CHI",           self.type_check_box, 0x200, 0, False ],
                ["CHM_INDEX_ENCODING",     self.type_edit,      0x200, 0 ],
                ["BINARY_TOC",             self.type_check_box, 0x200, 0, False ],
                ["TOC_EXPAND",             self.type_check_box, 0x200, 0, False ],
                ["SITEMAP_URL",            self.type_edit,      0x200, 0 ],
                
                ["GENERATE_QHP",           self.type_check_box, 0x200, 0, False ],
                ["QCH_FILE",               self.type_edit,      0x200, 1 ],
                ["QHP_VIRTUAL_FOLDER",     self.type_edit,      0x200, 0 ],
                ["QHP_CUST_FILTER_NAME",   self.type_edit,      0x200, 0 ],
                ["QHP_CUST_FILTER_ATTRS",  self.type_edit,      0x200, 0 ],
                ["QHP_SECT_FILTER_ATTRS",  self.type_edit,      0x200, 0 ],
                ["QHG_LOCATION",           self.type_edit,      0x200, 1 ],
                
                ["GENERATE_ECLIPSEHELP",   self.type_check_box, 0x200, 0, False ],
                ["ECLIPSE_DOC_ID",         self.type_edit,      0x200, 0 ],
                ["DISABLE_INDEX",          self.type_check_box, 0x200, 0, False ],
                
                ["GENERATE_TREEVIEW",      self.type_check_box, 0x200, 0, True  ],
                ["FULL_SIDEBAR",           self.type_check_box, 0x200, 0, False ],
                
                ["ENUM_VALUES_PER_LINE",   self.type_spin,      0x200, 0 ],
                ["TREEVIEW_WIDTH",         self.type_spin,      0x200, 0 ],
                
                ["EXT_LINKS_IN_WINDOW",    self.type_check_box, 0x200, 0, False ],
                ["OBFUSCATE_EMAILS",       self.type_check_box, 0x200, 0, True  ],
                
                ["HTML_FORMULA_FORMAT",    self.type_combo_box, 0x200, 2, [ "png", "svg" ] ],
                ["FORMULA_FONTSIZE",       self.type_spin,      0x200, 0 ],
                ["FORMULA_MACROFILE",      self.type_edit,      0x200, 1 ],
                
                ["USE_MATHJAX",            self.type_check_box, 0x200, 0, False ],
                ["MATHJAX_VERSION",        self.type_combo_box, 0x200, 2, [ "MathJax_2", "MathJax_3" ] ],
                ["MATHJAX_FORMAT",         self.type_combo_box, 0x200, 2, [ "HTML + CSS", "NativeXML", "chtml", "SVG" ] ],
                
                ["MATHJAX_RELPATH",        self.type_edit,      0x200, 1 ],
                ["MATHJAX_EXTENSIONS",     self.type_edit,      0x200, 3 ],
                ["MATHJAX_CODEFILE",       self.type_edit,      0x200, 0 ],
                
                ["SEARCHENGINE",           self.type_check_box, 0x200, 0, False ],
                ["SERVER_BASED_SEARCH",    self.type_check_box, 0x200, 0, False ],
                ["EXTERNAL_SEARCH",        self.type_check_box, 0x200, 0, False ],
                ["SEARCHENGINE_URL",       self.type_edit,      0x200, 0 ],
                ["SEARCHDATA_FILE",        self.type_edit,      0x200, 1 ],
                ["EXTERNAL_SEARCH_ID",     self.type_edit,      0x200, 0 ],
                ["EXTRA_SEARCH_MAPPINGS",  self.type_edit,      0x200, 3 ]
            ]
            self.addElements(label_1_elements, 0x0700)
    
    class customScrollView_12(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(1000)
            
            label_1_elements = [
                ["GENERATE_LATEX",          self.type_check_box, 0x200, 0, False ],
                ["LATEX_OUTPUT",            self.type_edit,      0x200, 1 ],
                ["LATEX_CMD_NAMET",         self.type_edit,      0x200, 1 ],
                ["LATEX_MAKEINDEX_CMDT",    self.type_edit,      0x200, 0 ],
                ["COMPACT_LATEX",           self.type_check_box, 0x200, 0, False ],
                ["PAPER_TYPE",              self.type_combo_box, 0x200, 2, [ "a4", "letter", "executive" ] ],
                ["EXTRA_PACKAGES",          self.type_edit,      0x200, 3 ],
                ["LATEX_HEADER",            self.type_edit,      0x200, 1 ],
                ["LATEX_FOOTER",            self.type_edit,      0x200, 1 ],
                ["LATEX_EXTRA_STYLESHEET",  self.type_edit,      0x200, 3 ],
                ["LATEX_EXTRA_FILES",       self.type_edit,      0x200, 3 ],
                ["PDF_HYPERLINKS",          self.type_check_box, 0x200, 0, True  ],
                ["USE_PDFLATEX",            self.type_check_box, 0x200, 0, True  ],
                ["LATEX_BATCHMODE",         self.type_combo_box, 0x200, 2, [ "NO", "YWS", "BATCH", "NON-STOP", "SCROLL", "ERROR_STOP" ] ],
                ["LATEX_HIDE_INDICES",      self.type_check_box, 0x200, 0, False ],
                ["LATEX_BIB_STYLE",         self.type_edit,      0x200, 0 ],
                ["LATEX_EMOJI_DIRECTORY",   self.type_edit,      0x200, 1 ]
            ]
            self.addElements(label_1_elements, 0x0800)
    
    class customScrollView_13(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["GENERATE_RTF",         self.type_check_box, 0x200, 0, False ],
                ["RTF_OUTPUT",           self.type_edit,      0x200, 1 ],
                ["COMPACT_RTF",          self.type_check_box, 0x200, 0, False ],
                ["RTF_HYPERLINKS",       self.type_check_box, 0x200, 0, False ],
                ["RTF_STYLESHEET_FILE",  self.type_edit,      0x200, 1 ],
                ["RTF_EXTENSIONS_FILE",  self.type_edit,      0x200, 1 ]
            ]
            self.addElements(label_1_elements, 0x0900)
    
    class customScrollView_14(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["GENERATE_MAN",   self.type_check_box, 0x200, 0, False ],
                ["MAN_OUTPUT",     self.type_edit,      0x200, 1 ],
                ["MAN_EXTENSION",  self.type_edit,      0x200, 0 ],
                ["MAN_SUBDIR",     self.type_edit,      0x200, 0 ],
                ["MAN_LINKS",      self.type_check_box, 0x200, 0, False ],
            ]
            self.addElements(label_1_elements, 0x0A00)
    
    class customScrollView_15(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["GENERATE_XML",            self.type_check_box, 0x200, 0, False ],
                ["XML_OUTPUT",              self.type_edit,      0x200, 1 ],
                ["XML_PROGRAMLISTING",      self.type_check_box, 0x200, 0, False ],
                ["XML_NS_MEMB_FILE_SCOPE",  self.type_check_box, 0x200, 0, False ]
            ]
            self.addElements(label_1_elements, 0x0B00)
    
    class customScrollView_16(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(1400)
            
            label_1_elements = [
                ["GENERATE_DOCBOOK",  self.type_check_box, 0x200, 0, False ],
                ["DOCBOOK_OUTPUT",    self.type_edit,      0x200, 1 ],
            ]
            self.addElements(label_1_elements, 0x0C00)
    
    class customScrollView_17(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["GENERATE_AUTOGEN_DEF",  self.type_check_box, 0x200, 0, False ]
            ]
            self.addElements(label_1_elements, 0x0D00)
    
    class customScrollView_18(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["GENERATE_SQLITE3",     self.type_check_box, 0x200, 0, False ],
                ["SQLITE3_OUTPUT",       self.type_edit,      0x200, 1 ],
                ["SQLITE3_RECREATE_DB",  self.type_check_box, 0x200, 0, True  ],
            ]
            self.addElements(label_1_elements, 0x0E00)
    
    class customScrollView_19(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["GENERATE_PERLMOD",        self.type_check_box, 0x200, 0, False ],
                ["PERLMOD_LATEX",           self.type_check_box, 0x200, 0, False ],
                ["PERLMOD_PRETTY",          self.type_check_box, 0x200, 0, False ],
                ["PERLMOD_MAKEVAR_PREFIX",  self.type_edit,      0x200, 1 ]
            ]
            self.addElements(label_1_elements, 0x0F00)
    
    class customScrollView_20(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(800)
            
            label_1_elements = [
                ["ENABLE_PREPROCESSING",   self.type_check_box, 0x200, 0, True  ],
                ["MACRO_EXPANSION",        self.type_check_box, 0x200, 0, True  ],
                ["EXPAND_ONLY_PREDEF",     self.type_check_box, 0x200, 0, False ],
                ["SEARCH_INCLUDES",        self.type_check_box, 0x200, 0, False ],
                ["INCLUDE_PATH",           self.type_edit,      0x200, 3 ],
                ["INCLUDE_FILE_PATTERNS",  self.type_edit,      0x200, 3 ],
                ["PREDEFINED",             self.type_edit,      0x200, 3 ],
                ["EXPAND_AS_DEFINED",      self.type_edit,      0x200, 3 ],
                ["SKIP_FUNCTION_MACROS",   self.type_check_box, 0x200, 0, True  ]
            ]
            self.addElements(label_1_elements, 0x1000)
    
    class customScrollView_21(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(400)
            
            label_1_elements = [
                ["TAGFILES",          self.type_edit, 0x200, 3 ],
                ["GENERATE_TAGFILE",  self.type_edit, 0x200, 1 ],
                ["ALLEXTERNALS",      self.type_check_box, 0x200, 0, False ],
                ["EXTERNAL_GROUPS",   self.type_check_box, 0x200, 0, True  ],
                ["EXTERNAL_PAGES",    self.type_check_box, 0x200, 0, True  ]
            ]
            self.addElements(label_1_elements, 0x1100)
    
    class customScrollView_22(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(1600)
            
            label_1_elements = [
                ["HIDE_UNDOC_RELATIONS",   self.type_check_box, 0x200, 0, False ],
                ["HAVE_DOT",               self.type_check_box, 0x200, 0, False ],
                ["DOT_NUM_THREADS",        self.type_spin     , 0x200, 0 ],
                
                ["DOT_COMMON_ATTR",        self.type_edit, 0x200, 0 ],
                ["DOT_EDGE_ATTR",          self.type_edit, 0x200, 0 ],
                ["DOT_NODE_ATTR",          self.type_edit, 0x200, 0 ],
                ["DOT_FONTPATH",           self.type_edit, 0x200, 1 ],
                
                ["CLASS_GRAPH",            self.type_combo_box, 0x200, 2, [ "YES", "NO" ] ],
                ["COLLABORATION_GRAPH",    self.type_check_box, 0x200, 0, True  ],
                ["GROUP_GRAPHS",           self.type_check_box, 0x200, 0, True  ],
                ["UML_LOOK",               self.type_check_box, 0x200, 0, False ],
                ["UML_LIMIT_NUM_FIELDS",   self.type_spin     , 0x200, 0 ],
                ["DOT_UML_DETAILS",        self.type_combo_box, 0x200, 2, [ "NO", "YES" ] ],
                ["DOT_WRAP_THRESHOLD",     self.type_spin     , 0x200, 0 ],
                
                ["TEMPLATE_RELATIONS",     self.type_check_box, 0x200, 0, False ],
                ["INCLUDE_GRAPH",          self.type_check_box, 0x200, 0, False ],
                ["INCLUDED_BY_GRAPH",      self.type_check_box, 0x200, 0, False ],
                ["CALL_GRAPH",             self.type_check_box, 0x200, 0, False ],
                ["CALLER_GRAPH",           self.type_check_box, 0x200, 0, False ],
                ["IGRAPHICAL_HIERARCHY",   self.type_check_box, 0x200, 0, False ],
                ["DIRECTORY_GRAPH",        self.type_check_box, 0x200, 0, False ],
                
                ["DIR_GRAPH_MAX_DEPTH",    self.type_spin     , 0x200, 0 ],
                ["DOT_IMAGE_FORMAT",       self.type_combo_box, 0x200, 2, [ "png", "svg" ] ],
                
                ["INTERACTIVE_SVG",        self.type_check_box, 0x200, 0, False ],
                
                ["DOT_PATH",               self.type_edit     , 0x200, 1 ],
                ["DOTFILE_DIRS",           self.type_edit     , 0x200, 3 ],
                
                ["DIA_PATH",               self.type_edit     , 0x200, 1 ],
                ["DIAFILE_DIRS",           self.type_edit     , 0x200, 3 ],
                
                ["PLANTUML_JAR_PATH",      self.type_edit     , 0x200, 1 ],
                ["PLANTUML_CFG_FILE",      self.type_edit     , 0x200, 1 ],
                ["PLANTUML_INCLUDE_PATH",  self.type_edit     , 0x200, 3 ],
                
                ["DOT_GRAPH_MAX_NODES",    self.type_spin     , 0x200, 0 ],
                ["MAX_DOT_GRAPH_DEPTH",    self.type_spin     , 0x200, 0 ],
                
                ["DOT_MULTI_TARGETS",      self.type_check_box, 0x200, 0, False ],
                ["GENERATE_LEGEND",        self.type_check_box, 0x200, 0, False ],
                ["DOT_CLEANUP",            self.type_check_box, 0x200, 0, True  ],
                ["MSCGEN_TOOL",            self.type_edit     , 0x200, 1 ],
                ["MSCFILE_DIRS",           self.type_edit     , 0x200, 3 ]
            ]
            self.addElements(label_1_elements, 0x1200)
    
    class customScrollView_23(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(1400)
            
            label_1_elements = [
                ["EXTRACT_ALL",              self.type_check_box, 0x200, 0, False ],
            ]
            self.addElements(label_1_elements, 0x1300)
    
    class customScrollView_24(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(1400)
            
            label_1_elements = [
                ["EXTRACT_ALL",              self.type_check_box, 0x200, 0, False ],
            ]
            self.addElements(label_1_elements, 0x1400)
    
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
            menubar.setStyleSheet(tr(menu_item_style))
            
            menu_file = menubar.addMenu("File")
            menu_edit = menubar.addMenu("Edit")
            menu_help = menubar.addMenu("Help")
            
            menu_font = menu_file.font()
            menu_font.setPointSize(11)
            
            menu_file.setFont(menu_font)
            menu_edit.setFont(menu_font)
            menu_help.setFont(menu_font)
            
            menu_file.setContentsMargins(0,0,0,0)
            
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
            menu_file.setStyleSheet("background-color:navy;")
            
            # ----------------------------------------
            # help menu action's ...
            # ----------------------------------------
            menu_help_about   = QWidgetAction(menu_help)
            
            menu_style_bg = "background-color:navy;"
            menu_file.setStyleSheet(menu_style_bg)
            menu_help.setStyleSheet(menu_style_bg)
            
            menu_label_style = tr("menu_label_style")
            
            menu_help_widget = QWidget()
            menu_help_layout = QHBoxLayout(menu_help_widget)
            #
            menu_help_about_icon = QWidget()
            menu_help_about_icon.setFixedWidth(26)
            menu_help_about_icon.setContentsMargins(0,0,0,0)
            #
            menu_help_about_label = QLabel("About...")
            menu_help_about_label.setContentsMargins(0,0,0,0)
            menu_help_about_label.setStyleSheet(menu_label_style)
            menu_help_about_label.setMinimumWidth(160)
            #
            menu_help_about_shortcut = QLabel("F1")
            menu_help_about_shortcut.setContentsMargins(0,0,0,0)
            menu_help_about_shortcut.setMinimumWidth(100)
            menu_help_about_shortcut.setStyleSheet(tr("menu_item"))
            
            menu_help_layout.addWidget(menu_help_about_icon)
            menu_help_layout.addWidget(menu_help_about_label)
            menu_help_layout.addWidget(menu_help_about_shortcut)
            
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
            menu_label_1.setContentsMargins(0,0,0,0)
            menu_label_1.setStyleSheet(menu_label_style)
            menu_label_1.setMinimumWidth(160)
            menu_label_1_shortcut = QLabel("Ctrl-N")
            menu_label_1_shortcut.setContentsMargins(0,0,0,0)
            menu_label_1_shortcut.setMinimumWidth(100)
            menu_label_1_shortcut.setStyleSheet(tr("menu_item"))
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
            menu_label_2_shortcut.setStyleSheet(tr("menu_item"))
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
            menu_label_3_shortcut.setStyleSheet(tr("menu_item"))
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
            
            menu_help_about.setDefaultWidget(menu_help_widget)
            
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
            
            menu_help_about.triggered.connect(self.menu_help_clicked_about)
            menu_help.addAction(menu_help_about)
            
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
        
        def menu_help_clicked_about(self):
            showInfo("" \
            + "DOXYGEN wrapper 1.0\n"               \
            + "(c) 2024 by Jens Kallup - paule32\n" \
            + "all rights reserved.")
    
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
            textfield.setPlainText(tr("LICENSE"))
        
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
                + "language = en_us\n"
                output_file.write(content)
                output_file.close()
                ini_lang = "en_us" # default is english; en_us
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
        
        print("po: " + po_file_name)
        if not os.path.exists(convertPath(po_file_name)):
            if isPythonWindows() == True:
                showApplicationInformation(__error__locales_error)
                sys.exit(EXIT_FAILURE)
            else:
                print(__error__locales_error)
                sys.exit(EXIT_FAILURE)
        
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
