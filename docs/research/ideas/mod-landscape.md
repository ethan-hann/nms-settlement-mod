# Settlement mod landscape

The settlement mods on Nexus as of 2026-10-09, what their users ask for, and the gaps nobody fills. Figures come from the public Nexus API. Comment excerpts come from the first page of each mod's Posts tab, so older requests may be missing.

Mod URLs follow `https://www.nexusmods.com/nomanssky/mods/<id>`.

## Settlement mods

Cosmos (7.0) shipped on 2026-09-09. Partial EXML patches often survive game updates, so an older date does not always mean a mod is broken.

| ID | Mod | Updated | Endorse / DL | What it does | State |
|---|---|---|---|---|---|
| 4635 | Overseer's Toolkit | 2026-10-08 | 3 / 198 | Paths, curbs, lamp, signs, fortify judgement, 489 decor parts | This mod; the only content mod |
| 2067 | gSettlement Timers (Gumsk) | 2025-06-05 | 668 / 26,898 | Timer multipliers from instant to 10x; the author recommends slower | Works on Cosmos; most downloaded |
| 2409 | Fleet Expedition and Settlement Timer Reductions | 2025-06-13 | 348 / 21,348 | Instant or short timers | Beacon era |
| 2077 | Faster Fleet Expeditions and Settlement Timers | 2023-04-26 | 555 / 21,234 | 60 to 100% timer cuts | Abandoned; users rebuild it with AMUMSS |
| 3699 | Accelerated Settlements | 2026-06-24 | 325 / 17,931 | 5 s phases, 20x output, frequent decisions, 100 NPCs | Not Cosmos; comments report no effect, crashes, Collective Dwelling broken |
| 2855 | BetterSettlements | 2025-11-23 | 318 / 15,913 | Faster upgrades, +500% production, better starting perks | Crash reports |
| 2063 | Settlement Fasttrack | 2021-10-22 | 243 / 6,276 | 10 s builds, 1 to 2 min decisions | Abandoned |
| 2078 | Bomber's Natural Settlements | 2024-05-01 | 231 / 6,392 | Race-themed production (Gek agriculture, Korvax science, Vy'keen weapons), bigger towns | Abandoned; planned new buildings never shipped |
| 2676 | Settlement Timer Adjustment | 2025-06-26 | 215 / 8,359 | 1 to 5 min timers | Partly broken |
| 3673 | SETTLEMENTS Instant Builds and Quests | 2025-08-11 | 168 / 6,828 | Instant construction and quests | Works on 7.05 |
| 2643, 3662 | JE's Faster Settlement Population Growth I and II | 2024-10, 2026-09 | 164 / 5,629 and 64 / 3,159 | Larger population gains | II maintained |
| 3282 | More Comfortable Settlement | 2025-01-31 | 156 / 4,990 | Fast builds, attack interval 2600 s to 180000 s, more policy and visitor decisions | Broken on Beacon |
| 3371 | SMTL | 2025-06-05 | 95 / 2,255 | Timers divided by 30 | Beacon era |
| 3114 | Settlement Projects Rebalance | 2024-09-05 | 64 / 2,130 | Double cost, instant completion | Stale |
| 2187, 2191 | Aces Settlement and Population Tweaks | 2024-04-23 | 91 / 2,097 and 47 / 894 | Production cap past 1M, higher NPC cap, debt fix | Abandoned |
| 3907 | Fast Settlement Management | 2025-11-13 | 47 / 1,836 | 2 s upgrades, very frequent decisions | Too fast: breaks the first construction mission |
| 4114 | Fix Settlement Production | 2026-03-11 | 46 / 2,164 | Works around the inverted production bug | Probably unneeded after 7.04 |
| 3229 | Peaceful Settlements | 2026-09-12 | 66 / 2,995 | Attack interval 2600 s to 720000 s | Maintained |
| 3230 | More Settlements | 2026-09-11 | 77 / 4,686 | More settlements per planet type | Maintained; settlements lose buildings if removed |
| 3595 | No Settlement Class Markers | 2026-09-12 | 27 / 1,103 | Hides the class hologram | Maintained |
| 3559 | Settlement Bait Production | 2026-09-10 | 18 / 651 | Adds 6 baits to the production menu | Proves the production menu can be extended |
| 3625 | Settlement Fish Pond Adjusted | 2025-07-14 | 20 / 438 | Fish pond produces bait | 5.73 |
| 4310 | fnb Settlement Production Timer Fix | 2026-06-30 | 3 / 88 | Evens production timers across races | 6.45 |
| 2089 | SPDX It Takes A Village | 2022-03-14 | 42 / 784 | Race- and tier-based products, bigger towns, a settlement on every planet | Abandoned; its script no longer compiles |
| 2794 | Have a Foot in the Door | 2023-05-28 | 15 / 474 | Shrinks the base radius so a base fits inside a settlement | Broken |
| 4647 | No Settlements | 2026-10-08 | 0 / 6 | Removes settlements | 7.06 |

Adjacent mods that matter:

| ID | Mod | Endorse / DL | Relevance |
|---|---|---|---|
| 2225 | PTSd overhaul | 260 / 13,345 | Large settlement rebalance with race specialisation; only inside a full overhaul |
| 1369 | gBase Boundaries | 1,190 / 50,179 | The Toolkit's recommended companion. Users say it needs a Cosmos update, and one reports a crash teleporting to a settlement with a base inside it |
| 1214 | Ultra Base Building | 613 / 28,736 | Its author says custom part IDs are not synced in multiplayer, and the build menu has a hard item limit per tab |
| 1096 | Beyond Base Building | 3,957 / 203,354 | Placement fixes; says snap points are a hard limit |
| 367 | Eucli-ea | 1,021 / 48,892 | Custom models; the snap-point quota has not been raised since 6.18 |
| 4567 | Corvette Base Parts Unlocked | 5 / 910 | The corvette version of the Toolkit's decor module |
| 4609 | Snap Angles (NMS.py) | 9 / 471 | A runtime base-building mod shipped this week, which shows NMS.py works on the current build |

## What users ask for in mod comments

- Stop or limit the constant sentinel attacks (2855). A town stuck at a permanent 100% alert (2643).
- Choose or preview production before taking over (2187). "You as the overseer should be able to change what your settlement produces."
- Bigger product stacks per cycle (3699).
- Construction-only and decisions-only splits, and fleet-only files (2409, 3699, 2077).
- Shorter mini-expedition timers (2676).
- A free-cost option, and support for locked difficulty (3673).
- Build normal base parts or terraform inside the settlement (1369). Place a base computer inside (2794).
- Turn production off or slow it down (3282).
- Spawn control, for example settlements only on Paradise planets (2089). Link settlements to trading posts (3230; the author says the exe controls this).
- Balanced pacing: "one minute per build" rather than instant (3907).
- Publish the Lua and list modified files, because merging `GCSETTLEMENTGLOBALS` edits is the main source of conflicts (2078, 2077).
- More small decor (1214).

## Gaps nobody fills

1. **Content.** Nobody else adds judgements, perks, story chains, parts or missions. The data supports all of them.
2. **A production catalogue.** Race- and tier-based products were done twice (SPDX, Bomber's) and both are abandoned. PTSd does it only inside a full overhaul.
3. **Defence by design.** The only answers to attacks are stretching the interval. The Toolkit's Perimeter Watch is the only perk- or decision-based option.
4. **Building in the town.** gBase Boundaries shares one radius with player bases and needs a Cosmos update. Have a Foot in the Door is broken. The Toolkit already covers paths, lamps and signs; fences, gates, stalls, flags and plazas are the obvious next parts.
5. **Balanced pacing.** Mods are either vanilla-slow or instant, and instant breaks the first construction mission.
6. **Visual variety.** No mod touches settlement colour palettes, material tables or the building-generation data.
7. **Merge-friendly patches.** Users ask authors to list changed files and keep patches small. The Toolkit already ships partial EXML and a generated COMPATIBILITY.md, which is worth mentioning on the Nexus page.
8. **Cosmos space-station ownership** is a new overseer-like system with no mods yet. It is adjacent, not researched here.

## Positioning note

The Toolkit's partial EXML patches and generated compatibility list answer the most common meta-complaint in settlement mod comments: conflicts over `GCSETTLEMENTGLOBALS`. Any new module that touches that file should patch only the fields it needs and list them, as Defense does today.
