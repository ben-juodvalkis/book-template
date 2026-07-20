# Recipes

Optional, self-contained add-ons for the template. Each recipe is something a
book *might* want but most don't need, so it lives here instead of in the default
setup. Follow a recipe only if you want what it describes; ignore the rest.

| Recipe | For |
|---|---|
| [`two-person-collaboration.md`](two-person-collaboration.md) | Two people sharing one private book repo, where one works with git only through Claude Code. Adds an auto-pull-on-open hook, a destructive-git safety block, and a plain-English commit/sync protocol. |
| [`setup-collaborator-machine.md`](setup-collaborator-machine.md) | The one-time, click-by-click machine setup that the collaboration recipe assumes (install git, sign in to GitHub, clone, install Claude Code). |

The template ships **without** any of these applied — a clean single-author,
single-machine starting point. The collaboration recipe explains exactly which
files to add and what to paste into them if you want that workflow.
