# Progress log

One entry per milestone and test session, newest last. Forward-looking notes live here, not in code comments.

## 2026-10-06: M0, tooling and safety

Done:

- `tools/tools.lock.json` pins MBINCompiler v7.04.1-pre3 (with release hashes), hgpaktool 1.1.3, lz4, zstandard, pytest, and game build 180836 (Steam buildid 25732212). `tools/bootstrap.ps1` fetches and verifies them.
- `tools/testmode.py` (enter, exit, status, resolve) with 35 tests on a fake game tree, including a real fake `NMS.exe` process. Machine paths live in the gitignored `scratch/testmode.local.json`; tests refuse to build the real environment.
- `tools/extract.py`, `tools/check_build.py`, `tools/save_inspect.py`, `tools/merge_preview.py`, and the shared `tools/nmsenv.py` (game discovery through Steam's library list, running-game check).
- Verified from a fresh clone: bootstrap, extract, check_build and all 73 tests pass.

Findings:

- **Globals sit at the pak root** (`gcbuildingglobals.global.mbin`), not under `GLOBALS/`. gBase Boundary ships `GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML`, so it may not load at all on this build. Our patches use the pak path; P4 confirms it.
- **Patch semantics seen in installed mods:** `_id` matches or appends, `_index` matches, keyless list items append, `_overwrite="true"` replaces a list. `merge_preview.py` models this, and installed mods' table patches merge and compile under it.
- **Custom text:** three installed mods ship a `LocTable.MXML` (template `cTkLocalisationTable`) at the mod root. P3 tries that convention.
- `GCMODSETTINGS.MXML` has a BOM, CRLF line endings and no trailing newline. `testmode` round-trips the real file byte for byte.
- NMS.py's latest release (180383.0) is still one build behind the game.
- Save slots 1 to 5 are in use, so a new creative game should land in slot 6 (`save11.hg`, `save12.hg`). `testmode exit` learns the slot the first time it appears.

Open for later:

- `save_inspect.py` matches bases to settlements by address. The settlement address format is assumed and must be checked against the first real test-slot copy.

## 2026-10-06: M1 probes and Session 1

Built: `tools/gen_parts.py` (part tables from a spec, copied from vanilla parts), `tests/test_modules.py` (every module under mod/ merges, compiles, and has complete parts), and the probe module `mod/OverseersToolkit-Probes` (never shipped).

Session 1 ran in three short rounds on a new creative save, which became test slot 6 (`save11.hg`, `save12.hg`).

Results:

- **Safety:** every exit restored GCMODSETTINGS and removed `_OTDEV_PROBES`; protected saves and all other mods verified unchanged each time. The last exit flagged only the slot 6 files Ethan deleted in game to start a new creative game; he approved and it was resolved. `testmode` now allows deleting the known test slot.
- **P4 (open settlements): no.** With `RadiusMultiplier_DoNotPlaceAnywhereNear` at 0.000001 (pak-root globals patch), the base computer still showed "Cannot Build // Within Existing Base" (`BASEBUILD_INVALID_INSIDE_BASE`) until about 312u from the settlement marker. That matches the vanilla `MinRadiusForBases` of 300, so the settlement appears to count as a base with that radius. Unconfirmed: whether a pak-root globals patch loads at all; the visible check for it was in round 2, which crashed.
- **P1, P2, P3, new subgroup: inconclusive.** No probe part appeared, and no star (MOD) tab. Creative games know an explicit list (`difficultyconfig` `StartWithAllItemsKnownEnabledData.InitialKnownThings.KnownProducts`, 1386 IDs), which lists no new part and not DECALPATH. New parts need a way to become known before any of these can be judged.
- **P5, P6, P8:** not reached (P8 needs an owned settlement; P6 was not reported).
- **Crashes:** rounds 2 and 3 crashed while loading the test save and while creating a new creative game (crash IDs 180836M_0x4BE63F and 180836M_0x9BD78A). Round 1 loaded fine. Added in every crashing run: a mission appended to the empty `modmissiontable` (copied from vanilla GLASS_FIX, empty StartingConditions, inline recipe reward; it crashed even when teaching a vanilla part); `MinRadiusForBases` 100 and `BuildingPlacementMaxDistance` 150; BUILDPAVING in a second subgroup; the probe judgement's perk grant in its correct `GcSettlementJudgementPerkOption` form (round 1's malformed form compiled to an empty grant). The mission is the prime suspect but is not proven.
- **Save facts:** settlements live in a 100-entry ring buffer (`SettlementStatesV2`), most entries empty (address 0); a nearby settlement the player never visited is not stored. `save_inspect.py` now skips empty entries and reads the game mode from `DifficultyState`.

Process change (Ethan's feedback): no more iterating probes in game. Open questions get answered offline first (installed mods, public mod scripts, docs, data validation), and the rest is batched into one short Session 2.
