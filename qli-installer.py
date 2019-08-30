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

import sys
import os
import requests
import xml.etree.ElementTree as ElementTree
from conans import tools
import tempfile
import platform
import argparse
import re
import colorama
import atexit

if platform.system() == "Windows":
    colorama.init()
    
def reset_terminal_settings():
    colorama.deinit()

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

package_list = args[0].packages

host_args = None
if args[0].host_system == "windows":
    host_args = windowsParser.parse_args()
elif args[0].host_system == "mac":
    host_args = macParser.parse_args()
elif args[0].host_system == "linux":
    host_args = linuxParser.parse_args()
    
    
base_url = "https://download.qt.io/online/qtsdkrepository/"

# Qt version
qt_version = args[0].qt_version[0]
qt_ver_num = "5{0}{1}".format(args[0].qt_version[1], args[0].qt_version[2])
# one of: "linux", "mac", "windows"
os_name = args[0].host_system
# one of: "desktop", "android", "ios"
target = host_args.target

# Target architectures:
#
# linux/desktop:   "gcc_64"
# mac/desktop:     "clang_64"
# mac/ios:         "ios"
# windows/desktop: "win64_msvc2017_64, "win64_msvc2015_64",
#                  "win32_msvc2015", "win32_mingw53"
# */android:       "android_x86", "android_armv7"
arch = ""
if host_args.arch:
    arch = host_args.arch
elif os_name == "linux" and target == "desktop":
    arch = "gcc_64"
elif os_name == "mac" and target == "desktop":
    arch = "clang_64"
elif os_name == "mac" and target == "ios":
    arch = "ios"

if arch == "":
    print("Please supply a target architecture.")
    exit(1)

# Build repo URL
packages_url = base_url
if os_name == "windows":
    packages_url += os_name + "_x86/"
else:
    packages_url += os_name + "_x64/"
packages_url += target + "/"
packages_url += "qt5_" + qt_ver_num + "/"

print("Packages url", packages_url)

tempupdatesfile = os.path.join(tempfile.mkdtemp(), "Updates.xml")
 
tools.download(packages_url + "Updates.xml", tempupdatesfile)
print("Updates.xml downloaded to {0}".format(tempupdatesfile))
with open(tempupdatesfile, "r") as file:
    update_content = file.read()
update_xml = ElementTree.fromstring(update_content)

def findPackage(packname=None):
        package_desc = ""
        full_version = ""
        archives = []
        archives_url = ""
        def getPossibleVersionsList(packname):
            names = []
            if packname:
                names.append("qt.qt5.{}.{}.{}".format(qt_ver_num, packname, arch))
                names.append("qt.{}.{}.{}".format(qt_ver_num, packname, arch))
            else:
                names.append("qt.qt5.{}.{}".format(qt_ver_num, arch))
                names.append("qt.{}.{}".format(qt_ver_num, arch))     
            return names
                
        versionsList = getPossibleVersionsList(packname)    
        for packageupdate in update_xml.findall("./PackageUpdate"):
            name = packageupdate.find("Name").text
            # print("name qt5ver arch", name, qt_ver_num, arch)
            if name in versionsList:
                full_version = packageupdate.find("Version").text
                archives = packageupdate.find("DownloadableArchives").text.split(", ")
                # print("version archives", full_version, archives)
                package_desc = packageupdate.find("Description").text
                if ".qt5." in name:
                    archives_url = packages_url + versionsList[0]
                else:
                    archives_url = packages_url + versionsList[1]
                archives_url += '/'
                break
        if not full_version or not archives:
            print("Error while parsing package information for {}!", package)
            exit(1) 
        return package_desc, full_version, archives, archives_url

def install_archives(archives, archives_url, full_version):
    for archive in archives:
        url = archives_url + full_version + archive

        sys.stdout.write("\033[K")
        print("Downloading {}...".format(archive), end="\r")
        tools.download(url, "package.7z")

        sys.stdout.write("\033[K")
        print("Extracting {}...".format(archive), end="\r")
        if platform.system() == "Windows":
            os.system("7z x package.7z >NUL")
        else:
            os.system("7z x package.7z 1>/dev/null")
        os.remove("package.7z")
             
package_desc, full_version, archives, archives_url =  findPackage()
           
print("*****************************************************")
print("Installing main package {}".format(package_desc))
print("*****************************************************")
print("HOST:      ", os_name)
print("TARGET:    ", target)
print("ARCH:      ", arch)
print("Source URL:", archives_url)
if package_list:
    print("Packages:  ", package_list)
print("*****************************************************")
       
install_archives(archives, archives_url, full_version)

if package_list: 
    print("*****************************************************")
    print("Installing extra packages {}".format(package_desc))
    print("*****************************************************")
    for package in package_list:
        print("package:      ", package)
        package_desc = ""
        full_version = ""
        archives = []
        archives_url = ""    
        packname = "qt"+ package
               
        package_desc, full_version, archives, archives_url =  findPackage(packname)
        install_archives(archives, archives_url, full_version) 
    print("*****************************************************")
            
sys.stdout.write("\033[K")
print("Finished installation")
