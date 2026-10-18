# Contributing to Overseer's Toolkit 🛠️

This is about working on the mod itself. For installing and playing, see the [README](README.md).

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
