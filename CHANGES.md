# Changes

## Unreleased

**OverseersToolkit-FairLedger (new, optional)**
- The Administration Terminal in the overseer's office gains two options: "Pay 100,000 debt" for 200,000 units and "Pay 1,000,000 debt" for 2,000,000 units. Each payment clears exactly the debt it names, in that town.
- The 1,000,000 payment shows a single "Settlement debt reduced: 100,000 units" message, but the debt drops by the full 1,000,000.
- The price follows the Purchases setting: free on Free, a third on Discounted, 2 units per debt on Standard, 3.32 on Expensive.
- Paying more than the remaining debt is lost. The game shows "Settlement reserves increased", but reserves are not stored anywhere.
- The terminal shows six options at most and the game uses four, so Fair Ledger takes the last two. Another mod that adds a terminal option pushes one of them off.
- Clearer text for upkeep and debt: "Maintenance Cost" becomes "Upkeep", the name the building pages already use, and the two debt tips explain how debt falls, where to pay it, and that overpaying is lost.
- Side effect: the positive expedition debrief's debt cut becomes a flat 100,000 instead of 50,000 to 100,000, since both use the same step.
- Adds no parts, so removing it deletes nothing from a save. Debt already paid stays paid.
- Its text is in every game language. Like the other translations, it has not been checked by native speakers.

**OverseersToolkit-FairLedger-Rebalance (new, optional)**
- At class C, the starport, infrastructure, trade center, small industrial, administrative building, storage facility, farm, factory and Autophage RoboArm cost exactly as much upkeep as they produce, instead of more, so each one breaks even. Upgrades stay the way to profit.
- Residences, the bar and the fish pond keep their upkeep.
- Takes effect on existing buildings at once, and removing it restores the game's upkeep at once.
- Conflicts with economy overhauls that change building contributions, such as BetterSettlements.

**Every game language**
- Part names, descriptions, perks and decisions in the core, Defense and Settler Stories modules are now translated into every language the game offers. Before, players in any language but English saw raw text keys such as OT_PATH_TILE_NAME.
- The translations reuse the game's own words for settlements, settlers, the overseer, debt, Sentinels, units and nanites. They have not been checked by native speakers: corrections are welcome as a bug report on GitHub.

**Packaging**
- Every module file now uses LF line endings. Files from earlier releases mixed CRLF and LF; the game loads both, and the change is line endings only.

## 1.1.0

A new optional module, Settler Stories, and warnings about removing modules.

**Read before removing any module**
- When the game saves without a module installed, it deletes every part that module added, and the save cannot get them back. Back up saves before removing a module. Settlement Decor's parts are the game's own and stay.
- Parts missing after an uninstall or a game update are still in the save until the game saves again (autosaves included): quit without saving and reinstall the module.
- Remove Settler Stories only when no story step is waiting at any settlement. Otherwise that settlement's terminal shows a decision that cannot be answered until Settler Stories is reinstalled and the step answered.

**OverseersToolkit-SettlerStories (new, optional)**
- Six new settlement decisions: a night market, salvage from a crashed freighter, a fevered traveller, a buried signal booster, a festival and a wage dispute.
- Three short stories of two and three steps: a stranger at the gate with pirates on their trail, a vault of ancient seeds, and an overdue survey team. Each step follows the previous choice at once. Story steps send no alert, so check the overseer's terminal.
- Every outcome is shown before choosing. Half the options reward the player (units, nanites, quicksilver, items, alien words, standing) and half the settlement (happiness, productivity, a fireworks party, and three new features: Sanctuary, Ancient Orchard and Relic Hall).
- The new decisions mix in with the game's own.

**Existing modules**
- Unchanged. Every 1.0.0 part and perk keeps its ID, so existing builds and settlements carry over.
- With Settler Stories installed, Defense's "Fortify the perimeter?" comes up less often, about once every 30 hours of judgements instead of 18, because four of the new decisions are requests too.

## 1.0.0

First release. Three modules; each works alone.

**OverseersToolkit (core)**
- New Decoration > SETTLEMENT build group, available from a settlement's own build menu with no base computer needed.
- Path kit: Path Tile, Path Triangle, Curb and Path Lamp. The lamp needs no power.
- 24 vanilla signs under their vanilla names: Illuminated Sign, Standing Sign, Station Billboard, the holographic displays, the Gek, Korvax and Vy'keen emblem decals and the number decals 0 to 9.
- Unlocks by settlement class: the path kit at class B, the signs at class A. New creative games know every part.

**OverseersToolkit-Defense (optional)**
- New settlement request "Fortify the perimeter?", about once every 18 hours of judgements. Accepting adds debt and grants the Perimeter Watch perk, which lowers the Sentinel alert level.
- Tower Pillar, a decorative tower, unlocked at settlement class S.

**OverseersToolkit-SettlementDecor (optional)**
- 489 vanilla decoration parts (exterior decor, lights, construction props, plants, statues, wall decals and posters) can be built in a settlement. The 13 lights that need power are left out. Side effect: these parts can also be placed outside a base.
