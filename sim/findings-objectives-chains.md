# Final objective deck — six mixed-terrain chains

Every card asks for the same shape in different terrain: **three tiles you
occupy in a chain**, the middle one touching both ends. Measured with seeking
bots, two objectives per batch so each gets 58–116 samples.

| Objective | Chain | Achieved | 95% interval |
|---|---|---|---|
| Foothills | mountain – forest – plains | **64.7%** | 56–73 |
| Highland Rivers | mountain – forest – ocean | **53.4%** | 44–63 |
| Fjord | mountain – ocean – mountain | **51.7%** | 39–65 |
| Mountain Pass | plains – mountain – plains | **48.3%** | 35–61 |
| Coastal Chain | plains – ocean – plains | **40.5%** | 32–49 |
| River Delta | ocean – plains – forest | **34.5%** | 22–47 |

All six land between 35% and 65%, and every interval overlaps its neighbours.
That is the tightest band any objective family has produced — the single-terrain
cards ranged from 10% to 47% depending on whether the setup happened to seed
them.

**Why chains work.** A chain of three terrains needs one tile of each, which is
exactly what a per-suit explore budget of about two supports. A single-terrain
pattern needs three of one suit and runs straight into that ceiling — unless the
starting map already seeded it, which is what made the mountain patterns look
achievable and the forest ones look broken.

**Points are flat at 4.** The spread is 1.9× from easiest to hardest, which is
narrow enough not to need compensating. More to the point, the global rate is
not what a player is choosing on: with deal-two-keep-one, the decision is which
chain suits the hand they drafted. Someone holding Ocean finds the Fjord close;
someone holding Plains finds the Mountain Pass close.

**Cut, and why.** Mountain Fortress and Mountain Range — the three-player
starting map is *itself* a mountain triangle, so those were occupied rather than
built, and only at three players. Deep Wood and Open Sea — genuine builds, but
they land near 20% with wide intervals because nothing seeds forest or ocean.
Everything requiring four or more tiles was already gone.

**What this costs.** Thematic range. Six chains have a family resemblance that
six different shapes did not, and there is no card that says "hold a wood" or
"command a sea". If the map is ever given real geography — terrain placed in
regions rather than at random — the single-terrain cards become buildable and
worth revisiting.

## Methodology note

Rates measured on 20–30 samples carry a 95% interval near ±20 points and swung
by 26 points between runs of the same objective. Use `seek3.py`, which runs two
objectives per batch and prints intervals. Note it assigns two of three seats to
the first objective and one to the second, so the first gets double the samples.
