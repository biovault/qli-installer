#!/usr/bin/env bash

set -ex

if [[ "$(uname -s)" == 'Darwin' ]]; then
    unset PYENV_ROOT
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
    export PATH="$HOME/.pyenv/bin:$PATH"

    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi
    
    HOMEBREW_NO_AUTO_UPDATE=1 brew install p7zip
    pyenv install 3.7.1
    pyenv virtualenv 3.7.1 conan
    pyenv rehash
    pyenv activate conan

fi

pip install --upgrade pip
pip install conan --upgrade
pip install conan_package_tools bincrafters_package_tools

conan user
