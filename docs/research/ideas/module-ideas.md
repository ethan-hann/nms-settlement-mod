# Module ideas

Thirty ideas for new or extended Overseer's Toolkit modules. Each one points at the complaints it answers in [player-feedback.md](player-feedback.md) (sections are cited as F1 to F14) and gets a feasibility tier from [modding-capabilities.md](modding-capabilities.md):

| Tier | Meaning |
|---|---|
| T1 | Data patch the existing generators already make, or nearly make |
| T2 | Data patch through a route the repo hasn't used yet; needs a generator change and an in-game probe |
| T3 | Runtime code that needs reverse engineering first |
| T4 | Not possible with known tools today |

Ideas at T3 and T4 carry a disclaimer. They stay on the list because tooling moves: NMS.py went from crashing on this build to shipping mods in under a week.

All ideas follow the plan's design principles ([../../plan.md](../../plan.md) section 2):
- target vanilla
- add rather than edit
- patch the fewest fields
- one optional module per feature
- vanilla scenes only
- text through localisation keys

## Summary

| ID | Idea | Answers | Tier | Demand |
|---|---|---|---|---|
| I-1 | Settler Stories judgement pack | F5, F3, F11 | T1 | High |
| I-2 | Town mission board | F5, F2, F11 | T2 | Medium |
| I-3 | Balanced Pacing presets | F2 | T1 | Very high |
| I-4 | Overtime crews (rush a build) | F2 | T2 | High |
| I-5 | Settlement Bonds (pay debt with your units) | F1 | T2 | High |
| I-6 | Fair Ledger rebalance | F1 | T1 | High |
| I-7 | Plain wording and an overseer's guide | F1, F13 | T1 | Medium |
| I-8 | Settlement Trade Goods | F3 | T1 | High |
| I-9 | Class rewards | F3, F9 | T1 | Medium |
| I-10 | Festivals and better gifts | F5, F11 | T1 | Low |
| I-11 | Settlement Structures | F6 | T1 | High |
| I-12 | Path Kit 2 | F6, F7 | T1 | High |
| I-13 | Plaza Foundation | F6 | T1 | Medium |
| I-14 | Settlement Farming | F8 | T2 | Medium |
| I-15 | Settlement Stores and Landing | F8, F6 | T2 | Medium |
| I-16 | Defense 2: perks and story chains | F4 | T1 | High |
| I-17 | Calmer Skies (attack pacing) | F4 | T1 | High |
| I-18 | Settlers stand their ground | F4, F11 | T2 / T4 | Medium |
| I-19 | Defence structures and turrets | F4 | T1 decor, T4 working turrets | High |
| I-20 | A visible brood alert | F4 | T4 | Low |
| I-21 | Livelier Towns | F11 | T1 | Medium |
| I-22 | Settlement Styles | F6 | T2 | Medium |
| I-23 | Autophage content | F12 | T1 | Low |
| I-24 | Find my building (mission marker) | F7 | T2 | High |
| I-25 | Building overview screen | F7 | T4 | Medium |
| I-26 | Multiplayer-safe parts | F6 | T1 | Unknown until tested |
| I-27 | Path tool, re-checked | F6 | T3 | High |
| I-28 | Runtime building markers | F7 | T3 | High |
| I-29 | Rearrange settlement buildings | F6 | T4 | Medium |
| I-30 | More than four settlements | F10 | T4 | Low |

---

## Decisions and stories

### I-1. Settler Stories (judgement pack)

- **Answers:** decisions that feel repetitive, random or punishing (F5); nothing to do (F3); passive settlers (F11).
- **What:** a new optional module of dilemmas.
  - Some are short multi-step stories using `ChainedJudgementID`. An example: a stranger asks for shelter, later turns out to be a deserter, and the town decides whether to hide them.
  - Each race gets its own flavour through custom NPC IDs and race-specific text.
  - Outcomes are always shown before you choose (`HidePerkInJudgement` false). Rewards go beyond stats: standing, alien words, nanites, items (`AdditionalRewards`), new perks.
  - Mostly positive or mixed outcomes, which answers "most events are negative".
- **How:** `gen_settlement.py` already appends judgements and perks. It needs chained follow-ups, which probably means `CustomJudgements` entries addressed by ID, plus reward-table entries.
- **Tier:** T1, with T2 for reward-table rewards.
- **To verify:**
  - whether a chained judgement can point at a `CustomJudgements` ID or must sit in the main pool
  - how new entries change the odds of vanilla ones; keep weightings low so they mix in
- **Why it's the top pick:** no other mod adds settlement content, and judgements are the system players touch most.

### I-2. Town mission board

- **Answers:** players asked for a mission board and for missions that speed construction instead of timers (F2, F5). Cantina missions and tip-offs (F11).
- **What:** repeatable settlement jobs that reward settlement stats, construction progress, or items. Examples: deliver supplies, clear a nearby hive, scan local fauna.
- **How:** missions copied from vanilla, appended to `NPCMISSIONTABLE` the way the class unlocks are. Gate them with `GcMissionConditionNearSettlement` and `HasSettlement`. Reward with `GcRewardSettlementStat`, `GcRewardSettlementProgress`, or `GcRewardSettlementCustomJudgement`.
- **Tier:** T2.
- **Disclaimer:** a new repeatable mission with its own giver may not be possible yet. Session 1 crashed after appending to `MODMISSIONTABLE`, and how missions get offered at a settlement is unknown. A fallback is to deliver the "job" as a judgement whose option starts a mission.

## Pacing

### I-3. Balanced Pacing presets

- **Answers:** the most-cited complaint, multi-hour timers (F2), and modders' requests for balanced pacing and split files.
- **What:** optional files that sit between vanilla and instant:
  - **Brisk:** about a quarter of vanilla build and upgrade times, decisions every 10 to 40 minutes.
  - **Construction-only.**
  - **Decisions-only.**
  
  None of them touch the overseer's office or the first construction mission, which instant mods break (Nexus 3907).
- **How:** a partial `GLOBALS/GCSETTLEMENTGLOBALS.EXML` setting only `BuildingUpgradeTimeInSeconds`, `SettlementBuildingTimes` entries and the judgement wait fields.
- **Tier:** T1.
- **Notes:**
  - The space is crowded: gSettlement Timers has 26.9k downloads and works on Cosmos. The edge would be balanced numbers, a Cosmos-current build, field-level patches and a COMPATIBILITY.md listing.
  - It conflicts with every timer mod by design, so say so on the page.
  - Read vanilla `SettlementBuildingTimes` first. `scratch/extracted` is not on this machine; run `tools/extract.py` where the game is installed.

### I-4. Overtime crews (rush a build)

- **Answers:** "pay more resources to shorten a cooldown" and "donate all materials at once" (F2).
- **What:** a "The builders offer to work overtime" dilemma that appears only while a building is under construction. Accepting adds debt or costs units, and advances the build.
- **How:**
  - A mission with `GcMissionConditionHasAnySettlementBuildingInProgress` fires a custom judgement through `GcRewardSettlementCustomJudgement`.
  - The option's reward is `GcRewardSettlementProgress` or `GcRewardBeginSettlementBuilding` with `IsUpgrade`.
  - `BuildingFreeUpgradeTimeInSeconds` may already be the shorter timer for free upgrades.
- **Tier:** T2.
- **To verify:** whether `GcRewardSettlementProgress` skips a stage or only nudges it, and whether a mission can fire a judgement while construction blocks decisions.

## Economy

### I-5. Settlement Bonds (pay debt with your own units)

- **Answers:** one of the oldest and most repeated requests (F1). Players with hundreds of millions of units can't clear 100k of town debt.
- **What:** a "Settlement Bond" item, bought for units, that clears a step of debt at the nearest owned settlement when used.
- **How:**
  - A new product, sold at the settlement market or through a specials-shop entry. The progress log notes the Consumerism mod's pattern for this.
  - Using it fires a reward through the consumable-item table.
  - The reward is `GcRewardSettlementStat` on `Debt`. The Defense module's fortify option adds debt with `NegativeMedium`, so a positive step should reduce it.
- **Tier:** T2.
- **To verify:**
  - the consumable-table route (vanilla `CONSUMABLEITEMTABLE`, not checked in this repo)
  - which settlement `GcRewardSettlementStat` applies to when the player owns four
  - whether settlement market inventories can be extended
- **Alternative:** a repeatable mission at the office whose cost is units and whose reward is the same debt step.

### I-6. Fair Ledger rebalance

- **Answers:** C-class buildings that lose money; advertised gains that don't arrive; upgrade materials like 63 Dirt (F1).
- **What:**
  - Retune `SettlementBuildingContributions` so a fresh C-class building breaks even rather than adding debt.
  - Replace upgrade stage costs that ask for items the town makes too slowly.
  - Optionally soften offline debt growth through `DailyDebtPaymentModifier`.
- **How:** a partial globals patch of specific array entries.
- **Tier:** T1 for the patch. Most of the work is balance.
- **Notes:** the debt and upkeep formulas are in the exe, so this changes inputs, not the math. 7.04 changed production behaviour, so measure on the current build before tuning. A save-inspect report of stats over a few days would help.

### I-7. Plain wording and an overseer's guide

- **Answers:** misleading "Donate to reserves" wording, no explanation of upkeep, debt or features (F1, F13).
- **What:**
  - Rewrite the confusing vanilla strings in plain English.
  - Add guide text to the Toolkit's own descriptions, for example a "Settlement Ledger" sign whose description explains how debt and reserves work.
- **How:** language patches for vanilla keys, plus `LocTable.MXML` entries.
- **Tier:** T1.
- **To verify:** whether a partial language patch can override vanilla keys. The Probes module has `LANGUAGE/` files, but the progress log doesn't record a result for overriding a vanilla string. English-only edits would leave other languages unchanged.

### I-8. Settlement Trade Goods

- **Answers:** nothing a settlement makes is unique; players want items they actually use (F3). Race-themed production from abandoned mods (Bomber's, SPDX).
- **What:** add useful, race-themed products to each race's production menu, gated by building type and level. Some options:
  - Gek trade goods and farm produce
  - Korvax tech parts
  - Vy'keen weapon and combat supplies
  - Autophage void-themed items
  - a few higher-tier items players asked for (storage augments, frigate modules, starship parts), unlocked only by S-class buildings
- **How:** append `GcSettlementProductionElement` entries to `*ProductionElementsSelectable`, as Settlement Bait Production (Nexus 3559) proves works. Set caps and multipliers per item.
- **Tier:** T1. It needs `gen_settlement.py` support for list appends in globals.
- **Notes:**
  - Balance against frigates and farming, or it becomes a cheat mod.
  - The production slot copies its multipliers when chosen, so changes apply to newly chosen products only.

### I-9. Class rewards

- **Answers:** S-class gives nothing (F3, F9).
- **What:** reward milestones with unlocks or items. For example:
  - an S-class Farm unlocks planters for the town (I-14)
  - an S-class Tower unlocks watch posts (I-19)
  - an S-class Market unlocks the trade-goods tier (I-8)
  - each first S-class building pays a one-off reward
- **How:** the existing `gen_unlocks.py` pattern, which uses `GcMissionConditionHasSettlementBuilding` with `MinimumClass` and a specific `BuildingClass`.
- **Tier:** T1.
- **To verify:** the class unlocks shipped in 1.0.0 have not been seen working in a non-creative game yet. Prove one before adding more.

### I-10. Festivals and better gifts

- **Answers:** few positive events (F5); a lifeless town (F11).
- **What:**
  - Dilemma options that throw a festival (`GcRewardSettlementParty`) with a happiness boost.
  - Richer per-race visitor gift pools (`*Gifts`). Visitor gifts were fixed in 5.73.
- **How:** judgements plus reward-table entries.
- **Tier:** T1.

## Building in the town

### I-11. Settlement Structures

- **Answers:** "build normal base parts in the settlement" (F6). It removes the need for the base-computer-at-the-edge trick and for gBase Boundaries, which isn't updated for Cosmos.
- **What:** an optional module that makes vanilla structure parts buildable from the settlement menu: stone, wood and metal walls, floors, stairs, arches and roofs. It mirrors what SettlementDecor does for decoration.
- **How:** `gen_parts.py group_edits` on the structure groups (`BuildableOnPlanet`), leaving out powered tech.
- **Tier:** T1.
- **To verify:**
  - `PlanetLimit` and `RegionLimit` for parts placed outside a base (stored in `PlayerStateData.BaseBuildingObjects`)
  - the per-tab build-menu limit
  - whether snapping works outside a base
  - the same side effect SettlementDecor has: the parts can be placed anywhere

### I-12. Path Kit 2

- **Answers:** requests for paving, roads, fences, benches, market stalls, flags and signposts (F6). Signs that help people find their way (F7).
- **What:** new `OT_` parts copied from vanilla scenes:
  - wide plaza tiles
  - steps and ramps for slopes
  - low and tall fences, and a gate or arch
  - benches and market stalls
  - race banners and flags
  - direction signs ("Office", "Landing Pad", "Market") using the existing sign scenes and number decals
- **How:** the core module's spec pattern.
- **Tier:** T1.
- **Notes:** pick parts that read well at settlement scale. Check I-26 first if new IDs turn out invisible to visitors.

### I-13. Plaza Foundation

- **Answers:** no terrain editing within about 300u of the monument; buildings and terminals buried in hills (F6).
- **What:** one large, flat, low-profile part that flattens the ground under it, for plazas and building pads. It is the path tile's terrain flattening at a bigger scale.
- **How:** copy `BUILDPAVING_BIG` or a large floor with `EditsTerrain=true` and `BaseTerrainEditShape=Cube`. Path tiles already flatten inside settlements (Session 2), so this is likely to work.
- **Tier:** T1.
- **Disclaimer:** free terraforming inside a settlement (dig, raise, smooth) may not be possible yet. The block on terrain editing appears to be in the exe. Placing flattening parts is the data workaround.

### I-14. Settlement Farming

- **Answers:** settlement planters and agri units are decoration only, and players want to grow crops (F8).
- **What:** let players place working vanilla planters and hydroponic trays in the settlement.
- **How:** `BuildableOnPlanet` on the vanilla planter parts, through the core or SettlementDecor pattern.
- **Tier:** T2.
- **To verify:** whether plants grow in a planter placed outside a base. Growth may depend on base ownership.
- **Disclaimer:** making the planters built into settlement buildings work may not be possible yet. They are scene props inside generated buildings, not base parts.

### I-15. Settlement Stores and Landing

- **Answers:** settlement storage, a warehouse holding tribute, an aquarium, a corvette pad (F8, F6, and the plan's wishlist).
- **What:** storage containers, a fish aquarium or display tank, and a corvette landing pad, buildable from the settlement menu.
- **How:** `BuildableOnPlanet` on the vanilla parts.
- **Tier:** T2.
- **To verify:** storage containers and landing pads may need a base computer to work or to save their contents.
- **Disclaimer:** a "tribute warehouse" that fills from settlement production may not be possible yet. The production slots are fixed at two and the delivery logic is in the exe.

## Defence

### I-16. Defense 2: perks and story chains

- **Answers:** constant attacks with nothing to do about them (F4).
- **What:** extend the Defense module.
  - **Train a militia** (perk): lowers Alert and raises happiness for Vy'keen towns.
  - **Pest control** (perk): lowers BugAttack, answering brood attacks that have no meter.
  - **A hive chain** (chained judgements): scouts find a brood nest, then you choose to fund an expedition, ask for help, or relocate farms.
  - **Hire a squadron** (request): borrows the vanilla squadron-pilot idea as a perk.
- **How:** `gen_settlement.py` perks and judgements; `BugAttack` is one of the eight stats.
- **Tier:** T1.
- **Notes:** the existing limit still applies. No condition checks whether a settlement owns a perk, so a perk dilemma can repeat. A custom judgement fired only once by a mission could avoid this, but that's T2.

### I-17. Calmer Skies (attack pacing)

- **Answers:** "how do I stop the constant attacks" (F4, Nexus 2855 comments).
- **What:** optional files with longer alert and bug-attack cycles: Calm (about 2x) and Quiet (about 5x). Unlike Peaceful Settlements (Nexus 3229), attacks still happen.
- **How:** partial `GCSETTLEMENTGLOBALS` with `AlertCycleDurationInSeconds`, `AlertUnitsPerCycleRateModifier`, and the BugAttack pair.
- **Tier:** T1.
- **Notes:** it conflicts with Peaceful Settlements and More Comfortable Settlement on those fields. Beacon already shares alert across settlements, so measure before picking multipliers.

### I-18. Settlers stand their ground

- **Answers:** settlers, even Vy'keen warriors, run back and forth during raids; players want towns that defend themselves (F4, F11).
- **What:** settlers stay outdoors and in cover during attacks instead of fleeing indoors.
- **How:** tune the `Afraid` state in `GcNPCSettlementBehaviourData`: lower `RunWhenOutdoorsProbability`, set `OnlyUseIndoorPOIs` false. The file path is not known yet.
- **Tier:** T2 for behaviour weights.
- **Disclaimer:** settlers who actually fight back may not be possible yet. NPC combat AI is not in any known data table, and NMS.py has no settlement hooks. That part is T4.

### I-19. Defence structures and turrets

- **Answers:** players want turrets, anti-air and defence buildings (F4).
- **What:**
  - **T1 now:** decorative defence parts from vanilla scenes (watch posts, barricades, sandbags, gun emplacement props). Each could come with a judgement that grants Perimeter Watch-style perks when built.
  - **T4 later:** working turrets.
- **Disclaimer:** working turrets that shoot raiders may not be possible yet. Vanilla has no player-buildable turret with combat behaviour. Adding one would need new entity behaviour that data patches don't reach, plus runtime code no one has written.

### I-20. A visible brood alert

- **Answers:** brood attacks have no alert meter (F4).
- **What:** show the BugAttack stat next to Sentinel Alert in the settlement overview.
- **Tier:** T4.
- **Disclaimer:** this may not be possible yet. `GcUIGlobals` has per-stat images and text for all eight stats, but which stats the overview shows looks hardcoded. A data probe could test whether filling the BugAttack slots makes it appear. Until then, I-16's pest-control perk makes the stat something players can act on.

## Life and looks

### I-21. Livelier Towns

- **Answers:** empty, passive towns; requests for more NPCs; Aces' population mod is abandoned (F11).
- **What:** raise `MaxNPCPopulation` modestly, and make settlers more sociable outdoors through behaviour weights.
- **How:** a partial globals patch, plus behaviour data (T2 part).
- **Tier:** T1 for the cap.
- **Notes:** this costs performance; test on a weak PC. Raising the population cap doesn't add settlers by itself (Nexus 3662 comments).

### I-22. Settlement Styles

- **Answers:** no customisation of how a town looks (F6).
- **What:** new weighted colour palettes and materials per upgrade level, for example weathered, clean or race-themed. Optional files could favour a style.
- **How:** `GcSettlementColourTable`, `GcSettlementMaterialTable`, `GcSettlementColourUpgradeTable`.
- **Tier:** T2. No mod has touched these.
- **Disclaimer:** choosing a style for one specific settlement may not be possible yet. Styles are rolled from the seed, so a patch changes the odds for every settlement.

### I-23. Autophage content

- **Answers:** a request for a "more fitting Autophage generator" building; Autophage towns have fewer events (F12).
- **What:** Autophage-only dilemmas (I-1 pattern), Autophage-themed decor in the settlement menu, and a decorative "generator" part from vanilla Autophage scenes.
- **Tier:** T1.
- **Disclaimer:** fixing Autophage towns that vanish or float may not be possible yet. That is an engine bug.

## Wayfinding

### I-24. Find my building (mission marker)

- **Answers:** no marker on the building being upgraded, a top complaint during the Cosmos expedition (F7).
- **What:** a marker on the building under construction or upgrade.
- **How:** vanilla construction missions use `GcMissionSequenceConstructSettlementBuildingWithScanEvent`, which places a scan-event marker. A patched or appended mission could keep that marker during upgrades too.
- **Tier:** T2.
- **To verify:** whether upgrades run through that sequence at all. If not, this moves to I-28.

### I-25. Building overview screen

- **Answers:** players want a list of every building with its status and class (F7).
- **Tier:** T4.
- **Disclaimer:** this may not be possible yet. The settlement UI pages are hardcoded (`SettlementOverview`, `SettlementBuildingDetails`), and data can't add a page. A runtime mod could draw its own list with pyMHF's GUI if settlement building data becomes readable at runtime.

## Cross-cutting

### I-26. Multiplayer-safe parts

- **Answers:** visitors may not see `OT_` parts (from the Ultra Base Building author; untested here).
- **What:** first, test it. Two players, one with the mod, look at a town with Path Tiles and signs. If new IDs are invisible, offer an alternative file that makes the vanilla parts themselves buildable in settlements (`S_FLOOR_Q`, `S_TRIFLOOR_Q`, the vanilla signs) instead of copying them. That is what SettlementDecor already does.
- **Tier:** T1.
- **Notes:** this edits vanilla entries, which goes against plan principle 2. That's why it would be an alternative file. Update the README's multiplayer line once the test is done.

## Runtime

### I-27. Path tool, re-checked

- **Answers:** "paths go down one piece at a time" (F6, the README roadmap).
- **What:** the planned path tool (M7 in the plan).
- **Why re-check:** NMS.py merged support for build 181442 on 2026-10-09, and NMS.py base-building mods shipped this week. Snap Angles (Nexus 4609) changes how parts are placed, so its source may point at the placement code M6 couldn't find.
- **Tier:** T3.
- **Disclaimer:** this may still not be possible. No known function places a base part from code.

### I-28. Runtime building markers

- **Answers:** finding buildings (F7) when I-24 isn't enough.
- **What:** HUD markers on settlement buildings under construction or upgrade.
- **How:** NMS.py exposes `cGcBaseBuildingManager::AddHUDMarker`. Settlement building positions would have to come from `cGcBuilding::Visited` or from new reverse engineering.
- **Tier:** T3.
- **Disclaimer:** this may not be possible yet. Nothing settlement-specific is hookable today.

## Not possible today

### I-29. Rearrange settlement buildings

- **Answers:** "reposition buildings into order"; layouts that put terminals in cliffs (F6).
- **Tier:** T4.
- **Disclaimer:** this may not be possible yet. Layout and plot assignment come from the settlement seed, and there are a fixed 48 plots. No data field places a building, and save editors can't move buildings either. Changing the seed regenerates the whole town. A distant option: a runtime hook into settlement generation, if anyone ever finds it.

### I-30. More than four settlements

- **Answers:** players running four towns ask for eight (F10).
- **Tier:** T4.
- **Disclaimer:** this may not be possible yet. The cap has no known data field. NomNom works around it by swapping settlements in and out of the save, which is not something a mod can ship.

---

## Probes to batch into the next test session

Following the progress log's rule to answer what can be answered offline first and batch the rest:

1. Do `OT_` parts show for a second player without the mod? (I-26)
2. Does a chained judgement fire from a `CustomJudgements` ID? (I-1)
3. Does `GcRewardSettlementStat` on Debt reduce debt, and on which settlement when the player owns several? (I-5)
4. Does a large `EditsTerrain` part flatten a plaza inside a settlement? (I-13)
5. Do planters grow, and do storage containers keep items, outside a base in a settlement? (I-14, I-15)
6. Does an appended production element show in the settlement's production menu? (I-8)
7. Does a class unlock fire in a normal game? It is still unverified from 1.0.0. (I-9)
