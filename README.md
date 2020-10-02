## A conan tool for packaging QT based on the install packages

Building QT, especially QT plus optional packages is difficult and slow. 
For example the build in including webengine does not fit in the free plans of the CI vendors (at time of writing 6 hours on Azure).

An alternative strategy is to package the SDK binaries & includes prebuilt by QT. The [python based QT installer](https://lnj.gitlab.io/post/qli-installer/) 
by Linus Jahn [also in GitLab](https://git.kaidan.im/lnj/qli-installer) already handles finding, downloading and unpacking the core
QT based on the `<qt-version> <host> <target> [<arch>]` flags. 

This project is a fork of Linus Jahn's original with additional options for extra packages and it run on Windows.

Example usage:

``python qli-installer.py 5.12.0 windows desktop --arch win64_msvc2017_64 -p webengine script``

Like the original it relies on 7z being installed, and a few additional non-default python packages are required: conan, colorama that can be obtained from pip.

