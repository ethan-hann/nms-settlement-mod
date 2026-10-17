# Remote Terminal: rough plan

Rough outline, written 2026-10-17. Not a spec yet. It started as a read-only town sign; Session 7 showed that no vanilla page is read-only, and the maintainer chose the remote terminal instead (decision 1 below). Target: 1.2.0, beside Fair Ledger, if Session 8 shows it works away from the town.

## Goal

An optional add-on module, `OverseersToolkit-RemoteTerminal`, with one new part: a copy of the settlement's Administration Terminal that the player can build anywhere on a planet, inside or outside a base. Players can then manage a settlement from a remote base. The idea came up while planning Fair Ledger ([../fair-ledger/plan.md](../fair-ledger/plan.md), decision 7).

Because it adds an `OT_` part, the module carries the removal warning: loading and saving without it deletes every placed terminal (verified 2026-10-12 for other parts).

## Decisions

Decided 2026-10-17:

1. **Ship route B as a remote terminal,** not a sign. A live-updating sign needs runtime code, and NMS.py is too heavy for one part. The terminal is buildable anywhere on a planet (`BuildableOnPlanet` and `BuildableOnPlanetBase`).

Fact from the maintainer: each planet holds at most one settlement. **Inferred:** a terminal anywhere on a settlement's planet resolves to that settlement, as the office terminal does.

## Session 8 result

Verified 2026-10-17: a copy placed on Funana Bridge's planet, well outside the town (the HUD showed the town 6 minutes away), shows every option disabled:
- "No pending decisions", although the town had a construction choice pending;
- "Terminal reserved for Overseer" on both the status and the all-settlements options (`UI_SETTLEMENT_NO_SETTLEMENT`).

So the terminal only works inside its town, and `C_SETTL_OWN` checks the town the terminal stands in, not "owns a settlement anywhere" as inferred before the session. The base and other-planet steps were skipped, since they cannot do better than the town's own planet.

**Verified in data:** the status and all-settlements options open their pages through `GcRewardOpenPage` rewards: `R_OPEN_SETHUB` opens `SettlementManagement` and `R_OPEN_SETOVIEW` opens `SettlementsOverview`. Neither reward names a place; the location check is the option's cost. **Unknown:** whether either page opens, and for which town, when an option with no cost runs the reward far from any settlement.

## What is left for the remote terminal

- **A. Drop it for 1.2.0.** Fair Ledger ships on its own.
- **B. One more probe:** an option with no cost on the terminal that opens `SettlementsOverview` (all settlements) or `SettlementManagement`, tried far from the town. Even if it works, the terminal dialog has six slots and Fair Ledger's two payment options fill it, so shipping both means Fair Ledger keeps one payment option or the remote option replaces one.

Decided 2026-10-17: the remote terminal is dropped. The maintainer judged it a dead end after Session 8, before B was built. Fair Ledger ships in 1.2.0 on its own.

Recommendation before the decision: **A,** and keep B on file. The terminal's main appeal was managing a town remotely: decisions, construction and payments. Those all ran through the local checks that failed. B could at most give a remote overview, at the price of a Fair Ledger option.

## Questions Session 8 set out to answer


- **Away from the town:** on the settlement's planet but outside the town, at a base on another planet, and in another system, what does the terminal show? Possibilities: the right town, the nearest one, nothing, or the "Terminal reserved for Overseer" message (`UI_SETTLEMENT_NO_SETTLEMENT`). The status and "Manage all settlements" options only check that the player owns a settlement somewhere (cost `C_SETTL_OWN`, verified), so they may work anywhere. "View pending decision" checks for a pending decision (`C_SETTL_JUDGE`); which town it reads is unknown.
- **Fair Ledger payments from afar:** the payment options sit on the same dialog, so they appear on every copy (inferred). Which town does a remote payment pay?
- **Inside a base:** does it build and work inside a base's boundary?

## Design questions for the maintainer, after Session 8

2. **Name and menu tab.** Draft name "Remote Overseer Terminal". The probe sat in a [TEST] tab under Decoration; Technology or the Toolkit's SETTLEMENT tab are the alternatives.
3. **Build cost.** The vanilla office terminal has no build-cost entry, so a copy costs nothing (verified). A cost could come from a vanilla terminal part's cost entry.
4. **Unlock in normal games.** Creative games learn it from `creative_known`. Normal games need an unlock: for example a mission that teaches it once the player owns a settlement (`GcMissionConditionHasSettlement`, the condition vanilla uses in six sentinel settlement missions), following the class unlocks' pattern.
5. **Thumbnail.** The vanilla product uses a stone-wall placeholder icon, so the part needs another vanilla icon.
6. **Scaling.** The vanilla entry allows scaling (`CanScale` true); keep or turn off.

## What the game files show

Each finding is marked verified, inferred or unknown, as in [../fair-ledger/vanilla-findings.md](../fair-ledger/vanilla-findings.md). Sources: the extracted base-part tables in `scratch/extracted/`, the settlement models and entities pulled read-only into `scratch/extracted-sign/` on 2026-10-17, the settlement UI pages in `scratch/extracted-ledger/ui/`, and libMBIN 7.4.1.3 through reflection.

### The settlement's own terminals are base parts

- **Verified:** vanilla lists the settlement's terminals in the base-part tables:

  | Object | Model | Interaction | Where it stands |
  |---|---|---|---|
  | `SET_MAYORTERM` | `SETTLEMENT/MAYOR_TERMINAL.SCENE.MBIN` | `SettlementAdminTerminal` (dialog `SETTLEMENT_ADMIN`) | The overseer's office |
  | `SET_INT_SUMMARY` | `SETTLEMENT/SUMMARY_TERMINAL.SCENE.MBIN`, through part `_SET_INT_SUMMARY` | `SettlementBuildingDetail` | Beside each building ("View building details") |
  | `SET_MONUMENT` and its timber, fibreglass and fabric variants | `SETTLEMENT/MONUMENT/MONUMENT0...` | `SettlementHub` | The town's centre monument |

- **Verified:** all three have products, `IsPlaceable` and `ShowInBuildMenu` true, sit in Furniture > Interior, and are not `BuildableOnPlanet`. None of them is in the creative preset's `KnownProducts` list.
- **Verified:** `SET_INT_SUMMARY` is a station-style part (no placement scene; the model comes from the parts table). `gen_parts.py` already copies parts like that.
- **Verified:** `SettlementBuildingDetail`, `SettlementHub` and `Settlement_TowerTerminal` have no dialog entry in `nms_dialog_gcalienpuzzletable`. **Inferred:** they open their UI pages directly.
- **Verified:** the settlement UI pages are `settlementpage` (overview, production, debt and an abandon action), `settlementbuildingpage` (one building's details), `settlementsummarypage` (history, with abandon), `settlement_npc_page` and `settlernpcpage`.
- **Verified in Session 7:** a copy of `SET_MAYORTERM` placed in open ground inside the town works as the full Administration Terminal: the same four options, and "View Funana Bridge status" opens the town's status page.
- **Verified in Session 7:** a copy of `SET_INT_SUMMARY` cannot be placed anywhere above water ("Must Be Constructed Underwater"). The vanilla entry has both `BuildableUnderwater` and `BuildableAboveWater` false, which the probe copied. What it opens away from a building is still unknown.
- **Verified in Session 7:** interacting with the monument (`SettlementHub`) opens the town's status page at once, with no options in between.
- **Verified in Session 7:** the status page is not read-only. It has "Change Output" buttons for production, and its Settlement History page has "Retire as Overseer".
- **Verified in Session 7:** both probe parts showed in the build menu with a wooden-wall thumbnail. The vanilla products behind them use `BUILDABLE.WALL_STONE.DDS` as a placeholder icon, so a shipped sign needs another vanilla icon.
- **Verified in Session 7:** an existing creative save learned both parts from the module's `creative_known` entries (`KnownProducts` in the save).

### Live text on a part

- **Inferred:** no data field binds settlement stats to text drawn on a placed object. The interaction component (`GcInteractionComponentData`) chooses an interaction type and costs, not displayed values, and the text parts in vanilla (message module, station billboard) show player-written or fixed text. A sign that displays live numbers in the world needs runtime code (tier T3) and is not a candidate for 1.2.0.

## Routes considered for the sign

- **A. A copy of the building-detail terminal.** A small holographic terminal, a vanilla scene, so visitors without the mod still see it. It is only useful if its page shows something about the town when it stands away from a building.
- **B. A copy of the Administration Terminal.** Known to open the full terminal: decisions, status, all settlements, and Fair Ledger's payments. It is a remote office terminal rather than a read-only sign, and its status page carries the abandon action too.
- **C. A vanilla model with a new entity.** For example the summary terminal's model with its interaction set to `SettlementHub`. This ships a modified scene and entity in the mod, so visitors without the mod would not see it, which breaks the "vanilla scenes only" design rule. Worth it only if the hub page is the right read-only view and A shows nothing.
- **D. Live numbers on the sign.** Runtime code; out of scope for 1.2.0.

No route is truly read-only if it opens the vanilla status page: it offers Change Output, and its history page offers Retire as Overseer (verified in Session 7). A read-only sign is out of reach with data alone. The closest thing is one interaction straight to the status page, which is what the monument does.

## Probe

`OverseersToolkit-SignProbes` (test-only) adds two parts to a [TEST] SIGN PROBES tab under Decoration, both buildable in the settlement and known to creative games:
- `OT_SP_SUMMARY`, a copy of `SET_INT_SUMMARY` (route A)
- `OT_SP_MAYOR`, a copy of `SET_MAYORTERM` (route B)

The session also checks route C's target page on the real monument: what the Settlement Interface shows the town's own overseer.

Probe parts are deleted when a later session runs without SignProbes, which is fine on the test slot. `testmode enter` refuses a session that leaves out a module whose parts the slot holds, so the parts are removed in game at the end of the session.

## Session 7 results by route

| Route | Result | What it would take |
|---|---|---|
| A. Building-detail terminal | Not placeable above water; page unknown | A second probe with `BuildableAboveWater` set, to see what it opens away from a building |
| B. Administration Terminal copy | Works: the full terminal anywhere in town, vanilla scene | Ready as data; it is a remote office terminal, not a sign |
| C. Small model with the monument's interaction | The monument opens the status page in one step | A new scene and entity shipped in the mod (visitors without it see nothing, inferred), and a probe |
| D. Live numbers | Runtime code | Not for 1.2.0 |

The route decision is recorded under Decisions above.
