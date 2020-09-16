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

def findPackage(qt_ver_num="", arch="", packages_url="", update_xml=None, packname=None, ):
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
            print("Error while parsing package information for {} {} {} {} {}!".format(qt_ver_num, arch, packages_url, update_xml, packname))
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

def install_qt(common_args, os_args):
    """Install prebuilt QT from the central repo 
    
    Args:
        common_args (dict of str: str) Non-platform dependant. Expected values are 
            qt_version - version string in the form 5.X.Y
            host_system - one of "linux", "mac", "windows"
            packages - list of zero or more of: 
                    "webengine", 
                    "webglplugin", 
                    "virtualkeyboard", 
                    "script",
                    "datavis3d", 
                    "charts", 
                    "networkauth", 
                    "purchasing",
                    "remoteobjects"
             
            
        os_args (dict of str: str) 
            target - one of: "desktop", "android", "ios"
            arch - depending on common_args.host_system/os_args.target 
                linux: "gcc_64"
                mac/desktop: "clang_64"
                mac/ios: "ios"
                windows/desktop: one of 
                    "win64_msvc2019_64, win64_msvc2017_64, "win64_msvc2015_64",
                    "win32_msvc2015", "win32_mingw53"
                */android: "android_x86", "android_armv7" 
                
    Quirks for 5.15 (and greater?) no 2017 is available but 2019 is supposed to
    be binary compatible. So we replacy 2017 by 2019
    """
    package_list = common_args["packages"]
    base_url = "https://download.qt.io/online/qtsdkrepository/"

    # Qt version
    version = common_args["qt_version"].split(".")
    print("version", version)
    qt_ver_num = "5{0}{1}".format(version[1], version[2])
    # one of: "linux", "mac", "windows"
    os_name = str(common_args["host_system"])
    print("OS name", os_name)
    # one of: "desktop", "android", "ios"
    target = str(os_args["target"])
    print("Target", target)

    # Target architectures:
    #
    # linux/desktop:   "gcc_64"
    # mac/desktop:     "clang_64"
    # mac/ios:         "ios"
    # windows/desktop: "win64_msvc2019_64", "win64_msvc2017_64", "win64_msvc2015_64",
    #                    "win32_msvc2015", "win32_msvc2017", 
    #                  "win32_msvc2015", "win32_mingw53"
    # */android:       "android_x86", "android_armv7"
    arch = ""
    if os_args["arch"]:
        arch = os_args["arch"]
        # See https://bugreports.qt.io/browse/QTBUG-84559 for msvc2017 use msvc2019 
        # for version 5.15 (and higher?)
        if os_name == "windows" and version[1] == "15"
            if arch == "win64_msvc2017_64":
                arch = "win64_msvc2019_64"
            if arch == "win32_msvc2017_64"":
                arch = "win32_msvc2019_64"
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
    print("Arch", arch) 
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

                 
    package_desc, full_version, archives, archives_url =  findPackage(qt_ver_num, arch, packages_url, update_xml)
               
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
                   
            package_desc, full_version, archives, archives_url =  findPackage(qt_ver_num, arch, packages_url, update_xml, packname)
            install_archives(archives, archives_url, full_version) 
        print("*****************************************************")
                
    sys.stdout.write("\033[K")
    print("Finished installation")
