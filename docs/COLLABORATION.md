# Collaborating on This Book with Claude Code + GitHub

A guide for two people sharing a private project, where one person uses the
command line and the other doesn't want to.

## How this works at a high level

We use **git** to track changes to the project and **GitHub** to sync those
changes between our two computers. GitHub hosts a private repository (a "repo" —
basically a synced folder with full history) that only we can access. Nothing is
public.

The clever part: on your machine, **Claude Code handles all the git stuff for
you**. You won't need to learn git commands or use any special app day-to-day.
You just tell Claude "I'm starting work" and "I'm done for now," and it pulls the
latest changes, saves your work, and syncs it back.

There's a one-time setup where we get everything installed and signed in on your
machine. After that, you can mostly forget it exists.

> **Two things are already set up for you in this project** and you never have to
> touch them: a `CLAUDE.md` file tells Claude exactly how to behave (the
> start/end protocols), and a `.claude/settings.json` file (a) automatically
> pulls the latest changes the moment you open the project and (b) blocks
> dangerous git commands so they can't run by accident. Both arrived
> automatically when you cloned the repo. See Part 4.

---

## Part 1: One-Time Setup (we'll do this together in person)

The detailed click-by-click version lives in **`docs/SETUP-HER-COMPUTER.md`** —
that's the checklist Ben follows at your computer. In short, we will:

1. **Install Git** — the underlying version control system.
2. **Install GitHub Desktop** — a simple app for signing into GitHub. You'll only
   need it once (or rarely), but it's the easiest way to get authenticated.
3. **Sign you into GitHub Desktop** with your GitHub account. Once you sign in
   here, your computer remembers it, and Claude Code can use that same login
   behind the scenes.
4. **Install Claude Code** — the tool we'll both be using.
5. **Clone the repository** — this downloads the project folder onto your
   machine, connected to the GitHub copy. The `CLAUDE.md` and
   `.claude/settings.json` files come down with it automatically.

After this, you can close GitHub Desktop and not open it again unless something
unusual happens.

---

## Part 2: Your Day-to-Day Workflow

This is the whole thing. There are really only two phrases to remember.

### Starting a work session

1. Open the project in Claude Code.
2. **The moment it opens, the latest changes are pulled automatically** — you'll
   see a short note about what came in (or nothing, if there's nothing new).
3. To be sure, you can also just say: **"I'm starting work."** Claude will
   double-check and summarize anything new.

Then start describing what you want to build or change.

### Ending a work session

When you're done, say: **"I'm done for now."**

Claude will:
- Show you a summary of what changed
- Propose a plain-English description of the work (you don't write it)
- Ask if you want to save and sync
- If yes: save the changes and push them up to GitHub so Ben can see them

That's it. You never have to think about git, branches, commits, or pushes as
concepts.

### During the session

Work normally. Ask Claude to build, change, or fix things. You don't need to save
anything manually — that's what the "I'm done" step is for.

---

## Part 3: What to Do When Things Go Sideways

There are really only two situations that could trip you up. Both are manageable.

### "Merge conflict"

This happens if both of us edited the same file between syncs. Git won't know
which version to keep, so it asks for help.

**What to do:** Tell Claude what's happening (it will probably already know).
Claude is very good at resolving these — it will look at both versions, propose a
combined version that keeps both of our intents, and ask you to confirm. Read
what it suggests and say yes if it looks right, or describe what you'd rather it
do.

If you're unsure, text Ben. We can hop on a call and sort it out in five minutes.

### "It says I have to pull first"

This happens if Ben pushed changes while you were already working. Just tell
Claude: "Please pull the latest changes and merge them with what I have." It'll
handle it.

### General rule

If anything feels weird or scary, **stop and text Ben before clicking anything**.
Git is very good at preserving history — it's almost impossible to actually lose
work — but it's much easier to fix things before they're committed than after.

---

## Part 4: The Files That Make This Work (for reference)

You don't need to read or edit either of these — they're set up for you. This is
just so you know what's going on under the hood.

**`CLAUDE.md`** (in the project folder) is an instruction file Claude reads every
session. Its `## Collaboration` section tells Claude exactly what to do when you
say "I'm starting work" or "I'm done for now," and that it must always show you a
change before saving and never save without your yes.

**`.claude/settings.json`** is the safety-and-automation file. It does two things
the instructions alone can't guarantee:

- **Auto-pull on open** — runs `git pull` automatically every time you start the
  project, so you always begin with the latest version even if you forget to say
  "I'm starting work."
- **Hard safety blocks** — the genuinely dangerous git commands (force-push,
  hard reset, force-clean, deleting branches, rebase) are *refused outright*.
  Even if something tried to run them, they won't execute. This is a real wall,
  not just a polite request.

Both files live in the repo, so they're identical on both our machines and stay
in sync.

---

## Part 5: What About Branches and Pull Requests?

You may have heard those terms. Here's the short version of when they matter:

- **For most of what we'll do together, we won't bother with branches.** We'll
  both commit to the main project, and as long as we communicate roughly about
  who's working when, it'll be fine.
- **If we want to try something experimental** without affecting the main
  project, Ben can have Claude create a "branch" — a separate parallel version.
  You don't have to do anything different.
- **Pull requests** are a GitHub feature for reviewing changes before they merge.
  If we ever want them (probably not at our scale), Ben will set it up and walk
  you through it.

---

## Summary cheat sheet

| Situation | What you say to Claude |
|---|---|
| Starting a session | "I'm starting work" |
| Ending a session | "I'm done for now" |
| Confused about something | "What's happening right now?" |
| Want to undo recent work | "Can you revert my last change?" |
| Something looks broken | "Please don't change anything else and explain what state we're in" |

When in doubt, **stop and ask** — either ask Claude to explain, or text Ben. Git
keeps a full history of everything, so as long as we haven't done anything wild,
it's almost always recoverable.

Welcome to the project!
