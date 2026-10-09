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

- **Safety:** every exit restored GCMODSETTINGS and removed `_OTDEV_PROBES`; protected saves and all other mods verified unchanged each time. The last exit flagged only the slot 6 files the maintainer deleted in game to start a new creative game; that was approved and resolved. `testmode` now allows deleting the known test slot.
- **P4 (open settlements): no.** With `RadiusMultiplier_DoNotPlaceAnywhereNear` at 0.000001 (pak-root globals patch), the base computer still showed "Cannot Build // Within Existing Base" (`BASEBUILD_INVALID_INSIDE_BASE`) until about 312u from the settlement marker. That matches the vanilla `MinRadiusForBases` of 300, so the settlement appears to count as a base with that radius. Unconfirmed: whether a pak-root globals patch loads at all; the visible check for it was in round 2, which crashed.
- **P1, P2, P3, new subgroup: inconclusive.** No probe part appeared, and no star (MOD) tab. Creative games know an explicit list (`difficultyconfig` `StartWithAllItemsKnownEnabledData.InitialKnownThings.KnownProducts`, 1386 IDs), which lists no new part and not DECALPATH. New parts need a way to become known before any of these can be judged.
- **P5, P6, P8:** not reached (P8 needs an owned settlement; P6 was not reported).
- **Crashes:** rounds 2 and 3 crashed while loading the test save and while creating a new creative game (crash IDs 180836M_0x4BE63F and 180836M_0x9BD78A). Round 1 loaded fine. Added in every crashing run: a mission appended to the empty `modmissiontable` (copied from vanilla GLASS_FIX, empty StartingConditions, inline recipe reward; it crashed even when teaching a vanilla part); `MinRadiusForBases` 100 and `BuildingPlacementMaxDistance` 150; BUILDPAVING in a second subgroup; the probe judgement's perk grant in its correct `GcSettlementJudgementPerkOption` form (round 1's malformed form compiled to an empty grant). The mission is the prime suspect but is not proven.
- **Save facts:** settlements live in a 100-entry ring buffer (`SettlementStatesV2`), most entries empty (address 0); a nearby settlement the player never visited is not stored. `save_inspect.py` now skips empty entries and reads the game mode from `DifficultyState`.

Process change: no more iterating probes in game. Open questions get answered offline first (installed mods, public mod scripts, docs, data validation), and the rest is batched into one short Session 2.

### Correction, same evening: globals belong under GLOBALS/

The M0 finding that globals "sit at the pak root" was right about the paks and wrong about mods. NMS.exe's mod-loading code references `/GLOBALS`, `/BASEBUILDINGPARTS` and `/LOCTABLE.MXML` as per-mod inputs, and all 25 globals patches among the installed mods use `<mod>/GLOBALS/` (every field still valid on this build). The probe's root-level globals patches were therefore most likely never applied, so **P4 never actually ran**, and the decision probe was inert too. gBase Boundary's GLOBALS/ path is the normal one, not a broken one. `merge_preview.py` now maps `GLOBALS/X` to the root-level vanilla file, and all globals patches move under `GLOBALS/`.

Other findings from mining the installed mods (all read-only):

- The loader also has a native `<mod>/BASEBUILDINGPARTS/` route; libMBIN defines `GcModBasePart` (ProductData, PartData, ID), and vanilla's unused `MOD` build group looks made for it. Not used by any installed mod; untested.
- No vanilla part sits in two subgroups of the same top-level group, but the probe put Paving in two Decoration subgroups. That is now the second crash suspect after the mission, and it has been removed.
- Working patterns for making items obtainable in existing saves: keyless nodes appended to unlock trees (Unlockable Expedition Exclusive Techs, Craftablemodules), specials-shop entries (Consumerism), reward-table appends (BetterRewardsCombined). No installed mod adds a mission, a judgement or a perk.
- Vanilla recipe-teaching catch-up missions (`STORAGE_FIX`, `BP_ANALYSER_FIX`) wait a moment before a silent reward; the probe's mission rewarded on the first tick, non-silently.

## 2026-10-06: M2 to M5 built, pending Session 2

Built in parallel worktrees by subagents and integrated here; every patch merges and compiles with the pinned MBINCompiler, and all tests pass.

- **M2 core (`OverseersToolkit`):** OT_PATH_TILE, OT_PATH_TRI (stone quarter floor and triangle), OT_CURB (short stone wall), OT_SIGNPOST (Data Display Unit scene), OT_LAMP (standing light with the vanilla street lamp's no-power settings) in a new Decoration > Settlement subgroup; DECALPATH gets a product, that subgroup and a 250 limit. New parts carry `IsFromModFolder=true`, as public part mods do. Vanilla parts that already exist elsewhere are not added to the subgroup: no vanilla part sits twice in one top-level group.
- **M3 (`OverseersToolkit-OpenSettlements`):** `MinRadiusForBases` 300 to 15 under GLOBALS/. Cost: every new base starts that small and grows by the vanilla extension as parts are placed. `tools/compat_report.py` regenerates COMPATIBILITY.md and scans a MODS folder read-only; on the installed mods it flags gBase Boundary (`MinRadiusForBases`) and notes the merged timer mod sharing GCSETTLEMENTGLOBALS.
- **M4 (`OverseersToolkit-Defense`, `-TestTuning`):** perk OT_WATCH lowers the hidden Alert gauge and the Sentinels stat ("Sentinel Alert Level" in the settlement screen; the plan's literal "raises Sentinels" contradicted its stated goal); appended Request judgement "Fortify the perimeter?" grants it for added debt; OT_TOWER reuses the stone support pillar scene. Estimate from vanilla rates: about one fortify decision per 55 hours of judgements without test tuning (corrected 2026-10-07: about 28 hours; the estimate counted the wrong number of vanilla requests).
- **M5 (class gating):** expressible in data. The only class check vanilla offers is the mission condition `GcMissionConditionHasSettlementBuilding` (MinimumClass). Unlock missions are copies of vanilla STORAGE_FIX appended to `npcmissiontable`: class B teaches the path kit, curb, lamp and DECALPATH; class A the signpost; class S the tower. New creative games know every part through the creative KnownProducts list.

Open for Session 2: whether the parts show and place in a new creative game; whether the decal follows slopes and flora clears (P5); whether a base can be claimed in a settlement with the smaller radius; whether the appended judgement and perk load and fire; whether the missions load without crashing (class gating itself needs a B-class building, which a short session can't reach).

## 2026-10-06: M6 runtime feasibility (desk spike)

The in-game spike could not run: the newest NMS.py is 180383.0 and the game is 180836, and no matching release, branch or PR exists yet. Past releases trailed game patches by 0 to 6 days, and one patch was skipped entirely. NMS.py also needs Python 3.13 or older, so it needs its own venv; `tools/.venv` is 3.14. What could be settled without the game:

| Step | Finding | Verdict |
|---|---|---|
| 1. Log a base's objects | `cGcGameState.mSavedInteractionsManager.maPersistentBaseBuffers` → `cGcPlayerBasePersistentBuffer.maBaseBuildingObjects` are declared in NMS.py's types. Of 393 hook patterns, 368 match exactly once in the 180836 exe, including every base-building hook the spikes use (offsets unverified). | Go once NMS.py supports 180836 |
| 2. World to base-local | Confirmed from a save: object positions are base-local, with Y = normalized base Position and Z = Forward. Implemented and tested in `runtime/spikes/base_frame.py`. The NMS.py stub types `GetBaseBuildingRootMatrix`'s result as a vector, where it should be a 3x4 matrix. | Go |
| 3. Place DECALPATH from code | No spawn, place or add function exists in NMS.py, its examples, or any public runtime mod. Finding the game's commit-a-part function means reverse engineering the 7.x exe. Writing straight into the object vector would not create the world object. | **No-go today** |
| 4. Flatten terrain | `ApplyTerrainEditFlatten` is declared, but its arguments and the beam instance are not. | Optional, low odds |

**Decision: no-go for a runtime path tool.** Per the plan, the fallback is the offline save-edit planner. It works on a copy of the creative test slot, and installing it needs the maintainer's approval.

Its pieces are known:
- The save codec is in `save_inspect.py`.
- The base frame is in `runtime/spikes/base_frame.py`.
- Objects are `{"ObjectID", "Position", "Up", "At", "Timestamp", "UserData"}` entries in `PersistentPlayerBases[*].Objects`.
- The maintainer's earlier corvette scripts already write saves and their `mf_` metadata (never tested in game).

The untested spike sketches in `runtime/spikes/` stay for when NMS.py catches up; each file states its assumptions. Asking upstream about a placement function needs the maintainer's GitHub or Discord account.

## 2026-10-06: Session 2, part A, and the fixes it led to

`testmode enter --modules core,open,defense,testtuning`, a new creative game in slot 6, with the test-only `SaveOutModdedMetadata` export on. Exit passed every safety check; the game's export went to `scratch/exported/20261006-222620`, and `tools/check_export.py` found every module edit in it (the cost table is not part of the export).

What the test session showed:
- No crash creating or loading the game.
- Decoration > SETTLEMENT listed the kit under its English names; the Tower Pillar sat under Structural Adornments.
- A base computer could be claimed about 110u from the settlement centre, against about 312u before.
- The path tiles flatten the ground. That is intended and stays.
- The lamp gave no light.
- The Settlement Path placed with a sound but showed nothing.
- "Fortify the perimeter?" appeared after about 20 minutes of being overseer, and again right after; the second acceptance showed Perimeter Watch. Both added debt.
- Inside the settlement, the overseer's build menu offered only fireworks, fossils and portable tech. Near the base the menu flipped between the base and the settlement.

What the save copy showed: OT_WATCH in the settlement's perks once, every kit part in KnownProducts, and the three unlock missions loaded (Progress -1).

Causes, from the game files:
- The lamp copied BUILDLIGHT2, whose bulb hangs under a connected-to-power node. The vanilla Lamp Post (S_STREETLAMP0) keeps its lights at the scene root. OT_LAMP now copies it.
- DECALPATH's scene is an empty `PathDecal` locator. Settlement paths are drawn by the settlement generator around that marker, so a placed copy renders nothing. It is out of the kit and the B unlock. A future runtime path tool would lay kit tiles, not DECALPATH.
- The overseer menu lists only parts with `BuildableOnPlanet=true` (built outside a base). Every kit part and the tower now set it.
- The repeat decision is the test tuning; judgements have no "already owned" condition, so a rare repeat in normal play costs debt for no new perk.
- The menu flip is the game choosing between overlapping base and settlement areas. It is a side effect of OpenSettlements and of gBase Boundary alike.

Decided 2026-10-06:
- The data-display signpost did not read as a sign. It is replaced by 24 vanilla signs copied under their vanilla names (so every game language has them): the Illuminated Sign, Standing Sign, Station Billboard, the holographic displays, the Gek, Korvax and Vy'keen emblem decals and the number decals 0 to 9. They unlock at class A.
- Scope: new optional module `OverseersToolkit-SettlementDecor` sets `BuildableOnPlanet` on every planet-base part in the Decoration, Exotics and Wall Art groups (489 today), leaving out the 13 lights that draw power. `gen_parts.py` gained `group_edits` to generate it from the vanilla groups. Side effect: those parts can also be placed outside any base.
- The side-effect check for the smaller base radius is settled by the maintainer's own play: gBase Boundary sets the same field to 10, and buildings and points of interest spawn normally.

## 2026-10-07: Session 2, final pass

Two launches on slot 6, each closed with every safety check passed.

Launch 1, `testmode enter --modules core,open,defense,decor,testtuning` (export `scratch/exported/20261007-201237`):
- Inside Funana Bridge the build menu listed the kit, the Path Lamp and all 24 signs under Decoration > SETTLEMENT, and the other decor tabs showed the SettlementDecor parts.
- Placed parts survived save and reload. The lamp lights indoors and at night.
- Perimeter Watch is still in the settlement's features.
- `check_export.py` on the five installed modules: every edit landed except the cost table, which the export does not include.

Launch 2, the same modules plus `--with-user-mods` (export `scratch/exported/20261007-202657`): the SETTLEMENT section and the placed parts were still there. Two expected differences in the export, both from the maintainer's mods loading over ours:
- gBase Boundary sets `MinRadiusForBases` to 10 instead of our 15 (listed in COMPATIBILITY.md).
- The merged timer mod sets `JudgementWaitTimeMin`/`Max` to 20/30 instead of TestTuning's 60/120. TestTuning is test-only, so this does not affect a release.

The save copy (`scratch/saves/save11.hg`, same counts in save12): placed parts are stored in `PlayerStateData.BaseBuildingObjects`, not in a player base (37 OT_CURB, 17 OT_PATH_TILE, 2 OT_LAMP, OT_SIGN_STAND, OT_HOLO_GEK, OT_DECAL_GEK). Every kit part and all 24 signs are in KnownProducts, OT_WATCH is in the settlement's perks once, and the three unlock missions are loaded.

Session 2 is closed. No open in-game questions remain from it.

## 2026-10-07: OpenSettlements dropped

Decided. Every part the mod adds is now built from the settlement's own menu (`BuildableOnPlanet`), so no base is needed to build in a settlement. The module's only remaining use was claiming a base beside a settlement for base-only parts (walls, floors, pads, powered tech). That came at a cost: it shrank the starting radius of every new base, made the build menu flip near settlements, and conflicted with gBase Boundary, which already does the same thing at radius 10.

Removed: `mod/OverseersToolkit-OpenSettlements`, its test, and the `open` key in `testmode.py`. COMPATIBILITY.md is regenerated, and a scan of the maintainer's MODS folder now finds no conflicts, only shared files. For the release facts: players who want full base-building next to a settlement can add gBase Boundary alongside this mod.

## 2026-10-07: NMS.py trial on build 180836

NMS.py 180383.0 was tried on game build 180836 anyway. Setup: uv-managed Python 3.13.14 and `nmspy==180383.0` (pymhf 0.2.4) in `runtime/.venv`, outside the tools venv. NMS.py has no version lock; it uses the exe hash only to name its pattern cache. The session ran under `testmode` (core, defense, decor, testtuning), and exit passed every safety check.

Result: NMS.exe crashed during startup on every launch, before the main menu and before FullLog.txt got any content. Windows logged Application Error 1000 each time: fault in ntdll.dll, exception 0xc0000374 (heap corruption).
- Two launches with spike 1 (`pymhf run runtime/spikes/spike1_log_base_objects.py`): injection completed, the pattern cache was written, the mod GUI opened, and then the game died after resuming.
- One launch of bare NMS.py (`pymhf run nmspy`, with an empty mod folder): same crash. The cause is NMS.py's own startup hooks (`cTkFSM.StateChange`, `cTkFSMState.StateChange`, `cGcApplication.Update`) on 180836, not our spike.

Conclusion: NMS.py 180383.0 does not run on 180836. The runtime path tool waits for an NMS.py release for the current build. `SUPPORTED_BUILDS` is back to 180383 only. An upstream issue with these crash details would need the maintainer's GitHub account.

## 2026-10-07: Release prep (M8), 1.0.0

Decided: version 1.0.0; the fortify decision should be rare, about once every 18 hours of judgements.

- **Fortify rate.** The vanilla pool has four Request judgements (total weighting 4.01), and Request is drawn for about 20% of judgements when BuildingChoice is not on offer. At weighting 1.0, fortify came up about once every 28 hours; it is now 1.8, about once every 18 hours (6.3% of judgements; two in a row 0.4%). Judgements are drawn independently, so the rate does not cluster. There is still no way in data to stop it after the perk is owned.
- **Packaging.** `tools/package.py` writes `dist/<Module>-<version>.zip` for OverseersToolkit, -Defense and -SettlementDecor. Each zip holds the module folder and only the files the loader reads. Probes and TestTuning are test-only; a test fails if a module is in neither list. The version lives in `VERSION`.
- **CHANGES.md** has the 1.0.0 entry.

Release facts, for the Nexus page and README:
- Game build: validated on NMS.exe 180836 (Steam build 25732212), MBINCompiler v7.04.1-pre3.
- Install: extract each zip into `GAMEDATA/MODS`. Core works alone; Defense and SettlementDecor are optional and independent of each other and of core.
- Use: become a settlement's overseer and open the build menu inside the settlement; the parts are under Decoration > SETTLEMENT (SettlementDecor adds parts to the other decor tabs).
- Not yet seen in game: the class B, A and S unlock missions granting parts in a normal (non-creative) game. They load without errors, but no test session reached a B-class building.
- Compatibility: COMPATIBILITY.md lists every vanilla entry and field each module edits. Against the maintainer's 55 installed mods, the scan finds no field conflicts. gBase Boundary is a good companion for building base-only parts beside a settlement.
- Multiplayer: every part reuses a vanilla scene, so visitors without the mod see the meshes.
- Known limits: the fortify decision can repeat after Perimeter Watch is owned; the Settlement Path decal is not buildable (its scene is an empty marker); no path-drawing tool yet (waits for an NMS.py release for the current game build).
