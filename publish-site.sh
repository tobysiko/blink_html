#!/bin/sh
# Publish Blink to deep-diversions.com, without ever overwriting a version
# somebody may have printed from.
#
#   sh publish-site.sh          # HTML + api + the PDFs that are already built
#   sh publish-site.sh --pdfs   # ...and rebuild the print PDFs first (slow)
#   FORCE=1 sh publish-site.sh  # allow replacing an already-published version
#
# TWO SHELVES, AND THE FILENAME IS WHAT DECIDES WHICH ONE A FILE IS ON.
#
#   Rolling  - no version in the name, overwritten every publish, always the
#              newest thing:  play.html, rulebook.html, card-effects.html,
#              map-objectives.html, api/blink.js. A link to one never rots.
#   Pinned   - the version IS in the name, written once and never again:
#              blink-rulebook-v0.24.pdf, blink-deck-v0.25.pdf, and so on.
#
# The print-and-play kit used to be on the rolling shelf under names like
# blink-deck.pdf, so the first v0.25 build would silently have replaced the
# v0.24 components under a URL that promised nothing in particular - and a
# printed deck that no longer matches its rulebook is not a thing anyone
# notices. Everything printable is pinned now, and this script refuses to write
# a pinned name that already exists.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SITE="${SITE:-$HOME/Code/deep-diversions}"
PUB="$SITE/public/blink"
VER="$(cat "$HERE/VERSION")"

[ -d "$PUB" ] || { echo "site repo not found at $SITE" >&2; exit 1; }
[ "$VER" = "0.24" ] && { echo "VERSION is 0.24, which is frozen as the Hippodice entry." >&2
                         echo "Bump VERSION before publishing." >&2; exit 1; }

echo "== publishing v$VER to $PUB"

# ---------------------------------------------------------------- 1. build
if [ "$1" = "--pdfs" ]; then
  echo "== rebuilding the print PDFs (this takes a few minutes)"
  sh "$HERE/source/build_pdfs.sh"
fi
echo "== building the app, the docs and the session service"
BLINK_API=/api/blink BLINK_SITE="$PUB" node "$HERE/app/build.js"
# The guard that has to hold, or multiplayer ships with no table service and
# playtest reports download to the tester instead of reaching Toby.
# The published page is MINIFIED, so the key loses its quotes - matching only
# the unminified spelling is how a guard passes on the workshop copy and never
# looks at the file that actually ships.
grep -qE '"?api"?:"/api/blink"' "$PUB/play.html" \
  || { echo "play.html has no api - BLINK_API did not take" >&2; exit 1; }

# ------------------------------------------- 2. the one-time v0.24 rescue
# The kit published on 5 Sep is v0.24 and is sitting under unversioned names.
# Give it its version before anything can land on top of it.
mig() {  # mig <unversioned> <versioned>
  [ -f "$PUB/$1" ] || return 0
  [ -f "$PUB/$2" ] && return 0
  git -C "$SITE" mv "public/blink/$1" "public/blink/$2" 2>/dev/null \
    || mv "$PUB/$1" "$PUB/$2"
  echo "   archived $1 -> $2"
}
mig blink-deck.pdf              blink-deck-v0.24.pdf
mig blink-deck-bw.pdf           blink-deck-bw-v0.24.pdf
mig blink-objective-cards.pdf   blink-objective-cards-v0.24.pdf
mig blink-player-board.pdf      blink-player-board-v0.24.pdf
mig blink-player-board-bw.pdf   blink-player-board-bw-v0.24.pdf
mig blink-player-aid.pdf        blink-player-aid-v0.24.pdf
mig blink-player-aid-bw.pdf     blink-player-aid-bw-v0.24.pdf
mig blink-first-game.pdf        blink-first-game-v0.24.pdf
mig blink-card-effects.pdf      blink-card-effects-v0.24.pdf

# --------------------------------------------------- 3. pin this version
# The newest thing any PDF is rendered from. A pinned file has to be younger
# than this or it is last version's document wearing this version's name -
# which is the exact failure this script exists to prevent, and the first run
# of it walked straight into: VERSION said 0.25, build_pdfs.sh had not been
# run since v0.24, and every component was copied to a v0.25 filename.
NEWEST="$(ls -t "$HERE/VERSION" "$HERE/source"/*.py "$HERE/source"/*.html \
                "$HERE/app/engine.js" 2>/dev/null | head -1)"
echo "== newest source: ${NEWEST#$HERE/}"

pin() {  # pin <workshop file> <site basename without version>
  src="$HERE/$1"
  dst="$PUB/$2-v$VER.pdf"
  [ -f "$src" ] || { echo "   MISSING $1 - run: sh publish-site.sh --pdfs" >&2
                     MISS=1; return 0; }
  if [ -n "$NEWEST" ] && [ "$NEWEST" -nt "$src" ]; then
    echo "   STALE $1 is older than ${NEWEST#$HERE/} - run: sh publish-site.sh --pdfs" >&2
    MISS=1; return 0
  fi
  if [ -f "$dst" ] && [ -z "$FORCE" ]; then
    if cmp -s "$src" "$dst"; then echo "   unchanged $2-v$VER.pdf"; return 0; fi
    echo "   REFUSING to replace $2-v$VER.pdf, which is already published." >&2
    echo "   Bump VERSION, or re-run with FORCE=1 if it was never linked." >&2
    MISS=1; return 0
  fi
  cp "$src" "$dst"; echo "   published $2-v$VER.pdf"
}
MISS=
echo "== pinning the printable kit as v$VER"
pin "Blink-rules-v$VER.pdf"          blink-rulebook
pin "Blink-rules-v$VER-bw.pdf"       blink-rulebook-bw
pin Blink-deck-colour.pdf            blink-deck
pin Blink-deck-bw.pdf                blink-deck-bw
pin Blink-objectives-colour.pdf      blink-objective-cards
pin Blink-objectives-bw.pdf          blink-objective-cards-bw
pin Blink-player-board-A4.pdf        blink-player-board
pin Blink-player-board-A4-bw.pdf     blink-player-board-bw
pin Blink-player-aid.pdf             blink-player-aid
pin Blink-player-aid-bw.pdf          blink-player-aid-bw
pin Blink-first-game.pdf             blink-first-game
pin Blink-first-game-bw.pdf          blink-first-game-bw
pin Blink-card-effects.pdf           blink-card-effects
pin Blink-card-effects-bw.pdf        blink-card-effects-bw
[ -n "$MISS" ] && { echo "== stopped: see above" >&2; exit 1; }

# ------------------------------------- 4. every link on the page must exist
# The whole point of pinned names is that a link cannot rot. Prove it rather
# than trust it: a 404 on the print page is the one thing a juror WILL see.
echo "== checking every link on the Blink page"
BAD=0
for href in $(grep -o 'href="/blink/[^"#?]*"' "$PUB/index.html" \
              | sed 's|href="/blink/||; s|"$||' | sort -u); do
  case "$href" in "" | */) continue;; esac
  [ -e "$PUB/$href" ] || { echo "   404: /blink/$href" >&2; BAD=1; }
done
[ "$BAD" = 0 ] || { echo "== the page links files that are not there" >&2; exit 1; }
grep -q "v$VER" "$PUB/index.html" \
  || echo "   note: index.html never mentions v$VER - is its copy still on the old version?"

echo
echo "== ready. Review, then commit both repos:"
echo "   git -C \"$HERE\" status --short"
echo "   git -C \"$SITE\" status --short"
echo "   git -C \"$SITE\" add -A public/blink api && git -C \"$SITE\" commit -m 'blink: v$VER'"
echo "   sh \"$SITE/blink_push.command\""
