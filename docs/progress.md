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

## 2026-10-09: Settler Stories tooling and test slice, pending Session 3

Plan, findings and decisions are in [modules/settler-stories/](modules/settler-stories/plan.md).

- **Generator.** `gen_settlement.py` writes custom judgements (Weighting 0), option chains, vanilla reward IDs and gift options. It rejects a chain that targets anything but a custom judgement, a story step no pool option can reach, and a chain loop. Options no longer inherit a chain from their source. A new module test fails when a generator stops writing a file, which the byte-for-byte check alone missed.
- **save_inspect.** Reports each settlement's race, pending custom judgement and last judgement time.
- **Test slice.** `OverseersToolkit-SettlerStories` (route A: a pool option chains to custom step `OT_SS_A2`) and the hand-written `OverseersToolkit-StoryProbes` (route B: a pool option's reward fires custom step `OT_SSP_B2`). Both are test-only and all text is marked [TEST]. Both merge and compile against vanilla.
- **Session 3 asks:** does route A or B start the follow-up, and how soon; does `%RACE%` show the town's race; do the nanites reward, the perk and the gift arrive; does a follow-up ever appear on its own.

## 2026-10-09: Session 3, Settler Stories chains

Modules: SettlerStories test slice (route A), StoryProbes (route B), TestTuning, on the creative test slot.

- **Route B fails.** The custom step fired by a reward on a pool option (`OT_SSP_B2`) appeared on its own, 4 times in a row, with no other decision shown. The save confirms 5 judgements settled (12 before, 17 after): one vanilla expedition debrief left pending from earlier play, then the 4 probe steps. Inferred cause: option rewards run when a judgement is drawn, and the fired judgement overrides it. The StoryProbes module is removed; it is in history at 533460a.
- **Route A untested.** Its first step never came up while route B's reward was installed.
- The custom step showed up only at the overseer terminal, with no in-game alert, 2 to 4 minutes apart.
- Safety: exit passed all checks.

## 2026-10-09: Session 3b, route A

Modules: SettlerStories (the real content) and TestTuning, on the creative test slot.

- **Route A works.** A Sealed Vault led straight to The Old Seeds, and Overdue to Shelter in the Ruins and then The Relics, each at once and with the story's own header. No story step appeared on its own. Item, productivity and nanite rewards arrived as previewed.
- **Alert has no label on the choice screen.** The Buried Beacon's second option showed the raw key `UI_SETTLEMENT_STAT_HAPPY_FMT` for its Alert change; no vanilla option changes Alert. The generator now rejects Alert and BugAttack in options, and those options use Sentinels instead.
- "Keep the best, plant the rest" paid out a random rare item (a predator skull); it now gives Hexaberries.
- Not yet seen in game: the Policy, StrangerVisit and Conflict dilemmas, the three-step Stranger at the Gate story, and the three perks. TestTuning favors Request.
- Safety: exit passed all checks.

## 2026-10-12: Session 3c, the other decision types

Modules: SettlerStories and StoryTuning, on the creative test slot.

- **All five non-Request dilemmas work:** The Night Market, The Wage Dispute, A Fevered Traveller, Festival of Lights and A Stranger at the Gate show correct text and labels, and their stat, item and quicksilver previews match what arrives.
- **The three-step story works.** A Stranger at the Gate led straight to Rumours and then The Crew Comes Looking; Stand together added the Sanctuary feature, confirmed in the save. Turn them away ended the story with its reward.
- **Festival of Lights** set off fireworks only when funded. `R_SET_FW_PARTY` shows its own random reason for the party, so the dilemma text no longer names one.
- The Wage Dispute came up three times because it is the only Conflict dilemma left under StoryTuning; normal play mixes it with the vanilla Conflict judgements.
- Not taken in game: Hand them over for the bounty (its 405 quicksilver preview showed), and the Ancient Orchard and Relic Hall perks (the same perk mechanism as Sanctuary).
- **Placed parts are deleted when a save is loaded and saved without the module that adds them.** The test slot held 38 OT_CURB and other OT_ parts on 2026-10-09; Sessions 3 and 3b ran without core, and by 2026-10-12 every OT_ part was gone while vanilla parts stayed. Test sessions on this slot need the modules whose parts it holds, and players need an uninstall warning. The 2026-10-09 backup (`overseers-toolkit-backups/20261009-192543`) still has the parts.
- Safety: exit passed all checks.

## 2026-10-12: Keeping placed parts safe for existing players

1.0.0 has about 370 downloads and is in a Nexus collection (Beyond Infinity, 89 mods), so player builds and update resilience now matter more than new features.

Verified in Sessions 3 and 3b: loading and saving without the module that adds a placed part deletes that part. Vanilla parts a module only edits (everything SettlementDecor touches) survive. Core adds 29 parts and Defense 1; SettlementDecor adds none.

The rules that follow from this (permanent part IDs, loadable earlier parts, the game-update check) are in `AGENTS.md`.

Open questions, for a session before the next release:
- What the game's mod loader does when a partial patch no longer matches after a game update: skip one file, skip the whole module, or stop loading. If it skips a module, a game update alone could delete builds when the player saves.
- Answered: a town perk whose module is missing is hidden, not deleted. Session 3c ran without Defense; the town did not show Perimeter Watch, yet the save still lists `OT_WATCH`, and nothing crashed. Whether it returns, and whether a hidden perk still changes stats, goes to Session 4.
- What happens to a save whose pending decision is a Settler Stories step (`PendingCustomJudgementID` set to an `OT_SS_` ID) when SettlerStories is removed. Must be tested before SettlerStories ships.

## 2026-10-15: Session 4, probes, removal and a broken patch

Three launches on the creative test slot. Safety: every exit passed all checks.

**Part A** (RewardProbes, StoryTuning):
- `%RACE%` in judgement text is shown literally; the dilemma screen does not fill it in.
- The vanilla `WORD` reward taught Gek words ("Gek", "friend") and `STANDING` raised Gek standing, both previewed on the option. The town is Gek and sits in a Gek system, so whether they follow the settlement's race or the system's is unknown.
- `UseGiftReward` gives a random item from the general gift list (nanites, Hex Core, Glowing Mineral), not the race list.
- A two-step probe story was left with its second step pending at save time (`PendingCustomJudgementID` `OT_RP_P3B`).

**Part B** (core and Defense only, so the pending step's module was missing):
- The save loads, but the terminal's "Greet settlement visitor" opens a placeholder decision (header "Judgement", subheading "Sub heading", raw `UI_SETTLEMENT_STAT_*_FMT` labels, `%NUM%` text, unrelated NPC dialogue) whose options cannot be chosen. The game had to be closed with Alt+F4. The step stays pending in the save, so this repeats until the module is back. The rest of the terminal works.
- Perimeter Watch, hidden while Defense was missing in Session 3c, shows again with Defense installed: a missing-module perk is hidden and returns, never deleted.

**Part C** (BrokenProbe, SettlerStories, StoryTuning, RewardProbes):
- With RewardProbes back, the pending step opened normally and answering it cleared it from the save.
- A patch file that sets a field the game does not have still loads: the game ignores that field and applies the rest of the file (BrokenProbe's decision appeared). Other modules were unaffected. Only an unknown field was tested; a renamed list or a template mismatch is still unknown.

Consequences:
- **Removing SettlerStories while a story step is pending soft-locks that town's decisions** until it is reinstalled. Recovery: reinstall, answer the step, remove again. Release notes and the README need this before SettlerStories ships.
- Game updates that rename a single field are less dangerous than feared: the rest of the patch still applies.
- `WORD` and `STANDING` are usable player rewards for race-neutral stories. `%RACE%` and the gift give no race flavour.

## 2026-10-15: 1.1.0 release prep

Decided 2026-10-15: ship Settler Stories as 1.1.0 with the removal warning first in the README section and the changelog, and rebalance the options to an even player and settlement split (see [modules/settler-stories/stories.md](modules/settler-stories/stories.md)).

- **Packaging.** SettlerStories ships; Probes, TestTuning, StoryTuning, RewardProbes and BrokenProbe are test-only, and a test pins both lists.
- **Testmode guard.** Until a session records the test slot, `enter` checks every slot from 6 up for parts from modules left out, instead of skipping the check. Tests now cover a real compressed save and the slot's second save file.
- **Fortify rate.** SettlerStories adds four Request decisions at weighting 1.0, so with it installed, fortify drops from about once every 18 hours of judgements to about once every 30 (same inferred draw model as 1.0.0).
- **Not yet seen in game:** the four options changed in the rebalance (they use only reward types proven in Session 4), the Orchard and Relic Hall perks, and the bounty path.

## 2026-10-17: Session 5, the 1.1.0 checks and game-update probes

Three launches on the creative test slot. Safety: every exit passed all checks.

**Part A** (core, Defense, SettlementDecor, SettlerStories, TestTuning):
- A Sealed Vault led to The Old Seeds, and planting them added **Ancient Orchard**. The second Overdue run ended in **Relic Hall**. Both perks show in the settlement's features and are in the save.
- "Leave the relics, copy the carvings" taught a Gek word ("I") and raised happiness, as previewed.

**Part B** (core, Defense, SettlementDecor, SettlerStories, StoryTuning):
- "Give them a bed" taught a Gek word ("you") and changed population and happiness as previewed. The preview names the reward only as "Uncharted words x 1", the game's own label.
- "Keep it small and join in" raised Gek standing from 9 to 11 in the save. Too small to notice in game; the preview said "Standing Increased: Gek".
- "Keep their secret" taught a word, and The Crew Comes Looking still followed at once: an option can pay a reward and chain to the next step.
- "Hand them over for the bounty" paid 423 quicksilver, matching the preview.
- The Wage Dispute came up often, as in Session 3c, because it is the only Conflict decision StoryTuning leaves.

**Part C** (core, Defense, SettlerStories, TestTuning, TemplateProbe, MissingIdProbe):
- **A wrong template name is ignored.** TemplateProbe's decision came up, and the export shows the file merged under the real template.
- **An edit to a part ID the game does not have is dropped, and the rest of the file applies.** The export has no `OT_NO_SUCH_PART`, WEAPONRACK became buildable on planets (seen in the build menu), and core's and Defense's 30 parts in the same table all landed. The build menu works normally.
- The export never contains `BASEBUILDINGCOSTSTABLE`, in this session or earlier ones, so check_export cannot confirm core's and Defense's cost entries. Inferred: the game does not export that table.

Consequences:
- Every 1.1.0 option and perk has now been seen working in game.
- Game updates are less likely to delete builds than feared. Verified: an unknown field, a renamed template, or a vanilla part ID removed from under SettlementDecor each leaves the rest of the patch in place. Still unknown: a renamed list, a changed struct type, and a field whose type changes.
- `WORD` and `STANDING` gave Gek rewards in a Gek town in a Gek system, so whether they follow the settlement's race or the system's is still unknown.

## 2026-10-17: Fair Ledger planning

Plan and findings are in [modules/fair-ledger/](modules/fair-ledger/plan.md); nothing is built. Extra vanilla tables (dialog, consumables, specials, trading costs, settlement UI) were pulled read-only into `scratch/extracted-ledger/`.

- Every building's C level costs more upkeep than it produces at the midpoint; production buildings turn positive by B or A class.
- The overseer's Administration Terminal is a dialog entry whose options take a cost ID and reward IDs, so a units-for-debt option looks possible in data. Which town the reward pays is unknown.
- A reward can only name a stat strength; the largest Debt step is 50,000 to 100,000.
- Installed mods already override vanilla text keys through `LocTable.MXML`.
- All five installed reward-table mods are now partial patches, so appended reward entries survive them.

Decided 2026-10-17, details in the plan: two modules (FairLedger with the debt option and wording, FairLedger-Rebalance with the contribution edits); pay at the Administration Terminal; Debt PositiveLarge made a flat 100,000, priced at 2 units per 1 debt; hide the option at zero debt if the session allows; break-even for production buildings only; English text overrides if other languages keep their text; no guide sign, with a read-only town sign kept as a later add-on idea.

Next: the probe module and one session.

## 2026-10-17: Session 6, Fair Ledger probes

Two launches on the creative test slot with core, Defense, SettlerStories and LedgerProbes. Safety: both exits passed all checks.

**Part A** (first probe build):
- The C-level upkeep marker landed at once on existing buildings: production building pages read "Upkeep cost 1,111", and Maintenance Cost fell from 381,454 to 127,768 a day. With productivity at 579,063, the town's debt turned to falling ("Debt will now be automatically repaid over time").
- The terminal showed the four vanilla options and the first two appended ones, after Leave. The third appended option never appeared. No vanilla dialog has more than six options.
- "Pay toward debt: 100,000" cut the local town's debt by exactly 100,000, with the message "Settlement debt reduced: 100,000 units".
- Prices showed at a third (66,000 for 200,000) and nothing was charged: units stayed at 332,096 in the save. The save's Purchases difficulty was Free, which scales units by 0.33 and makes interaction costs free (`CurrencyCostOptionData` in difficultyconfig).

**Part B** (six-option probe, Purchases set to Standard for the run and back to Free after):
- The price read 200,000 units. Each payment took exactly 200,000 units and cut exactly 100,000 debt. The save confirms every payment took the full price: units went from 5,332,096 to 932,096 over 22 payments, and the last one took 200,000 with only about 64,800 debt left.
- At zero debt the option stayed visible and selectable. A `DisablingConditions` entry with a Debt stat-level condition did nothing. Paying at zero debt took 200,000 units and showed "Settlement reserves increased: 100,000", but the saved Debt stat is 0 and the settlement state has no reserves field. The payment is lost.
- With debt at 0, the production panel showed the output slots again.
- The text override of `UI_SETTLEMENT_PROD_DEBT_TIP2` showed in English. In French, that tip and both [TEST] option labels showed their raw keys.
- "Reserves" appears nowhere in the overview or the history page.

Consequences:
- The terminal route works: the reward reaches the terminal's own town, and the flat 100,000 step makes the cut exact.
- The terminal holds two appended options at most, and only if no other mod adds one.
- No data guard stops a payment at zero debt; the option text must warn instead (plan decision 4, fallback B).
- A `LocTable.MXML` entry with only English and USEnglish shows the raw key in every other language. That applies to all Toolkit text, not just overrides.
- On Free Purchases the payment is free, and on Discounted it costs 0.66 units per debt.

Decided 2026-10-17: every text entry is translated into all 17 languages, using the game's own terms, with English as the fallback for keys not yet translated (issue #22); the payment's price follows the Purchases setting.

Decided 2026-10-17 for the build ([modules/fair-ledger/build-plan.md](modules/fair-ledger/build-plan.md)): ship the 100,000 and 1,000,000 payment options; each production building's C upkeep range becomes its C productivity range; issue #22 comes first and one 1.2.0 release carries both; one check session before release. Planning is complete.

Next: issue #22, then the FairLedger generator.

## 2026-10-17: Text in every game language

Decided 2026-10-17 (issue #22): every LocTable entry is translated into all 17 columns, using the game's own terms. Translations are not checked by native speakers; the changelog says so and asks for corrections.

- **Spec form.** A `text` entry in a spec is either a plain string (English in every column, used by the test-only modules) or an object with English and each of the 15 other languages. `null` marks a pending translation, which repeats the English. gen_parts.py rejects a translation that is empty, repeats the English without `null`, drops a `%PLACEHOLDER%` or names an unknown language. USEnglish always repeats English.
- **Tests.** Shipped modules must use the object form, and every `_NAME` must be its `_NAME_L` in capitals in every language, as vanilla does.
- **Glossary.** extract.py now pulls every language file, and tools/loc_glossary.py shows how vanilla words a term in each language. Verified: each vanilla language file fills only its own column, and TencentChinese is filled for about half the keys (none of the settlement decisions) with Simplified Chinese text, except for a different word for pirates.
- **Term reference.** The shipped specs are the reference for later text, Fair Ledger included: the cost brackets in OT_FORT_OPT1 (debt), OT_SS_D1_O2 (units), OT_SS_S3C_O2 (nanites) and OT_SS_D3_O1 (settlers) give each language's wording.
- **Coined terms.** Vanilla has no word for path tile, curb, foreman, night market or perimeter in most languages, so those are new wording. Where vanilla's word for vault is a storage box or compartment, German and Dutch use vanilla's seed-vault word instead (Samenkammer, kluis).
- **Seen in game (verified 2026-10-17):** the translated LocTables load and show their translations.

## 2026-10-17: Town sign exploration

Plan and findings are in [modules/remote-terminal/](modules/remote-terminal/plan.md). The settlement's own terminals are vanilla base parts: `SET_MAYORTERM` (the Administration Terminal), `SET_INT_SUMMARY` (the building-detail terminal) and `SET_MONUMENT` (the Settlement Interface). Each is placeable and has a product but is not buildable on planets or known to players. A sign that shows live numbers in the world needs runtime code. The test-only SignProbes module makes copies of the first two buildable, to see what they open away from their building.


## 2026-10-17: Session 7, town sign probes

One launch on the creative test slot with core, Defense, SettlerStories and SignProbes. Safety: exit passed all checks.

- Both probe parts showed in the build menu under the [TEST] tab, with a wooden-wall placeholder thumbnail. The existing creative save learned them from `creative_known`.
- The building-detail terminal copy could not be placed: "Must Be Constructed Underwater". Its vanilla entry allows neither water nor land.
- The Administration Terminal copy, placed in open ground, worked as the full office terminal, and its status page opened.
- The monument (Settlement Interface) opens the status page at once.
- The status page offers Change Output, and its history page offers Retire as Overseer, so no vanilla page is read-only.
- With LedgerProbes no longer installed, Maintenance Cost was back at 381,454 a day (127,768 with the probe's upkeep marker in Session 6). Removing a contribution patch restores vanilla upkeep at once.
- The slot's newer save file (`save12.hg`) holds no placed probe part; the older `save11.hg` still holds one Administration Terminal copy, so a session that leaves SignProbes out may be refused by `testmode enter`.

Decided 2026-10-17: ship the Administration Terminal copy as a remote terminal, buildable anywhere on a planet, inside or outside a base; a live-updating sign needs runtime code and is dropped. Plan in [modules/remote-terminal/plan.md](modules/remote-terminal/plan.md).

Next: Session 8, the terminal away from the town.

## 2026-10-17: Session 8, the terminal away from the town

One launch with core, Defense, SettlerStories and SignProbes. Safety: exit passed all checks.

- The Administration Terminal copy, placed on Funana Bridge's planet well outside the town, showed every option disabled: "No pending decisions" (though a construction choice was pending) and "Terminal reserved for Overseer" on status and all settlements. The terminal only works inside its own town.
- The rest of the checklist was skipped, since other planets and bases cannot do better.
- The slot's newer save file (`save12.hg`) holds no placed probe part.

Decided 2026-10-17: the remote terminal is dropped; Fair Ledger ships in 1.2.0 on its own. Findings stay in [modules/remote-terminal/plan.md](modules/remote-terminal/plan.md).

## 2026-10-17: Reproducible release zips

Decided 2026-10-17 (issue #17): module files are LF on every checkout. `.gitattributes` sets `eol=lf` for `.EXML` and `.MXML` under `mod/` and marks `.MBIN` binary. The index already held LF, so only working copies change. package.py refuses a text file holding a carriage return and writes every zip entry with a fixed timestamp and mode, so two builds of one commit give identical zips (verified 2026-10-17 by building twice with touched files). A test checks that the shipped module files on disk match the committed bytes. The next release changes the bytes of every file that shipped as CRLF; CHANGES.md says the change is line endings only.

## 2026-10-17: Fair Ledger built

Built per [modules/fair-ledger/build-plan.md](modules/fair-ledger/build-plan.md), pending the check session.

- `tools/gen_ledger.py` generates both modules from `specs/OverseersToolkit-FairLedger.json` and `specs/OverseersToolkit-FairLedger-Rebalance.json` and joins the stale-module checks in `tests/test_modules.py`.
- FairLedger: costs `C_OT_FL_PAY1` (200,000 units) and `C_OT_FL_PAY10` (2,000,000), rewards `R_OT_FL_DEBT1` (one Debt PositiveLarge step) and `R_OT_FL_DEBT10` (ten in one GiveAll list), two options appended to `SETTLEMENT_ADMIN` with `KeepOpen` and no disabling conditions, Debt PositiveLarge a flat -100,000, and five vanilla text overrides. All text is in 17 languages.
- Rebalance: the nine production buildings' C upkeep ranges equal their C productivity ranges, read from vanilla by stat type. The values match the build plan's table.
- Both are in `package.SHIPPED`, have testmode keys `fairledger` and `fairledgerrebalance`, and are listed in COMPATIBILITY.md. The text overrides do not appear there, because the report lists LocTable.MXML only as a whole file.
- Translation choices: `UI_SETTLEMENT_STAT_COST_NAME` keeps each language's vanilla wording, since only the English named the stat three ways and decision text around it may depend on its grammatical form. `UI_SETTLEMENT_STAT_UPKEEP` uses each language's upkeep word plus "per day", kept about as short as vanilla. Numbers follow each language's vanilla separator, with a no-break space where the separator is a space.
- New test-only module LedgerSetup (key `ledgersetup`): the test town had no debt and the test character 732,096 units (save copy after Session 8), too few for the 2,000,000 payment. It turns the terminal's "Manage all settlements" option into a free option giving 5,000,000 units and 25 Debt NegativeLarge steps, so the terminal stays at six options.
- Unknown until the session: whether ten stat steps in one GiveAll reward all apply (Session 6 tested one step per reward).

Next: the check session (Session 9), then release 1.2.0.

## 2026-10-17: Session 9, Fair Ledger check

Two launches on the creative test slot. Safety: both exits passed all checks.

**Launch 1** (core, Defense, SettlerStories, FairLedger, FairLedger-Rebalance, SignProbes, LedgerSetup; Purchases set to Standard for the run and back to Free after):
- The terminal listed six options in the expected order, the two payments last with "(200,000 Units)" and "(2,000,000 Units)".
- LedgerSetup's option gave 5,000,000 units and raised debt from 0 to about 2,414,900.
- "Pay 100,000 debt" took 200,000 units and cut 100,000, with "Settlement debt reduced: 100,000 units". "Pay 1,000,000 debt" took 2,000,000 units and cut 1,000,000. The save confirms 2,200,000 units taken (5,732,096 to 3,532,096); the debt readings differ from the cuts by under 1,100, which is the debt falling on its own between screenshots.
- Ten stat steps in one GiveAll reward all apply, but the game shows one message, "Settlement debt reduced: 100,000 units", for the 1,000,000 payment.
- Rebalance: each production building's upkeep equals its productivity exactly (Farm 18,130 and 18,130, Industrial Chimney 28,542 and 28,542). Inferred: one roll sets both, so a C-class production building nets exactly 0, not "about 0". Housing, the fish pond and the dance lounge kept vanilla upkeep. Maintenance Cost fell from 381,454 to 266,502 a day.
- The overrides showed in English: "Upkeep (per day)", "In debt: production is paused until the debt is paid", and the falling-debt tip. In French every Fair Ledger string showed translated, with no raw keys.
- The game formats numbers itself: in French the price read "200.000 unites" and productivity "579.063", so the labels' "100 000" did not match. No language file or type defines a separator; the exe holds a locale code table and imports GetLocaleInfoEx, but Windows' French separator is a space, so the game does not follow it (verified for French only).

**Launch 2** (the same without FairLedger):
- The save loaded normally. The terminal showed the four vanilla options and LedgerSetup's, with both payments gone. Debt was 1,307,890, keeping the amount paid. The vanilla text came back ("Maintenance Cost", the vanilla debt line and tip), while Rebalance's 266,502 a day stayed.

Also seen: the save list shows the slot in the language it was last saved in ("Colonie de Funana Bridge", "Creatif"), because the save stores its caption as text (`SaveSummary`).

## 2026-10-17: Session 9b, Fair Ledger text check

Four short launches on the creative test slot after adding vanilla color markup, "." separators and shorter text. Safety: every exit passed all checks.

- Vanilla markup works in a mod's LocTable.MXML: `<STELLAR>` (yellow), `<TECHNOLOGY>` (blue) and `<TRADEABLE>` (green) colored the marked words, and `<IMG>SLASH<>` drew the divider in the debt line, in English, French and Spanish.
- The French Pay labels and the game's own price matched: "Payer 100.000 de dette (66.000 unites)" on Free Purchases.
- The tip box holds about six lines. The first colored tips (up to 316 characters in French) were cut off, and a period after a colored phrase wrapped onto its own line. After shortening (decided 2026-10-17, from an ethan-voice draft), the rising-debt tip fit in English and in Spanish, the longest translation at 178 visible characters, which filled all six lines. The falling-debt tip fit in English.
- New test-only module LedgerRising (key `ledgerrising`) sets the base upkeep of residences and the bar to 400,000, which raised Upkeep to 2,573,692 a day so the rising-debt tip shows. It writes nothing to the save; without it, Upkeep was back at 266,502.
- Tip text for later modules: keep tips under about 175 visible characters in the longest language, and do not end a sentence on a colored phrase.

Decided 2026-10-17: keep only the overrides that add something. The debt banner override is dropped, since it only reworded vanilla and replaced the game's own translations. The overview label becomes plain "Upkeep", since the value already reads "/day". Fair Ledger now overrides four vanilla keys: the two tips, the label and the decision-text word.

Fair Ledger is ready for release as 1.2.0.

## 2026-10-17: Per-module versions and the all-in-one bundle

Decided 2026-10-17: each shipped module has its own version, and a new all-in-one download, OverseersToolkit-AllInOne, carries the Nexus page version and becomes the main file.

- Why: Vortex tracks each file on a Nexus page separately through the "new version of file X" link and ignores the page version (forum reports, not official docs), so a module that keeps its file and version prompts no update. One version for every module meant every release prompted every player for every module.
- `versions.json` replaces `VERSION`. `tools/versions.py check` compares it with the newest vX.Y.Z tag: changed module files need a higher version, unchanged ones keep theirs, and the bundle moves up when any module in it does. A release before versions.json counts as one bundle of every module at its VERSION. A test runs the check on the repo and skips when the clone has no tags (CI).
- The bundle is a zip of the separate module folders, not a merged module. A merged folder next to the separate ones would load twice: Fair Ledger's options would be appended twice (eight terminal options, two dropped) and every appended decision would come up twice as often. With separate folders, the bundle and a single module install the same files, and switching between them keeps every build.
- Bundle contents: core, Defense, Settler Stories and Fair Ledger. Settlement Decor and Fair Ledger Rebalance stay opt-in, since they change vanilla content broadly.
- Verified in the maintainer's install (vortex.deployment.json, read only): Vortex deploys an NMS archive's top-level entries into MODS as they are, folders and loose files alike.
- Versions for the next release: core, Defense and Settler Stories 1.2.0; Settlement Decor stays 1.1.0 (no file changed since v1.1.0, so it is not re-uploaded); FairLedger and FairLedger-Rebalance 1.0.0; bundle 1.2.0.
- Upload rules for Nexus: each module's new file is uploaded as a new version of that module's previous file; the bundle is a new main file with no update link, so Core-only players are never offered it; Core moves to the optional files.

## 2026-10-17: Vortex check of the bundle

The maintainer installed OverseersToolkit-AllInOne-1.2.0.zip through Vortex in the real setup, with the game closed throughout, and removed it again. MODS was snapshotted byte for byte before (1,162 files, 60 Vortex mods).

- The real setup already held Core, Defense and Settlement Decor 1.0.0 from Nexus through Vortex.
- Verified: the bundle deployed all four module folders intact (core, Defense, Settler Stories, Fair Ledger).
- Verified: Vortex reported "Unresolved file conflicts" between AllInOne and OverseersToolkit-1.0.0 (6 files) and OverseersToolkit-Defense-1.0.0 (8 files), and asked for a load-order rule. With AllInOne loading after, it owned all 14 files. Settlement Decor 1.0.0 was untouched.
- Verified: after removing AllInOne, MODS matched the snapshot exactly (no file added, removed or changed) and Vortex redeployed the 1.0.0 files.
- Consequence: a bundle next to separate downloads of a different version conflicts on different files, and load order picks the version. CHANGES.md now tells players to remove the separate downloads before switching to AllInOne.

