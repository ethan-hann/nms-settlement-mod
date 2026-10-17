# Fair Ledger: what the game files show

First pass, 2026-10-17, updated the same day with Session 6 results. Covers the three ideas behind the module: paying debt with the overseer's units (I-5), C-class buildings that lose money (I-6), and the wording around reserves and debt (I-7).

Each finding is marked:
- **Verified:** read directly in vanilla data, the type definitions, a save, or seen in a test session.
- **Inferred:** the most likely reading of the data, but not stated anywhere.
- **Unknown:** needs a game session.

## Sources

- Vanilla data, decompiled:
  - `scratch/extracted/`: settlement globals, reward, cost, perk and product tables, mission tables, English and USEnglish text. Extracted 2026-10-06; on 2026-10-17 the settlement globals, reward table and cost table in the installed game's archives hashed identical to these copies.
  - `scratch/extracted-ledger/`, new on 2026-10-17 and pulled read-only with the pinned hgpaktool and MBINCompiler: the consumable item table, the specials shop table, the trading cost table, the alien dialog ("puzzle") table, and the settlement UI pages.
- Type definitions: `tools/mbincompiler/libMBIN.dll` 7.4.1.3, read through .NET reflection.
- Saves: decoded copies of the test slot from Sessions 4 and 5 (`scratch/saves/`). The test town is Funana Bridge, a Gek settlement.
- The maintainer's installed mods, read only: which files they patch, and how.
- Earlier findings: [../settler-stories/vanilla-findings.md](../settler-stories/vanilla-findings.md) and [../../progress.md](../../progress.md).

## The eight settlement stats

- **Verified:** the stats are MaxPopulation, Happiness, Production, Upkeep, Sentinels, Debt, Alert and BugAttack. There is no Reserves stat and no reserves field in the saved settlement state (`GcSettlementState`).
- **Verified:** ranges from `StatsMinValues` and `StatsMaxValues`:

  | Stat | Min | Max |
  |---|---|---|
  | Production | 0 | 1,500,000 |
  | Upkeep | 0 | 1,000,000 |
  | Debt | 0 | 10,000,000 |

- **Verified:** a new settlement starts with 600,000 to 1,200,000 debt (`InitialStatsMinValues` and `InitialStatsMaxValues`) and 1 positive and 4 negative perks.
- **Verified:** `StatIsGoodWhenPositive` is false for Upkeep and Debt, and both the Debt bad and good thresholds are 0.5 of the 10,000,000 maximum.
- **Verified:** the UI shows Productivity and Maintenance Cost in units per day (`UI_SETTLEMENT_STAT_PROD_FMT` and `UI_SETTLEMENT_STAT_COST_FMT`, both "%NUM% u/day").
- **Verified in Session 6, roughly:** with productivity 579,063 and upkeep 127,768 a day, the game's "Time Until Cleared" for 2,272,871 debt was 128.6 hours, against 121 hours if the net 451,295 a day pays it down. So the net of productivity and upkeep is most of what moves debt; the gap is unexplained. The game text says so ("Reduce debt by constructing buildings and investing in settlement features to increase production and reduce maintenance costs"), but the formula is in the exe.
- **Verified (text):** while a settlement is in debt its production stops: "Settlement is in debt / Clear debts to restore production" (`UI_SETTLEMENT_PROD_DEBT`).
- **Verified:** `StatProductivityContributionModifiers` weights MaxPopulation 100, Happiness 30 and Production 30, and `StatProductionIsNegativeWhenBad` is true only for Happiness. **Inferred:** the productivity the town actually earns scales with beds and happiness, not just with building contributions. That fits the player report that production follows beds and that advertised gains arrive at less than half their value.

## Debt fields in the globals

- **Verified:** `InitialDebtCycles` is 1 and `DailyDebtPaymentModifier` is 4,000,000. These are the only debt scalars in data.
- **Unknown:** what either one does. The names suggest a daily repayment scale, but nothing in data or text uses them, and no public documentation was found.
- **Verified:** the saved settlement state keeps `LastDebtChangeTime` and `LastUpkeepDebtCheckTime`. In the Session 5 saves the debt timestamp moved with every save while the upkeep check stayed at 11:40 for over an hour. **Inferred:** upkeep is charged against debt on a long cycle, probably daily, and debt changes in between come from decisions.

## What buildings contribute

`SettlementBuildingContributions` gives each building type a list of stat ranges for `Base` and `Upgrade1` to `Upgrade3`. **Inferred:** Base is class C and each upgrade is one class step (B, A, S); the four levels match the four classes.

| Building (in-game name) | C productivity | C upkeep | C net, midpoint | Productivity added by 3 upgrades | Net at S, midpoint |
|---|---|---|---|---|---|
| Starport (LandingZone) | 10,000-15,000 | 20,000-22,500 | -8,750 | +38,750 | +30,000 |
| Leisure (Bar) | -5,000 to -1,000 | 20,000-25,000 | -25,500 | 0 | -25,500 |
| Infrastructure (Tower) | 20,000-30,000 | 30,000-40,000 | -10,000 | +46,250 | +36,250 |
| Trade Center (Market) | 20,000-25,000 | 35,000-50,000 | -20,000 | +68,750 | +48,750 |
| Small residence | 1,000-1,500 | 10,000-15,000 | -11,250 | 0 | -11,250 |
| Small industrial | 10,000-15,000 | 10,000-20,000 | -2,500 | +26,250 | +23,750 |
| Medium residence | 2,000-3,000 | 15,000-20,000 | -15,000 | 0 | -15,000 |
| Large residence | 2,000-3,500 | 30,000-35,000 | -29,750 | 0 | -29,750 |
| Administrative (SheriffsOffice) | 5,000-8,000 | 22,000-32,000 | -20,500 | +17,500 | -3,000 |
| Storage Facility (Double) | 15,000-25,000 | 30,000-35,000 | -12,500 | +66,250 | +53,750 |
| Farm | 15,000-25,000 | 30,000-40,000 | -15,000 | +82,500 | +67,500 |
| Factory | 20,000-30,000 | 40,000-50,000 | -20,000 | +90,000 | +70,000 |
| Fish Pond | 3,000-5,000 | 9,000-10,000 | -5,500 | 0 | -5,500 |
| Autophage RoboArm | 10,000-20,000 | 20,000-30,000 | -10,000 | +51,250 | +41,250 |

- **Verified:** every building's C level costs more upkeep than it produces at the midpoint. Only the small industrial building can come out ahead at C (a 15,000 productivity roll against a 10,000 upkeep roll); the tower and RoboArm reach break-even only on their best rolls.
- **Verified:** upgrades add productivity, population and happiness, and never upkeep. The production buildings turn positive by B or A class.
- **Verified:** residences, the bar and the fish pond never pay for themselves at any class. They pay in population and happiness instead, which feed productivity through the modifiers above (inferred).
- **Verified:** each contribution is a min-max range, so two buildings of the same type and class can differ by up to 15,000 a day. **Inferred:** the roll happens once per building and is kept.
- **Verified in Session 6:** building contributions are computed at runtime, not stored. A patch setting production buildings' C upkeep to 1,111 showed at once on existing buildings' pages, and Maintenance Cost fell from 381,454 to 127,768 a day, while the saved Upkeep stat stayed at -15,893. **Verified in Session 7:** removing the patch restores vanilla upkeep at once; with LedgerProbes no longer installed, Maintenance Cost was back at 381,454 a day.
- **Verified:** many starting negative perks add upkeep or cut productivity: 5 apply Upkeep NegativeMedium (30,000-50,000 more a day), 2 apply Upkeep NegativeLarge, and 5 apply Production NegativeMedium. A fresh town draws 4 negative perks and 1 positive one.
- **Verified:** the per-building UI page has an "Upkeep cost" field (`UI_SETTLE_BUILD_UPKEEP_TITLE`), so the player's report that upkeep is never shown may be out of date or refer to the office overview. **Unknown** which.

## Stat change strengths

Decisions, perks and rewards never name an amount; they name a strength, and `PerkStatStrengthValues` turns it into a range.

- **Verified:** Debt strengths:

  | Strength | Debt change |
  |---|---|
  | PositiveWide | -5,000 to -100,000 |
  | PositiveLarge | -50,000 to -100,000 |
  | PositiveMedium | -10,000 to -50,000 |
  | PositiveSmall | -5,000 to -10,000 |
  | NegativeSmall | +5,000 to +10,000 |
  | NegativeMedium | +10,000 to +50,000 |
  | NegativeLarge | +50,000 to +100,000 |

- **Verified:** Upkeep strengths run from -100,000 (PositiveLarge) to +100,000 (NegativeLarge), and Production from -100,000 to +100,000, on the same pattern.
- **Verified:** the largest debt cut any single stat change can make is 100,000, against a starting debt of up to 1,200,000 and a cap of 10,000,000.
- **Verified:** who uses Debt strengths today. Pool judgements: PositiveSmall 10 times, PositiveMedium 2, NegativeSmall 5, NegativeMedium 3, NegativeLarge 3. Custom judgements: only `J_DEBRIEF_POS` (PositiveLarge) and `J_DEBRIEF_NEG` (NegativeSmall). The Toolkit only adds debt: Defense's fortify option uses NegativeMedium, and Settler Stories uses NegativeSmall twice and NegativeMedium once. No perk changes Debt.
- **Inferred:** editing a Debt strength range changes every decision that uses it, vanilla and Toolkit alike. PositiveLarge is the least shared: only the positive expedition debrief uses it.

## Ways to take units and give a debt cut

### Rewards that change a settlement stat

- **Verified:** `GcRewardSettlementStat` has two fields: `StatToAward` (stat, strength, `DirectlyChangePopulation`) and `Silent`. There is no amount field and no field that picks a settlement.
- **Verified:** vanilla uses it three times, all inside the sentinel settlement mission table and all lowering Alert or BugAttack (`R_SENT_NO_ALERT`, `R_SETTL_SAFE`, `R_SETTL_BUGWIN`). Nothing in vanilla rewards a Debt change.
- **Verified:** a reward list (`GcRewardTableItemList`) can hold several items with `RewardChoice` GiveAll, so one reward can apply the same stat change several times.
- **Verified in Session 3:** the game finds and runs a reward entry a mod appends to the reward table's `SettlementTable` (`R_OT_SSP_B2` fired its custom judgement).
- **Verified in Session 6:** run from the Administration Terminal, `GcRewardSettlementStat` changes the terminal's own settlement. Each Debt PositiveLarge step, patched to a flat 100,000, cut exactly 100,000 and showed "Settlement debt reduced: 100,000 units".
- **Verified in Session 6:** a debt cut larger than the remaining debt stops at 0, and the excess is lost. A cut at zero debt shows "Settlement reserves increased: 100,000" (`UI_SETTLEMENT_WEALTH_MSG`), but the saved Debt stat stays 0 and nothing else in the settlement state changes.

### The overseer's terminal (recommended route)

- **Verified:** the Administration Terminal in the overseer's office is the dialog entry `SETTLEMENT_ADMIN` in `nms_dialog_gcalienpuzzletable` (interaction type `SettlementAdminTerminal`). It has four options: "View pending decision", "View %SETTLEMENT% status", "Manage all settlements" and "Leave".
- **Verified:** each option names a cost ID and a list of reward IDs. "View pending decision" costs `C_SETTL_JUDGE` (a pending-decision check) and gives `R_OPEN_SETJUDGE`. Options have `KeepOpen`, so the terminal can stay open after one is chosen.
- **Verified:** the building site entry `SETTLEMENT_CONSTRUCTION` ("Supply materials") works the same way: cost `C_SETTL_PROG`, reward `R_SETTL_PROG` (`GcRewardSettlementProgress`). It changes the settlement the player stands in, so settlement rewards from these terminals reach the local settlement (verified for these vanilla rewards; inferred for a stat reward).
- **Verified:** the cost table has 32 `GcCostMoney` entries, for example 50,000 units. A cost entry can show its price (`DisplayCost`) and can hide the option when the player cannot pay (`RemoveOptionIfCantAfford`).
- **Verified:** options also carry `DisablingConditions`, a list of mission conditions, and `GcMissionConditionSettlementStatLevel` (stat, normalised level, comparison) exists. No vanilla dialog option uses `DisablingConditions`, and vanilla uses the stat-level condition only for Alert and BugAttack at 0.99, inside sentinel missions.
- **Inferred:** an option appended to `SETTLEMENT_ADMIN` with a units cost and a reward of Debt stat changes would let the overseer pay debt in units, at the town's own terminal, with nothing added to the player's inventory and no product to remove later.
- **Verified in Session 6:** appended options sit after "Leave", and the terminal lists six options at most: with three appended, the third never showed. No vanilla dialog entry has more than six options, so two appended options fill the terminal.
- **Verified in Session 6:** a `DisablingConditions` entry (`GcMissionConditionSettlementStatLevel`, Debt, Greater than 0) did not hide or disable the option at zero debt.
- **Verified in Session 6:** a `GcCostMoney` cost on a terminal option charges exactly its price, scaled by the Purchases difficulty setting (`CurrencyCost` in data). At Standard, 200,000 units showed and was taken. At Free the price showed at a third and nothing was taken; at Discounted the price is also a third (verified in `difficultyconfig`: `Units` 0.33 for Free and Cheap, and `InteractionsCostsAreFree` only for Free).
- **Verified:** no installed mod patches the dialog table or the cost table.

### A bond item (I-5 as first written)

- **Verified:** consumables are `GcConsumableItem` entries (497 in vanilla): an item ID, a reward ID, an optional cost check, and whether the item is destroyed on use.
- **Verified:** the specials shop table lists items by ID with a shop number and no price. **Inferred:** the specials shop (the Space Anomaly) sells for quicksilver, not units, so a bond sold there would not spend the units players want to spend.
- **Verified, conflict risk:** the installed Consumerism mod replaces the whole specials table (`_overwrite="true"`), which would erase an appended bond.
- **Inferred:** the bond needs four new pieces (a product, a consumable, a reward, a shop entry) where the terminal option needs two (a cost and a reward), and it still has the unknown of which settlement the reward reaches when used away from a town.

### Decisions

- **Verified:** judgement options have no cost field, so a decision cannot charge units. Vanilla "funding" options add debt instead.
- **Verified:** decision options can already cut Debt through their stat changes (vanilla pool options and the positive debrief do).

## Reward table conflicts, re-checked

- **Verified on 2026-10-17:** five installed mods patch the reward table (BetterRewardsCombined, EqualPlantTimerAndProduction, gFreighter Legal SFMs, MoreSalvageData, Unlockable Expedition Exclusive Techs). All five now ship partial EXML patches without `_overwrite`. The Settler Stories finding that two of them ship the whole table as MBIN no longer matches this install.
- **Inferred:** a player with an older whole-table version of any reward-table mod could still lose appended entries, depending on load order.

## Wording

- **Verified:** the vanilla keys behind the debt and reserves text, all in `nms_loc7`:

  | Key | Current English |
  |---|---|
  | `UI_SETTLEMENT_STAT_UPKEEP` | Maintenance Cost |
  | `UI_SETTLEMENT_STAT_RESERVES` | Reserves |
  | `UI_SETTLEMENT_PROD_DEBT` | Settlement is in debt / Clear debts to restore production |
  | `UI_SETTLEMENT_PROD_DEBT_TIP` | Reduce debt by constructing buildings and investing in settlement features to increase production and reduce maintenance costs |
  | `UI_SETTLEMENT_PROD_DEBT_TIP2` | Settlement productivity has increased and debts are reducing! Debt will now be automatically repaid over time. |
  | `UI_SETTLEMENT_PROD_DEBT_LEFT` | Time Until Cleared |
  | `UI_SETTLEMENT_PROD_WEALTH_TITLE` | Current Reserves |
  | `UI_SETTLEMENT_STAT_COST_NAME` | upkeep costs |

- **Verified:** the game says "Maintenance Cost" in the overview, "Upkeep cost" on the building page, and "upkeep costs" in decision text, for the same stat.
- **Unknown:** where the "Donate to reserves" wording that players quote comes from. No English or USEnglish string contains "donate" together with reserves or settlement. It may be a paraphrase, a string outside the extracted files, or text that has since changed.
- **Verified in Session 6:** "Reserves" appears nowhere in the overview or the history page, even at zero debt. Only the zero-debt message names it. **Inferred:** reserves are a leftover concept with no stored value.
- **Verified:** installed mods override vanilla text through `LocTable.MXML` with vanilla key IDs: Normalize Economy Names (82 keys, for example `UI_CONFLICT_LEVEL_LOW_1`) and _PM_InformationStorm (305 keys, for example `WEATHER_HEAT1`). Both fill all 17 languages. **Inferred:** the override works, since the maintainer plays with both.
- **Verified:** the Toolkit's `LocTable.MXML` writes only English and USEnglish for its own new keys.
- **Verified in Session 6:** an override entry with only English and USEnglish shows the new text in English and the raw key (`UI_SETTLEMENT_PROD_DEBT_TIP2`) in French. The probe's own new keys showed raw in French too, so every Toolkit text key does the same outside English.

## Upgrade materials

- **Verified:** each construction and upgrade stage costs one item at a fixed amount. The "63 Dirt" report matches the farm's S-class stage, 64 Dirt (`TRA_MINERALS1`). Other large stages: 99 `TRA_EXOTICS1` for the bar's S class, 350 `GASGIANT1` for the factory's, and 55,000 units for the large residence's decoration stage.
- **Verified:** Dirt is a Gek trade commodity (`UI_TRADE_ITEM_MINERALS_1_NAME`). **Inferred:** it is bought at trade terminals, so the complaint is about knowing where to get it, not about the town making it.

## Other things noticed

- **Verified:** the test town's saved stats in Session 5: debt 2,294,024, productivity stat 343,379, upkeep stat -15,893, population 15. Its debt rose from 2,187,495 (Session 4) to 2,295,968 over sessions with test tuning, which fires a decision every one to two minutes and favours debt-adding requests. It is not a fair sample of normal play.
- **Verified:** the merged timer mod in the maintainer's setup patches only timer fields in the settlement globals, so it does not touch any economy field.
- **Verified:** `GcRepShopDonation` (guild donation shops) and `GcCostMoney` both exist, but no vanilla settlement interaction charges units.
