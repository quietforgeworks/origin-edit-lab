#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE="${LABPLOT_EXTERNAL_VIEWER_ROOT:?Set the path to the separately verified official LabPlot 2.12.1 extracted runtime and matching Qt headers}"
INC="$BASE/debian-runtime/usr/include/x86_64-linux-gnu/qt6"
for p in application_observer font_boundary_probe; do
 g++ -std=c++17 -shared -fPIC "$ROOT/$p.cpp" -I"$INC" -I"$INC/QtCore" -I"$INC/QtGui" -I"$INC/QtWidgets" -L"$BASE/squashfs-root/usr/lib" -lQt6Widgets -lQt6Gui -lQt6Core -ldl -Wl,-rpath,"$BASE/squashfs-root/usr/lib" -o "$ROOT/$p.so"
done
