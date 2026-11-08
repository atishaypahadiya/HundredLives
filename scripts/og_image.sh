#!/usr/bin/env bash
# Render the project page's share image and icons with headless Chrome and macOS sips:
#   docs/og.jpg              1200×630, the home valley's opening shot in ?og mode (title only, no nav or HUD), shared by
#                            the home and Runs pages; JPEG so chat apps that skip large preview images (WhatsApp) still show it
#   docs/favicon-32.png      the sheep mark (docs/favicon.svg), transparent
#   docs/apple-touch-icon.png 180×180, the sheep mark on the meadow green
# docs/favicon.svg is hand-written; each page also carries it inline. Rerun after changing the opening shot or the icon,
# then commit the images. The home page loads its data over HTTP, so the script serves docs/ on a local port.
#   scripts/og_image.sh
set -euo pipefail
cd "$(dirname "$0")/.."
chrome="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
shot() {  # out width height url [extra flags]; WebGL through SwiftShader, so the valley renders without a GPU
  local out=$1 w=$2 h=$3 url=$4; shift 4
  "$chrome" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars --force-prefers-reduced-motion \
    --virtual-time-budget=15000 --window-size="$w,$h" --screenshot="$out" "$@" "$url" 2>/dev/null
}
root="file://$PWD"
tmp=$(mktemp -d)
port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
python3 -m http.server "$port" --bind 127.0.0.1 --directory docs >/dev/null 2>&1 & server=$!
trap 'kill $server 2>/dev/null; rm -rf "$tmp"' EXIT
for _ in $(seq 50); do curl -fs "http://127.0.0.1:$port/" >/dev/null && break; sleep 0.1; done
shot "$tmp/og.png" 1200 630 "http://127.0.0.1:$port/?og"
sips -s format jpeg -s formatOptions 82 "$tmp/og.png" --out docs/og.jpg >/dev/null
# Headless Chrome renders tiny windows blank, so the icons are drawn at 512 and scaled down (sips, macOS).
shot "$tmp/apple.png" 512 512 "$root/scripts/icon.html"
shot "$tmp/fav.png" 512 512 "$root/scripts/icon.html?favicon" --default-background-color=00000000
sips -z 180 180 "$tmp/apple.png" --out docs/apple-touch-icon.png >/dev/null
sips -z 32 32 "$tmp/fav.png" --out docs/favicon-32.png >/dev/null
python3 - <<'PY'
import struct
for f, want in [("docs/apple-touch-icon.png", (180, 180)), ("docs/favicon-32.png", (32, 32))]:
    w, h = struct.unpack(">II", open(f, "rb").read()[16:24])
    assert (w, h) == want, f"{f} is {w}x{h}, expected {want}"
    print(f"{f}: {w}x{h}")
PY
sips -g pixelWidth -g pixelHeight docs/og.jpg | tail -2 | tr -s ' ' | paste -sd' ' -
echo "docs/og.jpg: $(( $(wc -c < docs/og.jpg) / 1024 )) KB"
