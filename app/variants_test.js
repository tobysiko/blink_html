/* The meld variants, from Blink-variants.html.
 *
 * Both widen what counts as a meld and nothing else, so this is mostly a
 * legality table — the cases the booklet prints, plus the ones it implies and
 * the ones that must stay illegal. Then a game of each, to prove the engine
 * survives its own wider rule.
 */
const E = require('./engine.js');
const fail = [];
const ok = (cond, what) => { if (!cond) fail.push(what); };

const C = (spec) => spec.split(' ').map((t) => {
  const m = t.match(/^(\d+)([pfom])$/);
  return { r: Number(m[1]), s: { p: 'plains', f: 'forest', o: 'ocean', m: 'mountain' }[m[2]] };
});
const legal = (spec) => E.isLegalMeld(C(spec));

// ------------------------------------------------------------ base rules
E.setMeldRules({});
ok(legal('4p'), 'a single card is not a meld');
ok(legal('4p 4f'), 'a pair is not a meld');
ok(legal('7f 8f 9o'), 'a run of three is not a meld');
ok(legal('2p 3f 3o 4p 4m'), 'a run with duplicates is not a meld');
ok(!legal('2p 2f 4p 4m'), '2-2-4-4 is legal without the combination variant');
ok(!legal('4p 6p'), '4+6 is legal without friends of 10s');
ok(!legal('3p 3f 7o 8o'), 'a pair plus a run is legal without combinations');

// --------------------------------------------------- combination melds
E.setMeldRules({ combo: true });
ok(legal('2p 2f 4p 4m'), 'two pairs are not a combination');
ok(legal('4p 4f 7f 8f 9o'), "the booklet's example (a pair plus a run) is not legal");
ok(legal('3p 3f 7o 8o'), 'a pair plus a run of two is not a combination');
ok(legal('2p 3p 6f 7f 10o 11o'), 'three runs of two are not a combination');
ok(!legal('2p 2f 5o'), 'a pair plus a SINGLE is legal — singles may never combine');
ok(!legal('2p 5o'), 'two unrelated singles are legal as a combination');
ok(!legal('2p 2f 5o 9m'), 'a pair plus two singles is legal');
ok(legal('7f 8f 9o'), 'the base run rule stopped working with combinations on');
// every card belongs to exactly one component
ok(!legal('2p 3p 4f 9o'), 'a run plus a leftover single is legal');

// ---------------------------------------------------- friends of 10s
E.setMeldRules({ friends: true });
for (const [spec, why] of [['4p 6f', '4+6=10'], ['1p 9o', '1+9=10'],
                           ['11f 9m', '11+9=20'], ['12p 8o', '12+8=20'],
                           ['11p 19f', '11+19=30'], ['20o 10m', '20+10=30']])
  ok(legal(spec), `${why} is not a friends pair`);
ok(!legal('4p 7f'), '4+7=11 counts as a friends pair');
ok(!legal('4p 6f 9o'), 'a friends pair plus a single is legal');
ok(!legal('5p 5f 10o 10m'), 'two friends pairs are legal without combinations');

// ------------------------------------------------------------- together
E.setMeldRules({ combo: true, friends: true });
ok(legal('5p 5f 10o 10m'), 'two friends pairs are not a combination when both are on');
ok(legal('4p 6f 7o 8m'), 'a friends pair plus a run of two is not a combination');
ok(!legal('4p 6f 9o'), 'a friends pair plus a single is legal even together');

// ----------------------------------------- what a hand can actually play
E.setMeldRules({});
const hand = C('2p 2f 3o 5m 5p 7f 8o 9m 10p 12f');
const base = E.enumerateMelds(hand, 4).length;
E.setMeldRules({ combo: true });
const combo = E.enumerateMelds(hand, 4).length;
E.setMeldRules({ friends: true });
const friends = E.enumerateMelds(hand, 4).length;
ok(combo > base, `combinations offer ${combo} melds, base offers ${base} — no wider`);
ok(friends > base, `friends offer ${friends} melds, base offers ${base} — no wider`);
console.log(`one ten-card hand at a limit of 4: ${base} melds base, `
  + `${combo} with combinations, ${friends} with friends of 10s`);

// every meld a variant offers must pass its own legality test, and fit the limit
for (const [name, r] of [['combo', { combo: true }], ['friends', { friends: true }],
                         ['both', { combo: true, friends: true }]]) {
  E.setMeldRules(r);
  for (const m of E.enumerateMelds(hand, 5)) {
    if (m.length > 5) fail.push(`${name}: a meld of ${m.length} broke the limit of 5`);
    if (!E.isLegalMeld(m)) fail.push(`${name}: offered a meld it calls illegal`);
  }
}

// ------------------------------------------------------ whole games run
for (const [name, opts] of [['combination melds', { comboMelds: true }],
                            ['friends of 10s', { friendsOf10: true }],
                            ['both', { comboMelds: true, friendsOf10: true }]]) {
  let played = 0, big = 0;
  for (let s = 0; s < 12; s++) {
    const g = E.playOut(3, s * 313 + 5, opts);
    if (!g.finished()) fail.push(`${name}: a game did not finish`);
    for (let i = 1; i <= 6; i++) {
      const c = g.stats['meld_' + i] || 0;
      played += c;
      if (i >= 4) big += c;
    }
    // the ten-card ceiling and the unit count still hold
    for (const p of g.P) {
      if (p.hand.length + p.discard.length + p.played.length > 10)
        fail.push(`${name}: a hand went over ten cards`);
      const on = [...g.m.tiles.values()].reduce(
        (a, t) => a + t.units.filter((u) => u === p.i).length, 0);
      if (on + p.reserve.reduce((a, b) => a + b, 0) !== 20)
        fail.push(`${name}: units do not add up to 20`);
    }
  }
  console.log(`${name}: 12 games clean, ${(big / played * 100).toFixed(0)}% of melds `
    + 'were four cards or more');
}

E.setMeldRules({});
console.log('');
console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : 'meld variants: the booklet\'s cases hold, singles never combine, every card '
    + 'belongs to one component, and whole games play out under each');
process.exit(fail.length ? 1 : 0);
