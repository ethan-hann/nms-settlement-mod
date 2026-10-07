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
- **M4 (`OverseersToolkit-Defense`, `-TestTuning`):** perk OT_WATCH lowers the hidden Alert gauge and the Sentinels stat ("Sentinel Alert Level" in the settlement screen; the plan's literal "raises Sentinels" contradicted its stated goal); appended Request judgement "Fortify the perimeter?" grants it for added debt; OT_TOWER reuses the stone support pillar scene. Estimate from vanilla rates: about one fortify decision per 55 hours of judgements without test tuning.
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

**Decision: no-go for a runtime path tool.** Per the plan, the fallback is the offline save-edit planner. It works on a copy of the creative test slot, and installing it needs Ethan's approval.

Its pieces are known:
- The save codec is in `save_inspect.py`.
- The base frame is in `runtime/spikes/base_frame.py`.
- Objects are `{"ObjectID", "Position", "Up", "At", "Timestamp", "UserData"}` entries in `PersistentPlayerBases[*].Objects`.
- Ethan's earlier corvette scripts already write saves and their `mf_` metadata (never tested in game).

The untested spike sketches in `runtime/spikes/` stay for when NMS.py catches up; each file states its assumptions. Asking upstream about a placement function needs Ethan's GitHub or Discord account.
