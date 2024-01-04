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
# DOXYGEN_PATH = <path\to\doxygen.exe>
#
# ATTENTION:
# -----------
# This is not an offical script for the offical doxygen reprosity !
# It is created mainly for using to my personal usage.
# So, I give no warantees for anything.
#
# !!! YOU USE IT AT YOUR OWN RISK !!!
# ----------------------------------------------------------------------------
try:
    import os            # operating system stuff
    import sys           # system specifies
    import re            # regular expression handling
    import glob          # directory search
    import subprocess    # start sub processes
    import platform      # Windows ?
    import shutil        # shell utils
    import traceback     # stack exception trace back
    
    from bs4         import BeautifulSoup, Doctype
    from bs4.element import Comment
    
    # ------------------------------------------------------------------------
    # branding water marks ...
    # ------------------------------------------------------------------------
    __version__ = "Version 0.0.1"
    __authors__ = "paule32"
    
    # ------------------------------------------------------------------------
    # main is out entry point, where normal application's begin to start their
    # script command's when you click on this script file (name), or execute
    # this script by press the enter key on the command prompt.
    # ------------------------------------------------------------------------
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1

    if __name__ == "__main__":
        # ---------------------------------------------------------
        # print a nice banner on the display device ...
        # ---------------------------------------------------------
        print(""                                \
        + "doxygen 1.10.0 HTML Filter 0.0.1\n"  \
        + "(c) 2024 by paule32\n"               \
        + "all rights reserved.\n")
        
        # ---------------------------------------------------------
        # at startup, check system settings ...
        # ---------------------------------------------------------
        pcount      = len(sys.argv) - 1
        doxy_env    = "DOXYGEN_PATH"
        doxy_path   = "./"
        doxyfile    = "Doxyfile"
        os_type     = 0
        
        if platform.system() == "Windows":
            os_type = 1
        
        if not doxy_env in os.environ:
            print("error: " + f"{doxy_env}" \
            + " is not set in your system settings.")
            sys.exit(EXIT_FAILURE)
        else:
            doxy_path = os.environ[doxy_env]
        
        # ---------------------------------------------------------
        # depend on the platform system, check if doxygen exec name
        # was set into DOXYGEN_PATH. If no such entry exists, then
        # add doxygen executable name to "doxy_path" ...
        # ---------------------------------------------------------
        if os_type == 1:
            doxy_path = doxy_path.replace("/", "\\")
            if doxy_path[-1] == "\\":
                if not "doxygen.exe" in doxy_path.lower():
                    doxy_path += "doxygen.exe"
                elif not "doxygen" in doxygen_path.lower():
                    doxy_path += "doxygen.exe"
            else:
                if not "doxygen.exe" in doxy_path.lower():
                    doxy_path += "\\doxygen.exe"
                elif not "doxygen" in doxy_path.lower():
                    doxy_path += "\\doxygen.exe"
        # ---------------------------------------------------------
        # this is for Linux user's ,,,
        # ---------------------------------------------------------
        else:
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
            print(""                          \
            + "info: no parameter given. "    \
            + "use default: 'Doxyfile' config.")
        elif pcount > 1:
            print(""                          \
            + "error: to many parameters. "   \
            + "use first parameter as config.")
            doxyfile = sys.argv[1]
        else:
            doxyfile = sys.argv[1]
        
        if os_type == 1:
            doxyfile = doxyfile.replace("/", "\\")
        
        # ---------------------------------------------------------
        # when config file not exists, then spite a error message:
        # ---------------------------------------------------------
        if not os.path.exists(doxyfile):
            print("error: config file: '" \
            + f"{doxyfile}" + "' does not exists.")
            sys.exit(EXIT_FAILURE)
        
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
        
        if os_type == 1:
            html_out = html_out.replace("/", "\\")
        
        # ---------------------------------------------------------
        # !!! CAUTION !!!: data can be lost there.
        # ---------------------------------------------------------
        if os.path.exists(html_out):
            shutil.rmtree(html_out)
        
        os.makedirs(html_out, exist_ok = True)
        
        # ---------------------------------------------------------
        # here, we try to open doxygen. The path to the executable
        # must be in the PATH variable of your system...
        # ---------------------------------------------------------
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
        
        if os_type == 1:
            html_directory  =  html_directory.replace("/", "\\")
        
        html_files = glob.glob(html_directory,recursive = True)
        file_names = []
        
        for file_name in html_files:
            if os_type == 1:
                file_name = file_name.replace("/", "\\")
            file_names.append(file_name)
        
        # ---------------------------------------------------------
        # open the html files where to remove the not neccassary
        # data from "read" content.
        # ---------------------------------------------------------
        for htm_file in file_names:
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
                meta = soup.find("meta", {"http-equiv": "X-UA-Compatible"})
                if meta:
                    meta.decompose()
                
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
                    print(f"warning: " + f"{ex}")
                
                # ---------------------------------------------------------
                # close old file, to avoid cross over's. Then write the
                # modified content back to the original file...
                # ---------------------------------------------------------
                input_file.close()
                
                with open(htm_file, "w", encoding="utf-8") as output_file:            
                    output_file.write(modh)
                    output_file.close()
        
        # ---------------------------------------------------------
        # all files are write, then create the CHM file ...
        # ---------------------------------------------------------
        dir_old = os.getcwd()
        dir_new = html_out + "/"
        
        if os_type == 1:
            dir_old = dir_old.replace("/", "\\")
            dir_new = dir_new.replace("/", "\\")
            
            os.chdir(dir_new)
            
            // TODO: hhc.exe !!!
            result = subprocess.run(["hhc.exe",f"{dir_new}" + "index.hhp"])
            exit_code = result.returncode
            
            # -----------------------------------------------------
            # when error level, then do nothing anyelse - exit ...
            # -----------------------------------------------------
            if exit_code > 0:
                print(""                               \
                + "error: hhc.exe aborted with code: " \
                + f"{exit_code}")
                sys.exit(EXIT_FAILURE)
            
            os.chdir(dir_old)
        else:
            print("error: this is script is for Windows hhc.exe")
            sys.exit(EXIT_FAILURE)
        
        # ---------------------------------------------------------
        # when all is gone, stop the running script ...
        # ---------------------------------------------------------
        print("Done.")
        sys.exit(EXIT_SUCCESS)

except ImportError:
    print("error: import module missing.")
    sys.exit(EXIT_FAILURE)

# ----------------------------------------------------------------------------
# E O F  -  End - Of - File
# ----------------------------------------------------------------------------
