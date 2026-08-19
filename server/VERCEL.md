# Running the tables on Vercel

The play page is already served from the site, so putting the session service
on the same domain means no second platform, no CORS, and one `git push` to
ship the page and the service together.

Two things Vercel does not give you, which a Cloudflare Durable Object did:

- **A home for the table.** A WebSocket is pinned to the instance that accepted
  it, but a *new* connection may land anywhere, and a deployment separates old
  connections from new ones. So the session lives in Redis and broadcasts go
  over pub/sub. `server/store.js` is the whole of that; nothing else in the
  codebase knows.
- **Serialised writes.** Two players answering at the same instant, on two
  instances, would both read a log of length 14 and both write 15 — and the
  game would quietly lose a move. Every change therefore goes through a
  compare-and-set with a retry. `server/store_test.js` forces exactly that
  collision and fails if the retry is removed.

One thing to know before you promise anyone a quiet evening: **Vercel closes a
WebSocket when the function reaches its maximum duration.** Every table will be
dropped periodically, whatever anyone does.

The config deliberately does not set `maxDuration` or `memory`: both are
plan-dependent, and a deployment that fails on a config value is a miserable
first experience. A shorter ceiling only means more reconnects, and those are
handled and tested. If you want fewer of them, add
`"functions": { "api/blink.js": { "maxDuration": 300 } }` — and if the deploy
complains, your plan does not allow that number. That is survivable only because the client treats reconnection as
normal: it keeps its player token, backs off, and rebuilds the whole game from
the log it is handed on the way back in — the same path a phone takes into a
tunnel, and the path `net_test.js` exercises on every run.

## Setting it up, once

1. **Add a Redis.** Vercel dashboard → Storage → Marketplace → any Redis. It
   sets `REDIS_URL` (or `KV_URL`) on the project for you. Without it the
   service still starts, but every instance keeps its own tables and two
   players will not see each other — the function logs a warning saying so.

   **The free plan is enough**, and here is the arithmetic rather than a
   shrug. A table is about 1.2 kB and a move costs two commands plus one
   publish (`store_test.js` counts them and fails if that grows):

   | free plan | what a playtest needs |
   |---|---|
   | 30 MB | ~25,000 tables |
   | 100 ops/sec | ~30 moves a second — thirty tables of people, all moving at once |
   | 5 GB/month | ~5 kB a move, so a few thousand games |
   | 30 connections | two per warm instance, so ~15 instances |

   Connections is the one to watch, and it is why the compare-and-set does not
   open one per move. The earlier WATCH version did, which would have
   exhausted the plan in about fifteen simultaneous moves.

   **Two things the free plan does not have**, and what they mean here:

   - *No persistence.* A restart loses tables in progress. That is a shrug —
     every client is holding the same log, and rejoining redeals the game. It
     is NOT a shrug for playtest reports, which is why those go to Blob
     storage instead (below) and why the page downloads the file if there is
     nowhere durable to put it.
   - *No high availability.* If the Redis is down, tables cannot be opened or
     joined. Solo and hot-seat play are unaffected — they never touch it.

2. **Add the dependencies** to the site's `package.json`:

   ```
   npm install ws redis
   ```

3. **Copy the function in.** `node server/build.js` writes
   `server/api/blink.js` and, if the site repo is checked out beside this one,
   copies it to `<site>/api/blink.js`. It is one generated file — engine,
   session rules, store, hub and routes — for the same reason the play page is
   one file: nothing can differ between what was tested and what is deployed.

4. **Add the rewrite** from `server/vercel.json` to the site's `vercel.json`,
   so `/api/blink/*` all reaches the one function. (Already written into the
   site repo.)

5. **Point the page at it** and rebuild:

   ```
   BLINK_API=https://deep-diversions.com/api/blink node app/build.js
   ```

   Then commit and push both repos. The page stamps itself with the commit it
   came from, so every playtest report names the exact version that produced it.

6. **Somewhere durable for the reports.** Blob is not in the Marketplace —
   it is a first-party Vercel product, so it is under Storage → Create
   Database → **Blob**, not under the Redis-style integrations. Faster from a
   terminal:

   ```
   cd ~/Code/deep-diversions
   npx vercel link          # once, to point the CLI at this project
   npx vercel blob create-store blink-reports --access public
   ```

   Either way it sets `BLOB_READ_WRITE_TOKEN` on the project. **Redeploy after
   creating it** — a running function does not gain an environment variable it
   did not start with.

   Without a Blob store the report route answers `stored: false` and the page
   downloads the file for the player to send on. That is honest, but it relies
   on them actually sending it.

   A **private** store is the better choice and is what the code now asks for
   first: reports carry names and free text people wrote for you, not for the
   internet. `putReport` tries private, then public, so either kind of store
   works — a store configured private while the code asked for public was a
   real outage, and its only symptom was a 500 at the moment somebody pressed
   send.

7. Optional: `ADMIN_KEY` as an environment variable, to read reports back.
   Writing one needs no key — that is a playtester finishing a game. Reading
   them does, because they carry names and free text people wrote for you.

       GET /api/blink/reports?key=…            what has arrived: keys and dates
       GET /api/blink/reports?key=…&full=1     what they actually WROTE — the
                                               feedback form, the flags raised
                                               mid-game, the rules in play

   `full` leaves the replay log out: it is most of the bytes and none of the
   reading. Newest first, 50 by default, `&limit=` to change it.

8. Optional: `BLINK_NOTIFY_URL`, to be **told** rather than having to look.

   Set it to a Slack or Discord incoming webhook and every finished report
   posts a short summary as it lands — who played, under which rules, how it
   went, and what they typed. One payload serves both: it carries `text`
   (which Slack reads and Discord ignores) and `content` (the reverse).

   Three things it deliberately does:
   - it never costs a report. A webhook that is down, slow or wrong leaves
     `stored` untouched and answers `notified: false`. The person has already
     written their three sentences; losing them to a chat integration would be
     absurd.
   - it fires even when storing FAILED. That is exactly when you want to know,
     because the page has handed the player a file and you need to ask for it.
   - it is awaited before the response. A serverless function can be frozen
     the instant it answers, so fire-and-forget would be a coin toss.

## When it answers FUNCTION_INVOCATION_FAILED

That error has no stack and no log line, so it is worth knowing the two things
that cause it here. Both are now caught before deployment — `node
server/build.js` refuses to write a bundle with no handler, and
`node server/vercel_test.js` loads the built file the way the platform does and
serves real requests through it.

- **The bundle exports nothing.** Vercel takes whatever the file exports and,
  if it is an http server, serves it. Lose `module.exports = server` and
  everything still parses; there is simply nothing to invoke.
- **The site is an ES module project.** `"type": "module"` in the site's
  package.json makes every `.js` file ESM, and in ESM `module.exports` assigns
  to an object nobody reads — so again, no handler. `api/package.json` saying
  `{"type":"commonjs"}` fixes it, and the build now writes that file next to
  the function.

## Checking it

```
curl https://deep-diversions.com/api/blink/health
# {"ok":true,"service":"blink-sessions","protocol":1,"store":"redis"}
```

`"store":"memory"` there means the Redis is not wired up, and tables will not
be shared between players.

## Locally

The dev server is the same code with the same store interface:

```
node server/dev.js                                  # memory store
REDIS_URL=redis://localhost:6379 node server/dev.js  # the real thing
```

Running it against a local Redis occasionally is worth the trouble: the
interesting bugs are the ones only a second instance can cause.
