#!/bin/sh
# Everything that is left, in the order it has to happen.
# Run from the blink_html checkout:   sh FINISH-VERCEL.sh
set -e

SITE="${SITE:-$HOME/Code/deep-diversions}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "== 1. unblock git in the site repo (stale locks) =="
rm -f "$SITE/.git/HEAD.lock" "$SITE/.git/index.lock"

echo "== 2. the site needs three packages =="
( cd "$SITE" && npm install ws redis @vercel/blob )

echo "== 3. build the function and the page, pointed at the same origin =="
node "$HERE/server/build.js"
BLINK_API=/api/blink node "$HERE/app/build.js"

# A plain `node app/build.js` leaves BUILD.api null and the page loses its
# "Play with friends" panel — silently, because a build with no table service
# is a perfectly valid thing. Refuse to hand over one of those by accident.
# The version used to be written into this line by hand, so the guard went on
# checking a v0.22 file that no longer exists — and a missing file makes grep
# fail, which made the guard fire on every run for the wrong reason.
VTAG="v$(cat "$HERE/VERSION")"
grep -q '"api":"/api/blink"' "$HERE/Blink-play-$VTAG.html" || {
  echo "the built page has no table service in it — did BLINK_API get lost?" >&2
  exit 1
}

echo "== 4. what changed =="
( cd "$HERE" && git status --short )
echo "---- site ----"
( cd "$SITE" && git status --short )

cat <<'NOTE'

Now, by hand, because these are yours to decide:

  cd BLINK_HTML && git add -A && git commit -m "build against the Vercel service" && git push
  cd SITE       && git add -A && git commit -m "Blink: session service and the v0.22 play page" && git push

Then, once Vercel has deployed:

  curl https://deep-diversions.com/api/blink/health

Expect  {"ok":true,...,"store":"redis"}.
"memory" means REDIS_URL did not reach the function — check the integration is
connected to the deep-diversions project, not to blink-html.
NOTE
