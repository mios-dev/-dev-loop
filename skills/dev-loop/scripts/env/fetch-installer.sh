#!/usr/bin/env bash
# fetch-installer.sh <url> <dest> — download a shell installer to <dest>, refusing anything that is
# not a shell script. Download-then-run (never pipe-to-shell) so a bad transfer fails loudly.
#
# --compressed is load-bearing: antigravity.google's CDN serves `Content-Encoding: gzip` from some
# cache nodes even when the request sent no Accept-Encoding (measured 2026-09-25: ~1 response in 3).
# Without it curl writes the raw gzip bytes and `bash install.sh` dies "cannot execute binary file"
# (rc 126). With it curl decodes whatever encoding arrives. The shebang check catches the next
# variant (an HTML error page, a captive portal) before bash runs it.
set -euo pipefail
[ "$#" -eq 2 ] || { echo "usage: fetch-installer.sh <url> <dest>" >&2; exit 2; }
url="$1"; dest="$2"
curl -fsSL --compressed --retry 4 --retry-delay 2 "$url" -o "$dest"
[ -s "$dest" ] || { echo "[fetch-installer] ERROR: downloaded installer is empty: $url" >&2; exit 1; }
if [ "$(head -c 2 "$dest")" != '#!' ]; then
    echo "[fetch-installer] ERROR: $url is not a shell script (no #! line; $(wc -c <"$dest") bytes) — refusing to run it" >&2
    exit 1
fi
