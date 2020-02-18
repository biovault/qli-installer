#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Baldur van Lew 2019 <b.van_lew@lumc.nl>
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

import os
import shutil
import sys

import configparser
from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration
from conans.model import Generator
from installutils import install_qt

class qt(Generator):
    @property
    def filename(self):
        return "qt.conf"

    @property
    def content(self):
        return "[Paths]\nPrefix = %s" % self.conanfile.deps_cpp_info["qt"].rootpath.replace("\\", "/")


class QtConan(ConanFile):

    _submodules = ["webengine", 
        "webglplugin", 
        "virtualkeyboard", 
        "script",
        "datavis3d", 
        "charts", 
        "networkauth", 
        "purchasing"]

    name = "qt"
    version = "5.5"
    description = "Qt is a cross-platform framework for graphical user interfaces."
    topics = ("conan", "qt", "ui")
    url = "https://github.com/bldrvnlw/qli-installer"
    homepage = "https://www.qt.io"
    license = "MIT"
    author = "Baldur van Lew <b.van_lew@lumc.nl>"
    exports = ["LICENSE.md", "installutils.py", "__init__.py"]
    settings = "os", "arch", "compiler", "build_type"

    options = dict({
        "target": ["desktop", "android", "ios"],
        "commercial": [True, False],
        "opengl": ["no", "es2", "desktop", "dynamic"],
        "openssl": [True, False],
        "webengine": [True, False],
        "webglplugin": [True, False],
        "virtualkeyboard": [True, False],
        "script": [True, False],
        "datavis3d": [True, False], 
        "charts": [True, False],
        "networkauth": [True, False],
        "purchasing": [True, False]       
    })
    no_copy_source = True
    default_options = dict({
        "commercial": False,
        "target": "desktop",
        "opengl": "desktop",
        "openssl": True,
        "webengine": True,
        "webglplugin": False,
        "virtualkeyboard": False,
        "script": True,
        "datavis3d": False, 
        "charts": False,
        "networkauth": False,
        "purchasing": False          
    })

    short_paths = True

    def configure(self):
    # Target platform specific stuff here
        if self.settings.os == 'Linux':
            self.options.target = "desktop"
        if self.settings.os == "Windows":
            self.options.target = "desktop" 
        if self.settings.os == "Macos":
            self.options.target = "desktop" 
            

    def build(self):
        common_args = dict({})
        os_args = dict({})
        
        os_map = dict({"Linux": "linux", "Windows": "windows", "Macos": "mac", "iOS": "mac"})
        # Use concatenated  settings.os settings.compiler.version settings.arch
        # to get an architecture string for the QT install
        arch_map = dict({
            "Windows15x86": "win32_msvc2017", 
            "Windows15x86_64": "win64_msvc2017_64", 
            "Windows14x86": "win32_msvc2015", 
            "Windows14x86_64": "win64_msvc2015_64",
            "Windows12x86": "win32_msvc2013", 
            "Windows12x86_64": "win64_msvc2013_64",            
            "Linux": "gcc_64",
            "Macos": "clang_64"
        })
        print(self.settings.os)
        print(self.settings.compiler.version)
        print(self.settings.arch)        
        
        if self.settings.os == 'Linux':
            arch_key = "Linux"
        elif self.settings.os == "Macos":
            arch_key = "Macos"
        else:
            arch_key = str(self.settings.os) + str(self.settings.compiler.version) + str(self.settings.arch)
            
        print(arch_key)    
        common_args["qt_version"] = self.version
        common_args["host_system"] = os_map[str(self.settings.get_safe("os"))]
        common_args["packages"] = [pkg for pkg in self._submodules if self.options.get_safe(pkg)]
        print("Packages to installed: ", common_args["packages"])
        os_args["target"] = self.options.target
        os_args["arch"] = arch_map[arch_key]
        
        
        install_qt(common_args, os_args)
        
    def package(self):
        self.copy("*")

    def package_info(self):
        if self.settings.os == "Windows":
            self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
