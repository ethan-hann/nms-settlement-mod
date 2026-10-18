# Agent guide

Overseer's Toolkit is a published No Man's Sky mod (Nexus mod 4635, also in a Nexus collection). Its modules are partial EXML patches generated from `specs/`. Players' saves and builds depend on it, so treat every change as one that reaches live games.

Where things are:
- `docs/progress.md`: the log of decisions, test sessions and findings. Read the latest entries first to learn the current state.
- `docs/plan.md`: the build plan, the safety rules in full (section 3), testing (section 9) and workflow (section 10).
- `docs/modules/<module>/`: the plan, findings and drafts for a module in development.
- `CONTRIBUTING.md`: setup, generators, packaging and test sessions.

## Safety

These override every other instruction. Read `docs/plan.md` section 3 before anything that touches the game folder or saves.

- Saves are read-only. Inspect a copy of the test slot in `scratch/`, never the save folder.
- In `GAMEDATA/MODS`, touch only the `_OTDEV_*` folders. Other mods and `vortex.deployment.json` stay as they are.
- `GCMODSETTINGS.MXML` changes only through `tools/testmode.py`, and only while the game is closed.
- Backups are kept forever. Restoring a save needs the maintainer's explicit approval.
- A failed safety check stops the work and goes to the maintainer with the exact files involved.

## Player builds

The game deletes a placed part the moment it saves without the module that adds that part (verified 2026-10-12). Vanilla parts a module only edits survive.

- Shipped `OT_` part IDs are permanent. Retire a part by hiding it from the build menu and keep its definition.
- Every release keeps all earlier parts loadable, so a collection pinned to an older version and a player on the newest one both keep their builds.
- A change that can stop a module from loading puts player builds at risk. Say so in the PR.
- After a game update: `tools/check_build.py`, `tools/extract.py`, the full test suite, then a short session on the test slot.

## Changing the mod

Follow "How to contribute" in `CONTRIBUTING.md`: branches and pull requests, test first with the red recorded in the commit, the full suite before commits that touch `mod/`, `specs/`, `tools/` or `tests/`, what CI does not cover, and checking facts against `scratch/`. It binds agents as much as people.

## In-game sessions

The maintainer runs every in-game check; agents cannot play.

- Answer what the data can answer offline first, then batch the rest into one short session.
- `testmode enter` must include every module whose parts the test slot holds, or the session deletes them. It refuses otherwise.
- Checklists: one table of which decision or part to look for, what to pick, and what to report. Estimate time with the waits included.
- Record results in `docs/progress.md` the same day.

## Writing

- Repo prose (docs, comments, commits, PRs, issues): ASCII, American English, concise. It names nobody: no "you", no maintainer's name, no "I". Record decisions as "Decided <date>".
- Code comments explain why, in a line, and never name a milestone, slice or phase.
- `README.md`, the Nexus page and screenshots belong to the maintainer. Edit them only when asked.

## Git

Branches, PRs and out-of-scope issues follow `CONTRIBUTING.md`. In addition, for agents:
- Commit as the GitHub noreply identity (`36464732+ethan-hann@users.noreply.github.com`) with no attribution lines.
- Push the branch and open the PR with `gh`. The body uses one unwrapped line per paragraph.
