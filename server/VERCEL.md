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
WebSocket when the function reaches its maximum duration** (`maxDuration` in
`vercel.json`, 300s here). Every table will be dropped periodically, whatever
anyone does. That is survivable only because the client treats reconnection as
normal: it keeps its player token, backs off, and rebuilds the whole game from
the log it is handed on the way back in — the same path a phone takes into a
tunnel, and the path `net_test.js` exercises on every run.

## Setting it up, once

1. **Add a Redis.** Vercel dashboard → Storage → Marketplace → any Redis. It
   sets `REDIS_URL` (or `KV_URL`) on the project for you. Without it the
   service still starts, but every instance keeps its own tables and two
   players will not see each other — the function logs a warning saying so.

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
   so `/api/blink/*` all reaches the one function.

5. **Point the page at it** and rebuild:

   ```
   BLINK_API=https://deep-diversions.com/api/blink node app/build.js
   ```

   Then commit and push both repos. The page stamps itself with the commit it
   came from, so every playtest report names the exact version that produced it.

6. Optional: `ADMIN_KEY` as an environment variable, to read reports back.
   Writing one needs no key — that is a playtester finishing a game. Reading
   them does, because they carry names and free text people wrote for you.

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
