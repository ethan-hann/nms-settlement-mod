# Settlement Planner: build plan

Working name: **Settlement Planner**. Part and perk ID prefix: `SP_`. Repo: `github.com/ethan-hann/nms-settlement-mod` (private for now; Nexus Mods release later).

A No Man's Sky mod that lets players lay out and improve settlements instead of just watching a procedural village. Written 2026-10-06 against game build 180836. "Verified" means checked on Ethan's PC that day.

**How to use this plan.** A `/goal` session builds it end to end with as little of Ethan's time as possible. Section 3 (safety) overrides everything else in this file. Section 10 says when to stop and ask.

## 1. Why this mod exists

Source: r/NoMansSkyTheGame post `1wzabl6`, "Laying down paths in a settlement is such a simple thing but really makes it feel so much nicer". A saved copy is at `X:\Files\Downloads\Laying down paths in a settlement ... .html`.

What players do today, and what goes wrong:

- **Building in a settlement takes a trick.** You claim a base just outside it and build inward. The base computer can be moved inside afterward, but the build area stays centered on the claim point.
- **Paths are hand-laid.** Players overlap small stone floor pieces (`S_FLOOR_Q`, `S_TRIFLOOR_Q`) and put low walls under the edges so NPCs can step up.
- **Flora pokes through paths.** Terrain edits don't apply inside settlements.
- **NPCs ignore player paths** and get stuck on player-built parts.
- **Game updates move settlement buildings**, which leaves player additions misaligned.
- **Wishlist:**
  - Class-gated parts: B for paths and lights, A for statues and billboards, S for walls and sentry towers that cut attacks.
  - Signposts, guard posts, vendors, a corvette pad, districts.

## 2. Design principles

This mod is for everyone, not one PC. Ethan's setup is one test case, not the target.

1. **Target the vanilla game.** Design and validate against vanilla data only. Never assume, require or tune around any other mod.
2. **Add rather than edit.** New `SP_` entries can't collide with other mods. Edit a vanilla entry only when the feature needs it, and list every vanilla `_id` and field the mod edits in `COMPATIBILITY.md` (generated, see section 9).
3. **Patch the fewest fields possible.** Ship partial EXML patches (section 5), never whole-file replacements.
4. **Modular.** Each feature is its own mod folder, so players can take what they want and drop what conflicts. These become optional files on Nexus:

   | Module folder | Contents | Edits vanilla? |
   |---|---|---|
   | `SettlementPlanner` (core) | Path kit, signposts, lighting | Exposes `DECALPATH`; everything else is new `SP_` parts |
   | `SettlementPlanner-OpenSettlements` | Build inside settlements without the base-claim trick | Yes, one or two global fields that other base mods also change |
   | `SettlementPlanner-Defense` | Fortify decision, defense perk, decorative tower | Adds a judgement and a perk; adds a selection entry |
   | `SettlementPlanner-Runtime` | NMS.py path tool (later, optional) | No data edits |

   Modules must not depend on each other. Core alone must work.
5. **No new 3D assets** for the data modules. New parts reuse vanilla scene files, so multiplayer visitors without the mod at least have the meshes.
6. **English first, translation-ready.** Text goes through localization keys, never hardcoded (if M1's probe shows custom keys load).
7. **Update-resilient.** The validator (section 9) fails loudly when a game update renames a field or `_id` the mod relies on.

## 3. Safety (overrides everything)

Ethan's save is years old. His mod setup is about 55 Vortex-managed mods. Neither may be damaged. These rules are absolute.

### Hard rules

1. **Saves are read-only.** Never write, move, rename or delete anything in `%APPDATA%\HelloGames\NMS\`. To inspect a save, copy the one test-slot file to `scratch/` and read the copy.
2. **Other mods are untouchable.** In `GAMEDATA\MODS\`, create, update or remove only the dev folders this project owns (`_SPDEV_*`). Never touch any other folder, file, or `vortex.deployment.json`.
3. **Game files are untouchable.** Never write under `PCBANKS` or `Binaries`, except `Binaries\SETTINGS\GCMODSETTINGS.MXML`, and only through `testmode.py`. That script backs it up first and restores it byte for byte.
4. **Never act while the game runs.** Every tool that touches the game folder refuses to run if `NMS.exe` is running.
5. **Backups are never deleted** by any tool or session.
6. **Main save protection.** Ethan's main game is slot 2 (`save3.hg`, `save4.hg`, last played 2026-10-03). Slots 1 to 5 are in use and Steam Cloud is on (`steam_autocloud.vdf`). Testing uses a new creative save in a free slot (6 or higher), never slots 1 to 5.
7. **Any safety check failure stops the session** and goes to Ethan with the exact files involved. Restoring a save from backup always needs his explicit approval. Steam Cloud can fight a restore, so plan it with him; never do it automatically.

### Test environment

- **Primary:** a fresh **creative-mode** save (settlements are quick to find and claim) with **only this mod's modules enabled**.
- **Compatibility pass:** the same creative save with Ethan's full mod list plus this mod. That's one realistic heavy setup, and it never involves his real saves.

### `tools/testmode.py`: the only way into and out of a test session

`testmode.py enter [--modules core,open,defense,testtuning] [--with-user-mods]`:

1. Refuses if `NMS.exe` is running.
2. Makes a full backup of the save folder plus `Binaries\SETTINGS\` to `X:\Files\Documents\!SAVED GAMES AND CONFIGS\No Mans Sky\settlement-planner-backups\<timestamp>\`. It writes a sha256 manifest and re-reads every file to verify it.
3. Records a read-only listing (names and sizes) of `GAMEDATA\MODS\`.
4. Copies the requested modules into `GAMEDATA\MODS\_SPDEV_<module>`.
5. Rewrites `GCMODSETTINGS.MXML` so every other mod is `Enabled=false` (with `--with-user-mods`, it leaves them as they were) and ours are `Enabled=true`. Nothing is deleted. `GCMODSETTINGS` is the game's own mod list, and Vortex doesn't write it (verified: Vortex tracks only files under `MODS`).
6. Writes `scratch/testmode.state.json` recording what it did.
7. Prints the session checklist and the warning: **load the test slot from the load menu; never press Continue.** If Continue lands on the main save while only test mods are active, the game could strip modded items from it when it saves.

`testmode.py exit`:

1. Refuses if `NMS.exe` is running.
2. Removes the `_SPDEV_*` folders, so Ethan's normal game never loads dev builds by accident.
3. Restores `GCMODSETTINGS.MXML` byte for byte from the backup and checks the hash.
4. Checks the `MODS` listing against the snapshot. Any difference outside `_SPDEV_*` is a safety failure.
5. Hash-compares every save file against the backup. Only the test slot's files, `accountdata.hg`, their `mf_` companions and `cache\` may differ. **Any other change is a safety failure**: stop and report.
6. Copies the test slot's save file to `scratch/saves/` for verification.

`testmode.py status` reports whether a session is open. The build session runs it before anything that touches the game. The first time a test slot appears, its slot number goes in `scratch/testmode.local.json` (gitignored). Later sessions treat only that slot as allowed to change.

`testmode.py` gets its own tests, run against a fake game tree in a temp directory and never the real folders. They must show that `exit` restores `GCMODSETTINGS` byte for byte, that it refuses while a fake `NMS.exe` process is running, and that a changed non-test save file is reported as a failure.

### Verifying results without Ethan

After each session, `tools/save_inspect.py` decodes the copied test save. The format is LZ4 block chunks with magic `0xFEEDA1E5`, and keys are de-obfuscated with MBINCompiler's `mapping.json`. That's the same approach as Ethan's existing script at `X:\Files\Documents\!SAVED GAMES AND CONFIGS\No Mans Sky\scratch dir\corvette-destroyer\inspect_save.py`. It checks, for example:

- which `SP_` and `DECALPATH` objects exist in `PersistentPlayerBases[*].Objects`
- where the base sits relative to the settlement
- settlement perks and stats

This keeps Ethan's checklist to "do these actions, save, quit". The game log (`GAMEDATA\FullLog.txt`) is useless here: it only records texture cache misses.

## 4. Scope

In scope, in order:

1. **Probes** that settle the unknowns cheaply, all in one test session.
2. **Core: settlement path kit.** Buildable settlement path decal, path tiles that work in settlements, curb and step pieces, signposts, lighting that needs no power.
3. **OpenSettlements.** Build inside settlements without the claim trick.
4. **Defense.** A fortify decision that grants a perk lowering sentinel alerts, plus a decorative tower.
5. **Class-gated unlocks**, if data can express them; otherwise they move to Runtime.
6. **Runtime path tool** (NMS.py), gated on a feasibility spike.

Out of scope: NPCs walking player paths, moving settlement buildings, protecting layouts from game updates (section 12).

## 5. Environment (verified 2026-10-06)

| Item | Value |
|---|---|
| Game install | `X:\SteamLibrary\steamapps\common\No Man's Sky` (Steam app 275850) |
| Game build | Steam buildid `25732212`; `NMS.exe` file version `180836` |
| Archives | HGPAK (`GAMEDATA\PCBANKS\NMSARC.*.pak`, magic `HGPA`), 97 paks |
| Mods folder | `GAMEDATA\MODS`, Vortex hardlink deployment, 799 tracked files, about 55 mods |
| Mod list and load order | `Binaries\SETTINGS\GCMODSETTINGS.MXML` (`ModPriority`, `Enabled`, `EnabledVR` per mod). Not written by Vortex. |
| Saves | `%APPDATA%\HelloGames\NMS\st_76561198023670358`. Slot N = `save{2N-1}.hg` and `save{2N}.hg` with `mf_` companions; slot 1 = `save.hg`/`save2.hg`. |
| Backup root | `X:\Files\Documents\!SAVED GAMES AND CONFIGS\No Mans Sky\` (Ethan's dated folders live here; ours go in `settlement-planner-backups\`) |
| MBINCompiler | v7.04.1-pre3 (2026-09-24), currently in `tools/mbincompiler/`. Older copies on the PC (5.54, 7.01) don't match this build. |
| hgpaktool | 1.1.3 from PyPI, currently in `tools/.venv/` (uv, Python 3.14) |
| NMS.py | Latest 180383.0 (2026-10-01), **one build behind the game**. It usually catches up within a week. |
| GitHub | `gh` logged in as `ethan-hann`, scopes include `repo` and `workflow` |

Tool notes:

- `hgpaktool.exe` needs Windows paths (`X:/...`); Git Bash `/x/...` paths fail.
- `hgpaktool -L -p <dir>` writes `filenames.txt` to the current directory. A full listing is at `scratch/all_files.txt` (194,738 entries).
- Extract with `hgpaktool -O <out> -f "<glob>" ... "<PCBANKS>"`; filters are OR'd.
- Decompile with `MBINCompiler.exe convert -y -q -f "<dir>"`.
- `scratch/extracted/` holds the 116 decompiled files used for this plan. Never commit it: it's Hello Games data.

### How mods patch data (verified from installed mods)

Installed mods ship **partial EXML patches**: small files containing only the changed fields. Table entries are matched by `_id`.

- `gBase Boundary 20000\GLOBALS\GCBUILDINGGLOBALS.GLOBAL.EXML` is 12 lines and changes 5 fields.
- `Unlockable Expedition Exclusive Techs\...\BASEBUILDINGOBJECTSTABLE.EXML` adds a `Groups` entry to existing parts by `_id`.

Unverified, settled by the M1 probes: whether a patch can **append** a new `_id`, and how two mods setting the same field resolve (presumably `ModPriority`).

## 6. What the game data says

Paths below are relative to `scratch/extracted/`.

### Paths

- **`DECALPATH`** (`metadata/reality/tables/basebuildingobjectstable`) is a ready-made path part. It reuses the settlement generator's own decal: `MODELS/PLANETS/BIOMES/COMMON/BUILDINGS/WFC/PATHDECAL_PLACEMENT.SCENE.MBIN`.
  - It has `ShowInBuildMenu=true`, `CanScale=true`, `CanRotate3D=true`, `PlanetBaseLimit=50`, `EditsTerrain=false`.
  - Its `Groups` list is **empty**, so it never shows in the build menu. It has a cost entry (`basebuildingcoststable`) but no `nms_basepartproducts` entry.
  - As a decal it should follow uneven ground. Whether grass draws over it is unknown.
- **Floors already edit terrain.** `S_FLOOR`, `S_FLOOR_Q`, `S_TRIFLOOR_Q`, `BUILDPAVING` and `BUILDPAVING_BIG` have `EditsTerrain=true` and `BaseTerrainEditShape=Cube`. Players report that terrain edits don't apply in settlements. Unverified: whether that block is data or hardcoded. Nothing settlement-related is in `gcterrainglobals`.
- Fields that matter for new parts: `PlacementScene`, `Groups`, `PlanetBaseLimit`, `EditsTerrain`, `BaseTerrainEditShape`, `CanScale`, `SnappingDistanceOverride`, `IsDecoration`, `BuildableOnPlanetBase`, `ColourPaletteGroupId`, `MaterialGroupId`. `IsFromModFolder` exists on every entry (all `false` in vanilla).
- Part IDs look like `TkID0x10`: **16 characters at most**.

### Building in settlements

- `gcbuildingglobals`: `RadiusMultiplier_DoNotPlaceAnywhereNear=2.5`, `Radius_DoNotPlaceAnywhereNear=200`.
  - gBase Boundaries' inline comment says this is the settlement build-exclusion radius. Unverified.
  - The neighboring fields (`RadiusMultiplier_DoNotPlace`, `_OnlyPlaceAround`) look like procedural building-placement rules, so a change may affect where buildings and points of interest spawn.
- Related: `TestDistanceForSettlementBaseBufferAlignment=150`, `MinRadiusForBases=300`, `MaxRadiusForPlanetBases=1000`.

### Settlement simulation (`gcsettlementglobals`)

- **Stats:** `MaxPopulation`, `Happiness`, `Production`, `Upkeep`, `Sentinels`, `Debt`, `Alert`, `BugAttack` (min, max and good/bad thresholds).
- **Attack cadence is data:** `AlertCycleDurationInSeconds=3400`, `BugAttackCycleDurationInSeconds=9000`, `AlertUnitsPerCycleRateModifier=20`, `BugAttackUnitsPerCycleRateModifier=20`.
- **Judgements (overseer decisions):** 36 in `Judgements`, 13 in `CustomJudgements`. Options can grant `Perks`, `StatChanges` and `AdditionalRewards`, and can chain (`ChainedJudgementID`). `JudgementWaitTimeMin=900` and `JudgementWaitTimeMax=7200` seconds control how often they appear.
- **Perks** (`settlementperkstable`, 90 entries): `StatChanges`, `AssociatedBuildings` and flags. `PROC_SENT` and `SENT_QUAR` are sentinel-related templates.
- **Settlement buildings** come from wave-function-collapse module sets in `metadata/simulation/solarsystem/wfcbuildings/`. When Hello Games changes those sets, existing settlements regenerate differently. That's the cause of the "updates moved my buildings" complaint.

### NPC navigation

`basebuildingpartsnavdatatable` defines per-part nav nodes (`Connection`, `Path`), but only for 57 freighter and space-base parts. Planet floors have none.

### Runtime hooks (NMS.py `nmspy/data/types.py`, master)

- Available:
  - `cGcBaseBuildingManager.GetBaseRootNode` and `GetBaseBuildingRootMatrix` (local and world positions)
  - `cGcPlayerBasePersistentBuffer.maBaseBuildingObjects` (objects in a base)
  - `cGcFrontendPageClaimBase.DoBaseClaimOptions` (the base-claim flow)
  - `cGcTerrainEditorBeam.ApplyTerrainEditFlatten`
- **Missing:** settlement structures, and any "spawn a base part here" function. Both need new reverse engineering. That's the main risk for Runtime.

## 7. Architecture and repo layout

The data modules are partial EXML patches plus localization. Runtime is an NMS.py mod that the data modules never depend on.

If NMS.py can't place parts, the fallback is an **offline save-edit path planner**, a separate tool that works on a copy of a save. It's only ever installed onto Ethan's creative test slot, never a real save, and only with his approval.

```
docs/plan.md                 this file
docs/progress.md             progress log: one entry per milestone and test session, plus forward-looking notes
mod/<Module>/                each module mirrors GAMEDATA/MODS/<Module>/ paths
mod/SettlementPlanner-TestTuning/   test-only (fast judgement timers and so on); never shipped
runtime/                     NMS.py mod
tools/
  bootstrap.ps1              fetch pinned MBINCompiler and hgpaktool into gitignored subfolders
  tools.lock.json            pinned tool versions plus the game build they were validated against
  extract.py                 rebuild scratch/extracted from the installed game (read-only on game files)
  check_build.py             compare the game build and the NMS.py version with tools.lock.json
  merge_preview.py           apply patches to vanilla MXML, compile the result with MBINCompiler
  compat_report.py           read-only scan of any MODS folder for files and fields we also patch
  testmode.py                section 3
  save_inspect.py            decode a copied save, report checklist facts
  package.py                 build dist/<Module>-<version>.zip per module for Nexus
tests/                       pytest
COMPATIBILITY.md             generated by compat_report.py: every vanilla _id and field the mod edits
scratch/  dist/              gitignored
```

`.gitignore` must ignore `scratch/`, `dist/`, `tools/.venv/`, `tools/mbincompiler/`, `__pycache__/`, and nothing else under `tools/`. The current file ignores `tools/*` and has to change in M0.

## 8. Milestones

Every milestone runs on a branch `m<n>-<slug>` and ends in a GitHub PR (section 10). **[SESSION n]** marks an in-game test session (section 3), with all checks batched to save Ethan's time.

### M0: Tooling and safety

1. Fix `.gitignore`. Add `bootstrap.ps1`, `tools.lock.json`, `extract.py`, `check_build.py`.
2. Build `testmode.py` and its tests first. **Nothing touches the game folder until these pass.**
3. `save_inspect.py`, tested against a decoded copy of a small save. The best candidate is any test-slot copy once one exists; until then, use a synthetic fixture.
4. pytest harness and `merge_preview.py`.

Done when bootstrap, extract, check_build and all tests run from a fresh clone, and `testmode` tests prove the safety guarantees.

### M1: Probes, then [SESSION 1]

Build a throwaway probe module (`_SPDEV_PROBES`, never shipped) that answers the unknowns in one session:

| Probe | Patch | What answers it |
|---|---|---|
| P1 edit-merge | `DECALPATH`: add a `Groups` entry, raise `PlanetBaseLimit` | Decal path appears in the build menu |
| P2 append | New `SP_PROBE` part copied from `S_FLOOR_Q` | It appears and can be placed |
| P3 text | A custom loc key for `SP_PROBE`'s name (a new `LANGUAGE/` file, or a partial patch of a vanilla language file) | The menu shows the custom name, not the raw key |
| P4 open settlements | Lower `RadiusMultiplier_DoNotPlaceAnywhereNear` | A base can be claimed inside a settlement |
| P5 terrain | (no patch) Place `BUILDPAVING` and `DECALPATH` inside a settlement | Whether flora clears, whether decals follow the slope |
| P6 isolation | `testmode` disables all non-test mods | The in-game mod list shows only `_SPDEV_PROBES` |

Extract `nms_reality_gcproducttable` and the `language/*english*` files first; P2 and P3 need them.

**[SESSION 1]**, Ethan's checklist (first time only: start a new creative game, which lands in a free slot):

1. Find and claim a settlement.
2. Check the mod list.
3. Place the decal path and the probe tile in the settlement.
4. Try claiming a base inside it.
5. Save and quit.

The build session confirms most of the results from the save copy. Ethan only reports what he saw for P3, P5 and P6.

Record the results in `docs/progress.md`. Re-plan M2 to M4 if P2 or P3 fail: fall back to editing existing entries and reusing vanilla names.

### M2: Core path kit

- Expose `DECALPATH` properly: build-menu group, product and blueprint entry or a free unlock, a sensible limit.
- New parts, each copied from a vanilla part with a vanilla scene:

  | Part | Copied from | Change |
  |---|---|---|
  | `SP_PATH_TILE`, `SP_PATH_TRI` | `S_FLOOR_Q`, `S_TRIFLOOR_Q` | Low profile, `EditsTerrain` set per the P5 result |
  | `SP_CURB` | The low wall players use as a step | Snaps under tile edges |
  | `SP_SIGNPOST` | A vanilla sign or plaque scene | |
  | `SP_LAMP` | A vanilla lamp | No power needed |

- Give all of them their own build-menu subgroup ("Settlement") if groups allow it.
- Tests: IDs unique and at most 16 characters, scenes exist in `scratch/all_files.txt`, every part has cost, product, group and loc entries.

### M3: OpenSettlements module

- Use the smallest exclusion change that P4 showed works.
- Before shipping, check for side effects: do buildings and points of interest still spawn normally around bases on a fresh planet? That goes in [SESSION 2].
- If the field turns out to control something else, drop the module and move the feature to Runtime (hook `DoBaseClaimOptions`).

### M4: Defense module

- Perk `SP_WATCH`: lowers `Alert`, raises `Sentinels`. Tune it against `StatsMaxValues` and `AlertUnitsPerCycleRateModifier`.
- Judgement `SP_J_FORTIFY`, "Fortify the perimeter?": the options cost resources and grant `SP_WATCH`. Copy the cost mechanism from vanilla sentinel judgements. Add it to the pool with the fewest edits possible.
- Decorative `SP_TOWER` reusing a settlement tower or sentinel pillar scene.
- `SettlementPlanner-TestTuning`: short `JudgementWaitTimeMin` and `JudgementWaitTimeMax` so the fortify decision shows up within minutes during testing.

### M5: Class-gated unlocks

Look for anything in data keyed on settlement class: unlock trees, blueprints, perks, vendor inventories.

- If something exists, gate the path kit at B, statues and billboards at A, and towers and walls at S.
- If nothing exists, record that, defer gating to Runtime, and in the meantime make the parts earnable through settlement judgement rewards.

### [SESSION 2]: Content, then compatibility

1. `testmode enter --modules core,open,defense,testtuning`. Ethan's checklist:
   1. Build a short path with the kit.
   2. Wait for and accept the fortify decision.
   3. Fly to a fresh planet and look around a new base site (OpenSettlements side-effect check).
   4. Save and quit.
2. `testmode exit`, then `testmode enter --with-user-mods --modules core,open,defense`. Ethan loads the **same creative save**, confirms the game starts, and confirms the parts and decision still work. Save and quit.
3. `compat_report.py` against Ethan's real `MODS` folder (read-only). It should flag gBase Boundaries (`RadiusMultiplier_DoNotPlaceAnywhereNear`) and the merged timer mod (`gcsettlementglobals`). Use the report to write `COMPATIBILITY.md`.

### M6: Runtime feasibility spike

1. Wait for an NMS.py release that matches the game build (`check_build.py`). Install it in a separate venv.
2. Prove, each as a throwaway mod:
   1. Log the current base's objects.
   2. Convert world positions to base-local ones.
   3. Place one `DECALPATH` from code. Ask upstream (NMS.py repo or Discord) about a placement function before deep reverse engineering.
   4. Optionally, flatten terrain inside a settlement.
3. **[SESSION 3]**, creative save, `--modules runtime-spike`.
4. Write a go or no-go to `docs/progress.md`. On no-go, build the offline save-edit planner instead, restricted to the creative test slot copy.

### M7: Path tool (after a go)

- An imgui panel: start, add point, finish, undo.
- Pieces are laid along the polyline, oriented to each segment, snapped to the terrain.
- Respect `PlanetBaseLimit` and the complexity budget.
- **[SESSION 4]**, then a release candidate.

### M8: Release prep

- `package.py` zips per module, a version bump, and a `CHANGES.md` entry list.
- **The Nexus page, README and screenshots are Ethan's.** The build session supplies the facts (features, compatibility list, install notes) in `docs/progress.md` and never writes those documents.

## 9. Testing

- **Automated (pytest, no game):**
  - Patches parse and templates match vanilla.
  - Edited `_id`s and fields exist; new IDs are valid and unique.
  - Scenes exist; every part has its full set of entries.
  - The merge preview compiles with the pinned MBINCompiler.
  - `testmode` safety tests and `save_inspect` tests pass.
- **Compatibility:** `compat_report.py` regenerates `COMPATIBILITY.md` from the patches, so the edit list is never written by hand.
- **In-game:** the batched [SESSION] checklists, with results confirmed from save copies where possible and recorded in `docs/progress.md`.
- **After a game update:** `check_build.py`, bump the tools, re-extract, rerun pytest. Failures name the renamed field or ID.
- **TDD rules:**
  - Write the test before the implementation, and don't design the fix inside the test.
  - A harness error is not a red.
  - Record the observed red in the commit message.
  - When a test passes on its first run, prove it can fail by breaking the code on purpose.

## 10. Workflow and autonomy

Ethan wants to be hands-off. The build session decides and proceeds on its own within this plan.

- **Git:**
  - One branch per milestone.
  - Commits as Ethan's global GitHub identity (`36464732+ethan-hann@users.noreply.github.com`). Check `git config user.email` before the first commit.
  - No attribution lines.
  - Push the branch and open a PR with `gh`. The body uses one unwrapped line per paragraph and notes the tests run.
  - **Merge it yourself** (merge commit, not squash, so the commit messages that record each TDD red survive) once automated tests pass and any session for that milestone is recorded. Ethan reviews merged PRs whenever he likes.
- **Stop and ask Ethan only for:**
  - each [SESSION] (send the checklist as one short message; use a push notification if he's away)
  - any safety failure
  - a scope change
  - a tool, game or NMS.py version mismatch that blocks progress
  - anything needing his accounts (Nexus, Discord)
- **Status updates:** a few lines, with any decision he needs to make first. Details go in PRs and `docs/progress.md`.
- **Comments in code and patches** explain why. They never name milestones, slices or phases; forward-looking notes go in `docs/progress.md`.
- **Out-of-scope findings** become GitHub issues on this repo.
- **Prose** in commits, PRs and docs: ASCII, American English, concise.

## 11. Definition of done for the `/goal` run

M0 through M5 merged, [SESSION 1] and [SESSION 2] recorded, the M6 spike report written, and `testmode.py status` reporting no open session with all safety checks passed. M7 and M8 follow in a later run, depending on the spike.

## 12. Risks and open questions

| Risk | Impact | Plan |
|---|---|---|
| Ethan presses Continue during a test session and loads his main save with only test mods | Modded items could be stripped from the main save | Warning in the checklist; full verified backup before every session; the `exit` hash check catches any change; restore only with his approval |
| A test session is left open and Ethan plays normally | Same as above | `exit` runs as soon as he reports the session done; `status` is checked at the start of every build-session turn that touches the game |
| A partial patch can't append new `_id`s | No new `SP_` parts | P2. Fall back to exposing and retuning vanilla parts |
| Custom text can't be added | Vanilla names reused | P3. Cosmetic |
| The exclusion field does more than claimed | Spawn side effects | P4 plus the [SESSION 2] check; fall back to Runtime |
| NMS.py lags or lacks a placement function | No path tool | M6 gate; save-edit fallback on the test slot only |
| Multiplayer visitors without the mod | Missing or odd parts | Vanilla scenes only; test with a second player before release (needs Ethan) |
| Game updates rename fields or regenerate settlements | Patches stop applying; paths misalign | The validator catches renames. Regeneration is Hello Games' and out of scope |
| NPC pathing | Players expect NPCs to use paths | Out of scope. Research note: per-part nav nodes exist for freighter parts; adding them to planet path parts might or might not be read by settlement NPCs. A one-hour spike after M7 at most |
| Moving settlement buildings | Wishlist item | Out of scope (generated layouts plus save data) |

## 13. Reproducing the investigation

hgpaktool `-f` filters used for `scratch/extracted/`:

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

Still to extract: `metadata/reality/tables/nms_reality_gcproducttable*` and `language/*english*` (M1).
