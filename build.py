#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import platform

from bincrafters import build_template_default

if __name__ == "__main__":
    
    if playform.system() == "Darwin":
        os.environ['CONAN_SKIP_BROKEN_SYMLINKS_CHECK'] = 1
        
    builder = build_template_default.get_builder()

    builder.run()
