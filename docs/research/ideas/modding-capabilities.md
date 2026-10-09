# What modding can change about settlements

This file covers each modding route, what it can reach, and where the known hard limits are. Struct and field names come from MBINCompiler `development` at commit `fbfc377` (identical to release v7.07.0-pre1, 2026-10-08) and NMS.py `master` at `6ac15ca` (2026-10-09). No settlement struct changed between v7.04.1-pre3, which this repo pins, and v7.07.0-pre1.

Unless marked otherwise, the "what it likely controls" notes are read from field names and have not been tested in game.

## Feasibility tiers used in module-ideas.md

| Tier | Meaning |
|---|---|
| T1 | A data patch the repo's generators already make, or nearly make (parts, perks, judgements, unlock missions, globals values) |
| T2 | A data patch through a route the repo has not used yet (reward table, consumables, production lists, NPC behaviour, palettes, new missions). It needs a generator change and an in-game probe |
| T3 | Runtime code (NMS.py or a native DLL) that hooks functions NMS.py does not expose yet, so reverse engineering comes first |
| T4 | Not possible with known tools today: hardcoded in the exe, a fixed enum, or engine behaviour. Listed anyway; it could open up later |

## 1. Data patches (EXML through MBINCompiler)

This is what the Toolkit ships today: partial EXML patches under `GAMEDATA/MODS/<Module>/`, merged by the game.

### `GcSettlementGlobals` levers

| Area | Fields |
|---|---|
| Construction time | `BuildingUpgradeTimeInSeconds`, `BuildingFreeUpgradeTimeInSeconds`, `SettlementBuildingTimes[63]` per building class |
| Construction cost | `SettlementBuildingCosts[63]`, each with 9 stage costs (Start, GroundStorey, RegularStorey, Roof, Decoration, Upgrade1 to 3, Other): products or substances, amount range, currency |
| Building effects | `SettlementBuildingContributions[63]`: stat ranges for Base and Upgrade1 to 3 |
| Decisions | `JudgementWaitTimeMin/Max`, `JudgementSelectionWeights[12]`, `Judgements` (the random pool), `CustomJudgements` (fired by ID) |
| Attacks | `AlertCycleDurationInSeconds`, `AlertUnitsPerCycleRateModifier`, `BugAttackCycleDurationInSeconds`, `BugAttackUnitsPerCycleRateModifier`, `ScanEventsThatPreventSentinelAlert` |
| Production | `ProductionCycleDurationInSeconds`, `ProductUnitsPerCycleRateModifier`, `SubstanceUnitsPerCycleRateModifier`, `ProductionBoostConversionRate`, `StatProductivityContributionModifiers[8]`, and per-race `Gek/Korvax/Vykeen/AutophageProductionElementsSelectable` (product, building-level requirement, cap, amount and time multipliers) |
| Stats | `StatsMinValues/MaxValues[8]`, initial ranges, good and bad thresholds, `PerkStatStrengthValues` (the numbers behind each strength step) |
| Population | `PopulationGrowthRatePerDayBad/Neutral/Good`, the band thresholds, `StartingPopulationScalar`, `MaxNPCPopulation` |
| Perks | `MaxPerksCount`, the initial positive and negative counts, per-stat `PolicyPerks`, `ResearchPerks`, `AltResearchPerks`, `TechGiftPerks` |
| Debt | `InitialDebtCycles`, `DailyDebtPaymentModifier` |
| Gifts and jobs | Per-race `*Gifts` (text plus a reward ID), `JobTypes` |
| Towers and expeditions | `TowerRechargeTime`, `TowerPowerRechargeTime[4]`, `SettlementMiniExpeditionTime`, `SettlementMiniExpeditionSuccessChance` |

### Judgements

`GcSettlementJudgementData` has:
- a type (one of 12)
- a weighting
- the title, question and dilemma text
- custom NPC IDs, names and hologram effects
- up to four option lists

Each `GcSettlementJudgementOption` carries:
- `Perks`, each with a chance
- `HidePerkInJudgement`
- `StatChanges`
- `AdditionalRewards` (reward-table IDs)
- `ChainedJudgementID` (a follow-up dilemma)
- gift, policy and tech-perk flags
- a standing change

Multi-step stories and new dilemmas are pure data. The Toolkit's Defense module already appends one judgement and one perk, and its generator (`tools/gen_settlement.py`) handles both.

### Missions and rewards that touch settlements

- **Conditions:**
  - has a settlement, optionally of a given race
  - has a settlement building of a class and a minimum C to S level
  - a building is in progress
  - a judgement is pending
  - a stat is above or below a level
  - the player is near a settlement
- **Rewards:**
  - change a settlement stat by a strength step
  - queue a judgement of given types
  - fire a custom judgement
  - begin or advance a building
  - throw a party with fireworks
  - start or end a settlement expedition
  - a pirate attack (not settlement-specific)
- **Costs:** own a settlement, a building upgrade level, advance a settlement building, a pending judgement.
- **Where the Toolkit stands:** its class-gated unlocks already use `GcMissionConditionHasSettlementBuilding`, with copies of vanilla `STORAGE_FIX` appended to `NPCMISSIONTABLE`. Session 1 crashed with a mission appended to `MODMISSIONTABLE`; the cause was not proven ([../../progress.md](../../progress.md)). New missions should follow the `NPCMISSIONTABLE` pattern.

### Other settlement data

- **NPC behaviour:** `GcNPCSettlementBehaviourData` sets weights per mood state (Generic, Sociable, Productive, Tired, Afraid). It covers building-class capacity and weight, object types, `RunWhenOutdoorsProbability` and `OnlyUseIndoorPOIs`. The file path was not found.
- **Looks:** `GcSettlementColourTable`, `GcSettlementMaterialTable` and `GcSettlementColourUpgradeTable` hold weighted palettes and materials per upgrade level. They also have a `DecorationPartIds` list. The WFC building data (`GcWFCBuilding`, module and decoration sets) sets how buildings are assembled. No mod touches any of this.
- **Spawn density:** `PLANETBUILDINGTABLE`, as used by More Settlements (Nexus 3230).
- **Build parts:** `BASEBUILDINGOBJECTSTABLE`, as the Toolkit does now. Settlement buildings themselves are not base parts. Nothing links a placed part to a settlement building class.

### Hard limits of data patches

- **Fixed sizes:**
  - 8 stats
  - 12 judgement types
  - 63 building classes (settlement ones are a subset)
  - 9 construction levels, so at most 3 upgrade tiers
  - 48 building plots
  - 2 production slots
  - 4 tower powers
  - 100 saved settlement slots

  New building classes or stats are not possible.
- **Layout:** layout and plot assignment come from the settlement seed. No field places a given building on a given plot.
- **Formulas:** these are in the exe. That covers how Alert turns into an attack, the debt and upkeep math, and how happiness drives population. Data only exposes scalar modifiers. The 4114 mod author says: "We can only mess with the values, not the formula."
- **Settlement cap:** the 4-settlement limit and the claim rules have no known data field.
- **Build menu:** each tab has a hardcoded item limit, worked around with composite objects and recategorising mods (Ultra Base Building, BuildFrame RecTUM).
- **Snap points:** the global snap-point quota has not been raised since 6.18 (Eucli-ea author).
- **Multiplayer:** custom part IDs are not synced, so visitors without the mod may not see `OT_` parts (Ultra Base Building author). Untested for this mod. Vanilla IDs made buildable, as in the SettlementDecor module, should sync.
- **File conflicts:** every settlement-tuning mod patches `GCSETTLEMENTGLOBALS`. Partial EXML patches merge field by field; whole-file MBIN mods win outright.

## 2. AMUMSS (Lua mod scripts)

AMUMSS decompiles game files, applies Lua change tables, and rebuilds a mod. Players use it to merge mods that touch the same file and to rebuild abandoned mods. It adds nothing the EXML route cannot reach, but players ask for the Lua because it is how they merge. The Toolkit's spec-driven generators fill the same role. Latest build: 5.6.2.0W ([Nexus 957](https://www.nexusmods.com/nomanssky/mods/957)).

## 3. NMS.py and pyMHF (runtime hooks)

- **It is current again.** NMS.py merged "Update for NMS 181442" on 2026-10-09 and has followed each Cosmos build within days. Runtime mods shipped on Nexus this week: Snap Angles (4609), Inventory and QoL (4600), Better Flight (4475). This contradicts the repo's 2026-10-07 finding that NMS.py 180383.0 crashed on 180836, and the README roadmap line. Check `tools/check_build.py` against the installed build before acting on it. [NMS.py commits](https://github.com/monkeyman192/NMS.py/commits/master)
- **No settlement surface.** About 276 named functions are hookable, and none is settlement logic. Useful entries include:
  - `cGcBaseBuildingManager::Update`, `GetBaseRootNode`, `GetBaseBuildingRootMatrix` and `AddHUDMarker`
  - `cGcBuilding::Visited`
  - player, inventory, HUD and notification functions
  
  `cGcRealityManager` points at the settlement perks table and the sentinel-settlement mission table, but judgement choice, production ticks and alert growth have no hooks.
- **Placing parts:** there is still no known "place a base part" function (M6 in [../../plan.md](../../plan.md)). Snap Angles changes how the player places parts, which suggests the placement code is reachable. That is worth reading before any path-tool work.
- **Native alternative:** Planetary Surveyor (4521) moved from NMS.py to a C++ DLL loaded through a `version.dll` proxy. Players then don't need Python.
- **Friction for players:** they need Python and a launcher. Mod 4600 bundles a runtime to hide this.

## 4. Custom models and textures

- **NMSDK** (Blender 4.2+) imports and exports scenes; it is actively maintained. The STEP wiki has tutorials for adding custom models to the build menu. [NMSDK](https://github.com/monkeyman192/NMSDK), [STEP tutorial](https://stepmodifications.org/wiki/NoMansSky:Tutorials/Importing_Custom_Models)
- Custom models and decals ship in mods such as Eucli-ea and Kibbles 'n Bits.
- **Limits:**
  - no complex animation
  - collision support is doubtful
  - shaders are hard to edit
  - custom parts are invisible to visitors
  - new snappable parts compete for the frozen snap quota
- **For this repo:** plan principle 5 (no new 3D assets) and Ethan's art constraint both apply. Custom models would have to come from free marketplaces or be built with Claude in Blender. Ideas below prefer vanilla scenes.

## 5. Save editors (NomNom, goatfungus)

- **NomNom** edits a settlement's stats, perks, name, seed (which changes its look), next decision and timers. It keeps a "collection" that works around the settlement limit by swapping. [NomNom wiki](https://github.com/zencq/NomNom/wiki/Save.-Planetary-Settlement)
- **goatfungus** players use the raw JSON to change production items and reset debt.
- **Limits:** buildings can't be moved; they regenerate from seeds. Editing the alert value does not fix a stuck alert for long. Raising population raises the cap, not the settler count.
- **For this repo:** `tools/save_inspect.py` already decodes saves. The plan restricts any save writing to Ethan's creative test slot, so save-edit tools are for testing, not shipping.
