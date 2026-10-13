# Overseer's Toolkit 🏘️

**Your settlement deserves better than dirt and fireworks.**

Overseer's Toolkit is a No Man's Sky mod that gives settlement overseers the stuff a real town needs: stone paths, curbs, street lamps that run without power, and proper signs. Everything builds straight from the settlement's own build menu.

[![No Man's Sky 7.06 (COSMOS)](https://img.shields.io/badge/No%20Man's%20Sky-7.06%20COSMOS-blueviolet)](#compatibility)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Issues](https://img.shields.io/github/issues/ethan-hann/nms-settlement-mod)](https://github.com/ethan-hann/nms-settlement-mod/issues)

## What's in the box

The mod comes in three modules. Core works on its own; the other two are optional, and none of them depends on another.

| Module | What you get | Required? |
|---|---|---|
| 🧱 **OverseersToolkit** | A new **Decoration > SETTLEMENT** section: Path Tile, Path Triangle, Curb, Path Lamp, and 24 signs from the game (Illuminated Sign, Standing Sign, Station Billboard, holo displays, Gek / Korvax / Vy'keen emblems, number decals 0 to 9) | Yes |
| 🛡️ **OverseersToolkit-Defense** | A rare **"Fortify the perimeter?"** judgement that grants the **Perimeter Watch** perk (lower Sentinel alert level) for some debt, plus the decorative **Tower Pillar** | Optional |
| 🌿 **OverseersToolkit-SettlementDecor** | **489 vanilla decoration parts** buildable in settlements: exterior decor, lights, construction props, plants, statues, wall decals and posters | Optional |

### Unlocks

| Settlement class | Unlocks |
|---|---|
| B | Path Tile, Path Triangle, Curb, Path Lamp |
| A | All 24 signs |
| S | Tower Pillar (Defense module) |

In creative mode, everything is available from the start.

> [!WARNING]
> **Removing a module deletes what you built with it.** The moment the game saves without a module installed, every part that module added disappears from your save for good. That means the paths, curbs, lamps and signs from core, and the Tower Pillar from Defense. Settlement Decor only unlocks the game's own parts, so those stay. See [Uninstalling](#uninstalling) before you remove anything.

> **Heads up:** the class unlocks haven't been tested in a survival or normal game yet. They load fine and should™ work. If a part doesn't unlock when your settlement levels up, please [open an issue](https://github.com/ethan-hann/nms-settlement-mod/issues).

## Installing

**With Vortex:** install from Nexus as usual and pick the optional modules you want.

**By hand:**

1. Grab the zips you want from Nexus or the [releases](https://github.com/ethan-hann/nms-settlement-mod/releases).
2. Extract each one into `No Man's Sky\GAMEDATA\MODS`. Each zip already contains its own module folder.
3. Launch the game.

## Uninstalling

> [!WARNING]
> When the game saves without a module, it deletes every part that module added, and they can't be recovered from that save. Autosaves count too.

1. **Back up your saves first.** They live in `%APPDATA%\HelloGames\NMS\`.
2. Replace anything you want to keep with the game's own parts. Settlement Decor parts are the game's own, so they're safe.
3. Remove the module in Vortex, or delete its folder from `GAMEDATA\MODS`.

**Parts missing after an uninstall or a game update?** Quit without saving, reinstall the module (or wait for an update if a game patch broke it), then load again. Your parts are still in the save until the game saves without them.

## Using it

1. Become your settlement's overseer.
2. Stand inside the settlement and open the build menu.
3. The new parts are under **Decoration > SETTLEMENT**. With Settlement Decor installed, the other decoration tabs fill up too.

A few things worth knowing:

- Path tiles flatten the ground under them, so your streets stay flat.
- The Path Lamp lights up with no power hookup. 💡
- The fortify judgement is rare on purpose: about once every 18 hours of judgements, and judgements are drawn independently, so it doesn't come in bursts.

## Compatibility

- Built and tested on **No Man's Sky 7.06 (COSMOS)**.
- The mod ships small EXML patches and adds new `OT_` parts instead of editing vanilla ones wherever it can. [COMPATIBILITY.md](COMPATIBILITY.md) lists every vanilla entry and field each module touches, and it's generated from the patches, so it's always current.
- Want to build base-only parts (walls, landing pads, tech) right next to your settlement? Pair it with [gBase Boundries](https://www.nexusmods.com/nomanssky/mods/1369).
- Multiplayer: every part reuses a vanilla model, so visitors without the mod should still see what you built.

## Known limits

- The fortify judgement can turn up again after you already have Perimeter Watch. Just turn it down (it costs a little happiness).
- With Settlement Decor installed, those decoration parts can also be placed outside a base.
- No path-drawing tool yet: paths go down one piece at a time, like any other part.
- After a game update, check that your paths and signs are still there before you save. If they're gone, the update may have stopped the mod from loading: quit without saving and check the [issues](https://github.com/ethan-hann/nms-settlement-mod/issues) or the Nexus page.

## Reporting bugs and ideas 🐛

Please use the [issue tracker](https://github.com/ethan-hann/nms-settlement-mod/issues). Include your game version, which modules you have installed, and your other mods if you can. Screenshots of your towns are always welcome.

## Roadmap

- **Path tool.** Click points along a route and have the kit tiles laid for you, turned and snapped to the ground. It needs [NMS.py](https://github.com/monkeyman192/NMS.py) to support the current game build first; the latest release crashes the game at startup on 7.06.

## For modders and contributors 🛠️

Everything below is about working on the mod itself. Players can stop here.

### Repo layout

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
```

`OverseersToolkit-Probes` and `OverseersToolkit-TestTuning` live in `mod/` for test sessions only and are never packaged.

### Setup (Windows, PowerShell)

You need [uv](https://docs.astral.sh/uv/) and a Steam install of No Man's Sky.

```powershell
.\tools\bootstrap.ps1                          # Python venv + pinned MBINCompiler, hash-checked
.\tools\.venv\Scripts\python.exe tools\extract.py   # vanilla data from your install into scratch/ (never committed)
.\tools\.venv\Scripts\python.exe -m pytest -q
```

Pinned versions (game build, MBINCompiler, Python packages) are in [tools/tools.lock.json](tools/tools.lock.json).

### How parts are made

Parts, perks, judgements and unlock missions aren't written by hand. Each module's spec in `specs/` names what to add and which vanilla entry to copy, and the generators write the patches:

| Tool | Writes |
|---|---|
| `gen_parts.py` | build parts, build groups, costs, products, `LocTable.MXML` text |
| `gen_settlement.py` | settlement perks and judgements |
| `gen_unlocks.py` | class-gated unlock missions |

New parts reuse vanilla scenes only, so no custom 3D assets. The test suite merges every patch into vanilla data and compiles the result with the pinned MBINCompiler, so a broken patch fails before it ever reaches the game.

### Testing in game safely

`tools/testmode.py` is the only way in and out of a test session:

```powershell
python tools\testmode.py enter --modules core,defense,decor   # add --with-user-mods to keep your own mods on
python tools\testmode.py exit
python tools\testmode.py status
```

`enter` backs up your saves and settings, installs the modules as `_OTDEV_*` folders and points the game's mod list at them. It refuses when the test slot holds parts from a module you left out, because saving without that module would delete them. `exit` removes them, restores the mod list byte for byte, and proves nothing changed outside the test slot. Both refuse while the game is running. Local paths and the test slot go in `scratch/testmode.local.json`.

> Always use **Load** and pick the test slot. Never press **Continue**.

After a session, `save_inspect.py` decodes the copied save and `check_export.py` checks the game's merged-data export, so results come from data, not from memory.

### Packaging a release

```powershell
python tools\package.py
```

This writes `dist/<Module>-<version>.zip` for each shipped module, using the version in [VERSION](VERSION).

### After a game update

```powershell
python tools\check_build.py
```

It compares the installed build with the pinned one. Then update the pins, rerun `extract.py` and the tests. Failures name the field or ID that changed.

## Credits

- [MBINCompiler](https://github.com/monkeyman192/MBINCompiler) and [hgpaktool](https://pypi.org/project/hgpaktool/) for reading the game's data
- [NMS.py](https://github.com/monkeyman192/NMS.py) for the runtime experiments
- Hello Games for No Man's Sky

## License

[MIT](LICENSE)
