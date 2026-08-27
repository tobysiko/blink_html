/* Victory row perks — dealt to players, assigned by them.
 *
 * PROPOSAL, off by default. See VROW-PERKS.md.
 *
 * Every perk is equal. Players are dealt a few and choose which slot each goes
 * in, permanently, before anything reaches the row. Three things can go wrong:
 * an unfair deal, an assignment that keeps changing after it should have
 * locked, and a perk firing at the wrong row depth.
 */
const E = require('./engine.js');
const fail = [];
const ok = (c, what) => { if (!c) fail.push(what); };

const withRow = (n, dealt, band) => {
  const p = new E.Player(0, E.BANDS, dealt);
  for (let i = 0; i < n; i++) p.vrow.push({ r: 5 + i, s: 'plains' });
  if (band) for (let j = 0; j < band; j++) p.reserve[j] = 0;
  return p;
};

// ---------------------------------------------------------- off by default
ok(E.playOut(3, 7, {}).P[0].perks === null, 'perks are on without being asked for');
{
  const plain = new E.Player(0, E.BANDS);
  plain.vrow = [1, 2, 3, 4, 5].map((r) => ({ r, s: 'plains' }));
  ok(!plain.hasPerk('roads') && plain.freeMoves() === E.BANDS[0][4],
     'a player with no perks still gained one');
}

// --------------------------------------------------- needs = 6 - slot
ok(JSON.stringify(E.PERK_SLOTS) === '[1,2,3,4]',
   `perks are assignable to ${JSON.stringify(E.PERK_SLOTS)} — slot 5 should stay blank`);
ok(E.PERK_DEAL === 4, `each player is dealt ${E.PERK_DEAL}, not 4`);
for (const [slot, needs] of [[1, 5], [2, 4], [3, 3], [4, 2]]) {
  ok(E.perkSlotNeeds(slot) === needs,
     `slot ${slot} claims to need ${E.perkSlotNeeds(slot)} cards, not ${needs}`);
  for (let n = 0; n <= 5; n++) {
    const p = withRow(n, { [slot]: 'roads' });
    ok(p.hasPerk('roads') === (n >= needs),
       `a perk on slot ${slot} is ${p.hasPerk('roads') ? 'live' : 'dead'} at ${n} cards`);
  }
}

// ------------------------------------------------------ the deal is FAIR
// Everyone gets the same number. The first version of dealPerks handed the
// last seat nothing when the pool was small, which nobody would notice until
// the game after next.
{
  for (const n of [2, 3, 4]) {
    const g = E.playOut(n, 7, { perks: true });
    const counts = g.P.map((p) => p.dealt.length);
    ok(new Set(counts).size === 1,
       `${n}p was dealt unequal perks: ${counts.join('/')}`);
    ok(counts[0] > 0, `${n}p was dealt no perks at all`);
    const all = [].concat(...g.P.map((p) => p.dealt));
    ok(new Set(all).size === all.length,
       `${n}p dealt the same perk twice — there is one token of each`);
    ok(counts[0] <= E.PERK_DEAL, `${n}p was dealt more than PERK_DEAL`);
  }
}
// Only wired perks are ever dealt: a half-built prompt is worse than none.
{
  for (const id of E.playablePerks()) ok(!E.PERKS[id].todo, `${id} is todo but dealable`);
  for (let s = 1; s <= 60; s++)
    for (const p of E.playOut(3, s * 131, { perks: true }).P)
      for (const id of p.dealt) ok(!E.PERKS[id].todo, `seed ${s} dealt unwired ${id}`);
}
// Dealt from the game's rng, so a table replays identically on every client.
{
  const one = (seed) => JSON.stringify(E.playOut(3, seed, { perks: true }).P.map((p) => p.dealt));
  ok(one(12345) === one(12345), 'the same seed dealt different perks');
  const seen = new Set();
  for (let s = 1; s <= 40; s++) seen.add(one(s * 7919));
  ok(seen.size > 1, 'every seed dealt the same perks — the deal is not random');
}

// ------------------------------------------- assignment, and the lock
{
  const p = new E.Player(0, E.BANDS, ['roads', 'coinage', 'granary']);
  ok(Object.keys(p.perks).length === 3, 'the opening arrangement lost a perk');
  ok(!p.perksLocked(), 'the arrangement locked before the row had a card');

  ok(p.assignPerk('roads', 1), 'could not move a perk to an empty slot');
  ok(p.slotOf('roads') === 1, 'the perk did not move');

  /* Moving onto an OCCUPIED slot swaps, so no perk is ever lost. */
  const displaced = p.perks[1];
  ok(p.assignPerk('coinage', 1), 'could not swap onto an occupied slot');
  ok(p.slotOf('coinage') === 1, 'the swap did not land');
  ok(p.slotOf(displaced) !== null, `the swap lost ${displaced}`);
  ok(Object.keys(p.perks).length === 3, 'a perk vanished during a swap');
  ok(new Set(Object.values(p.perks)).size === 3, 'a perk was duplicated by a swap');

  ok(!p.assignPerk('pioneering', 2), 'assigned a perk that was never dealt');
  ok(!p.assignPerk('roads', 9), 'assigned a perk to a slot that does not exist');

  /* The row is where a perk lives, so the arrangement locks the moment the row
   * holds anything. */
  p.vrow.push({ r: 7, s: 'plains' });
  ok(p.perksLocked(), 'the arrangement did not lock once the row had a card');
  const before = JSON.stringify(p.perks);
  ok(!p.assignPerk('roads', 5), 'a locked arrangement was still rearranged');
  ok(JSON.stringify(p.perks) === before, 'a locked arrangement changed anyway');
}

// -------------------------------------------------------- the wired perks
{
  const base = E.BANDS[0][4];
  const p = withRow(2, { 4: 'roads' });            // slot 4 needs two cards
  ok(p.freeMoves() === base + 1, `Roads gave ${p.freeMoves() - base} extra moves`);
  ok(p.spendPerk('roads'), 'Roads could not be spent while live');
  ok(p.freeMoves() === base, 'Roads still paying out after it was spent');
  ok(!p.spendPerk('roads'), 'Roads was spent twice between recycles');
  p.refreshPerks();
  ok(p.freeMoves() === base + 1, 'the recycle did not turn Roads back over');
}
{
  const p = withRow(2, { 4: 'scholarship' });
  ok(p.rankCap() === E.BANDS[0][6] + 1, `Scholarship gave cap ${p.rankCap()}`);
  p.spendPerk('scholarship');
  ok(p.rankCap() === E.BANDS[0][6], 'Scholarship still lifting the cap once spent');
}
{
  // Granary is a RATE, not a use: its token never turns over. Tribe eats
  // nothing, so walk up a tier to see it.
  const p = withRow(2, { 4: 'granary' }, 1);
  const band = p.band();
  ok(band > 0, 'the fixture did not reach a tier that pays food');
  ok(p.food() === Math.max(0, E.BANDS[band][3] - 1), `Granary left food at ${p.food()}`);
  p.spendPerk('granary');
  ok(p.food() === Math.max(0, E.BANDS[band][3] - 1), 'Granary stopped after a spend');
  ok(withRow(2, { 4: 'granary' }).food() >= 0, 'Granary drove food negative');
}
// Pioneering relaxes the touch-two rule, and only while live and unspent.
{
  const g = E.playOut(3, 7, { perks: { 0: { 4: 'pioneering' } } });
  const q = g.P[0];
  q.vrow = [{ r: 5, s: 'plains' }, { r: 8, s: 'forest' }];
  q.refreshPerks();
  const strict = g.m.legalSpaces(2).size;
  const loose = g.spacesFor(q).size;
  ok(loose > strict, `Pioneering opened ${loose - strict} cells — expected some`);
  q.spendPerk('pioneering');
  ok(g.spacesFor(q).size === strict, 'Pioneering still loose after it was spent');
  q.refreshPerks();
  ok(g.spacesFor(q).size === loose, 'the recycle did not restore Pioneering');
  ok(g.spacesFor(g.P[1]).size === strict, 'a player without it saw the loose map');
}

// Outposts widens reach by a ring. Compare the SAME player with the perk live
// and spent — comparing two different players measures their territories, not
// the perk, which is a mistake that reads as a pass.
{
  const g = E.playOut(3, 7, { perks: { 0: { 4: 'outposts' } } });
  const q = g.P[0];
  q.vrow = [{ r: 5, s: 'plains' }, { r: 8, s: 'forest' }];   // slot 4 needs two
  q.refreshPerks();
  ok(q.hasPerk('outposts'), 'the fixture never made Outposts live');
  const wide = g.reachFor(q).size;
  q.spendPerk('outposts');
  const narrow = g.reachFor(q).size;
  ok(wide > narrow, `Outposts changed reach by ${wide - narrow}`);
  q.refreshPerks();
  ok(g.reachFor(q).size === wide, 'the recycle did not restore Outposts');
  /* and it is one ring, not the whole map */
  ok(wide < g.m.tiles.size * 4, 'Outposts reached implausibly far');
}
// Navigation is a rate: live while the slot holds a card, never turned over.
{
  ok(E.PERKS.navigation.once === false,
     'Navigation is marked once-per-recycle, but "every sea move" is not one use');
  const p = withRow(2, { 4: 'navigation' });
  ok(p.hasPerk('navigation'), 'Navigation was not live at its slot depth');
  p.spendPerk('navigation');
  ok(p.hasPerk('navigation'), 'Navigation switched off when something spent it');
}

// The tokens carry SPEND or STANDING, and nothing else — the old deck names
// implied a power order this design removed. `once` is the only tag left, so
// it has to be right: a STANDING perk that reports as spendable would print a
// token telling the player to turn over something that never turns over.
{
  ok(!('deck' in E.PERKS.roads), 'the deck flavour tag survived in the engine');
  const standing = E.playablePerks().filter((id) => !E.PERKS[id].once);
  const spend = E.playablePerks().filter((id) => E.PERKS[id].once);
  ok(standing.length > 0 && spend.length > 0,
     'every wired perk is the same kind — one of the two labels is unused');
  /* A standing perk must keep working after something tries to spend it. */
  for (const id of standing) {
    const p = withRow(2, { 4: id });
    ok(p.hasPerk(id), `${id} was not live at slot 4 with two cards`);
    p.spendPerk(id);
    ok(p.hasPerk(id), `${id} is STANDING but switched off when spent`);
  }
  /* A spend perk must stop until the recycle. */
  for (const id of spend) {
    const p = withRow(2, { 4: id });
    ok(p.perkReady(id), `${id} was not ready at slot 4 with two cards`);
    p.spendPerk(id);
    ok(!p.perkReady(id), `${id} is SPEND but stayed ready after being spent`);
    p.refreshPerks();
    ok(p.perkReady(id), `${id} did not come back on the recycle`);
  }
}

// Slot 5 is not assignable — the engine refuses it, and the UI must not offer
// it either. It rendered as a drop target for a while, which silently threw a
// player's selection away.
{
  const p = new E.Player(0, E.BANDS, ['roads', 'coinage']);
  ok(!E.PERK_SLOTS.includes(5), 'slot 5 is in the assignable list');
  ok(!p.assignPerk('roads', 5), 'the engine accepted an assignment to slot 5');
  ok(p.slotOf('roads') !== 5, 'a perk ended up on slot 5 anyway');
  for (let s = 1; s <= 60; s++)
    for (const q of E.playOut(3, s * 17, { perks: true }).P)
      ok(!q.perks[5], `seed ${s} dealt a perk onto slot 5`);
}

// ------------------------------------------------ a whole game, perks on
{
  for (let s = 1; s <= 40; s++) {
    const g = E.playOut(3, s * 2654435761 % 2147483647, { perks: true });
    const total = g.score().reduce((a, x) => a + x.total, 0);
    ok(Number.isFinite(total) && total > 0, `seed ${s} scored ${total}`);
    ok(g.round > 0 && g.round < 60, `seed ${s} ran ${g.round} rounds`);
    for (const p of g.P) {
      ok(p.vrow.length <= 5, 'a victory row grew past five');
      ok(new Set(Object.values(p.perks)).size === Object.keys(p.perks).length,
         'a perk ended up on two slots');
    }
  }
}
// And that they fire at all. Every player holds Coinage here, so it is the
// deal that is pinned, not the odds.
{
  let coinage = 0, tribute = 0;
  const each = (id) => { const o = {}; for (let i = 0; i < 4; i++) o[i] = { 4: id }; return o; };
  for (let s = 1; s <= 120; s++) {
    coinage += (E.playOut(4, s * 40503, { perks: each('coinage') }).stats || {}).perk_coinage || 0;
    tribute += (E.playOut(4, s * 40503, { perks: each('tribute') }).stats || {}).perk_tribute || 0;
  }
  ok(coinage > 0, 'Coinage never paid out in 120 games — is it wired?');
  ok(tribute > 0, 'Tribute never paid out in 120 games — is it wired?');
  console.log(`    (coinage fired ${coinage}x, tribute ${tribute}x over 120 games each)`);
}

console.log(fail.length ? 'FAIL:\n  ' + fail.join('\n  ')
  : `perks: ${E.PERK_IDS.length} defined, ${E.playablePerks().length} wired, `
    + `dealt ${E.PERK_DEAL} a player from one flat pool — equal hands, no `
    + `duplicates, any perk on any slot, locked once the row has a card, and `
    + `off unless asked for`);
process.exit(fail.length ? 1 : 0);
