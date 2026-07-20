# Recipe: two-person collaboration (one person doesn't use git)

A setup for **two people sharing one private book repo**, where one person is
comfortable on the command line and the other would rather never touch git. The
non-technical person drives everything through Claude Code with two phrases —
"I'm starting work" and "I'm done for now" — and Claude does the pulling,
committing, and pushing for them.

This is **opt-in**. The template ships without it so that forks start clean. If
you want it, apply the three pieces below.

> This recipe assumes a **private** repo (a shared book usually is). None of it is
> required to use the template, and it has nothing to do with the print pipeline.

---

## What it's made of

Three cooperating pieces:

1. **A protocol in `CLAUDE.md`** telling Claude what to do on "I'm starting work"
   / "I'm done for now" (below — paste it into your `CLAUDE.md`).
2. **`.claude/settings.json` automation + safety** — auto-pull the latest changes
   the moment the project opens, and hard-block destructive git commands (below).
3. **A one-time machine setup** for the non-technical collaborator's computer —
   see [`setup-collaborator-machine.md`](setup-collaborator-machine.md).

---

## 1. Add the protocol to `CLAUDE.md`

Paste this section into your `CLAUDE.md` (near the top is good):

```markdown
## Collaboration (two-person shared repo)

This private repo is shared by two people; one is non-technical and works with
git ONLY through you. Follow these protocols exactly.

**Session start** — when the user says "I'm starting work" (a `git pull` hook
also runs automatically on session start):
1. `git status`; if there are uncommitted changes from a prior session, ask
   whether to commit them BEFORE pulling.
2. `git pull --no-rebase`. Summarize what changed in plain English, or say
   "nothing new" if clean.
3. On a merge conflict: STOP. Explain it simply, propose a resolution that keeps
   both sides' intent, and wait for explicit confirmation before committing.

**Session end** — when the user says "I'm done for now":
1. `git status` and `git diff`; summarize the changes in plain English.
2. Draft an intent-based commit message (the WHY, not the file list); show it.
3. Ask for confirmation to save + sync. Only on yes: `git add` the changed
   files, `git commit`, `git push`. Then confirm "everything is synced."

**Always**
- Never run destructive git (force-push, reset --hard, clean -f, branch -D,
  rebase). These are also blocked in `.claude/settings.json`.
- Show what you're about to commit before committing; never commit without a yes.
- If a pull is not a clean fast-forward/auto-merge, stop and ask.
- Default to `main`; don't create branches unless explicitly asked.
```

## 2. Add automation + safety to `.claude/settings.json`

Merge this into your `.claude/settings.json`. The `hooks` block auto-pulls on
open; the `deny` list makes destructive git commands a hard wall, not a polite
request.

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force)",
      "Bash(git push --force *)",
      "Bash(git push -f)",
      "Bash(git push -f *)",
      "Bash(git reset --hard *)",
      "Bash(git clean -f *)",
      "Bash(git clean -d *)",
      "Bash(git clean -fd *)",
      "Bash(git checkout -- *)",
      "Bash(git branch -D *)",
      "Bash(git rebase *)"
    ]
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "git -C \"$CLAUDE_PROJECT_DIR\" pull --no-rebase --no-edit 2>&1 | tail -n 20"
          }
        ]
      }
    ]
  }
}
```

Both files live in the repo, so they are identical on both machines and stay in
sync. (Claude Code must **trust** the project before hooks and deny-lists take
effect — it asks once on first run; say yes.)

## 3. Set up the non-technical collaborator's machine

Follow [`setup-collaborator-machine.md`](setup-collaborator-machine.md) once, in
person if you can. After that they only ever say the two phrases.

---

## Day-to-day workflow (for the non-technical collaborator)

There are really only two phrases to remember.

**Starting a session**
1. Open the project in Claude Code. The latest changes pull automatically — you'll
   see a short note about what came in (or nothing, if there's nothing new).
2. To be sure, you can also say: **"I'm starting work."** Claude double-checks and
   summarizes anything new.

**Ending a session** — say: **"I'm done for now."** Claude will show a summary of
what changed, propose a plain-English description of the work, ask if you want to
save and sync, and only push after you say yes.

You never have to think about git, branches, commits, or pushes.

### Cheat sheet

| Situation | What you say to Claude |
|---|---|
| Starting a session | "I'm starting work" |
| Ending a session | "I'm done for now" |
| Confused about something | "What's happening right now?" |
| Want to undo recent work | "Can you revert my last change?" |
| Something looks broken | "Please don't change anything else and explain what state we're in" |

---

## When things go sideways

**"Merge conflict."** Both of you edited the same file between syncs. Tell Claude
what's happening (it probably already knows). It will look at both versions,
propose a combined version that keeps both intents, and ask you to confirm. If
you're unsure, message the other collaborator.

**"It says I have to pull first."** The other person pushed while you were working.
Tell Claude: "Please pull the latest changes and merge them with what I have."

**General rule.** If anything feels weird, **stop and ask** — either ask Claude to
explain, or message the other collaborator. Git keeps a full history, so as long
as nothing wild happened, work is almost always recoverable — and it's much easier
to fix before a commit than after.
