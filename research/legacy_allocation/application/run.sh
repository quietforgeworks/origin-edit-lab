#!/bin/bash
set -euo pipefail
if (( $# < 2 || $# > 3 )); then echo 'Usage: run.sh original|expanded51|expanded257|expanded1024 INPUT [plot]' >&2; exit 2; fi
case "$1" in original|expanded51|expanded257|expanded1024) ;; *) echo 'Unsafe or unsupported case identifier' >&2; exit 2;; esac
mode="${3:-plot}"
if [[ "$mode" != plot ]]; then echo 'Unsupported layer mode for this experiment' >&2; exit 2; fi
ROOT="$(cd "$(dirname "$0")" && pwd)"
python "$ROOT/../verify_source_artifacts.py" --check-paths "$2" "$ROOT/results" "$ROOT/profiles" "${LABPLOT_RUNTIME_ROOT:?Set the separately verified official LabPlot 2.12.1 runtime root}"
name="$1"; input="$(realpath -e -- "$2")"; dest="$ROOT/results/$name"; profile="$ROOT/profiles/$name"
if ! test -f "$input"; then echo 'Input must be a regular file' >&2; exit 2; fi
for parent in "$ROOT/results" "$ROOT/profiles"; do
  if [[ -L "$parent" || ( -e "$parent" && ! -d "$parent" ) ]]; then echo 'Unsafe result/profile parent' >&2; exit 3; fi
done
if [[ -e "$dest" || -L "$dest" || -e "$profile" || -L "$profile" ]]; then echo 'Refusing existing case or profile' >&2;exit 3;fi
BASE="$(realpath -e -- "${LABPLOT_RUNTIME_ROOT:?Set the separately verified official LabPlot 2.12.1 runtime root}")"
python "$ROOT/../verify_source_artifacts.py" "$name" "$input"
test -f "$ROOT/application_observer.so" || { echo 'Build the authored observer first' >&2; exit 2; }
# Pin the official executable and importer library, not an arbitrary local app.
printf '%s  %s\n' c11d801f47329fcd69b03c8f6acf5a5f8f74a9dc6a2f3bbdaa32293804e17554 "$BASE/squashfs-root/usr/bin/labplot" 81d571e53b9dfb793f07cbbb9307d418391103ae7c8679a36284d12422e10fbf "$BASE/squashfs-root/usr/lib/liblabplot.so.2.12.1" | sha256sum --check --status
mkdir -p "$ROOT/results" "$ROOT/profiles"
mkdir "$dest" "$profile";cd "$dest"
for d in home config cache state data runtime tmp; do mkdir -p "$profile/$d";done
chmod 700 "$profile/runtime"
export HOME="$profile/home" XDG_CONFIG_HOME="$profile/config" XDG_CACHE_HOME="$profile/cache" XDG_STATE_HOME="$profile/state" XDG_DATA_HOME="$profile/data" XDG_RUNTIME_DIR="$profile/runtime" TMPDIR="$profile/tmp"
export OBSERVER_BUNDLED_LIB="$BASE/squashfs-root/usr/lib/liblabplot.so.2.12.1" OBSERVER_RAW_NUMERIC=1 OBSERVER_OUT="$dest" OBSERVER_INPUT="$dest/source-evidence.opj" OBSERVER_LAYER_MODE="$mode"
sha256sum "$input" > input.before.sha256
cp "$input" source-evidence.opj
# Verify the exact private run snapshot too, then import it rather than a mutable external path.
cmp -s "$input" source-evidence.opj
python "$ROOT/../verify_source_artifacts.py" "$name" "$input"
chmod 400 source-evidence.opj
printf '%s\n' "$mode" > layer-mode.txt
status=0
timeout 11s env LD_PRELOAD="$ROOT/application_observer.so" "$BASE/squashfs-root/AppRun" -platform offscreen --no-splash > application.log 2>&1 || status=$?
printf '%s\n' "$status" > exit-status.txt
if test "$status" != 0 && test "$status" != 124; then echo "Unexpected app exit $status" >&2;exit 7;fi
sha256sum "$input" > input.after.sha256
if ! cmp -s input.before.sha256 input.after.sha256;then echo 'Input changed!' >&2;exit 5;fi
if ! cmp -s "$input" source-evidence.opj;then echo 'Observed source snapshot changed!' >&2;exit 5;fi
if ! test -f imported-application.lml;then echo 'No application save!' >&2;exit 6;fi
exit 0
