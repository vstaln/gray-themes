#!/bin/sh
here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
sys="$(uname -s)"
case "$sys" in
MINGW* | MSYS* | CYGWIN*) rel="x86_64-pc-windows-msvc/gray-themes.exe" ;;
Darwin*)
    case "$(uname -m)" in
    arm64) rel="aarch64-apple-darwin/gray-themes" ;;
    *) rel="x86_64-apple-darwin/gray-themes" ;;
    esac ;;
*)
    case "$(uname -m)" in
    aarch64 | arm64) rel="aarch64-unknown-linux-musl/gray-themes" ;;
    *) rel="x86_64-unknown-linux-musl/gray-themes" ;;
    esac ;;
esac
if [ -x "$here/$rel" ]; then exec "$here/$rel" "$@"; fi
for cand in "$here/target/release/gray-themes.exe" "$here/target/release/gray-themes" "$here/target/debug/gray-themes.exe" "$here/target/debug/gray-themes"; do
    if [ -x "$cand" ]; then exec "$cand" "$@"; fi
done
echo "gray-themes binary not found in $here" >&2
exit 1
