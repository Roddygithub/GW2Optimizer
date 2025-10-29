#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OS=linux
ARCH=amd64
case "$(uname -m)" in
  x86_64|amd64) ARCH=amd64 ;;
  arm64|aarch64) ARCH=arm64 ;;
  *)
    echo "Architecture $(uname -m) non prise en charge" >&2
    exit 1
    ;;
esac

API=https://api.github.com/repos/rhysd/actionlint/releases/latest
json_tmp="$(mktemp)"
trap 'rm -f "$json_tmp"' EXIT
curl -fsSL -H 'Accept: application/vnd.github+json' -H 'User-Agent: gw2optimizer-actionlint-installer' "$API" -o "$json_tmp"

readarray -t urls < <(python3 - "$OS" "$ARCH" "$json_tmp" <<'PY'
import json
import sys

os_name, arch, path = sys.argv[1:4]
with open(path, 'r', encoding='utf-8') as fh:
    release = json.load(fh)

prefix = f"{os_name}_{arch}"
tar_url = ''
sha_url = ''
for asset in release.get('assets', []):
    url = asset.get('browser_download_url', '')
    if not url:
        continue
    if url.endswith('.tar.gz') and prefix in url:
        tar_url = url
    elif url.endswith('checksums.txt'):
        sha_url = url

print(tar_url)
print(sha_url)
PY
)

url_tar="${urls[0]:-}"
url_sum="${urls[1]:-}"

if [[ -z "${url_tar:-}" || -z "${url_sum:-}" ]]; then
  echo "Impossible de trouver les assets actionlint pour ${OS}/${ARCH}" >&2
  exit 1
fi

install_cache=".cache/actionlint"
mkdir -p "$install_cache"
cd "$install_cache"

echo "Téléchargement: $url_tar"
curl -fsSLO "$url_tar"
curl -fsSLO "$url_sum"

tar_file="$(basename "$url_tar")"
sum_file="$(basename "$url_sum")"

echo "Vérification du checksum…"
grep "$tar_file" "$sum_file" | sha256sum -c -

echo "Extraction…"
tar -xzf "$tar_file"

BIN_DIR="$ROOT_DIR/bin"
mkdir -p "$BIN_DIR"
cp -f actionlint "$BIN_DIR/actionlint"
chmod +x "$BIN_DIR/actionlint"

echo "actionlint installé: $($BIN_DIR/actionlint --version)"
