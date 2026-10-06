# Settlement Planner: build plan

Working name: **Settlement Planner**. Part ID prefix: `SP_`.

A No Man's Sky mod that makes settlements something you can lay out and improve, not just a procedural village you watch. The plan was written 2026-10-06 against game build 180836. Every "verified" fact below was checked on this PC that day.

## 1. Why this mod exists

Source: r/NoMansSkyTheGame thread "Laying down paths in a settlement is such a simple thing but really makes it feel so much nicer" (post `1wzabl6`, saved copy at `X:\Files\Downloads\Laying down paths in a settlement ... .html`).

What players do today, and what goes wrong:

- **Building in a settlement takes a trick.** You claim a base just outside the settlement, then build inward. The base computer can be moved inside afterward, but the build area stays centered on the original claim point.
- **Paths are hand-laid.** Players overlap small stone floor squares and triangles (`S_FLOOR_Q`, `S_TRIFLOOR_Q`) and put low walls under the edges so NPCs can step up onto them.
- **Flora pokes through paths.** Terrain editing is blocked inside settlements.
- **NPCs ignore player paths** and get stuck on anything outside their fixed navigation map.
- **Game updates move settlement buildings.** That leaves player additions misaligned, and several players gave up decorating because of it.
- **Wishlist from the thread:**
  - Parts that unlock by settlement class: B for paths and lights, A for statues and billboards, S for walls and sentry towers that cut attacks.
  - Signposts, guard posts, more vendors, a corvette pad, districts.

## 2. Scope

In scope, in build order:

1. **Settlement path kit.** Make the game's own settlement path decal buildable, add path pieces that work in settlements (low-profile tiles, curb or step pieces), and make lighting easy.
2. **Build in settlements without the base-claim trick.**
3. **Settlement defense.** A data-only overseer decision that fortifies the settlement and cuts sentinel alerts.
4. **Class-gated unlocks**, if data can express them. Otherwise they move to the runtime mod.
5. **Runtime path tool (NMS.py)**, gated on a feasibility spike: pick points and the path lays itself along the ground.

Out of scope for now: making NPCs walk player paths, moving settlement buildings, and protecting layouts from game updates. Section 9 explains why. Each has a research note in case it comes back.

## 3. Environment (verified 2026-10-06)

| Item | Value |
|---|---|
| Game install | `X:\SteamLibrary\steamapps\common\No Man's Sky` (Steam app 275850) |
| Game build | Steam buildid `25732212`; `NMS.exe` file version `180836` |
| Archive format | HGPAK (`GAMEDATA\PCBANKS\NMSARC.*.pak`, magic `HGPA`), 97 paks |
| Mods folder | `GAMEDATA\MODS`, managed by Vortex (`vortex.deployment.json`), about 55 mods |
| Mod load order | `Binaries\SETTINGS\GCMODSETTINGS.MXML` (`ModPriority`, `Enabled` per mod folder) |
| Saves | `%APPDATA%\HelloGames\NMS\st_76561198023670358` (the active profile) |
| Save and mod backups | `X:\Files\Documents\!SAVED GAMES AND CONFIGS\No Mans Sky` (dated folders) |
| MBINCompiler | v7.04.1-pre3 (2026-09-24), in `tools\mbincompiler\`. The copies in the backup folder (5.54, 7.01) are too old. |
| hgpaktool | 1.1.3 (PyPI), in `tools\.venv\` (`uv venv`, Python 3.14) |
| NMS.py | Latest is 180383.0 (2026-10-01). **One game build behind 180836.** It usually catches up within days to a week. |

Tool usage notes:

- `hgpaktool.exe` needs Windows-style paths (`X:/...`). Git Bash `/x/...` paths fail.
- `hgpaktool -L -p <pak dir>` writes `filenames.txt` to the current directory. A full listing of all 97 paks is saved at `scratch\all_files.txt` (194,738 entries).
- Extract with `hgpaktool -O <out> -f "<glob>" ... "<PCBANKS dir>"`. Filters are OR'd.
- Decompile with `MBINCompiler.exe convert -y -q -f "<dir>"`, which writes `.MXML` next to each `.mbin`.
- `scratch\extracted\` holds the 116 decompiled files used for this plan. It is reproducible and must not be committed (it's Hello Games data).

### How installed mods patch data

Verified by reading the installed mods.

The installed mods ship **partial EXML patches**, not whole files. For example, `gBase Boundary 20000\GLOBALS\GCBUILDINGGLOBALS.GLOBAL.EXML` is 12 lines and changes 5 fields. Table edits match an entry by `_id`, as in `Unlockable Expedition Exclusive Techs\METADATA\REALITY\TABLES\BASEBUILDINGOBJECTSTABLE.EXML`, which adds a `Groups` entry to existing parts.

So this mod ships partial EXML patches too. Two things are unverified and get settled in M1 and M2: whether a patch can **append a brand-new `_id` entry** to a table, and the exact merge rule when two mods set the same field (presumably `ModPriority` decides).

### Installed mods that touch the same files

All of these are partial patches, so they only collide where the same field is set:

| File | Installed mod | Overlap risk |
|---|---|---|
| `GCBUILDINGGLOBALS.GLOBAL` | gBase Boundary 20000 | Already sets `RadiusMultiplier_DoNotPlaceAnywhereNear` to 0.000001. That is the same field M3 changes. |
| `GCSETTLEMENTGLOBALS` | _Merged_MOD_MTR_+_LMF_Always-SClass-MaxStats | Changes settlement timers (`SettlementMiniExpeditionTime`, `SettlementBuildingTimes`). M4 adds judgements; avoid those fields. |
| `BASEBUILDINGOBJECTSTABLE` | Unlockable Expedition Exclusive Techs | Edits other `_id`s. Low risk. |
| `NMS_REALITY_GCPRODUCTTABLE`, `UNLOCKABLEITEMTREES` | Craftablemodules, Unlockable Expedition Exclusive Techs | Low risk unless the same `_id`s are edited. |
| `NMS_BASEPARTPRODUCTS` | EqualPlantTimerAndProduction | Low risk. |
| `SENTINELSETTLEMENTMISSIONTABLE` | mission_hints_stay_forever | Not touched by this plan. |

Because gBase Boundaries is installed, this PC probably already allows building in settlements. M3 has to be tested with that mod disabled.

## 4. What the game data says

Every finding below cites the file in `scratch\extracted\`.

### Paths

- **`DECALPATH`** (`basebuildingobjectstable`) is a ready-made path part that reuses the settlement generator's own path decal: `MODELS/PLANETS/BIOMES/COMMON/BUILDINGS/WFC/PATHDECAL_PLACEMENT.SCENE.MBIN`.
  - It has `ShowInBuildMenu=true`, `CanScale=true`, `CanRotate3D=true`, `PlanetBaseLimit=50`, `EditsTerrain=false`.
  - Its `Groups` list is **empty**, so it never appears in the build menu. It has a cost entry (`basebuildingcoststable`) but no entry in `nms_basepartproducts`.
  - Because it's a decal, it should project onto uneven ground, which fixes the step problem. Whether grass draws over it has to be tested in game.
- **Floor parts edit terrain already.** `S_FLOOR`, `S_FLOOR_Q`, `S_TRIFLOOR_Q` and the stone paving parts `BUILDPAVING` and `BUILDPAVING_BIG` have `EditsTerrain=true` with `BaseTerrainEditShape=Cube`. The thread says terrain edits don't apply inside settlements, which explains the flora poking through. Unverified: whether the block is a data value or hardcoded. Nothing settlement-related turned up in `gcterrainglobals`.
- Per-part fields that matter for new parts: `PlacementScene`, `Groups`, `PlanetBaseLimit`, `EditsTerrain`, `BaseTerrainEditShape`, `CanScale`, `SnappingDistanceOverride`, `IsDecoration`, `BuildableOnPlanetBase`, `ColourPaletteGroupId`, `MaterialGroupId`.
- `IsFromModFolder` exists on every entry (all `false` in vanilla), so the game expects modded parts.
- Part IDs look like `TkID0x10`, which means **16 characters at most**. Keep `SP_` IDs short.

### Building in settlements

- `gcbuildingglobals`: `RadiusMultiplier_DoNotPlaceAnywhereNear=2.5` and `Radius_DoNotPlaceAnywhereNear=200`.
  - gBase Boundaries' inline comment says this controls the "settlement build exclusion radius". That claim is unverified.
  - The neighboring fields (`RadiusMultiplier_DoNotPlace`, `_OnlyPlaceAround`) look like procedural building-placement rules, so changing it may also affect where points of interest spawn near bases. M3 has to check for side effects.
- Related: `TestDistanceForSettlementBaseBufferAlignment=150`, `MinRadiusForBases=300`, `MaxRadiusForPlanetBases=1000`.

### Settlement simulation (`gcsettlementglobals`)

- **Stats** are `MaxPopulation`, `Happiness`, `Production`, `Upkeep`, `Sentinels`, `Debt`, `Alert` and `BugAttack`, with min, max and good/bad thresholds.
- **Attack cadence** is data: `AlertCycleDurationInSeconds=3400`, `BugAttackCycleDurationInSeconds=9000`, `AlertUnitsPerCycleRateModifier=20`, `BugAttackUnitsPerCycleRateModifier=20`.
- **Judgements** (overseer decisions): `Judgements` has 36 entries and `CustomJudgements` has 13. Each option can grant `Perks`, `StatChanges` and `AdditionalRewards`, and can chain to another judgement (`ChainedJudgementID`). Selection weights by type are in `JudgementSelectionWeights`.
- **Perks** (`settlementperkstable`, 90 entries): each has `StatChanges`, `AssociatedBuildings` and flags (`IsNegative`, `IsStarter`, `IsProc`, `IsJob`, `IsBlessing`). `PROC_SENT` and `SENT_QUAR` are existing sentinel-related perks to copy from.
- **Settlement buildings** are generated by a wave-function-collapse system from module sets in `metadata/simulation/solarsystem/wfcbuildings/{builders,stone,wood,fibreglass,cuboid3}`. When Hello Games changes these sets, existing settlements regenerate differently. That's the root cause of the "updates moved my buildings" complaint.

### NPC navigation

- `basebuildingpartsnavdatatable` gives per-part navigation nodes (`Connection` and `Path` node types, local positions, links), but only for 57 freighter and space-base parts (`_FRE_*`, `_CORRIDOR_SPACE`, and so on).
- Planet floor parts have none. Settlement NPCs probably use a separate system. Unverified, see section 9.

### Runtime hooks (NMS.py `nmspy/data/types.py`, master branch)

- `cGcBaseBuildingManager` has `GetBaseRootNode`, `GetBaseBuildingRootMatrix` (converts between base-local and world positions), `AddObjectMarker` and `Update`.
- `cGcPlayerBasePersistentBuffer.maBaseBuildingObjects` is the list of objects in a base.
- `cGcFrontendPageClaimBase.DoBaseClaimOptions` is the base-claim flow, a possible hook for claiming inside settlements.
- `cGcTerrainEditorBeam.ApplyTerrainEditFlatten` and `ApplyTerrainEditStroke` handle terrain flattening.
- **Missing:** any settlement class or structure, and any "spawn a base part at this position" function. Both need new reverse engineering. That's the main risk for the runtime mod.

## 5. Architecture

Two deliverables, built in order:

**A. Data mod `SettlementPlanner`.** Partial EXML patches plus any new text strings. It survives game updates as long as the patched field and `_id` names still exist, and the validator (section 7) catches it when they don't. No new 3D assets: every new part reuses an existing scene file.

**B. Runtime mod `settlement_planner.py` (NMS.py).** Only built if the M6 spike passes. It provides the path tool and anything else data can't express. It breaks on game updates until NMS.py catches up, so the data mod must never depend on it.

Fallback for B if NMS.py can't place parts: an offline save-file path planner. You already have a working save-editing pipeline in `X:\Files\Documents\!SAVED GAMES AND CONFIGS\No Mans Sky\scratch dir\corvette-destroyer\` (stage, install and validate scripts built on libMBIN). Base objects are stored in the save with base-local positions. Decal paths need only approximate heights because they project onto the ground.

### Repo layout

```
docs/plan.md              this file
docs/progress.md          progress log, one entry per finished milestone, plus forward-looking notes
mod/SettlementPlanner/    the shippable data mod, mirroring GAMEDATA/MODS/<mod>/ paths
  GLOBALS/...EXML
  METADATA/REALITY/TABLES/...EXML
  LANGUAGE/...            only if M2a proves custom strings load
runtime/                  NMS.py mod (M6 onward)
tools/
  bootstrap.ps1           fetch pinned MBINCompiler and hgpaktool into tools/
  tools.lock.json         pinned tool versions and the game build they were checked against
  extract.py              reproduce scratch/extracted from the installed game
  check_build.py          compare the installed game build with tools.lock.json; fail loudly on mismatch
  merge_preview.py        apply our patches to vanilla MXML, write merged files, compile them with MBINCompiler
  deploy.py               copy mod/SettlementPlanner to GAMEDATA/MODS/SettlementPlanner, or build dist/*.zip
tests/                    pytest, run against scratch/extracted
scratch/                  gitignored: extracted game data, listings
dist/                     gitignored: release zips
```

## 6. Milestones

Each milestone ends in a commit. Steps marked **[YOU]** need you in the game, because Claude can't play it. At those points the build session stops and asks, with an exact checklist of what to look at.

### M0: Repo and tooling

1. `git init`. Before the first commit, set the repo-local identity and signing key for the Forgejo noreply address (see the memory on Forgejo private-email signing). Add `.gitignore` for `scratch/`, `dist/`, `tools/.venv/`, `tools/mbincompiler/*.exe|*.dll`, `__pycache__/`.
2. `tools/bootstrap.ps1` and `tools.lock.json`: MBINCompiler v7.04.1-pre3, hgpaktool 1.1.3, game build 180836.
3. `tools/extract.py` reproduces `scratch/extracted` (the exact filter list used for this plan is in section 10).
4. `tools/check_build.py` reads `appmanifest_275850.acf` and the `NMS.exe` file version and fails if either differs from the lock.
5. A Forgejo remote is optional. The API token can't create repos, so you'd create `ethan-hann/settlement-planner` by hand first.

Done when: bootstrap, extract and check_build run cleanly from a fresh clone.

### M1: Prove the pipeline end to end

1. **Tests first:**
   - Every EXML under `mod/` parses and declares a `template`.
   - Every `_id` it edits exists in the matching vanilla file.
   - Every property name it sets exists in that vanilla entry.
   - `merge_preview.py` output compiles with MBINCompiler.
   - Record the observed red in the commit message.
2. The smallest real patch: `DECALPATH` `PlanetBaseLimit` 50 to 200.
3. `deploy.py` copies the mod into `GAMEDATA/MODS/SettlementPlanner`. Never touch other mod folders or `vortex.deployment.json`. Vortex leaves unmanaged folders alone, but say so in the deploy output.
4. **[YOU]** Back up saves first (copy the save folder into the dated backups folder). Launch, confirm `SETTLEMENTPLANNER` appears in `GCMODSETTINGS.MXML` and the in-game mod list, and that nothing else broke.

Done when the game loads with the mod enabled and the patch takes effect. `DECALPATH` isn't buildable yet, so this proves loading and merging only. Seeing the limit change has to wait for M2.

### M2: Settlement path kit

**M2a, text strings spike.** Can a mod add new localization keys, for example `LANGUAGE/NMS_SP_ENGLISH.MBIN` or a partial patch of an existing language file? No installed mod does this.
- If yes, new parts get their own names.
- If no, reuse existing vanilla keys for names and descriptions, and record that in `docs/progress.md`.

**M2b, expose `DECALPATH`.**
- Add a `Groups` entry (pick a build-menu group by reading `Groups` and `PaletteGroups` in `basebuildingobjectstable`).
- Add the product and blueprint entries it needs (`nms_basepartproducts` or `nms_reality_gcproducttable`, `purchaseablebuildingblueprints`, or a free unlock in `unlockableitemtrees`).
- Raise the limit.
- This step also settles whether a patch can append a new `_id`. If it can't, fall back to patching existing entries only and rethink M2c.

**M2c, new `SP_` parts**, each reusing an existing scene:

| Part | Copied from | Change |
|---|---|---|
| `SP_PATH_TILE`, `SP_PATH_TRI` | `S_FLOOR_Q`, `S_TRIFLOOR_Q` | `EditsTerrain=false`, so they don't fight settlement terrain locks; keep snapping |
| `SP_CURB` | The low wall the thread uses as a step (find its ID by matching the "low alloy wall" scene) | Snaps under the tile edges |
| `SP_PATH_DECAL_W` | `DECALPATH` | A wider default scale, if the scene allows it |

Lighting: check whether the existing lamp posts and lanterns need power. The thread's workaround was lanterns flipped upside down. A powerless `SP_LAMP` clone is an option.

Tests: new IDs are unique and at most 16 characters, every `PlacementScene` path exists in `scratch/all_files.txt`, and every part has cost, product and group entries.

**[YOU]** In a settlement:
- The parts appear in the build menu and can be placed.
- Decals sit flush on slopes.
- Note whether grass draws over decals and tiles.
- NPCs can step onto tiles that have curbs.

### M3: Build in settlements without the trick

1. Disable gBase Boundary 20000 temporarily ([YOU], in the in-game mod list or Vortex). Confirm vanilla still blocks claiming a base inside a settlement.
2. Patch `RadiusMultiplier_DoNotPlaceAnywhereNear`, and `Radius_DoNotPlaceAnywhereNear` if needed. Use the smallest change that works, not 0.000001.
3. **[YOU]**
   - Claim a base inside a settlement and build.
   - Visit a fresh planet and check that points of interest and buildings still spawn normally near bases (the side-effect check).
4. If the field turns out to control something else, record the finding, drop the patch, and move this feature to the runtime mod (hook `DoBaseClaimOptions`).
5. Document that gBase Boundaries sets the same field. Whichever loads last wins.

### M4: Settlement defense (data only)

1. Read `PROC_SENT`, `SENT_QUAR` and the sentinel-related judgements to copy their shape.
2. New perk `SP_WATCH`: `StatChanges` lowers `Alert` and raises `Sentinels`. Tune it against `StatsMaxValues` (Alert max 1000) and `AlertUnitsPerCycleRateModifier` (20).
3. New custom judgement `SP_J_FORTIFY`: "Fortify the perimeter?" with options that cost resources (find how vanilla judgements charge costs, for example `CustomCostText` and `AdditionalRewards`) and grant `SP_WATCH`. Add it to the pool through `JudgementSelectionWeights` or the custom list, without touching the fields the installed timer mod changes.
4. Optional: a buildable sentry-tower decoration (`SP_TOWER`) reusing a settlement tower or sentinel pillar scene. It's decorative unless M5 or the runtime mod can tie it to the perk.
5. **[YOU]** Debug-test by waiting out judgement timers or using a save near a judgement. Confirm the option appears, the perk applies and the Alert stat drops.

### M5: Class-gated unlocks (investigate, then build or defer)

1. Find whether anything in data keys on settlement class (`unlockableitemtrees`, `purchaseablebuildingblueprints`, perks, settlement shop inventories).
2. If yes, gate the path kit at B, statues and billboards at A, and towers and walls at S.
3. If no, record that and leave gating to the runtime mod. As an interim, make the parts purchasable from settlement-related vendors or judgement rewards, so they at least feel earned.

### M6: Runtime feasibility spike (NMS.py)

1. Wait until NMS.py has a release for the installed game build (`check_build.py` compares the NMS.py version to the game build). Install it in a separate venv with `uv pip install nmspy`, run with `pymhf run nmspy`.
2. Prove, in order, each as a tiny throwaway mod:
   1. Read `maBaseBuildingObjects` for the current base and log part IDs and positions.
   2. Convert a world position to base-local with `GetBaseBuildingRootMatrix`.
   3. Place one `DECALPATH` at the player's feet through code. This needs a placement function NMS.py doesn't expose yet, so start from `cGcBaseBuildingManager` and the persistent buffer and ask upstream (the NMS.py Discord or repo) before deep reverse engineering.
   4. Optionally, flatten terrain under a point with `ApplyTerrainEditFlatten` inside a settlement.
3. Write the result to `docs/progress.md` as go or no-go.
   - **No-go** on step 3: switch the path tool to the offline save-edit planner (section 5).

### M7: Path tool (only after a go from M6)

- An imgui panel (pyMHF's GUI extra): start path, add point, finish, undo last path.
- Pieces are laid every N meters along the polyline, oriented to the segment and snapped to terrain height. Decals by default, `SP_` tiles optional.
- Respect `PlanetBaseLimit` and the base complexity budget. Show the count before committing.
- **[YOU]** Lay a path through a settlement, reload the save, and confirm it persists and loads for an unmodded visitor (multiplayer check, see section 9).

## 7. Testing

**Automated** (pytest, fast, no game needed):
- Patch files parse.
- Templates match vanilla.
- Edited `_id`s and fields exist.
- New IDs are valid, unique and at most 16 characters.
- Every scene path exists.
- Every new part has its cost, product, group and string entries.
- `merge_preview.py` output compiles with the pinned MBINCompiler.
- `check_build.py` passes.

**Manual** ([YOU] checkpoints above): one short checklist per milestone, written into `docs/progress.md` along with the result.

**After every game update:** run `check_build.py`, bump the tools, re-extract, and rerun pytest. A failing test names the field or ID the update renamed.

TDD rules for the build session (from your standing preferences):
- Write the test before the implementation, and don't design the fix inside the test.
- A harness error is not a red.
- Record the observed failure in the commit message.
- When a test passes on its first run, prove it can fail by breaking the patch on purpose.

## 8. Rules for the build session

- Code and patch comments say why, never which milestone or slice. Forward-looking notes go in `docs/progress.md`.
- Never edit other mods' folders, `vortex.deployment.json` or save files. The one exception is the M6 save-edit fallback, which works on copies and installs only after you approve.
- Back up the save folder before every [YOU] checkpoint.
- Never commit Hello Games data (`scratch/`, extracted MBIN or MXML). The mod's own partial patches are fine.
- Prose in commits, PRs and docs: ASCII, American English, concise.
- Out-of-scope findings go to the issue tracker, not session chips.
- Stop and ask at every [YOU] step. Don't guess in-game results.

## 9. Risks and open questions

| Risk | Impact | Plan |
|---|---|---|
| A partial patch can't append new `_id` entries | No new `SP_` parts | M2b settles it. Fall back to exposing and retuning existing parts (`DECALPATH`, paving). |
| New text strings can't be added | Parts reuse vanilla names | M2a. Cosmetic only. |
| The exclusion field does more than gBase's comment says | Side effects on spawning | M3 side-effect check. Fall back to the runtime claim hook. |
| NMS.py lags the game or lacks a placement function | No path tool | M6 gate. Save-edit fallback. |
| Multiplayer: unmodded visitors see missing or odd parts, or hit build limits | Friends see a broken settlement | Reusing vanilla scenes helps (visitors have the meshes). Test in M2 or M7 with a second account or a friend. Unverified until then. |
| Game updates rename fields or regenerate settlements | Patches stop applying; player paths misalign | The validator catches renames. Misalignment is Hello Games' layout regeneration; out of scope. |
| NPC pathing | Players expect NPCs to use paths | Out of scope. Research note: the per-part nav-node table exists for freighter parts. Adding nav nodes to planet path parts might be read by settlement NPCs, but nothing shows that. Worth a one-hour spike after M7, not before. |
| Moving settlement buildings | Wishlist item | Out of scope. Layouts come from wave-function-collapse generation and the save; any fix is save editing or deep runtime work. |

## 10. Reproducing the investigation

Files extracted for this plan (hgpaktool `-f` filters, run against `PCBANKS`):

```
gcbuildingglobals*  gcsettlementglobals*  gcplacementglobals*  gcterrainglobals*
gcnavigationglobals*  gcmultiplayerglobals*  gcgameplayglobals*
metadata/reality/tables/basebuilding*
metadata/reality/tables/settlementperkstable*
metadata/reality/tables/nms_basepartproducts*
metadata/reality/tables/purchaseablebuildingblueprints*
metadata/reality/tables/unlockableitemtrees*
metadata/reality/tables/legacybasebuildingtable*
metadata/simulation/npcs/npcsettlementbehaviours*
metadata/simulation/solarsystem/wfcbuildings/*
metadata/simulation/environment/planetbuildingtable*
metadata/simulation/missions/tables/sentinelsettlementmissiontable*
metadata/reality/cataloguebuilding*
```

Not yet extracted but needed: `metadata/reality/tables/nms_reality_gcproducttable*` (M2b) and the `language/*english*` files (M2a).
