# Fair Ledger: rough plan

Rough outline, written 2026-10-17. Not a spec yet. Nothing is built.

## Goal

Make the settlement economy something an overseer can read and act on:
- Pay a town's debt with the overseer's own units (idea I-5).
- C-class buildings that break even instead of adding debt (I-6).
- Plain wording for upkeep, debt and reserves (I-7).

The research is in [../../research/ideas/module-ideas.md](../../research/ideas/module-ideas.md). The economy is the top unfixed player complaint (F1 in [player-feedback.md](../../research/ideas/player-feedback.md)): debt cannot be paid with units even by players holding hundreds of millions, every C-class building runs at a loss, and the wording is confusing (F13). The facts behind this plan are in [vanilla-findings.md](vanilla-findings.md).

## Scope

In:
- A units-for-debt option at the overseer's Administration Terminal.
- Retuned C-class contributions so production buildings break even.
- Rewritten English text for the debt, upkeep and reserves strings, and a short explanation of how debt works.

Out:
- The debt and upkeep formulas. They are in the exe; data only changes inputs.
- Offline debt growth (`DailyDebtPaymentModifier`, `InitialDebtCycles`) until a session shows what the fields do.
- Upgrade material costs. The "63 Dirt" stage is 64 Dirt, a Gek trade commodity sold at trade terminals (vanilla-findings, "Upgrade materials"), so explaining it beats changing it.
- New build parts.
- Production menu changes. That is idea I-8.

## Design rules

- Patch the fewest fields, and append rather than replace lists.
- Add no `OT_` parts. Then removing the module never deletes a player's build, and the permanent-ID rule never applies.
- Every number the player pays or receives is shown before they choose.
- No module depends on another Toolkit module.
- Text goes through `LocTable.MXML` keys, English and USEnglish first.

## Decisions

Decided 2026-10-17:

1. **Two modules.** `OverseersToolkit-FairLedger` carries the debt option and the wording; `OverseersToolkit-FairLedger-Rebalance` carries the contribution edits.
2. **Pay at the Administration Terminal** through an option appended to `SETTLEMENT_ADMIN`.
3. **Exact steps at a premium of 2 units per 1 debt.** The Debt PositiveLarge range becomes a flat 100,000, so a cut always matches its price. Two options: a 100,000 cut for 200,000 units and a 1,000,000 cut for 2,000,000 units. Any price is possible: `GcCostMoney` takes a plain amount, and vanilla entries go up to 1,000,000,000 (verified). The range edit is a vanilla value the debt option depends on, so it lives in FairLedger, not the Rebalance module, and COMPATIBILITY.md lists it.
4. **Hide the option at zero debt** with `DisablingConditions` first. Only if the session shows that cannot work, keep the option visible and warn in its text.
5. **Break-even covers production buildings only,** by lowering their C upkeep to their C productivity. Residences, the bar and the fish pond keep their cost.
6. **Override the four text keys** in English and USEnglish, if the session shows other languages keep their vanilla text. Otherwise fall back to new text only.
7. **No guide sign in Fair Ledger.** A read-only town sign is a possible add-on module; see "Later: a town sign" below.

### What Session 6 changed

Results are in [../../progress.md](../../progress.md) and [vanilla-findings.md](vanilla-findings.md).

- **Decisions 2 and 3 hold.** The terminal option charged exactly 200,000 units and cut exactly 100,000 debt in its own town. The terminal shows six options at most and vanilla uses four, so the two shipped options fill it. Another mod that appends a terminal option would push one of them off.
- **Decision 4 falls back to B.** The `DisablingConditions` guard did nothing at zero debt, and a payment there is lost: 200,000 units for no change, despite a "Settlement reserves increased" message. The option text has to warn about it.
- **Decision 5 is supported.** Contributions are computed at runtime, so the upkeep change reached existing buildings at once, and it turned the test town's debt from rising to falling.
- **Decision 6 needs a new call.** A text entry with only English and USEnglish shows the raw key in every other language, and so does any new Toolkit key. Falling back to "new text only" has the same problem.

### Decided after Session 6

Decided 2026-10-17:

8. **Fill all 17 languages in every text entry.** Overrides keep each language's vanilla translation outside English; new keys repeat the English text. The repo-wide change is issue #22.
9. **Accept the Purchases scaling.** The price follows the player's Purchases setting; a line for the mod page goes to the maintainer.

The options and evidence for 8 and 9:


8. **Text in other languages.**
   - **A. Fill all 17 languages in every entry.** Overrides keep the vanilla translation outside English, copied from the game's language files. New keys repeat the English text, so other languages see English instead of a raw key.
   - **B. English only, as today.** Other languages see raw keys.

   Evidence: verified in Session 6 in French. Installed text mods fill all 17 languages (Normalize Economy Names, _PM_InformationStorm). A needs the other languages' files extracted and a generator change, and it touches every module's `LocTable.MXML`, so it is a repo-wide change, filed as issue #22. Recommendation: **A.**
9. **Purchases difficulty.** The payment's price follows the Purchases setting: free on Free, a third (0.66 units per debt) on Discounted, 2 units per debt on Standard, and 3.32 on Expensive (Units multiplier 1.66). No cost field opts out (inferred from the cost types).
   - **A. Accept it** and say so on the mod page: the player chose cheaper purchases.
   - **B. Charge with something other than units.** The only unscaled currency in the multipliers is Specials (quicksilver), which is not what players asked for.

   Recommendation: **A.**

The options, evidence and recommendations behind each decision follow.

### 1. One module or two

- **A. One module, `OverseersToolkit-FairLedger`,** with the debt option, the rebalance and the wording.
- **B. Two modules:** `OverseersToolkit-FairLedger` (debt option and wording, adds only) and `OverseersToolkit-FairLedger-Rebalance` (edits vanilla contribution numbers).

Evidence:
- The rebalance edits vanilla values in `SettlementBuildingContributions`, which the plan's design rules avoid unless a module exists for it ([../../plan.md](../../plan.md) section 2). Overhaul mods such as BetterSettlements (Nexus 2855) change the same economy, and a player using one would want the debt option without the rebalance.
- The debt option adds new cost and reward entries and appends one option to the vanilla `SETTLEMENT_ADMIN` dialog entry, which COMPATIBILITY.md would list. The wording overrides vanilla text keys. Neither conflicts with an installed mod (verified: no installed mod patches the dialog or cost tables).

Recommendation: **B.** Players choose the rebalance on its own, and COMPATIBILITY.md can flag it alone.

### 2. How the overseer pays debt

- **A. Terminal option.** Append an option to the Administration Terminal (`SETTLEMENT_ADMIN`), for example "Pay 500,000 units toward the debt". Its cost is a new `GcCostMoney` entry, and its reward a new reward-table entry of Debt stat changes.
- **B. Bond item.** A product bought for units that cuts debt when used (I-5 as first written).
- **C. A decision.** A request whose options cut debt.

Evidence:
- A needs two new entries (a cost and a reward). The terminal sits in the town's own office, its vanilla options already act on that town, and options can stay open for repeat payments (`KeepOpen`). Verified in data; whether a stat reward reaches the terminal's town is unknown until a session.
- B needs a product, a consumable, a reward and a shop entry. The only data shop found, the specials shop, sells for quicksilver (inferred), and the installed Consumerism mod replaces that whole table (verified). Which town a used bond pays is also unknown.
- C is impossible as asked: decision options have no cost field, so they cannot take units (verified).
- Appended reward-table entries load and run (verified in Session 3). All five installed reward-table mods are now partial patches (verified 2026-10-17), so an appended entry survives them.

Recommendation: **A.**

### 3. Price and step size

A reward cannot name an amount, only a strength (verified). The largest Debt step is PositiveLarge, a random 50,000 to 100,000. A starting town owes 600,000 to 1,200,000, and the cap is 10,000,000.

- **A. Stack vanilla steps.** For example, one option gives ten PositiveLarge steps: a cut of 500,000 to 1,000,000, about 750,000 on average. The price is fixed, so the player sometimes pays more than the cut.
- **B. Make the step exact.** Patch the Debt PositiveLarge range to a flat 100,000 and stack ten for a 1,000,000 cut. This edits a vanilla value and turns the positive expedition debrief's 50,000 to 100,000 cut into a flat 100,000, its only other user (verified).

The exchange rate is a balance call:
- 1 unit per 1 debt makes debt trivial for late-game players, who hold far more than the 10,000,000 cap.
- A premium, for example 2 units per 1 debt, keeps buildings and decisions the main way out while still offering an exit.

Recommendation: **B** at **1:1**, with two options, 100,000 and 1,000,000. The cut then always matches the price, which is the point of the module, and the debrief change is a small buff. If the maintainer prefers no vanilla edits in the main module, **A** priced at the cut's maximum, so the player never pays for debt that is not cleared.

### 4. Paying when there is no debt

The debt stat bottoms out at 0, so a payment on a town with less debt than the cut most likely wastes units (inferred).

- **A. Hide the option** with a `DisablingConditions` entry, `GcMissionConditionSettlementStatLevel` on Debt. The fields exist, but no vanilla dialog option uses them (verified), so it needs a session.
- **B. Accept it** and say so in the option text.

Recommendation: **A** if the session shows it works, otherwise **B**. The small 100,000 option limits the loss either way.

### 5. What "break even" means

Every building's C level costs more upkeep than it produces at the midpoint; production buildings turn positive by B or A class, and residences, the bar and the fish pond never do (verified, table in vanilla-findings).

- **A. Production buildings only.** Lower the C upkeep of the factory, farm, market, storage facility, tower, starport, small industrial, administrative building and RoboArm to their C productivity, so their midpoint net is 0. Residences, the bar and the fish pond keep their cost; they pay in population and happiness.
- **B. Every building.** Also cut residence, bar and fish pond upkeep to 0 at C.
- **C. Raise productivity** instead of lowering upkeep. **Inferred:** productivity may also drive production output, so this would change more than debt.

Recommendation: **A,** by lowering upkeep only. It answers the complaint without making towns free, and it touches one stat. It needs a session to confirm that existing buildings pick up the change, which the save layout suggests (inferred).

### 6. Plain wording

Installed mods override vanilla text keys through `LocTable.MXML` (verified). The Toolkit writes only English and USEnglish, and what other languages show for a partial override entry is unknown.

- **A. Override in English and USEnglish only,** if the session shows other languages keep their vanilla text.
- **B. Add new text only.** Explain debt in the new terminal option and leave vanilla strings alone.

Draft overrides (English):

| Key | Now | Proposed |
|---|---|---|
| `UI_SETTLEMENT_STAT_UPKEEP` | Maintenance Cost | Upkeep (per day) |
| `UI_SETTLEMENT_PROD_DEBT` | Settlement is in debt / Clear debts to restore production | In debt: production is paused until the debt is paid |
| `UI_SETTLEMENT_PROD_DEBT_TIP` | Reduce debt by constructing buildings and investing in settlement features to increase production and reduce maintenance costs | Each day, productivity pays upkeep and the rest pays down debt. Upgrade buildings, choose features that cut upkeep, or pay at the Administration Terminal. |
| `UI_SETTLEMENT_STAT_COST_NAME` | upkeep costs | upkeep |

Recommendation: **A** for these four keys, the same key list in both languages, with **B** as the fallback. "Reserves" stays unchanged until a session shows what it counts (unknown).

### 7. A guide sign

I-7 also suggested a "Settlement Ledger" sign whose description explains debt.

Evidence: a new part gets a permanent `OT_` ID, and the game deletes placed parts when their module is missing (verified 2026-10-12).

Recommendation: **no sign.** The explanation goes in the terminal option's text and the overridden tip, so the module adds no parts.

## Later: a town sign

An idea for an add-on module, separate from Fair Ledger: a 3D town sign placed anywhere in the settlement that shows the town's stats and status. It is read-only; management stays at the terminal. It adds a new `OT_` part, so its module needs the removal warning every part module carries.

What the data says so far:
- **Verified:** no vanilla base part references a settlement interaction, and only the office terminal (`SettlementAdminTerminal`) and building sites (`SettlementBuildingSite`) use settlement dialog types.
- **Inferred:** live stat text drawn on a part is not possible in data. No field binds settlement stats to a placed object, so that version needs runtime code.
- **Unknown:** whether a placed part can open the vanilla status page on interaction, for example through a dialog entry that offers only "View %SETTLEMENT% status" (`R_OPEN_SETOVIEW`). That would be the data-only version of the sign, and it needs its own probe.

## To verify in one session

What the data cannot answer, batched into one session on the creative test slot. A test-only `OverseersToolkit-LedgerProbes` module carries the probes, all text marked [TEST]. Besides the two payment options it adds a free option that grants 5,000,000 units, because the test save holds far less than its debt, and it sets the C upkeep of every production building to 1,111 so the change is easy to spot:

1. A terminal option charging 200,000 units for a flat 100,000 Debt cut. Does the option show, does the cut match, does it charge, does the debt drop, and in which town if the slot owns two?
2. The same option at zero debt: are the units taken, and does a `DisablingConditions` entry hide it?
3. A contribution patch lowering one building type's C upkeep. Does the building page and overview pick it up for a building that already exists?
4. A text override of `UI_SETTLEMENT_PROD_DEBT_TIP` in English and USEnglish. Does it show, and what does another game language show?
5. Where the reserves figure appears, and when it changes.

Estimate: about 30 minutes with load and save waits, since each probe is read at the terminal or in the overview. The session checklist table comes with the probe module.

## Rough steps

1. Decisions: recorded above on 2026-10-17.
2. Tooling, tests first: a generator (or a `gen_settlement.py` extension) writing the cost entry, the reward entry, the dialog option append, contribution edits and text overrides from `specs/OverseersToolkit-FairLedger*.json`.
3. Probe module and session as above; results in [../../progress.md](../../progress.md) the same day.
4. Write the shipped spec and balance the numbers against the session.
5. Package, add to COMPATIBILITY.md and CHANGES.md, and teach `testmode` the new module keys. README and Nexus text go to the maintainer.

## Risks

- **Wrong town:** if a terminal reward pays a different town than the terminal's, route A fails, and the fallback is a mission bound to the local town (`GcMissionConditionNearSettlement`), which needs more probing.
- **Shared tables:** the dialog table is large and other mods may patch it elsewhere. An appended option merges cleanly by the patch rules seen so far, and an option on an entry a game update removes is dropped (inferred from Session 5's missing-ID probe).
- **Strength edit:** decision 3B changes a vanilla range every Debt PositiveLarge user shares, including any other mod's.
- **Balance:** with no cap, rich players can still clear any debt at once, even at 2 units per 1 debt. That is the request, but it removes debt as pressure for them.
- **Removal:** the module adds no parts or stored IDs, so removing it leaves only the debt already paid (inferred). The rebalance's numbers would revert on the next upkeep check.
