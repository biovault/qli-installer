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
import urllib.request

# Support packages are similar to but are not addons
support_packages = ["qt5compat", "qtshadertools", "qtquick3d", " qtquicktimeline"]


def download(url, dest):
    response = urllib.request.urlopen(url)
    data = response.read()
    with open(dest, "wb") as f:
        f.write(data)


def findPackage(
    maj_version="",
    qt_ver_num="",
    arch="",
    packages_url="",
    update_xml=None,
    packname=None,
):
    package_desc = ""
    full_version = ""
    archives = []
    archives_url = ""

    addon_infix = ""
    if maj_version == "6":
        addon_infix = "addons."

    # non-addon support packages have no infix
    if packname in support_packages:
        addon_infix = ""

    def getPossibleVersionsList(packname):
        names = []
        if packname:
            names.append(
                f"qt.qt{maj_version}.{qt_ver_num}.{addon_infix}{packname}.{arch}"
            )
            names.append(f"qt.{qt_ver_num}.{addon_infix}{packname}.{arch}")
        else:
            names.append(f"qt.qt{maj_version}.{qt_ver_num}.{arch}")
            names.append(f"qt.{qt_ver_num}.{arch}")
        print(f"Names for {packname}: {names}")
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
            if f".qt{maj_version}." in name:
                archives_url = packages_url + versionsList[0]
            else:
                archives_url = packages_url + versionsList[1]
            archives_url += "/"
            break
    if not full_version or not archives:
        print(
            f"Error while parsing package information for {qt_ver_num} {arch} {packages_url} {update_xml} {packname}!"
        )
        exit(1)
    return package_desc, full_version, archives, archives_url


def install_archives(archives, archives_url, full_version):
    for archive in archives:
        url = f"{archives_url}{full_version}{archive}"

        sys.stdout.write("\033[K")
        print(f"Downloading {url}...")  # , end="\r")
        download(url, "package.7z")

        sys.stdout.write("\033[K")
        print(f"Extracting {archive}...")  # , end="\r")
        if platform.system() == "Windows":
            os.system("7z x package.7z >NUL")
        else:
            os.system("7z x package.7z 1>/dev/null")
        os.remove("package.7z")


def install_qt(common_args, os_args):
    """Install prebuilt QT from the central repo

    Args:
        common_args (dict of str: str) Non-platform dependant. Expected values are
            qt_version - version string in the form 5.X.Y, 6.X.Y
            host_system - one of "linux", "mac", "windows"
            packages - list of zero or more of:
                    "positioning",   for Qt6 with webengine
                    "webchannel",   for Qt6 with webengine
                    "webengine",
                    "imageformats",  for Qt6 to get tiff support
                    "virtualkeyboard",
                    "datavis3d",
                    "charts",
                    "networkauth",
                    "remoteobjects"'
                    "qt5compat" "multimedia"   A Qt support package backward compatibility for Qt5 (in Qt6)


        os_args (dict of str: str)
            target - one of: "desktop", "android", "ios"
            arch - depending on common_args.host_system/os_args.target
                linux: "gcc_64"
                mac/desktop: "clang_64"
                mac/ios: "ios"
                windows/desktop: one of
                    "win64_msvc2022_64", "win64_msvc2019_64", "win64_msvc2017_64", "win64_msvc2015_64",
                    "win32_msvc2015", "win32_mingw53"
                */android: "android_x86", "android_armv7"

    Changes for Qt5.15 (and greater): no 2017 packages are available but 2019 is
    binary compatible. So we replace 2017 by 2019 for a 2017 package
    """
    package_list = common_args["packages"]
    base_url = "https://download.qt.io/online/qtsdkrepository/"

    # Qt version
    version = common_args["qt_version"]
    print("version", version)
    qt_ver_num = f"{version[0]}{version[1]}{version[2]}"
    # one of: "linux", "mac", "windows"
    os_name = str(common_args["host_system"])
    print("OS name", os_name)
    # one of: "desktop", "android", "ios"
    target = str(os_args["target"])
    print("Target", target)
    maj_version = version[0]
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
        if (
            os_name == "windows"
            and (version[0] == "5" and version[1] == "15")
            or (version[0] == "6")
        ):
            if arch == "win64_msvc2017_64":
                arch = "win64_msvc2019_64"
            if arch == "win32_msvc2017_64":
                arch = "win32_msvc2019_64"
            # as far as 6.72 no msvc 2022 in qt download
            # from 6.8 only msvc 2022
            if version[0] == "6" and int(version[1]) < 8:
                if arch == "win32_msvc2022_64": 
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
    packages_url += f"qt{maj_version}_{qt_ver_num}" + "/"

    print("Packages url", f"{packages_url}Updates.xml")

    tempupdatesfile = os.path.join(tempfile.mkdtemp(), "Updates.xml")

    download(f"{packages_url}Updates.xml", tempupdatesfile)
    print("Updates.xml downloaded to {0}".format(tempupdatesfile))
    with open(tempupdatesfile, "r") as file:
        update_content = file.read()
    update_xml = ElementTree.fromstring(update_content)

    package_desc, full_version, archives, archives_url = findPackage(
        maj_version, qt_ver_num, arch, packages_url, update_xml
    )

    print("*****************************************************")
    print(f"Installing main package {package_desc}")
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
            if package in support_packages:
                package_prefix = ""
            else:
                package_prefix = "qt"
            package_desc = ""
            full_version = ""
            archives = []
            archives_url = ""
            packname = package_prefix + package

            package_desc, full_version, archives, archives_url = findPackage(
                maj_version, qt_ver_num, arch, packages_url, update_xml, packname
            )
            install_archives(archives, archives_url, full_version)
        print("*****************************************************")

    sys.stdout.write("\033[K")
    print("Finished installation")
