#!/bin/bash
set -euo pipefail
if (( $# != 2 ));then echo 'Usage: run.sh original|curves2|curves5|curves10 INPUT' >&2;exit 2;fi
case "$1" in original|curves2|curves5|curves10) ;; *) exit 2;;esac
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE="$(realpath -e -- "${LABPLOT_RUNTIME_ROOT:?Set existing verified runtime}")"
name="$1";input="$(realpath -e -- "$2")";dest="$ROOT/results/$name";profile="$ROOT/profiles/$name"
python "$ROOT/../verify_source.py" --case "$name" --input "$2" --check-path "$dest" "$profile" "$BASE"
printf '%s  %s\n' c11d801f47329fcd69b03c8f6acf5a5f8f74a9dc6a2f3bbdaa32293804e17554 "$BASE/squashfs-root/usr/bin/labplot" 81d571e53b9dfb793f07cbbb9307d418391103ae7c8679a36284d12422e10fbf "$BASE/squashfs-root/usr/lib/liblabplot.so.2.12.1" | sha256sum --check --status
[[ ! -e "$dest" && ! -e "$profile" ]] || exit 3
mkdir -p "$ROOT/results" "$ROOT/profiles";mkdir "$dest" "$profile";cd "$dest"
for d in home config cache state data runtime tmp;do mkdir "$profile/$d";done
chmod 700 "$profile/runtime"
export HOME="$profile/home" XDG_CONFIG_HOME="$profile/config" XDG_CACHE_HOME="$profile/cache" XDG_STATE_HOME="$profile/state" XDG_DATA_HOME="$profile/data" XDG_RUNTIME_DIR="$profile/runtime" TMPDIR="$profile/tmp"
export OBSERVER_BUNDLED_LIB="$BASE/squashfs-root/usr/lib/liblabplot.so.2.12.1" OBSERVER_RAW_NUMERIC=1 OBSERVER_OUT="$dest" OBSERVER_INPUT="$dest/source-evidence.opj" OBSERVER_LAYER_MODE=plot
sha256sum "$input" > input.before.sha256
cp "$input" source-evidence.opj;cmp -s "$input" source-evidence.opj;chmod 400 source-evidence.opj
python "$ROOT/../verify_source.py" --case "$name" --input source-evidence.opj
status=0
timeout 11s env LD_PRELOAD="$ROOT/application_observer.so" "$BASE/squashfs-root/AppRun" -platform offscreen --no-splash > application.log 2>&1 || status=$?
printf '%s\n' "$status" > exit-status.txt
[[ "$status" == 0 || "$status" == 124 ]] || exit 7
sha256sum "$input" > input.after.sha256;cmp -s input.before.sha256 input.after.sha256;cmp -s "$input" source-evidence.opj
test -f imported-application.lml
