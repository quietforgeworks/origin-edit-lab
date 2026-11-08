#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE="$(realpath -e -- "${LABPLOT_RUNTIME_ROOT:?Set the separately verified official LabPlot 2.12.1 runtime root}")"
INC="$BASE/debian-runtime/usr/include/x86_64-linux-gnu/qt6"
g++ -std=c++17 -shared -fPIC "$ROOT/application_observer.cpp" -I"$INC" -I"$INC/QtCore" -I"$INC/QtGui" -I"$INC/QtWidgets" -I"$INC/QtTest" -L"$BASE/squashfs-root/usr/lib" -lQt6Test -lQt6Widgets -lQt6Gui -lQt6Core -ldl -Wl,-rpath,"$BASE/squashfs-root/usr/lib" -o "$ROOT/application_observer.so"
