#!/bin/bash
set -euo pipefail
if (( $# < 2 || $# > 3 )); then echo 'Usage: run.sh CASE INPUT [plot|coordinate]' >&2; exit 2; fi
if [[ ! "$1" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then echo 'Unsafe case identifier' >&2; exit 2; fi
mode="${3:-plot}"
if [[ "$mode" != plot && "$mode" != coordinate ]]; then echo 'Unsupported layer mode' >&2; exit 2; fi
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE="${LABPLOT_EXTERNAL_VIEWER_ROOT:?Set the path to the separately verified official LabPlot 2.12.1 extracted runtime and matching Qt headers}"
name="$1"; input="$(realpath "$2")"; dest="$ROOT/results/$name"; profile="$ROOT/profiles/$name"
if ! test -f "$input"; then echo 'Input must be an existing regular file' >&2; exit 2; fi
if [[ -e "$dest" || -L "$dest" || -e "$profile" || -L "$profile" ]]; then echo 'Refusing existing case or profile' >&2;exit 3;fi
mkdir -p "$ROOT/results" "$ROOT/profiles"
mkdir "$dest" "$profile";cd "$dest"
for d in home config cache state data runtime tmp; do mkdir -p "$profile/$d";done
chmod 700 "$profile/runtime"
export HOME="$profile/home" XDG_CONFIG_HOME="$profile/config" XDG_CACHE_HOME="$profile/cache" XDG_STATE_HOME="$profile/state" XDG_DATA_HOME="$profile/data" XDG_RUNTIME_DIR="$profile/runtime" TMPDIR="$profile/tmp"
export OBSERVER_BUNDLED_LIB="$BASE/squashfs-root/usr/lib/liblabplot.so.2.12.1" OBSERVER_RAW_NUMERIC=1 OBSERVER_OUT="$dest" OBSERVER_INPUT="$input" OBSERVER_LAYER_MODE="$mode" FONT_PROBE_OUT="$dest/font-boundaries.jsonl"
sha256sum "$input" > input.before.sha256
cp "$input" source-evidence.opj
printf '%s\n' "$mode" > layer-mode.txt
status=0
timeout 11s env LD_PRELOAD="$ROOT/application_observer.so:$ROOT/font_boundary_probe.so" "$BASE/squashfs-root/AppRun" -platform offscreen --no-splash > application.log 2>&1 || status=$?
printf '%s\n' "$status" > exit-status.txt
sha256sum "$input" > input.after.sha256
if ! cmp -s input.before.sha256 input.after.sha256;then echo 'Input changed!' >&2;exit 5;fi
if ! test -f imported-application.lml;then echo 'No application save!' >&2;exit 6;fi
exit 0
