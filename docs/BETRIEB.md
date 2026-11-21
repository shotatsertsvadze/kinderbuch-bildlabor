# Betrieb der öffentlichen Demo

Ein kleiner Server mit Docker: Caddy (HTTPS über Let's Encrypt) vor einem nur lesbaren Container.
Die Demo hat keinen veränderlichen Zustand; der Demonstrationsstand `demo/` liegt im Image.

## Voraussetzungen vor dem ersten Start

1. `demo/` angelegt und geprüft (docs/DEMO_KURATIERUNG.md), Lizenzangaben in `demo/LICENSES.md`
   ausgefüllt.
2. `rechtliches/impressum.md` und `rechtliches/datenschutz.md` ausgefüllt (keine `OFFEN:`-Zeile).
3. Alles committet und gepusht. Das Image entsteht mit `git archive` nur aus dem committeten Stand.

Der Image-Bau bricht ab, solange Punkt 1 oder 2 offen ist.

## Server einrichten (einmalig)

1. Hetzner Cloud: kleinster Shared-Tarif, Standort Deutschland, Image: aktuelle Ubuntu-LTS (26.04 oder 24.04), eigenen
   SSH-Schlüssel beim Anlegen hinterlegen. Preis laut hetzner.com am 20.11.2026: ab 5,49 Euro im
   Monat ohne Umsatzsteuer; IPv4 und Domain kommen gegebenenfalls hinzu. x86 und Arm funktionieren
   beide, das Image wird auf dem Server gebaut.
2. Hetzner Cloud Firewall anlegen und dem Server zuweisen: eingehend nur 22/TCP (möglichst nur die
   eigene IP), 80/TCP, 443/TCP, 443/UDP. Wichtig: Von Docker veröffentlichte Ports umgehen `ufw`
   auf dem Server; die Hetzner-Firewall liegt davor und gilt trotzdem.
3. In der Hetzner Console den Auftragsverarbeitungsvertrag abschließen.
4. DNS: A-Eintrag (und AAAA) der Domain auf die Server-IP.
5. Als `root` anmelden, Benutzer anlegen und Schlüssel übernehmen:

   ```bash
   adduser --disabled-password --gecos "" demo
   usermod -aG sudo demo
   passwd demo   # Passwort nur für sudo, nicht für SSH
   install -d -m 700 -o demo -g demo /home/demo/.ssh
   install -m 600 -o demo -g demo /root/.ssh/authorized_keys /home/demo/.ssh/authorized_keys
   apt update && apt -y full-upgrade && apt -y install unattended-upgrades git
   ```

6. In einem zweiten Terminal prüfen, dass `ssh demo@<server>` funktioniert. Erst dann SSH härten:

   ```bash
   printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\n' \
     > /etc/ssh/sshd_config.d/10-haertung.conf
   sshd -t && systemctl reload ssh
   ```

7. Docker Engine mit Compose-Plugin aus dem offiziellen Docker-Repository installieren:
   <https://docs.docker.com/engine/install/ubuntu/>. Danach `sudo usermod -aG docker demo` und neu
   anmelden. Die Gruppe `docker` entspricht Root-Rechten; nur dieser Benutzer gehört hinein.

## Bereitstellen

Als `demo` auf dem Server:

```bash
git clone https://github.com/shotatsertsvadze/kinderbuch-bildlabor.git
cd kinderbuch-bildlabor
DOMAIN=demo.example.de deploy/deploy.sh
```

`deploy.sh` baut das Image aus dem Commit (`docker build --pull`, Tag = Commit), startet beide
Container und wartet höchstens 120 Sekunden, bis der Gesundheitscheck der Anwendung grün ist.
Caddy holt das Zertifikat beim ersten Aufruf; DNS muss dafür bereits zeigen.

## Nach jedem Bereitstellen prüfen

```bash
TAG=$(git rev-parse --short HEAD) DOMAIN=demo.example.de docker compose -f deploy/compose.yaml ps
curl -fsS https://demo.example.de/_stcore/health   # erwartet: ok
curl -sI https://demo.example.de/ | grep -i -E 'strict-transport|content-security|x-content-type'
```

Dann in einem privaten Browserfenster docs/RUNDGANG_DEMO.md durchgehen: Startseite, Leitbeispiel,
alle fünf Schritte, Bibliotheksdaten, Downloads, „Impressum und Datenschutz“.

## Überwachung

- Ein externer Verfügbarkeitsdienst (kostenloser Tarif genügt) ruft alle 5 Minuten
  `https://<domain>/_stcore/health` auf und meldet Ausfälle per E-Mail.
- Bei Bedarf auf dem Server: `docker stats --no-stream` (Speicher, CPU),
  `docker compose -f deploy/compose.yaml logs --tail 100 app` (mit `TAG` und `DOMAIN` wie oben),
  `df -h` und `docker system df` (Plattenplatz).
- Docker startet abgestürzte Container neu (`restart: unless-stopped`), auch nach einem
  Server-Neustart.

## Aktualisieren, zurücksetzen, abschalten

- Aktualisieren: `git pull`, dann erneut `DOMAIN=... deploy/deploy.sh`. Monatlich auch ohne
  Codeänderung neu bauen: `--pull` holt Sicherheitsupdates des Basis-Images. Das Betriebssystem
  aktualisiert sich über `unattended-upgrades`.
- Zurücksetzen: vorhandene Stände mit `docker image ls kinderbuch-bildlabor` anzeigen, dann
  `TAG=<früherer Commit> DOMAIN=demo.example.de docker compose -f deploy/compose.yaml up -d --wait`.
  Ältere Images erst löschen, wenn der neue Stand geprüft ist.
- Abschalten: `TAG=x DOMAIN=x docker compose -f deploy/compose.yaml down`; um Kosten zu beenden,
  den Server in der Hetzner Console löschen.
- Totalverlust: neuer Server, dieselben Schritte. Eine Datensicherung des Servers ist nicht nötig.

## Schutz im Container

Nur lesbares Dateisystem, `/tmp` als kleines tmpfs, keine Linux-Capabilities, `no-new-privileges`,
höchstens 128 Prozesse, 768 MB Speicher, 1 CPU, kein Volume, kein veröffentlichter Port (nur Caddy
erreicht die Anwendung). Die Anwendung verweigert im Demomodus jedes Schreiben, jeden Netzabruf und
jeden Programmaufruf. Fehlerdetails und Stacktraces werden nicht angezeigt. Caddy führt kein
Zugriffsprotokoll, begrenzt Anfragen auf 2 MB und setzt Sicherheits-Header; Container-Protokolle
sind auf 10 MB begrenzt.

Nicht abgesichert: Lastspitzen durch sehr viele gleichzeitige Besucher (kein Rate-Limiting). Bei
Überlastung startet Docker den Container neu.

## Lokal prüfen (ohne Server)

Nach dem Commit, mit installiertem Docker:

```bash
git archive --format=tar HEAD | docker build -t kinderbuch-bildlabor:test -
docker run --rm -p 127.0.0.1:8501:8501 --read-only --tmpfs /tmp:size=16m,noexec,nosuid \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 --memory 768m --cpus 1 \
  kinderbuch-bildlabor:test
```

Dann <http://127.0.0.1:8501> öffnen. `docker ps` muss nach etwa 30 Sekunden `healthy` zeigen.
