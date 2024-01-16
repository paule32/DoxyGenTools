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
    
    # ------------------------------------------------------------------------
    # branding water marks ...
    # ------------------------------------------------------------------------
    __version__ = "Version 0.0.1"
    __authors__ = "paule32"

    __date__    = "2024-01-04"
    
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
                    loca = gettext.translation(__app__name, localedir=__locale__, languages=[__locale__enu[:2]])  # english
                 if lang.lower() == __locale__deu[:2]:
                    loca = gettext.translation(__app__name, localedir=__locale__, languages=[__locale__deu[:2]])  # german
            elif system_lang.lower() == __locale__deu:
                 if lang.lower() == __locale__enu[:2]:
                    loca = gettext.translation(__app__name, localedir=__locale__, languages=[__locale__enu[:2]])  # english
                 if lang.lower() == __locale__deu[:2]:
                    loca = gettext.translation(__app__name, localedir=__locale__, languages=[__locale__deu[:2]])  # german
            else:
                    loca = gettext.translation(__app__name, localedir=__locale__, languages=[__locale__enu[:2]])  # fallback
            
            loca.install()
            return loca
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
    # create a scroll view for the project tab on left side of application ...
    # ------------------------------------------------------------------------
    class customScrollView_1(QScrollArea):
        def __init__(self, name):
            super().__init__()
            
            self.__button_style_css = "" \
            + "QPushButton { border-radius: 3px;" \
            + "background: #012d8c;" \
            + "background-image: linear-gradient(to bottom, #185d8c, #2980b9);" \
            + "font-family: Arial;" \
            + "color: #f7ff03;" \
            + "font-size: 11pt;" \
            + "padding: 10px 20px 10px 20px;" \
            + "text-decoration: none;" \
            + "}" \
            + "QPushButton::hover { background: #183b91;" \
            + "background-image: linear-gradient(to bottom, #183b91, #5145bf); "\
            + "text-decoration: none;}"
            self.name = name
            
            self.init_ui()
        
        def init_ui(self):
            content_widget = QWidget(self)
            layout = QVBoxLayout(content_widget)
            
            font = QFont("Arial")
            font.setPointSize(10)
            
            widget_1_label_1 = QLabel("Provide some informations about the Project you are documenting")
            widget_1_label_1.setMinimumWidth(600)
            widget_1_label_1.setFont(font)
            layout.addWidget(widget_1_label_1)
            
            layout_2 = QHBoxLayout()
            widget_2_label_1 = QLabel("Project name:")
            widget_2_label_1.setMinimumWidth(160)
            widget_2_label_1.setMaximumWidth(220)
            widget_2_label_1.setFont(font)
            widget_2_texte_1 = QLineEdit()
            widget_2_texte_1.setMinimumWidth(280)
            widget_2_texte_1.setFont(font)
            layout_2.addWidget(widget_2_label_1)
            layout_2.addWidget(widget_2_texte_1)
            layout.addLayout(layout_2)
            
            layout_3 = QHBoxLayout()
            widget_3_label_1 = QLabel("Project author:")
            widget_3_label_1.setMinimumWidth(160)
            widget_3_label_1.setMaximumWidth(220)
            widget_3_label_1.setFont(font)
            widget_3_texte_1 = QLineEdit()
            widget_3_texte_1.setMinimumWidth(280)
            widget_3_texte_1.setFont(font)
            layout_3.addWidget(widget_3_label_1)
            layout_3.addWidget(widget_3_texte_1)
            layout.addLayout(layout_3)
            
            layout_4 = QHBoxLayout()
            widget_4_label_1 = QLabel("Project version or id:")
            widget_4_label_1.setMinimumWidth(160)
            widget_4_label_1.setMaximumWidth(220)
            widget_4_label_1.setFont(font)
            widget_4_texte_1 = QLineEdit()
            widget_4_texte_1.setMinimumWidth(280)
            widget_4_texte_1.setFont(font)
            layout_4.addWidget(widget_4_label_1)
            layout_4.addWidget(widget_4_texte_1)
            layout.addLayout(layout_4)
            
            layout_4 = QHBoxLayout()
            widget_4_label_1 = QLabel("Project logo:")
            widget_4_label_1.setAlignment(Qt.AlignLeft)
            widget_4_label_1.setFont(font)
            widget_4_pushb_1 = QPushButton("Select")
            widget_4_pushb_1.setMinimumHeight(32)
            widget_4_pushb_1.setMinimumWidth(84)
            widget_4_pushb_1.setMaximumWidth(84)
            widget_4_pushb_1.setFont(font)
            widget_4_licon_1 = QLabel(self)
            widget_4_licon_1.setPixmap(QIcon("img/floppy-disk.png").pixmap(42,42))
            layout_4.addWidget(widget_4_label_1)
            layout_4.addWidget(widget_4_pushb_1)
            layout_4.addWidget(widget_4_licon_1)
            layout.addLayout(layout_4)
            
            layout_5 = QHBoxLayout()
            widget_5_frame_1 = QFrame()
            widget_5_frame_1.setFrameShape(QFrame.HLine)
            widget_5_frame_1.setFrameShadow(QFrame.Sunken)
            layout_5.addWidget(widget_5_frame_1)
            layout.addLayout(layout_5)
            
            layout_6 = QHBoxLayout()
            widget_6_label_1 = QLabel("Source dir:")
            widget_6_label_1.setMinimumWidth(120)
            widget_6_label_1.setMaximumWidth(120)
            widget_6_label_1.setFont(font)
            widget_6_texte_1 = QLineEdit()
            font.setBold(True)
            widget_6_texte_1.setMinimumWidth(120)
            widget_6_texte_1.setFont(font)
            widget_6_texte_1.setText("E:\\temp\\src")
            widget_6_pushb_1 = QPushButton("Select")
            widget_6_pushb_1.setMinimumHeight(40)
            widget_6_pushb_1.setMaximumHeight(40)
            widget_6_pushb_1.setMinimumWidth(84)
            widget_6_pushb_1.setMaximumWidth(84)
            widget_6_pushb_1.setFont(font)
            layout_6.addWidget(widget_6_label_1)
            layout_6.addWidget(widget_6_texte_1)
            layout_6.addWidget(widget_6_pushb_1)
            layout.addLayout(layout_6)
            
            layout_7 = QHBoxLayout()
            font.setBold(False)
            widget_7_label_1 = QLabel("Destination dir:")
            widget_7_label_1.setMinimumWidth(120)
            widget_7_label_1.setMaximumWidth(120)
            widget_7_label_1.setFont(font)
            widget_7_texte_1 = QLineEdit()
            font.setBold(True)
            widget_7_texte_1.setMinimumWidth(180)
            widget_7_texte_1.setFont(font)
            widget_7_texte_1.setText("E:\\temp\\src\\html")
            widget_7_pushb_1 = QPushButton("Select")
            widget_7_pushb_1.setMinimumHeight(40)
            widget_7_pushb_1.setMaximumHeight(40)
            widget_7_pushb_1.setMinimumWidth(84)
            widget_7_pushb_1.setMaximumWidth(84)
            widget_7_pushb_1.setFont(font)
            layout_7.addWidget(widget_7_label_1)
            layout_7.addWidget(widget_7_texte_1)
            layout_7.addWidget(widget_7_pushb_1)
            layout.addLayout(layout_7)
            
            layout_8 = QHBoxLayout()
            widget_8_frame_1 = QFrame()
            widget_8_frame_1.setFrameShape(QFrame.HLine)
            widget_8_frame_1.setFrameShadow(QFrame.Sunken)
            layout_8.addWidget(widget_8_frame_1)
            layout.addLayout(layout_8)
            
            layout_9 = QHBoxLayout()
            widget_9_checkbutton_1 = QCheckBox("Scan recursive")
            widget_9_checkbutton_1.setFont(font)
            layout_9.addWidget(widget_9_checkbutton_1)
            layout.addLayout(layout_9)
            
            
            
            btn_1 = QPushButton("Convert")
            btn_1.setStyleSheet(self.__button_style_css)
            
            btn_1.clicked.connect(self.btn_clicked_1)
            
            btn_1.setMinimumWidth  = 100
            btn_1.setMinimumHeight = 26
            
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimumWidth = 100
            self.progress_bar.setMinimumHeight = 24
            
            btn_2 = QPushButton("Compile")
            btn_2.setStyleSheet(self.__button_style_css)
            
            btn_2.clicked.connect(self.btn_clicked_2)
            
            btn_2.setMinimumWidth  = 100
            btn_2.setMinimumHeight = 26
            
            
            btn_3 = QPushButton("HelpNDoc")
            btn_3.setStyleSheet(self.__button_style_css)
            
            btn_3.clicked.connect(self.btn_clicked_3)
            
            btn_3.setMinimumWidth  = 100
            btn_3.setMinimumHeight = 26
            
            layout.addWidget(btn_1)
            layout.addWidget(btn_2)
            layout.addWidget(self.progress_bar)
            layout.addWidget(btn_3)
            
            
            
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
    
    # ------------------------------------------------------------------------
    # create a scroll view for the mode tab on left side of application ...
    # ------------------------------------------------------------------------
    class myCustomScrollArea(QScrollArea):
        def __init__(self, name):
            super().__init__()
            
            self.name = name
            self.font = QFont("Arial")
            self.font.setPointSize(10)
            
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
    
    class customScrollView_2(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            
            label_2 = QLabel("Select a desired extraction mode:")
            self.font.setBold(True);   label_2.setFont(self.font)
            self.font.setBold(False)
            label_2.setMinimumHeight(30)
            label_2.setMinimumWidth(200)
            
            radio_button_1 = QRadioButton("Documentet entries only")
            radio_button_2 = QRadioButton("All entries")
            check_box      = QCheckBox("Include cross referenced source code in the output:")
            
            radio_button_1.setFont(self.font)
            radio_button_2.setFont(self.font)
            check_box     .setFont(self.font)
            
            frame_1 = QFrame()
            frame_1.setFrameShape (QFrame.HLine)
            frame_1.setFrameShadow(QFrame.Sunken)
            
            self.layout.addWidget(label_2)
            self.layout.addWidget(radio_button_1)
            self.layout.addWidget(radio_button_2)
            self.layout.addWidget(check_box)
            self.layout.addWidget(frame_1)
            
            label_3 = QLabel("Select programming language to optimize the results for:")
            self.font.setBold(True); label_3.setFont(self.font)
            self.font.setBold(False)
            
            radio_button_3_1 = QRadioButton("Optimize for C++ output")
            radio_button_3_1.setFont(self.font)
            radio_button_3_2 = QRadioButton("Optimize for C++ / CLI output")
            radio_button_3_2.setFont(self.font)
            radio_button_3_3 = QRadioButton("Optimize for Java or C-Sharp / C# output")
            radio_button_3_3.setFont(self.font)
            radio_button_3_4 = QRadioButton("Optimize for C or PHP output")
            radio_button_3_4.setFont(self.font)
            radio_button_3_5 = QRadioButton("Optimize for Fortran output")
            radio_button_3_5.setFont(self.font)
            radio_button_3_6 = QRadioButton("Optimize for VHCL output")
            radio_button_3_6.setFont(self.font)
            radio_button_3_7 = QRadioButton("Optimize for SLICE output")
            radio_button_3_7.setFont(self.font)
            
            self.layout.addWidget(label_3)
            self.layout.addWidget(radio_button_3_1)
            self.layout.addWidget(radio_button_3_2)
            self.layout.addWidget(radio_button_3_3)
            self.layout.addWidget(radio_button_3_4)
            self.layout.addWidget(radio_button_3_5)
            self.layout.addWidget(radio_button_3_6)
            self.layout.addWidget(radio_button_3_7)
    
    # ------------------------------------------------------------------------
    # create a scroll view for the output tab on left side of application ...
    # ------------------------------------------------------------------------
    class customScrollView_3(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            
            label_1 = QLabel("Select the output format(s) to generate:")
            self.font.setBold(True);   label_1.setFont(self.font)
            self.font.setBold(False)
            
            # HTML
            check_box_1 = QCheckBox("HTML")
            self.font.setBold(True); check_box_1.setFont(self.font)
            self.font.setBold(False)
            #
            radio_button_1 = QRadioButton("plain HTML")
            radio_button_1.setFont(self.font)
            radio_button_2 = QRadioButton("with navigation Panel")
            radio_button_2.setFont(self.font)
            radio_button_3 = QRadioButton("prepare for compressed HTML .chm")
            radio_button_3.setFont(self.font)
            check_box_2    = QCheckBox("with search function")
            check_box_2.setFont(self.font)
            
            frame_1 = QFrame()
            frame_1.setFrameShape (QFrame.HLine)
            frame_1.setFrameShadow(QFrame.Sunken)
            
            self.layout.addWidget(label_1)
            self.layout.addWidget(check_box_1)
            self.layout.addWidget(radio_button_1)
            self.layout.addWidget(radio_button_2)
            self.layout.addWidget(radio_button_3)
            self.layout.addWidget(check_box_2)
            self.layout.addWidget(frame_1)
            
            
            # LaTeX
            check_box_2 = QCheckBox("LaTeX")
            self.font.setBold(True); check_box_2.setFont(self.font)
            self.font.setBold(False)
            #
            radio_button_4 = QRadioButton("an intermediate format for hypter-linked PDF")
            radio_button_4.setFont(self.font)
            radio_button_5 = QRadioButton("an intermediate format for PDF")
            radio_button_5.setFont(self.font)
            radio_button_6 = QRadioButton("an intermediate format for PostScript")
            radio_button_6.setFont(self.font)
            
            frame_2 = QFrame()
            frame_2.setFrameShape (QFrame.HLine)
            frame_2.setFrameShadow(QFrame.Sunken)
            
            self.layout.addWidget(check_box_2)
            self.layout.addWidget(radio_button_4)
            self.layout.addWidget(radio_button_5)
            self.layout.addWidget(radio_button_6)
            self.layout.addWidget(frame_2)
            
            
            # misc
            check_box_3 = QCheckBox("Man pages")
            check_box_3.setFont(self.font)
            check_box_4 = QCheckBox("Rich Text Format - RTF")
            check_box_4.setFont(self.font)
            check_box_5 = QCheckBox("XML")
            check_box_5.setFont(self.font)
            check_box_6 = QCheckBox("DocBook")
            check_box_6.setFont(self.font)
            
            self.layout.addWidget(check_box_3)
            self.layout.addWidget(check_box_4)
            self.layout.addWidget(check_box_5)
            self.layout.addWidget(check_box_6)
    
    # ------------------------------------------------------------------------
    # create a scroll view for the diagrams tab on left side of application ...
    # ------------------------------------------------------------------------
    class customScrollView_4(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            
            label_1 = QLabel("Diagrams to generate:")
            self.font.setBold(True);   label_1.setFont(self.font)
            self.font.setBold(False)
            
            radio_button_1 = QRadioButton("No diagrams")
            radio_button_1.setFont(self.font)
            radio_button_2 = QRadioButton("Text only")
            radio_button_2.setFont(self.font)
            radio_button_3 = QRadioButton("Use built-in diagram generator")
            radio_button_3.setFont(self.font)
            radio_button_4 = QRadioButton("Use Dot-Tool from the GrappVz package")
            radio_button_4.setFont(self.font)
            
            frame_1 = QFrame()
            frame_1.setFrameShape (QFrame.HLine)
            frame_1.setFrameShadow(QFrame.Sunken)
            
            self.layout.addWidget(label_1)
            self.layout.addWidget(radio_button_1)
            self.layout.addWidget(radio_button_2)
            self.layout.addWidget(radio_button_3)
            self.layout.addWidget(radio_button_4)
            self.layout.addWidget(frame_1)
            
            label_2 = QLabel("Dot graphs to gnerate:")
            self.font.setBold(True);   label_2.setFont(self.font)
            self.font.setBold(False)
            
            check_box_10_1 = QCheckBox("Class graph")
            check_box_10_1.setFont(self.font)
            check_box_10_2 = QCheckBox("Colaboration diagram")
            check_box_10_2.setFont(self.font)
            check_box_10_3 = QCheckBox("Overall Class hiearchy")
            check_box_10_3.setFont(self.font)
            check_box_10_4 = QCheckBox("Include dependcy graphs")
            check_box_10_4.setFont(self.font)
            check_box_10_5 = QCheckBox("Included by dependcy graphs")
            check_box_10_5.setFont(self.font)
            check_box_10_6 = QCheckBox("Call graphs")
            check_box_10_6.setFont(self.font)
            check_box_10_7 = QCheckBox("Called-by graphs")
            check_box_10_7.setFont(self.font)
            
            self.layout.addWidget(label_2)
            self.layout.addWidget(check_box_10_1)
            self.layout.addWidget(check_box_10_2)
            self.layout.addWidget(check_box_10_3)
            self.layout.addWidget(check_box_10_4)
            self.layout.addWidget(check_box_10_5)
            self.layout.addWidget(check_box_10_6)
            self.layout.addWidget(check_box_10_7)
    
    class customScrollView_5(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            self.label_1.hide()
            self.content_widget.setMinimumHeight(1000)
            
            font_primary   = "Consolas"
            font_secondary = "Courier New"
            
            self.font_a = QFont("Consolas"); self.font_a.setPointSize(10)
            self.font_b = QFont("Arial");    self.font_a.setPointSize(10)
            
            self.font_a.setFamily(font_primary)
            font_id = QFontDatabase.addApplicationFont(self.font_a.family())
            if font_id != -1:
                self.font_a.setFamily(font_primary)
                self.font_a.setPointSize(10)
            else:
                self.font_a.setFamily(font_secondary)
                self.font_a.setPointSize(10)
            
            label_1_elements = [
                "DOXYFILE_ENCODING","PROJECT_NAME","PROJECT_NUMBER","PROJECT_BRUEF","PROJECT_LOGO",
                "OUTPUT_DIRECTORY","CREATE_SUBDIRS","CREATE_SUBDIRS_LEVEL","ALLOW_UNICODE_NAMES","OUTPUT_LANGUAGE",
                "BRIEF_MEMBER_DESC","REPEAT_BRIEF","ABBREVIATE_BRIEF","ALWAYS_DETAILED_SEC","INLINE_INHERITED_MEMB","FULL_PATH_NAMES",
                "STRIP_FROM_PATH","STRIP_FROM_INC_PATH","SORT_NAMES","JAVADOC_AUTOBRIEF","JAVADOC_BANNER",
                "QT_AUTOBRIEF","MULTILINE_CPP_IS_BRIEF","PYTHON_DOCSTRING","INHERITED_DOCS","SEPERATE_MEMBER_PAGES","TAG_SIZE","ALIASES",
                "OPTIMIZE_OUTPUT_FOR_C","OPTIMIZE_OUTPUT_JAVA","OPTIMIZE_FOR_FORTRAN","OPTIMIZE_OUTPUT_VHCL","OPTIMIZE_OUTPUT_SLICE",
                "EXTERNAL_MAPPING","MARKDOWN_SUPPORT","MARKDOWN_ID_STYLE","TOC_INCLUDE_HEADINGS","AUTOLINK_SUPPORT","BUILTIN_STL_SUPPORT",
                "CPP_CLI_SUPPORT","SIP_SUPPORT","IDL_PROPERTY_SUPPORT","DESTRIBUTE_GROUP_DOC","GROUP_NESTED_COMPOUNDS","SUBGROUPING",
                "INLINE_GROUPED_CLASSES","INLINE_SIMPLE_STRUCTS","TYPEDEF_HIDES_STRUCT","LOOKUP_CACHE_SIZE","NUM_PROC_THREADS","TIMESTAMP"
            ]
            
            for i in range(0, len(label_1_elements)):
                s1 = "label_1_" + str(i+1)
                s2 = "editfield_1_" + str(i+1)
                
                lh_0 = QHBoxLayout()
                vw_0 = QWidget()
                vw_1 = QLabel(label_1_elements[i])
                vw_1.setMinimumHeight(32)
                vw_1.setFont(self.font_a)
                vw_1.setMinimumWidth(200)
                setattr(self, s1, vw_1)
                
                vw_2 = QLineEdit()
                vw_2.setFont(self.font_b)
                vw_2.font().setPointSize(10)
                vw_2.setMinimumWidth(120)
                vw_2.setMinimumHeight(21)
                setattr(self, s2, vw_2)
                
                sp_1 = QFrame()
                sp_1.setFrameShape(QFrame.HLine)
                
                lh_0.addWidget(vw_1)
                lh_0.addWidget(vw_2)
                lh_0.addWidget(sp_1)
                
                self.layout.addLayout(lh_0)
            
            # change font, because we use consolas earlier
            #self.font.setFamily("Arial")
    
    class customScrollView_6(myCustomScrollArea):
        def __init__(self, name):
            super().__init__(name)
            self.init_ui()
        def init_ui(self):
            i = 1
    
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
            
            self.__css__widget_item = ""                                          \
            + "QListView::item{background-color:white;color:black;"               \
            + "border:0px;padding-left:10px;padding-top:5px;padding-bottom:5px;}" \
            + "QListView::item::selected{background-color:blue;color:yellow;"     \
            + "font-weight:620;border:none;outline:none;}"                        \
            + "QListView::icon{left:10px;}"                                       \
            + "QListView::text{left:10px;}"
            
            self.__button_style_css = "" \
            + "QPushButton { border-radius: 3px;" \
            + "background: #012d8c;" \
            + "background-image: linear-gradient(to bottom, #185d8c, #2980b9);" \
            + "font-family: Arial;" \
            + "color: #f7ff03;" \
            + "font-size: 11pt;" \
            + "padding: 10px 20px 10px 20px;" \
            + "text-decoration: none;" \
            + "}" \
            + "QPushButton::hover { background: #183b91;" \
            + "background-image: linear-gradient(to bottom, #183b91, #5145bf); "\
            + "text-decoration: none;}"
            
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
            menu_item_style = ""          \
            + "QMenuBar{"                 \
            + "background-color:navy;"    \
            + "padding:2px;margin:0px;"   \
            + "color:yellow;"             \
            + "font-size:11pt;"           \
            + "font-weight:bold;}"        \
            + "QMenuBar:item:selected {"  \
            + "background-color:#3366CC;" \
            + "color:white;}"
            
            # ----------------------------------------
            # create a new fresh menubar ...
            # ----------------------------------------
            menubar = QMenuBar()
            menubar.setStyleSheet(menu_item_style)
            
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
            
            menu_label_style = "" \
            + "QLabel{background-color:navy;color:yellow;" \
            + "font-weight:bold;font-size:11pt;padding:4px;margin:0px;}" \
            + "QLabel:hover{background-color:green;color:yellow;}"
            
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
            
            toolbar_action_new  = QAction(QIcon("img/new-document.png"),"New Config.", self)
            toolbar_action_open = QAction(QIcon("img/open-folder.png") ,"Open existing Config.", self)
            toolbar_action_save = QAction(QIcon("img/floppy-disk.png") ,"Save current session.", self)
            
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
            
            self.tab_widget_1.setStyleSheet("" \
            + "QTabWidget::pane    { border-top: 2px solid #C2C7CB;}" \
            + "QTabWidget::tab-bar { left: 5px;  }" \
            + "QTabBar::tab {" \
            + "background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1," \
            + "stop: 0 #E1E1E1, stop: 0.4 #DDDDDD," \
            + "stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);" \
            + "border: 2px solid #C4C4C3;" \
            + "border-bottom-color: #C2C7CB;" \
            + "border-top-left-radius: 4px;" \
            + "border-top-right-radius: 4px;" \
            + "min-width: 20ex;" \
            + "padding: 2px;}" \
            + "QTabBar::tab:selected, QTabBar::tab:hover {" \
            + "background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,"\
            + "stop: 0 #fafafa, stop: 0.4 #f4f4f4,"\
            + "stop: 0.5 #e7e7e7, stop: 1.0 #fafafa);}" \
            + "QTabBar::tab:selected {" \
            + "border-color: #9B9B9B;" \
            + "border-bottom-color: #C2C7CB;}" \
            + "QTabBar::tab:!selected { margin-top: 2px; }")
            
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
        
        loca = handle_language(ini_lang)
        if not loca == None:
            _  = loca.gettext
        
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
            
            # !! TODO !!
            #sys.exit(EXIT_FAILURE)
        
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
        
        appWindow = mainWindow()
        appWindow.show()
        appWindow.exec_()
        
        del appWindow  # free memory
        
        result = app.exec_()
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
