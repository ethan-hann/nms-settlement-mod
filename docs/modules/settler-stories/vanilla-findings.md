# Settler Stories: what the game files show

Second pass, 2026-10-09. It replaces the first pass from the same day, which read only `gcsettlementglobals` and got two things wrong (see "Corrections").

Each finding is marked:
- **Verified:** read directly in vanilla data, the type definitions or a save.
- **Inferred:** the most likely reading of the data, but not stated anywhere.
- **Unknown:** needs a game session.

## Sources

- Vanilla data, decompiled: `scratch/extracted/` (settlement globals, reward table, perks table, five mission tables, English and USEnglish language files) and `scratch/extracted-stories/` (seven more mission tables, `ui/interactionjudgementpage`, `gcuiglobals`, `statdefinitionstable`). Pulled from the game's own archives with the repo's pinned hgpaktool and MBINCompiler.
- Type definitions: `tools/mbincompiler/libMBIN.dll` 7.4.1.3, read through .NET reflection. `scratch/nmspy_types.py` doesn't cover these structs.
- Saves: the decoded test-slot saves under `scratch/saves/` (round1, session2a, session2 final).
- Earlier session notes: `docs/progress.md` and `scratch/session*.md`.
- Other mods: `scratch/realmods/` and the export of a 55-mod test setup, `scratch/exported/20261007-202657/`.
- Web: Hello Games' Beacon update page and the Step modding wiki. Neither documents these fields; nothing else public was found.

## Corrections to the first pass

- **Mission appends did not "crash in session 1".** One mission appended to the empty `modmissiontable` was among several changes in the crashing runs. It was the prime suspect, never proven. Missions appended to `NPCMISSIONTABLE` ship in 1.0.0 and load fine (Progress -1 in saves). None has yet been seen to start and pay out in a normal game.
- **Route B has no vanilla precedent.** No judgement option in vanilla starts a custom judgement through a reward, directly or through a mission. The first pass called both halves "proven"; they exist separately but are never joined.

## Judgement structure

- **Verified:** the two lists:
  - `Judgements`: the random pool, 36 entries. Entries have no `ID` field and no `_id`, so nothing can point at a pool judgement.
  - `CustomJudgements`: 13 entries addressed by a 16-byte `ID`.
- **Verified:** a custom entry wraps the same `GcSettlementJudgementData` as a pool entry, plus `CustomCostText` and `CustomMissionObjectiveText`.
- **Verified:** sizes from libMBIN:
  - judgement `ID`, `ChainedJudgementID`, each `AdditionalRewards` element, perk IDs and reward table `Id`s are 16-byte strings;
  - text keys are 32-byte strings.
  
  Whether 16 bytes means 15 or 16 usable characters is **unknown**. The repo's tools disagree (`gen_parts.py` uses 16, `gen_unlocks.py` 15), so new IDs stay at 15 characters or fewer.
- **Verified:** the judgement types are None, StrangerVisit, Policy, NewBuilding, BuildingChoice, Conflict, Request, BlessingPerkRelated, JobPerkRelated, ProcPerkRelated, UpgradeBuilding and UpgradeBuildingChoice. `JudgementSelectionWeights` sets NewBuilding, UpgradeBuilding and UpgradeBuildingChoice to 0.
- **Verified:** no judgement field works as a requirement: no minimum class, required building or required perk.
- **Verified:** an option's perk entry has only `Perk` and `PerkChance`, with no guard against a perk the settlement already owns. In session 2, accepting the fortify request twice left `OT_WATCH` in the save once.

## Chains and custom judgements

- **Verified:** all 8 non-empty `ChainedJudgementID` values are on custom judgements and point at custom judgements:
  - `J_SENT_MISS_1` to `1B`
  - `J_SENT_MISS_3` to `3B` or `3C`
  - `J_SENT_4_ARMS` and `J_SENT_4_LEGS` to `4B` or `4C`

  No pool option chains.
- **Verified:** vanilla starts the first step of a custom judgement in four ways:

  | Route | Judgements | Where |
  |---|---|---|
  | Mission reward `GcRewardSettlementCustomJudgement` | `J_SENT_MISS_1`, `J_SENT_MISS_3`, `J_SENT_4_LEGS`, `J_SENT_4_ARMS` (Sentinel missions); `J_BUI_VISITOR` (`SETTLE_MGR`) | sentinel settlement mission table |
  | The same reward in a seasonal mission | `J_S23_BEACON` (mission `BEACON`) | seasonal bespoke mission table |
  | Globals `MiniMissionSuccessJudgement` / `MiniMissionFailJudgement` | `J_DEBRIEF_POS`, `J_DEBRIEF_NEG` | settlement globals |
  | Chain from another custom judgement | the B and C steps above | settlement globals |

- **Verified:** every custom entry has `Weighting` 1.0 except `J_DEBRIEF_POS` and `J_DEBRIEF_NEG`, which are 0.0. The debriefs still fire, so a weight of 0 doesn't stop a custom judgement that is awarded directly.
- **Inferred:** the random draw never picks custom judgements. Nothing references them by weight, and the save tracks a pool judgement by type alone (`PendingJudgementType`) and a custom one by ID (`PendingCustomJudgementID`). Not stated anywhere.
- **Unknown:** whether a pool option's `ChainedJudgementID` can point at a custom judgement (route A). Vanilla never does it.
- **Unknown:** whether a judgement option can fire a custom judgement through a reward (route B). Vanilla never does it.
- **Unknown:** what `CanOverrideNonCustomJudgement` does. It's true on six of the seven rewards and false only on `J_BUI_VISITOR`. Only one judgement can be pending at a time (verified from the save format).

## Rewards

- **Verified:** `AdditionalRewards` IDs resolve from several places:
  - the reward table's `SettlementTable` (`R_J_GIFTITEM1`, `R_SET_FW_EXPED`)
  - its `GenericTable` (`TECHFRAG_XL`)
  - a mission's own `Rewards` list (`R_SENT3_J_ALT`, `R_SENT4_LEGS`)
- **Unknown:** whether a mission-local reward needs its mission to be active when the option is chosen.
- **Verified:** `SettlementTable` has 71 entries, including 37 gift entries `R_J_GIFTITEM1` to `37` and `R_J_BOUNTY`. Currency gifts: `R_J_GIFTITEM1` gives 500-600 nanites, `R_J_GIFTITEM2` 100,000-300,000 units, and `R_J_BOUNTY` 200-500 quicksilver. The rest give specific products, substances or procedural items.
- **Verified:** a judgement option can start a mission. `J_BUI_VISITOR` gives `R_J_BUI_VISITOR` and `R_J_BUI_SCAN`, which start `SETTLE_BUI_J` and `SETTLE_BUI_SE`.
- **Verified, conflict risk:** two installed mods (EqualPlantTimerAndProduction, Unlockable Expedition Exclusive Techs) ship the whole reward table as MBIN. Either one, loaded after this module, would erase any entry it appends to `SettlementTable`.
- **Verified, conflict risk:** in the 55-mod export, an unidentified mod raises eight vanilla `SettlementTable` payouts. For example, `R_J_GIFTITEM1` goes from 500-600 nanites to 2500-3000, and `R_J_BOUNTY` from 200-500 quicksilver to 2000-5000. Reusing vanilla gift IDs means other mods can change this module's rewards.
- **Verified:** per-race gift lists exist in the globals:
  - `GekGifts`: `R_J_GIFT_TRA1`, `TRA2`
  - `KorvaxGifts`: `R_J_GIFT_EXP1`, `EXP2`
  - `VykeenGifts`: `R_J_GIFT_WAR1`, `WAR2`
  - `AutophageGifts`: reuses `EXP1`, `EXP2`

  There is also a general `Gifts` list. Options with `UseGiftReward` true (3 vanilla options) **probably** draw from the settlement race's list. That reading is inferred.

## Race

- **Verified:** judgements have no race field. The only race-related fields are `DilemmaTextIsAlien` (true only on `J_BUI_VISITOR`) and `JudgementSpecificRacePartyChance` (0.16, parties only).
- **Verified:** the save stores each settlement's race (`GcSettlementState.Race`). The test-slot saves show `Warriors` (Vy'keen) and `Traders` (Gek).
- **Verified:** the race enum names are Traders (Gek), Warriors (Vy'keen), Explorers (Korvax), Robots, Atlas, Diplomats, Exotics, None, and Builders (Autophage).
- **Verified:** the mission condition `GcMissionConditionHasSettlement` takes `SpecificAlienRace`. Vanilla sets it to Builders only in the Autophage storyline (`SETTLE_BUI_SE`, `SETTLE_MGR`).
- **Inferred, well supported:** it means "the player owns a settlement of that race", not "is standing in one". `SETTLE_BUI_SE` marks an unowned Autophage settlement and ends when that condition turns true. `SETTLE_MGR` pairs it with a `NearSettlement` that excludes Autophage settlements. No condition anywhere tests the race of the settlement the player is at.
- **Verified:** `AwardToClosestSettlement` is false on six vanilla custom-judgement rewards. It's true only on the seasonal `BEACON` mission.
- **Unknown:** which settlement receives a fired judgement when the player owns several, with the flag false or true. A race-gated mission could land its judgement at a different-race settlement.
- **Verified:** the text placeholder `%RACE%` exists in 16 vanilla strings, for example "%RACE% Planetary Settlement" and "%RACE% words". None is a judgement string.
- **Unknown:** whether the dilemma screen fills in `%RACE%`. Judgement text uses many other placeholders: `%NAME1%` (187 strings), `%NUM%`, `%NAME%`, `%SETTLEMENT%`, `%ITEM%`, and more.

## Missions

- **Verified:** what the repo ships. `gen_unlocks.py` copies vanilla `STORAGE_FIX` into `NPCMISSIONTABLE` as Guide-class missions with `AutoStart` AllModes, gated on `GcMissionConditionHasSettlementBuilding` (`CheckAllSettlements` true).
- **Verified:** vanilla's own judgement-to-mission chain (Autophage) never restarts. `RestartOnCompletion` and `IsRecurring` are false.
- **Verified:** missions can test for a specific pending judgement with `GcMissionConditionHasPendingSettlementJudgement` (`SpecificID`).
- **Unknown:** whether a Guide-class `NPCMISSIONTABLE` mission can give `GcRewardSettlementCustomJudgement` without crashing, and to which settlement it goes.
- **Unknown:** exactly how a mission group's `ConditionTest` is evaluated. The `SETTLE_MGR` Autophage branch reads inconsistently either way.

## Text

- **Verified:** vanilla judgement strings live in `nms_loc7` and `nms_loc9`, in both English and USEnglish. `gen_parts.py` already writes both.
- **Verified:** the longest vanilla text key is 31 characters, which matches the 32-byte field.
- **Verified:** text markup tags in use include `<TECHNOLOGY>`, `<STELLAR>`, `<TRADEABLE>`, `<COMMODITY>`, `<SPECIAL>` and `<TRANS_DIP>`.
- **Unknown:** what other languages show for the module's keys. Nothing is tested outside English.

## Other things noticed

- **Verified:** 4 option slots hold more than one variant: Conflict pool entries 3 and 4, and BlessingPerkRelated 30. The variants differ only in text and stat changes, with no weight field. **Inferred:** the game picks one at random.
- **Verified:** `GcRewardTriggerSettlementJudgement` (in `R_OPEN_SETJUDGE`) has no fields and nothing references it. **Unknown:** what it does.
- **Verified:** `GcRewardSettlementJudgement` (`JudgementTypes`, `Silent`) exists in the types. Nothing in the extracted data uses it.
- **Verified:** `SETTLE_MGR` checks for a pending `J_SENT_MISS_4`, which doesn't exist. It's a stale vanilla reference and harmless.
- **Verified:** no installed mod and no mod found on Nexus adds judgements, custom judgements or settlement missions.
