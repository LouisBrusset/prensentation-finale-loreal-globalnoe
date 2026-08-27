#!/usr/bin/env bash
# =============================================================================
# Lanceur pour Git Bash / MINGW64 (le shell ou tu es quand tu vois "MINGW64 ~").
#
#   ./make.sh install
#   ./make.sh dev
#   ./make.sh            (affiche l'aide)
#
# Memes cibles que make.ps1 et que le Makefile.
# =============================================================================

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# 8010 par defaut : le port 8000 est occupe par des regles netsh portproxy (WSL).
PORT_API="${FP_PORT:-8010}"
PORT_USER=5173
PORT_DECK=5174
ADMIN_TOKEN="${FP_ADMIN_TOKEN:-loreal2026}"

# Git Bash convertit tout seul les arguments qui ressemblent a des chemins Unix
# ("/app" devient "C:/Program Files/Git/app"). On desactive pour nos appels.
export MSYS_NO_PATHCONV=1

lan_ip() {
  uv run python -c "import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('8.8.8.8', 80)); print(s.getsockname()[0])
except OSError:
    print('127.0.0.1')
finally:
    s.close()"
}

post_admin() {
  local path="$1" body="$2"
  uv run python -c "
import json, sys, urllib.request
req = urllib.request.Request(
    'http://localhost:${PORT_API}${path}',
    data=sys.argv[1].encode(),
    headers={'Content-Type': 'application/json', 'X-Admin-Token': '${ADMIN_TOKEN}'},
)
print(urllib.request.urlopen(req).read().decode())
" "$body"
}

case "${1:-help}" in

  help)
    cat <<'EOF'

  final_presentation - cibles disponibles
  ---------------------------------------
  ./make.sh install      Cree .venv et installe les dependances (uv)
  ./make.sh dev          Lance TOUT en local (API + deck + app participant)
  ./make.sh back         Lance uniquement l'API FastAPI
  ./make.sh serve-user   Sert frontend_user seul (statique pur, comme Netlify)
  ./make.sh serve-deck   Sert frontend_main seul
  ./make.sh test         Lance les tests backend
  ./make.sh lint         Verifie le style (ruff)
  ./make.sh format       Corrige le style (ruff)
  ./make.sh ip           Affiche l'IP LAN a donner aux telephones
  ./make.sh qr           Genere static/qr/join.png
  ./make.sh qr-lan       Genere le QR pointant vers l'IP LAN
  ./make.sh seed         Injecte 25 faux participants
  ./make.sh reset        Remet la session a zero
  ./make.sh clean        Supprime .venv, caches et QR generes

EOF
    ;;

  install)
    uv venv
    uv sync --all-groups
    echo
    echo "Environnement pret. Lance maintenant : ./make.sh dev"
    ;;

  dev | back)
    ip="$(lan_ip)"
    echo
    echo "  Deck presentateur : http://localhost:${PORT_API}/deck"
    echo "  App participant   : http://localhost:${PORT_API}/app"
    echo "  Depuis un telephone du meme wifi : http://${ip}:${PORT_API}/app"
    echo "  Doc API           : http://localhost:${PORT_API}/docs"
    echo
    uv run uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port "${PORT_API}"
    ;;

  serve-user)
    uv run python -m http.server "${PORT_USER}" --directory frontend_user --bind 0.0.0.0
    ;;

  serve-deck)
    uv run python -m http.server "${PORT_DECK}" --directory frontend_main --bind 0.0.0.0
    ;;

  test)   uv run pytest -q ;;
  lint)   uv run ruff check backend scripts ;;
  format) uv run ruff check --fix backend scripts && uv run ruff format backend scripts ;;

  ip)
    ip="$(lan_ip)"
    echo "IP LAN : ${ip}"
    echo "App participant depuis un telephone : http://${ip}:${PORT_API}/app"
    ;;

  qr)     uv run python scripts/gen_qr.py ;;
  qr-lan) uv run python scripts/gen_qr.py ;;  # le defaut vise deja l'IP LAN

  seed)   post_admin "/api/admin/seed" '{"participants": 25}' ;;
  reset)  post_admin "/api/admin/reset" '{}' ;;

  clean)
    rm -rf .venv .pytest_cache .ruff_cache
    rm -f static/qr/*.png
    echo "Nettoye."
    ;;

  *)
    echo "Cible inconnue : $1" >&2
    echo "Lance ./make.sh help pour la liste." >&2
    exit 1
    ;;
esac
