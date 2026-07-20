# One-time setup — the collaborator's machine (macOS)

A click-by-click checklist for the **technical collaborator** to follow while
sitting at the **non-technical collaborator's** Mac. Do these once, in order.
Allow ~30–45 minutes. This is the machine setup the
[two-person collaboration recipe](two-person-collaboration.md) assumes.

Goal: by the end, they can open Terminal, start Claude Code in the project
folder, and the auto-pull works — without ever opening GitHub Desktop again.

> Most steps assume macOS. On Windows the shape is the same but the install
> commands differ — ask Claude to adapt.

Throughout, replace `your-org/your-book-repo` with your actual private repo.

---

## Before you arrive

- [ ] Make sure they have (or create together) a **GitHub account**.
- [ ] On GitHub.com, add their account as a **collaborator** on the private repo:
      `your-org/your-book-repo` → **Settings → Collaborators → Add people**. They
      must **accept the email invite** before cloning will work.
- [ ] Decide where the project will live on their Mac, e.g. `~/Documents/book`.
      (This checklist uses `~/Documents` below.)

---

## 1. Install Git

Git often comes with Apple's Command Line Tools. Check first:

```
git --version
```

- If it prints a version, Git is installed. Skip to step 2.
- If macOS offers to install the Command Line Tools, click **Install**, wait,
  then re-run `git --version`.

---

## 2. Install GitHub Desktop (used once, for sign-in)

1. [ ] Download from <https://desktop.github.com> and drag it to Applications.
2. [ ] Open **GitHub Desktop**.
3. [ ] **File → Options → Accounts → Sign in to GitHub.com** and sign in with
       *their* GitHub account (the one you invited as a collaborator).
4. [ ] This quietly stores their credentials in the macOS Keychain. That's the
       point — Claude Code and the command line reuse this login, so they never
       type a password or token again.

> Keep GitHub Desktop installed, but you won't need it day-to-day.

---

## 3. Clone the repository

Pick one option.

### Option A — via GitHub Desktop (recommended, fewest surprises)

1. [ ] In GitHub Desktop: **File → Clone repository**.
2. [ ] Select `your-org/your-book-repo` from the list.
3. [ ] Set the local path (e.g. `~/Documents/your-book-repo`) and click **Clone**.

### Option B — via the command line

1. [ ] In Terminal:
   ```
   cd ~/Documents
   git clone https://github.com/your-org/your-book-repo.git
   ```
   Because they signed into GitHub Desktop in step 2, this should authenticate
   automatically. If it prompts for a password, the Keychain sign-in didn't take
   — redo step 2.

2. [ ] Confirm the files that make this workflow work came down:
   ```
   cd ~/Documents/your-book-repo
   ls .claude/settings.json CLAUDE.md docs/recipes/two-person-collaboration.md
   ```

---

## 4. Install Claude Code

1. [ ] Install via the official method (Homebrew, the installer, or an IDE
       extension). With Homebrew:
   ```
   brew install --cask claude-code
   ```
   (No Homebrew? Get it from <https://brew.sh> or download from
   <https://claude.com/claude-code>.)
2. [ ] Verify: `claude --version`
3. [ ] Sign them into Claude Code on first run (their Anthropic/Claude login,
       separate from GitHub).

---

## 5. First run — confirm everything works

1. [ ] In Terminal:
   ```
   cd ~/Documents/your-book-repo
   claude
   ```
2. [ ] **Watch for the auto-pull.** On startup the SessionStart hook runs
       `git pull`; you should see "Already up to date" or a summary. If you see
       nothing git-related, the hook didn't fire — see Troubleshooting.
3. [ ] Type **`I'm starting work`** and confirm Claude checks status and
       summarizes (proves it's reading `CLAUDE.md`).
4. [ ] **Test the safety block once, so you trust it:** ask Claude to run
       `git reset --hard HEAD`. It should be **refused/blocked**, not executed.
5. [ ] **Test the happy path:** make a tiny harmless change, then say
       **`I'm done for now`**. Confirm Claude shows the diff, proposes a message,
       asks before saving, and only pushes after a yes. Then `git log --oneline -1`.

If all five pass, they're ready. Walk them through the
[collaboration recipe](two-person-collaboration.md) cheat sheet.

---

## Troubleshooting

**Clone asks for a password / says repo not found.** They either haven't accepted
the collaborator invite, or the Keychain sign-in (step 2) didn't take. Re-open
GitHub Desktop, confirm they're signed in, and retry.

**Auto-pull didn't run on startup.**
- Confirm `.claude/settings.json` exists and is valid JSON with `permissions` and
  `hooks` (see the collaboration recipe for the exact contents).
- Make sure Claude Code is **trusted** in this folder — it asks once on first run.
- The hook only fires on a *fresh* start (matcher `startup`), not on resume.

**The safety block didn't block `git reset --hard`.** Usually the same trust issue
— settings aren't active until the project is trusted. Confirm the `deny` list is
present.

---

## What they never have to do

- Type git commands, write commit messages, open GitHub Desktop after setup, or
  understand branches, staging, or pushes.

All handled by Claude Code following `CLAUDE.md`, with `.claude/settings.json` as
the safety net.

---

## Installing the build toolchain

The steps above cover git + GitHub + Claude Code. To actually **build the book**
on this machine (render the PDF), also follow the "Install the toolchain" section
of the main [`README.md`](../../README.md) — one virtualenv and
`pip install -r requirements.txt`. If the non-technical collaborator only reviews
and edits text and never needs to produce the print PDF themselves, you can skip
that on their machine.
