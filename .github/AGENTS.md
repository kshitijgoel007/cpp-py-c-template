# CI and Release Instructions

`sudo` is prohibited in every workflow. Python 3.14 is the default CI and
wheel version. CI environments must be created with `virtualenv`.

Keep pull-request CI separate from release-wheel publication. Native CI must
cover Linux GCC, Linux Clang, macOS Clang, and Windows MSVC. Wheel jobs must
repair artifacts with the platform-standard tool before upload.

