#!/bin/sh
# Download the Alpine minirootfs, check its SHA-256, and extract it into
# ./rootfs. The archive is untrusted input, so it goes into a fresh directory.
set -eu

VERSION=3.24.3
FILE=alpine-minirootfs-$VERSION-x86_64.tar.gz
URL=https://dl-cdn.alpinelinux.org/alpine/v${VERSION%.*}/releases/x86_64/$FILE
SHA256=f8e1cafba9b1b283b5d30d06f9885c8d2bc161ffe9083ade8e2e157813a53407

[ -e rootfs ] && { echo "rootfs/ already exists; remove it first" >&2; exit 1; }
curl -fsSLo "$FILE" "$URL"
echo "$SHA256  $FILE" | sha256sum -c -
mkdir rootfs
tar -xzf "$FILE" -C rootfs --no-same-owner
rm "$FILE"
