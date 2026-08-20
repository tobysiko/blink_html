# Putting v0.22 on GitHub

The commit is made — 177 files, and I verified from my side that **no file went
in empty**. Two things remain.

## 1 · Drop two files that are mine, not yours

`sim/_cmp_tmp.py` and `sim/_verify_tmp.py` are scratch scripts I copied into
`sim/` to run comparisons against the Python engine. The mount would not let me
delete them afterwards, so they ended up in the commit. Nothing is pushed yet,
so amend rather than adding a second commit:

```
cd ~/Documents/Claude/Projects/Blink/Blink_July2026/v0.23
git rm --cached -q sim/_cmp_tmp.py sim/_verify_tmp.py
rm sim/_cmp_tmp.py sim/_verify_tmp.py
git commit --amend --no-edit
```

## 2 · Create the repo and push — no `gh` needed

`gh` is not installed on your machine, and you do not need it.

Go to **github.com/new**:

- **Name:** `blink-v0.22`
- **Visibility: Private.** This is an unpublished design in submission to Hans im
  Glück, and the repo carries the full rulebook, the artwork and the
  print-and-play PDFs. Vercel deploys private repos without any trouble. You can
  open it later; you cannot close it again.
- **Do not** tick "Add a README", ".gitignore" or a licence — the repo already
  has them, and an initialised remote makes the first push conflict.

Then, using the URL GitHub shows you:

```
git remote add origin https://github.com/<your-user>/blink-v0.22.git
git push -u origin main
```

If you have SSH keys set up, `git@github.com:<your-user>/blink-v0.22.git` is
smoother — an HTTPS push asks for a personal access token rather than your
password.

Prefer the CLI after all? `brew install gh`, then `gh auth login`, then
`gh repo create blink-v0.22 --private --source=. --push`.

## 3 · Then Vercel deploys itself

On vercel.com: **Add New → Project → Import** the repo, then set

- **Root Directory:** `deploy`
- **Framework Preset:** Other
- no build command, no output directory

Every push to `main` republishes from then on, so the loop is:
edit `app/` → `node build.js` → commit → push → live.

Finally, Settings → Domains → `blink.deep-diversions.com`. Details in
`deploy/DEPLOY.md`.

---

### A note on the checks I gave you

The `find` command failed because I left a trailing `# expect no output` on it —
zsh does not treat `#` as a comment at an interactive prompt, so it was passed
to `find` as an argument. My mistake. You do not need to run it: I checked the
committed tree directly and every blob has content.

If you ever do want that check, without the comment:

```
find . -size 0 -type f -not -path "./.git/*"
```
