# Changes

## Unreleased

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
