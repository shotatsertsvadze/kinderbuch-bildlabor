#!/bin/sh
# Baut das Image aus dem committeten Stand (git archive: nie unversionierte Arbeitsdaten)
# und startet es. Rücksetzen: TAG=<früherer Commit> DOMAIN=... docker compose ... up -d
set -eu
: "${DOMAIN:?DOMAIN setzen, z. B. DOMAIN=demo.example.de}"
cd "$(dirname "$0")/.."
test -z "$(git status --porcelain)" || { echo "Arbeitsverzeichnis nicht sauber." >&2; exit 1; }
TAG=$(git rev-parse --short HEAD)
# --pull: Basis-Image mit aktuellen Sicherheitsupdates
git archive --format=tar HEAD | docker build --pull -t "kinderbuch-bildlabor:$TAG" -
# --wait: kehrt erst zurück, wenn der Gesundheitscheck des Containers grün ist
TAG=$TAG DOMAIN=$DOMAIN docker compose -f deploy/compose.yaml up -d --wait --wait-timeout 120
echo "Gestartet: kinderbuch-bildlabor:$TAG auf https://$DOMAIN"
