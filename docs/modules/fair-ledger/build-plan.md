# Fair Ledger: build plan

Written 2026-10-17, after Session 6 and the decisions in [plan.md](plan.md). Covers how the two shipped modules are built, tested and released. The facts behind it are in [vanilla-findings.md](vanilla-findings.md).

## Order

1. Issue #22 first: language support in the generators and translations for core, Defense and Settler Stories. Done 2026-10-17 (#25).
2. Then Fair Ledger, built on that support so it ships translated.
3. One short check session, then release both as 1.2.0.

## Decisions

Decided 2026-10-17:

1. **Two payment options:** "Pay 100,000 debt" for 200,000 units and "Pay 1,000,000 debt" for 2,000,000 units, at Standard Purchases. They take the terminal's last two slots.
2. **Issue #22 comes first,** and one release carries both.
3. **One check session** on the test slot before release.
4. **C upkeep matches C productivity** for the nine production buildings. Each one's Base upkeep range becomes its Base productivity range. Cost and output still roll separately, so a single building's net at C lands anywhere from minus to plus the range width, averaging 0. Upgrades stay the dependable profit, and housing, the bar, the fish pond, starting perks and decisions still add debt.

## The two modules

### OverseersToolkit-FairLedger

| File | What it holds |
|---|---|
| `METADATA/REALITY/TABLES/COSTTABLE.EXML` | `C_OT_FL_PAY1` (200,000 units) and `C_OT_FL_PAY10` (2,000,000 units) in `InteractionTable`, copied from vanilla `C_FLT_TRADE_9` |
| `METADATA/REALITY/TABLES/REWARDTABLE.EXML` | `R_OT_FL_DEBT1` (one Debt PositiveLarge step) and `R_OT_FL_DEBT10` (ten) in `SettlementTable`, shaped like vanilla `R_SENT_NO_ALERT` but not silent |
| `METADATA/REALITY/TABLES/NMS_DIALOG_GCALIENPUZZLETABLE.EXML` | The two options appended to `SETTLEMENT_ADMIN`, copied from its first option, with `KeepOpen` true and no `DisablingConditions` (they did nothing in Session 6) |
| `GLOBALS/GCSETTLEMENTGLOBALS.EXML` | Debt PositiveLarge set to a flat -100,000 |
| `LocTable.MXML` | The two option labels and the overridden vanilla text, in all 17 languages |

### OverseersToolkit-FairLedger-Rebalance

One file, `GLOBALS/GCSETTLEMENTGLOBALS.EXML`, editing the Upkeep item of each building's `Base` list by `_index` (verified 2026-10-17 in the extracted globals):

| Building | C productivity | C upkeep now | C upkeep after | `_index` |
|---|---|---|---|---|
| `Settlement_LandingZone` | 10,000-15,000 | 20,000-22,500 | 10,000-15,000 | 2 |
| `Settlement_Tower` | 20,000-30,000 | 30,000-40,000 | 20,000-30,000 | 2 |
| `Settlement_Market` | 20,000-25,000 | 35,000-50,000 | 20,000-25,000 | 2 |
| `Settlement_SmallIndustrial` | 10,000-15,000 | 10,000-20,000 | 10,000-15,000 | 2 |
| `Settlement_SheriffsOffice` | 5,000-8,000 | 22,000-32,000 | 5,000-8,000 | 2 |
| `Settlement_Double` | 15,000-25,000 | 30,000-35,000 | 15,000-25,000 | 3 |
| `Settlement_Farm` | 15,000-25,000 | 30,000-40,000 | 15,000-25,000 | 3 |
| `Settlement_Factory` | 20,000-30,000 | 40,000-50,000 | 20,000-30,000 | 3 |
| `Settlement_Builders_RoboArm` | 10,000-20,000 | 20,000-30,000 | 10,000-20,000 | 2 |

The generator reads both ranges from vanilla rather than from this table, so a game update that changes productivity carries through. It finds the Upkeep item by its stat type, not by a fixed index, and fails the build if a building lacks one.

## Text

New keys use the `OT_FL_` prefix, 31 characters or fewer.

| Key | English draft |
|---|---|
| `OT_FL_PAY_S` | Pay 100,000 debt |
| `OT_FL_PAY_L` | Pay 1,000,000 debt |

The game appends the price, for example "(200,000 Units)". Labels stay short because a long label scrolled in Session 6 and translations run longer.

Overridden vanilla keys (English drafts; the warning about lost payments lives in the two tips, since labels have no room for it):

| Key | Now | Draft |
|---|---|---|
| `UI_SETTLEMENT_STAT_UPKEEP` | Maintenance Cost | Upkeep |
| `UI_SETTLEMENT_STAT_COST_NAME` | upkeep costs | upkeep |
| `UI_SETTLEMENT_PROD_DEBT_TIP` | Reduce debt by constructing buildings ... | Each day, productivity pays upkeep and the rest pays down debt. Upgrade buildings, choose features that cut upkeep, or pay at the Administration Terminal. Paying more than the debt is lost. |
| `UI_SETTLEMENT_PROD_DEBT_TIP2` | Settlement productivity has increased ... | Productivity now covers upkeep, so the debt is falling on its own. You can also pay it at the Administration Terminal; paying more than the debt is lost. |

Translations follow issue #22: the game's own terms from its language files, new wording in each language for the overrides, and English as the fallback for any key not yet translated.

## Tooling

A new generator, `tools/gen_ledger.py`, builds both modules from `specs/OverseersToolkit-FairLedger.json` and `specs/OverseersToolkit-FairLedger-Rebalance.json`, and joins `GENERATORS` in `tests/test_modules.py`, so a hand edit or a stale file fails the suite as with the other modules.

Spec keys (new):
- `terminal_options`: a list of `{"id", "text", "debt_steps"}`. The generator writes the cost `C_OT_FL_<id>` (`2 * 100,000 * debt_steps` units), the reward `R_OT_FL_DEBT<debt_steps>` and the dialog option from it. `text` is the option's loc key, and it needs an entry in `text`.
- `debt_step`: the flat Debt PositiveLarge amount, 100000.
- `text_overrides`: the vanilla keys the spec's `text` overrides. The text itself stays in `text`, because gen_parts.py writes LocTable.MXML. Every other text key must start with `OT_FL_`, and an override must name a key vanilla has.
- `match_upkeep_to_production`: the list of buildings for the Rebalance module.

The cost-to-step ratio lives in one constant, so the 2 units per debt rule cannot drift between options.

## Behaviours to test

Each one gets a failing test first, seen to fail on an assertion.

- Each terminal option's cost is exactly 2 units per debt for its steps, and its reward holds only Debt PositiveLarge steps.
- The Debt PositiveLarge range is flat at the spec's step.
- `SETTLEMENT_ADMIN` has six options or fewer after the merge.
- Option IDs, cost IDs and reward IDs are 15 characters or fewer and start with `OT_FL_`, `C_OT_FL_` or `R_OT_FL_`.
- The Rebalance module edits only Upkeep items, only in `Base`, only for the listed buildings, and each new range equals that building's vanilla productivity range.
- The generator fails when a listed building has no Upkeep item, or when a terminal option has no text.
- Every text key has all 17 languages filled (from issue #22).
- Both modules merge and compile against vanilla (the existing check).

## Packaging and compatibility

- `package.py` ships both modules; LedgerProbes and LedgerSetup stay test-only.
- `testmode.py` gets the keys `fairledger` and `fairledgerrebalance`.
- `compat_report.py` regenerates COMPATIBILITY.md. It lists the appended `SETTLEMENT_ADMIN` options, the Debt PositiveLarge edit and the nine Upkeep edits.
- Known conflicts:
  - Another mod appending terminal options would push one of ours past the six-slot limit.
  - Economy overhauls that change `SettlementBuildingContributions` (BetterSettlements, Nexus 2855) clash with the Rebalance module.
  - Another mod changing Debt PositiveLarge changes the payment.
- Removal: FairLedger stores nothing, so removing it leaves the debt already paid (inferred, checked in the session). Removing Rebalance restores vanilla upkeep at once (verified in Session 7 with the probe's upkeep marker).

## Check session

About 25 minutes on the test slot. Purchases is set to Standard for the run and set back afterwards. Modules: core, Defense, SettlerStories, FairLedger, FairLedger-Rebalance, SignProbes (the slot still lists its parts) and the test-only LedgerSetup.

The test town had no debt and the test character 732,096 units after Session 8 (verified in the save copy), too few for the 2,000,000 payment. LedgerSetup turns the terminal's "Manage all settlements" option into a free "[TEST] Add debt and 5,000,000 units" option (25 Debt NegativeLarge steps, at least 1,250,000 debt), so the terminal keeps six options.

| Check | Expect |
|---|---|
| Terminal options | Both show with their prices, after Leave |
| Pay 100,000 debt | Takes 200,000 units, cuts 100,000 debt |
| Pay 1,000,000 debt | Takes 2,000,000 units, cuts 1,000,000 debt |
| Production building pages | Upkeep within the building's productivity range |
| Debt tips in English and one other language | The new text, translated, no raw keys |
| A second launch without FairLedger | Loads normally; debt keeps the paid amount; terminal back to four options |

Results go in [../../progress.md](../../progress.md) the same day.

## Release notes for the maintainer

Facts for CHANGES.md, the README and the Nexus page:
- The payment's price follows the Purchases setting: free on Free, a third on Discounted, 2 units per debt on Standard, 3.32 on Expensive.
- Paying more than the remaining debt is lost.
- The terminal holds six options; Fair Ledger uses the last two.
- Translations are not checked by native speakers; corrections are welcome.
