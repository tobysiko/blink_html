# Putting v0.22 on GitHub

`README.md` and `.gitignore` are written and ready. The commit has to be made by
you — see *Why* at the bottom.

## Decide first: private or public

This is an unpublished design in submission to Hans im Glück, and the repo would
contain the full rulebook, the card and board artwork, and the print-and-play
PDFs. **Private is the safer default**; Vercel deploys private repos without any
trouble. Make it public later if you want print-and-play in the open — you
cannot un-publish something that has been public.

## Create it

```
cd ~/Documents/Claude/Projects/Blink/Blink_July2026/v0.22
git init -b main
git add -A
git commit -m "Blink v0.22 — rules, components, simulation and browser prototype"
```

Then, with the GitHub CLI:

```
gh repo create blink-v0.22 --private --source=. --push
```

Or without it: make an empty repo on github.com, then

```
git remote add origin git@github.com:<you>/blink-v0.22.git
git push -u origin main
```

## Check nothing went up empty

Worth doing once, because it is exactly what went wrong here:

```
git ls-files | wc -l                          # expect ~176
find . -size 0 -not -path "./.git/*" -type f  # expect no output
```

If any file lists as zero bytes, do not push — say so and we will work out why.

## Then Vercel deploys itself

On vercel.com: **Add New → Project → Import** the repo, then set

- **Root Directory:** `deploy`
- **Framework Preset:** Other (it is a single static file)
- no build command, no output directory

Deploy. Every push to `main` then republishes automatically, and
`app/build.js` regenerates `deploy/index.html`, so the loop is:
edit `app/` → `node build.js` → commit → live.

Finally add the subdomain — Settings → Domains → `blink.deep-diversions.com`.
Details in `deploy/DEPLOY.md`.

## Why I could not make the commit

My sandbox reaches your folder through a mount, and **49 of the files cannot be
read through it** — `stat` reports the right size but every read fails with
`Resource deadlock avoided`. They are the files I had not opened earlier in the
session: the rulebook and deck PDFs, `PRINT-AND-PLAY.md`, `README.txt`, most of
`source/`, and the `sim/findings-*.txt` set.

That is not a harmless failure. When I copied the tree to build the repo, `tar`
hit the read errors and left **files of the correct length containing nothing but
zero bytes** — and a size check said everything matched. Only comparing
checksums caught it. Committing that would have published 49 empty files that
look fine in a directory listing.

Run the commands above on your own machine, where the files are real, and none
of this applies.
