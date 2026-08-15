#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

zig_bin="${1:-../toolchain/node_modules/@oven/zig/zig}"
cache_root="${2:-../zig-build-cache}"

node scripts/generate_payload.mjs payload src/payload_generated.h

ZIG_GLOBAL_CACHE_DIR="$cache_root/global" \
ZIG_LOCAL_CACHE_DIR="$cache_root/local" \
  "$zig_bin" rc /c 65001 /fo src/installer.res src/installer.rc

ZIG_GLOBAL_CACHE_DIR="$cache_root/global" \
ZIG_LOCAL_CACHE_DIR="$cache_root/local" \
  "$zig_bin" cc \
    -target x86_64-windows-gnu \
    -O2 \
    -Wall -Wextra -Werror \
    -Wl,/subsystem:windows \
    src/installer.c src/installer.res \
    -o HumanitarianDataPlatform_Setup_Native_GUI_v4.0.0.exe \
    -lcomctl32 -lshell32 -ladvapi32 -lwinhttp -lws2_32 -lbcrypt -lgdi32
