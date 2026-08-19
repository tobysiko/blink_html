/* Does the built function actually work when Vercel loads it?
 *
 * This exists because of a deployment whose only symptom was
 *
 *     A server error has occurred
 *     FUNCTION_INVOCATION_FAILED
 *
 * with no stack, no log line and nothing to grep. Two separate faults produced
 * it, and both are the kind that only appear once the file leaves this repo:
 *
 *   1. **The bundle exported nothing.** Editing the source truncated the last
 *      two lines, and `module.exports = server` went with them. Everything
 *      still parsed; there was simply no handler to invoke.
 *
 *   2. **The site is an ES module project.** `"type": "module"` in the site's
 *      package.json makes every .js file ESM — under which `module.exports`
 *      assigns to an object nobody reads, so again: no handler. The fix is a
 *      package.json beside the function saying `commonjs`, and the failure
 *      without it is silent.
 *
 * So this loads the generated file the way the platform does — in a temporary
 * directory with a `"type": "module"` package.json above it, which is the
 * hostile case — and then actually serves requests through it.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');

const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const BUILT = path.join(__dirname, 'api', 'blink.js');
const PKG = path.join(__dirname, 'api', 'package.json');

if (!fs.existsSync(BUILT)) {
  console.error('server/api/blink.js is missing — run: node server/build.js');
  process.exit(2);
}

/* Stage it exactly as a Vite or Next site would: an ESM package at the root,
 * the function in api/. If the commonjs marker is missing, this is where it
 * shows. */
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'blink-fn-'));
fs.mkdirSync(path.join(root, 'api'));
fs.writeFileSync(path.join(root, 'package.json'),
  JSON.stringify({ name: 'site', private: true, type: 'module' }));
fs.copyFileSync(BUILT, path.join(root, 'api', 'blink.js'));
ok(fs.existsSync(PKG), 'the build did not emit api/package.json — under a '
  + '"type": "module" site the function would export nothing at all');
if (fs.existsSync(PKG)) fs.copyFileSync(PKG, path.join(root, 'api', 'package.json'));

let mod = null;
try { mod = require(path.join(root, 'api', 'blink.js')); }
catch (e) { fail.push('the built function will not load: ' + e.message); }

const server = mod && (typeof mod.listen === 'function' ? mod
  : (mod.default && typeof mod.default.listen === 'function' ? mod.default : null));
ok(!!server, 'the built function exports no http server — this is exactly what '
  + 'FUNCTION_INVOCATION_FAILED looks like, and it has no other symptom');

if (!server) { report(); }
else {
  /* And serve for real. A handler that exports correctly and then throws on
   * the first request is the same outage with a different cause. */
  server.listen(0, async () => {
    const port = server.address().port;
    const get = (p) => new Promise((done) => {
      http.get({ host: '127.0.0.1', port, path: p }, (res) => {
        let b = '';
        res.on('data', (c) => { b += c; });
        res.on('end', () => done({ status: res.statusCode, body: b }));
      }).on('error', (e) => done({ status: 0, body: e.message }));
    });
    const post = (p, obj) => new Promise((done) => {
      const data = JSON.stringify(obj);
      const req = http.request({ host: '127.0.0.1', port, path: p, method: 'POST',
        headers: { 'content-type': 'application/json', 'content-length': Buffer.byteLength(data) } },
        (res) => {
          let b = '';
          res.on('data', (c) => { b += c; });
          res.on('end', () => done({ status: res.statusCode, body: b }));
        });
      req.on('error', (e) => done({ status: 0, body: e.message }));
      req.end(data);
    });

    /* The route the deploy check uses. If this is not a clean 200 with JSON,
     * nothing else about the service matters. */
    const h = await get('/api/blink/health');
    ok(h.status === 200, `/health answered ${h.status}: ${h.body.slice(0, 120)}`);
    let health = null;
    try { health = JSON.parse(h.body); } catch (e) { fail.push('/health is not JSON: ' + h.body.slice(0, 80)); }
    ok(health && health.ok === true, '/health does not report ok');
    ok(health && typeof health.store === 'string',
       '/health does not say which store it is using — that is the one thing '
       + 'it is for');
    ok(health && health.store === 'memory',
       `/health says store=${health && health.store}, but no REDIS_URL is set here`);

    /* The rewrite sends every /api/blink/* path to this one file, so the
     * routing has to happen inside it. */
    const bare = await get('/api/blink');
    ok(bare.status === 200, `the bare /api/blink path answered ${bare.status}`);

    const made = await post('/api/blink/session', { n: 3, seed: 5, objectives: 'off' });
    ok(made.status === 200, `opening a table answered ${made.status}: ${made.body.slice(0, 120)}`);
    let session = null;
    try { session = JSON.parse(made.body); } catch (e) { /* reported below */ }
    ok(session && session.ok && /^[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(session.code || ''),
       'opening a table did not return a readable code: ' + made.body.slice(0, 100));

    if (session && session.code) {
      const got = await get('/api/blink/session/' + session.code);
      ok(got.status === 200, `reading the table back answered ${got.status}`);
      const gone = await get('/api/blink/session/ZZZZ-ZZZZ');
      ok(gone.status === 404, `an unknown table answered ${gone.status}, expected 404`);
    }

    /* A report with nowhere durable to go must SAY so rather than accept it
     * and drop it — the page relies on that flag to fall back to a download. */
    const rep = await post('/api/blink/report', { schema: 3, id: 'TEST1234', started: '2026-08-15' });
    ok(rep.status === 200, `posting a report answered ${rep.status}`);
    let stored = null;
    try { stored = JSON.parse(rep.body); } catch (e) { /* reported below */ }
    ok(stored && stored.stored === false,
       'with no Blob token the service claimed to have stored a report');

    /* A store that REFUSES the write must also come back as stored:false, not
     * as a 500.
     *
     * This is the shape of a real outage. The live Blob store is configured
     * private; the function asked for `access: "public"`; the SDK threw; the
     * throw reached the route; the route answered 500. The page treats any
     * failure as "download it instead", so nothing was lost — but nothing was
     * ever kept either, and the only symptom was an error at the exact moment
     * somebody had finished typing their thoughts about the game.
     *
     * Simulated by planting a @vercel/blob in the staged directory whose `put`
     * always throws the message Vercel actually returned. */
    fs.mkdirSync(path.join(root, 'node_modules', '@vercel', 'blob'), { recursive: true });
    fs.writeFileSync(path.join(root, 'node_modules', '@vercel', 'blob', 'package.json'),
      JSON.stringify({ name: '@vercel/blob', version: '0.0.0-test', main: 'index.js' }));
    fs.writeFileSync(path.join(root, 'node_modules', '@vercel', 'blob', 'index.js'),
      'module.exports = {\n'
      + '  put: async () => { throw new Error("Vercel Blob: Cannot use public '
      + 'access on a private store. The store is configured with private access."); },\n'
      + '  list: async () => { throw new Error("Vercel Blob: private store"); },\n'
      + '};\n');
    process.env.BLOB_READ_WRITE_TOKEN = 'test-token';

    const angry = await post('/api/blink/report',
                             { schema: 3, id: 'TEST5678', started: '2026-08-15' });
    ok(angry.status === 200,
       `a Blob store that refuses the write made the route answer ${angry.status} — `
       + 'the page shows that to the player as a failure');
    let told = null;
    try { told = JSON.parse(angry.body); } catch (e) { /* reported below */ }
    ok(told && told.ok === true && told.stored === false,
       `a refused write reported ${angry.body.slice(0, 90)} — it must be ok with `
       + 'stored:false, so the page saves the file instead');

    /* The listing has the same duty: the one person allowed to read it is the
     * designer, holding the key, and a stack trace is no use to them. */
    process.env.ADMIN_KEY = 'letmein';
    const listed = await get('/api/blink/reports?key=letmein');
    ok(listed.status === 200,
       `listing reports from a broken store answered ${listed.status}`);
    ok(/listing failed/.test(listed.body),
       `a broken listing said: ${listed.body.slice(0, 90)}`);
    delete process.env.BLOB_READ_WRITE_TOKEN;
    delete process.env.ADMIN_KEY;

    /* ---- reading the feedback back --------------------------------------
     *
     * A list of blob keys answers "did anything arrive". It does not answer
     * "what did they say", which is the only reason the file exists. `?full=1`
     * has to return the words. Simulated with a store that holds one report. */
    const kept = { schema: 3, id: 'KEPT0001', started: '2026-08-18',
      build: { commit: 'abc1234' }, lang: 'de',
      outcome: { rounds: 11, scores: [{ seat: 0, total: 44 }, { seat: 1, total: 25 }] },
      setup: { n: 2, seed: 9, meldScore: 'sum' },
      players: [{ seat: 0, kind: 'human', name: 'Toby' }],
      flags: [{ r: 4, t: 'turn', note: 'why is this greyed out' }],
      feedback: { confusing: 'the final round ended early', best: 'the map', name: 'Toby' },
      replay: new Array(80).fill({ kind: 'end' }),      // bulk that must NOT come back
    };
    fs.writeFileSync(path.join(root, 'node_modules', '@vercel', 'blob', 'index.js'),
      'const REPORT = ' + JSON.stringify(kept) + ';\n'
      + 'module.exports = {\n'
      + '  put: async () => ({ url: "https://blob/x" }),\n'
      + '  list: async () => ({ blobs: [{ pathname: "blink/reports/abc1234/2026-08-18/KEPT0001.json",'
      + '    size: 900, uploadedAt: "2026-08-18T10:00:00Z", url: "https://blob/x" }] }),\n'
      + '  get: async (p, o) => (o && o.access === "private"\n'
      + '    ? { stream: [Buffer.from(JSON.stringify(REPORT))] }\n'
      + '    : (() => { throw new Error("public access on a private store"); })()),\n'
      + '};\n');
    process.env.BLOB_READ_WRITE_TOKEN = 'test-token';
    process.env.ADMIN_KEY = 'letmein';
    /* node caches the module it already loaded, so drop it. */
    delete require.cache[require.resolve(path.join(root, 'node_modules', '@vercel', 'blob', 'index.js'))];

    const full = await get('/api/blink/reports?key=letmein&full=1');
    ok(full.status === 200, `reading the reports answered ${full.status}`);
    let read = null;
    try { read = JSON.parse(full.body); } catch (e) { /* below */ }
    const one = read && read.reports && read.reports[0];
    ok(one && !one.unreadable,
       `the stored report came back unreadable: ${full.body.slice(0, 140)}`);
    ok(one && one.feedback && /final round ended early/.test(one.feedback.confusing),
       'the feedback text is not in the reply — a listing of keys is not an answer '
       + 'to "what did they say"');
    ok(one && one.flags && one.flags.length === 1
       && /greyed out/.test(one.flags[0].note),
       'the flags raised mid-game did not come back');
    ok(one && one.scores === '0:44 1:25', `the scores read "${one && one.scores}"`);
    ok(one && !('replay' in one),
       'the whole replay log is being returned — that is most of the bytes and '
       + 'none of the reading');

    /* And the plain listing still works, without dragging every file down. */
    const brief = await get('/api/blink/reports?key=letmein');
    ok(brief.status === 200 && /KEPT0001/.test(brief.body),
       `the plain listing answered ${brief.status}: ${brief.body.slice(0, 90)}`);
    ok(!/final round ended early/.test(brief.body),
       'the plain listing is pulling the report contents down as well');
    delete process.env.BLOB_READ_WRITE_TOKEN;
    delete process.env.ADMIN_KEY;

    /* And reports are not readable without the key. */
    const peek = await get('/api/blink/reports');
    ok(peek.status === 403, `listing reports without a key answered ${peek.status}, expected 403`);

    const nope = await get('/api/blink/nonsense');
    ok(nope.status === 404, `an unknown route answered ${nope.status}`);

    server.close();
    report(`health, routing, open a table, read it back, 404s, report flagged `
      + `as unstored, a refusing Blob store still answers 200/stored:false, `
      + `?full=1 returns the words people wrote and not the replay, `
      + `reports refused without a key`);
  });
}

function report(what) {
  try { fs.rmSync(root, { recursive: true, force: true }); } catch (e) { /* */ }
  console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
    : `vercel function: loads and serves inside a "type": "module" site — ${what}`);
  process.exit(fail.length ? 1 : 0);
}
