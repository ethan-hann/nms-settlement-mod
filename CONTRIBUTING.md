# Contributing to Overseer's Toolkit 🛠️

This is about working on the mod itself. For installing and playing, see the [README](README.md).

## How to contribute

Players' saves and builds depend on this mod, so every change is treated as one that reaches live games.

### Branches and pull requests

- Use one branch per piece of work. Never commit to `main`.
- Every change goes in through a pull request, and the maintainer merges.
- The PR body notes the tests you ran.
- If a change can stop a module from loading, say so in the PR. It puts player builds at risk.
- Out-of-scope findings become [GitHub issues](https://github.com/ethan-hann/nms-settlement-mod/issues) on this repo.

### Changing the mod

- Generated modules: edit the spec in `specs/` and rerun the generators. `tests/test_modules.py` fails when a generated file is edited by hand or goes stale.
- Test first: write the failing test before the implementation and see it fail on an assertion. An import or harness error isn't a red. Record the observed red in the commit message.
- When a test passes on its first run, break the code on purpose once to prove it can fail.
- Run Python through `tools/.venv`. Run the full suite with `tools/.venv/Scripts/python.exe -m pytest -q` before every commit that changes `mod/`, `specs/`, `tools/` or `tests/`. Commits that change only docs skip it.
- CI (`.github/workflows/tests.yml`) runs the suite on every PR and on pushes to `main`. It has no game data, so the tests that need `scratch/extracted` skip there, including the stale-module checks. A green CI run doesn't replace the local run.
- Check facts against the extracted game data in `scratch/` before proposing a design, and mark findings as verified, inferred or unknown.

### Player builds

The game deletes a placed part the moment it saves without the module that adds that part. So:

- Shipped `OT_` part IDs are permanent. Retire a part by hiding it from the build menu and keep its definition.
- Every release keeps all earlier parts loadable.

### Test session safety

- Saves are read-only. Inspect a copy of the test slot in `scratch/`, never the save folder.
- In `GAMEDATA/MODS`, touch only the `_OTDEV_*` folders.
- `GCMODSETTINGS.MXML` changes only through `tools/testmode.py`, and only while the game is closed.
- The full rules are in [docs/plan.md](docs/plan.md) section 3.

### Writing

- Repo prose (docs, comments, commits, PRs, issues) is ASCII, American English and concise, and names nobody.
- Code comments explain why in one line and never name a milestone, slice or phase.

## Repo layout

```
mod/<Module>/        each module, mirroring GAMEDATA/MODS/<Module>/
specs/<Module>.json  what each module adds; the generators turn these into patches
tools/               generators, checks, packaging and the test-session tool
tests/               pytest suite
runtime/spikes/      throwaway NMS.py experiments (not shipped)
docs/plan.md         build plan
docs/progress.md     progress log: decisions, test sessions, findings
COMPATIBILITY.md     generated list of vanilla edits
CHANGES.md           release notes
versions.json        each shipped module's version, plus the AllInOne bundle's version and contents
```

`OverseersToolkit-Probes`, `-TestTuning`, `-StoryTuning`, `-RewardProbes`, `-BrokenProbe`, `-TemplateProbe`, `-MissingIdProbe`, `-LedgerProbes`, `-SignProbes`, `-LedgerSetup` and `-LedgerRising` live in `mod/` for test sessions only and are never packaged. `-BrokenProbe` and `-TemplateProbe` are broken on purpose.

## Setup (Windows, PowerShell)

You need [uv](https://docs.astral.sh/uv/) and a Steam install of No Man's Sky.

```powershell
.\tools\bootstrap.ps1                          # Python venv + pinned MBINCompiler, hash-checked
.\tools\.venv\Scripts\python.exe tools\extract.py   # vanilla data from your install into scratch/ (never committed)
.\tools\.venv\Scripts\python.exe -m pytest -q
```

Pinned versions (game build, MBINCompiler, Python packages) are in [tools/tools.lock.json](tools/tools.lock.json).

## How parts are made

Parts, perks, judgements and unlock missions aren't written by hand. Each module's spec in `specs/` names what to add and which vanilla entry to copy, and the generators write the patches:

| Tool | Writes |
|---|---|
| `gen_parts.py` | build parts, build groups, costs, products, `LocTable.MXML` text |
| `gen_settlement.py` | settlement perks and judgements |
| `gen_unlocks.py` | class-gated unlock missions |
| `gen_ledger.py` | Fair Ledger's terminal payment options (cost, reward, dialog option), the flat debt step, and the Rebalance upkeep edits |

New parts reuse vanilla scenes only, so no custom 3D assets. The test suite merges every patch into vanilla data and compiles the result with the pinned MBINCompiler, so a broken patch fails before it ever reaches the game.

## Testing in game safely

`tools/testmode.py` is the only way in and out of a test session:

```powershell
python tools\testmode.py enter --modules core,defense,decor   # add --with-user-mods to keep your own mods on
python tools\testmode.py exit
python tools\testmode.py status
```

`enter` backs up your saves and settings, installs the modules as `_OTDEV_*` folders and points the game's mod list at them. It refuses when the test slot holds parts from a module you left out, because saving without that module would delete them. Until a session has recorded the test slot, it checks every slot from 6 up.

`exit` removes them, restores the mod list byte for byte, and proves nothing changed outside the test slot.

Both refuse while the game is running. Local paths and the test slot go in `scratch/testmode.local.json`.

> [!IMPORTANT]
> Always use **Load** and pick the test slot. Never press **Continue**.

After a session, `save_inspect.py` decodes the copied save and `check_export.py` checks the game's merged-data export, so results come from data, not from memory.

## Packaging a release

Each module's version and the bundle's live in [versions.json](versions.json). A module's version goes up only when its own files change, and the bundle's goes up when anything in it does.

```powershell
python tools\versions.py check     # compare versions.json with the last vX.Y.Z release tag
python tools\versions.py changed   # list what moved
```

The test suite runs the same check.

```powershell
python tools\package.py             # every shipped module, plus the bundle
python tools\package.py --changed   # only what moved since the last release
```

This writes `dist/<Module>-<version>.zip` for each shipped module plus `dist/OverseersToolkit-AllInOne-<version>.zip`. With `--changed`, it builds only the modules whose version moved since the last release, plus the bundle when one of its modules did.

On Nexus, upload each module's zip as a new version of that module's previous file, so Vortex only offers it to players who have that module. Upload AllInOne as the main file, never as an update of a single module's file.

After a release, tag the commit `vX.Y.Z`.

## After a game update

```powershell
python tools\check_build.py
```

It compares the installed build with the pinned one. Then update the pins, rerun `extract.py` and the tests. Failures name the field or ID that changed.
