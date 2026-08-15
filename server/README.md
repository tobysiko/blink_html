# Blink session service

Two people in two places, one table. Deploy this and the play page grows a
"Play with friends" panel; leave it undeployed and the page is exactly what it
was — a single file that works with no network at all.

## What it holds

Not a board. A game of Blink is a pure function of its seed, its options and
the answers people gave, so a session is:

    seed · options · who is sitting where · the list of answers

Every client runs its own engine and stays in step by applying the same
answers in the same order. A whole finished three-player game is about 1.2 kB.
Reconnecting is "here is the list again".

## Layout

| file | what it is |
|---|---|
| `worker.src.js` | routes and sockets — Cloudflare Worker + Durable Object |
| `dev.js` | the same service on your machine, on node and `ws` |
| `build.js` | glues `app/engine.js` + `app/session.js` + `worker.src.js` into `worker.js` |
| `wrangler.toml` | the bindings: one Durable Object, one R2 bucket, one secret |
| `worker.js` | **generated** — do not edit |

Both servers are pure transport around `sessionHandle()` in
`app/session.js`. Every decision about who may do what lives there, and is
tested there, because two implementations of that would drift and the one that
drifted would be the one nobody tested.

## Locally

    (cd ../app && npm install ws)
    node build.js
    node dev.js                                     # http://localhost:8787
    BLINK_API=http://localhost:8787 node ../app/build.js

Then open `../Blink-play-v0.22.html` through a web server (not `file://` — the
page needs an origin for the socket). Sessions live in memory and reports land
in `server/reports/`; losing both on Ctrl-C is the point of a dev server.

## Deployed

    npx wrangler r2 bucket create blink-reports
    npx wrangler secret put ADMIN_KEY
    node build.js && npx wrangler deploy
    BLINK_API=https://blink-sessions.<you>.workers.dev node ../app/build.js

Then commit and push the rebuilt page. The build stamps itself with the commit
it came from, so every playtest report can name the exact version that
produced it.

## Routes

| | |
|---|---|
| `POST /session` | open a table; body is the rules, returns the code |
| `GET /session/:code` | the state, for a page that has not connected yet |
| `GET /session/:code/ws` | the socket |
| `POST /report` | a playtest report, stored as it arrives |
| `GET /reports?key=…` | list them |
| `GET /report/:id?key=…` | read one |

Reports are not public: they carry names and free text people wrote for the
designer, so reading them back needs `ADMIN_KEY`. Writing one does not — that
is a playtester finishing a game.

## Messages

Client to server: `hello` · `sit` · `start` · `answer` · `undo` · `flag` ·
`sync` · `ping`.
Server to client: `welcome` · `seats` · `start` · `answer` · `undo` · `sync` ·
`flagged` · `error` · `pong`.

An `answer` carries the step the client believed it was answering at. That one
number is the guard against a double tap, a slow network and two tabs open at
once: if it does not match the log, the server sends the truth back as `sync`
instead of an error, and the client rebuilds rather than trying to work out
which message went missing.
