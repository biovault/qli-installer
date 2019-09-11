#!/usr/bin/env python3
#
# Original work Copyright (C) 2018 Linus Jahn <lnj@kaidan.im>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


# Modified work Copyright (C) Baldur van Lew 2019 <b.van_lew@lumc.nl>
#
# This is an extended version of Linus Jahn's script from his repo https://git.kaidan.im/lnj/qli-installer
# It allow the retrieval of exttra packages.
# Usage example including extra packages:
#
# python qli-installer.py 5.12.0 windows desktop --arch win64_msvc2017_64 -p webengine script
#
#  The code is designed to work in an environment with conan package manage installed

import platform
import argparse
import re
import colorama
import atexit
   
def reset_terminal_settings():
    colorama.deinit()

if __name__ == "__main__":
    if platform.system() == "Windows":
        colorama.init()
        
    atexit.register(reset_terminal_settings)
        
    semver_pattern = re.compile('5\.(\d+).(\d+)')

    def semver_string(string):
        m = semver_pattern.match(string)
        # is the string format 5.x.y
        if not m:
            msg = "%r is not a semver string" % string
            raise argparse.ArgumentTypeError(msg)
        return [m.group(0), m.group(1), m.group(2)]
        
    baseParser = argparse.ArgumentParser(add_help=False)
    baseParser.add_argument("qt_version", type=semver_string, help="QT version 5.X.Y")
    baseParser.add_argument("host_system", choices = ["linux", "mac", "windows"], help="os")
    baseParser.add_argument("-p", "--packages", 
        nargs="*", 
        choices = ["webengine", 
            "webglplugin", 
            "virtualkeyboard", 
            "script",
            "datavis3d", 
            "charts", 
            "networkauth", 
            "purchasing",
            "remoteobjects"], 
        help="additional Qt packages to be installed")

    linuxParser = argparse.ArgumentParser(description="Install for Linux", parents=[baseParser])
    linuxParser.add_argument("target", choices = ["desktop", "android"], help="target platform")
    linuxParser.add_argument("-a", "--arch", choices = ["gcc_64"], help="supported architectures") 

    macParser = argparse.ArgumentParser(description="Install for Mac", parents=[baseParser])
    macParser.add_argument("target", choices = ["desktop", "ios"], help="target platform")
    macParser.add_argument("-a", "--arch", choices = ["clang_64", "ios"], help="supported architectures")

    windowsParser = argparse.ArgumentParser(description="Install for Windows", parents=[baseParser])
    windowsParser.add_argument("target", choices = ["desktop", "android"], help="target platform")
    windowsParser.add_argument("-a", "--arch", 
        choices = ["win64_msvc2017_64", "win64_msvc2015_64", "win32_msvc2015", "win32_mingw53"], 
        help="supported architectures")

    args = baseParser.parse_known_args()
    print(args)

    os_args = None
    if args[0].host_system == "windows":
        os_args = windowsParser.parse_args()
    elif args[0].host_system == "mac":
        os_args = macParser.parse_args()
    elif args[0].host_system == "linux":
        os_args = linuxParser.parse_args()
        
    install_qt(args[0], os_args)
    