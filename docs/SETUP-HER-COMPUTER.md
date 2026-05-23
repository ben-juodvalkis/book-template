# One-Time Setup Checklist — Her Computer (macOS)

A click-by-click checklist for **Ben** to follow while sitting at the
collaborator's Mac. Do these once, in order. Allow ~30–45 minutes.

Goal: by the end, she can open Terminal, start Claude Code in the project folder,
and the auto-pull works — without ever opening GitHub Desktop again.

> Most steps assume macOS. If she's on Windows, the shape is the same but the
> install commands differ — ask Claude to adapt.

---

## Before you arrive

- [ ] Make sure she has (or create with her) a **GitHub account**.
- [ ] On GitHub.com, add her account as a **collaborator** on the private repo:
      `ben-juodvalkis/book-template` → **Settings → Collaborators → Add people**.
      She must **accept the email invite** before cloning will work.
- [ ] Decide where the project will live on her Mac, e.g. `~/Documents/book` or
      `~/DevWork`. (The checklist uses `~/Documents` below.)

---

## 1. Install Git

Git often comes with Apple's Command Line Tools. Check first:

```
git --version
```

- If it prints a version (e.g. `git version 2.39.x`), Git is installed. Skip to
  step 2.
- If macOS pops up a dialog offering to install the Command Line Tools, click
  **Install** and wait. Then re-run `git --version`.

---

## 2. Install GitHub Desktop (used once, for sign-in)

1. [ ] Download from <https://desktop.github.com> and drag it to Applications.
2. [ ] Open **GitHub Desktop**.
3. [ ] **File → Options → Accounts → Sign in to GitHub.com** and sign in with
       *her* GitHub account (the one you invited as a collaborator).
4. [ ] This step quietly stores her credentials in the macOS Keychain. That's the
       whole point — Claude Code and the command line will reuse this login, so
       she never has to type a password or token again.

> You can keep GitHub Desktop installed but you won't need it day-to-day.

---

## 3. Clone the repository

You can clone via GitHub Desktop (easiest) **or** the command line. Pick one.

### Option A — via GitHub Desktop (recommended, fewest surprises)

1. [ ] In GitHub Desktop: **File → Clone repository**.
2. [ ] Select `ben-juodvalkis/book-template` from the list.
3. [ ] Set the local path (e.g. `~/Documents/book-template`) and click **Clone**.

### Option B — via the command line

1. [ ] In Terminal:
   ```
   cd ~/Documents
   git clone https://github.com/ben-juodvalkis/book-template.git
   ```
   Because she signed into GitHub Desktop in step 2, this should authenticate
   automatically (no password prompt). If it does prompt, the Keychain sign-in
   didn't take — redo step 2.

2. [ ] Confirm the files are there, including the ones that make this work:
   ```
   cd ~/Documents/book-template
   ls .claude/settings.json CLAUDE.md docs/COLLABORATION.md
   ```
   All three should exist. They came down with the clone — nothing to install.

---

## 4. Install Claude Code

1. [ ] Install via the official method (Homebrew, the installer, or the IDE
       extension — whichever you both prefer). If using Homebrew and it's
       present:
   ```
   brew install --cask claude-code
   ```
   (If Homebrew isn't installed, get it from <https://brew.sh> first, or use the
   download from <https://claude.com/claude-code>.)
2. [ ] Verify:
   ```
   claude --version
   ```
3. [ ] Sign her into Claude Code the first time it runs (follow its prompts —
       this is her Anthropic/Claude login, separate from GitHub).

---

## 5. First run — confirm everything works

1. [ ] In Terminal:
   ```
   cd ~/Documents/book-template
   claude
   ```
2. [ ] **Watch for the auto-pull.** On startup, the SessionStart hook in
       `.claude/settings.json` runs `git pull`. You should see a line like
       "Already up to date" or a summary of changes. *If you see nothing related
       to git on startup, the hook didn't fire — see Troubleshooting.*
3. [ ] Type: **`I'm starting work`** and confirm Claude responds by checking
       status and summarizing (this proves it's reading `CLAUDE.md`).
4. [ ] **Test the safety block (do this once so you trust it):** ask Claude to
       run `git reset --hard HEAD`. It should be **refused/blocked**, not
       executed. If it runs, the deny-list isn't loading — see Troubleshooting.
5. [ ] **Test the happy path:** make a tiny change (ask Claude to add a blank line
       somewhere harmless), then say **`I'm done for now`**. Confirm Claude shows
       the diff, proposes a message, asks before saving, and only pushes after you
       say yes. Then check it landed:
   ```
   git log --oneline -1
   ```

If all five pass, she's ready. Walk her through `docs/COLLABORATION.md` (the
two phrases and the cheat sheet) and you're done.

---

## Troubleshooting

**Clone asks for a password / says repo not found**
She either hasn't accepted the collaborator invite, or the Keychain sign-in
(step 2) didn't take. Re-open GitHub Desktop, confirm she's signed in, and retry.

**Auto-pull didn't run on startup**
- Confirm the file exists and is valid: `cat .claude/settings.json` (it should be
  the JSON with `permissions` and `hooks`).
- Make sure Claude Code is **trusted** in this folder — on first run it may ask
  you to confirm you trust the project before hooks/settings activate. Say yes.
- The hook only fires on a *fresh* start (matcher `startup`), not on resume.

**The safety block didn't block `git reset --hard`**
- Same trust issue as above is the usual cause — settings aren't active until the
  project is trusted.
- Confirm the `deny` list is present in `.claude/settings.json`.

**She accidentally opened GitHub Desktop and it's confusing**
That's fine — she can close it. It's only needed for the one-time sign-in. Day to
day, everything happens through Claude Code in Terminal.

---

## What she never has to do

- Type git commands herself
- Write commit messages
- Open GitHub Desktop after setup
- Understand branches, staging, or pushes

All of that is handled by Claude Code following `CLAUDE.md`, with
`.claude/settings.json` as the safety net.
