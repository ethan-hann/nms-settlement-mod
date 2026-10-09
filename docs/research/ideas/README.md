# Settlement research: player feedback and module ideas

Research done on 2026-10-09 against No Man's Sky 7.06 (Cosmos). It answers three questions. What do players complain about or ask for in settlements? What can modding change today? Which new Overseer's Toolkit modules would answer those complaints?

## Files

| File | What it holds |
|---|---|
| [player-feedback.md](player-feedback.md) | Complaints and suggestions by theme, from Frontiers (2021) to today, with what Hello Games has fixed and what is still open |
| [mod-landscape.md](mod-landscape.md) | Every settlement mod on Nexus, what its users ask for, and the gaps nobody fills |
| [modding-capabilities.md](modding-capabilities.md) | What data patches, AMUMSS, NMS.py, custom models and save editors can and cannot change about settlements |
| [module-ideas.md](module-ideas.md) | 30 module ideas, each tied to the complaints it answers, with a feasibility tier and a disclaimer where the tooling may not support it yet |

## Main findings

1. The Toolkit is the only settlement mod on Nexus that adds content. About 30 others exist, and nearly all of them change timers or production numbers in `GCSETTLEMENTGLOBALS`. Content is the open lane.
2. The top unfixed complaints after Beacon (5.7, June 2025) are:
   - an economy players can't read, where debt can't be paid with the overseer's own units
   - multi-hour build timers with one upgrade at a time
   - no way to find the building being upgraded
   - no unique reason to own a settlement
   - farm planters that are decoration only
   - passive defenders and attacks that need the player present
   - still no free building inside the town
   - decisions that feel repetitive
3. The data supports far more than mods use. Judgements can chain, missions can fire custom judgements and change settlement stats, the per-race production menus can be extended, and perks, gifts, NPC behaviour and colour palettes are all in data.
4. NMS.py is current again. It merged support for game build 181442 on 2026-10-09, and runtime mods shipped on Nexus this week. The roadmap's "path tool waits for NMS.py" blocker needs re-checking. NMS.py still exposes no settlement functions, though.
5. One finding contradicts the README. The Ultra Base Building author says custom part IDs are not synced in multiplayer, so visitors may not see `OT_` parts even though they reuse vanilla models. This needs a two-player test before the README's multiplayer line is trusted.

## Recommended next modules

Ranked by player demand, how unique the module would be on Nexus, and how much of it the current generators already support. Details are in [module-ideas.md](module-ideas.md).

1. **Settler Stories** (I-1): a judgement pack with chained, race-flavoured dilemmas whose outcomes are shown before you choose.
2. **Fair Ledger** (I-5, I-6, I-7): pay debt with your own units, C-class buildings that break even, and wording that explains reserves.
3. **Settlement Trade Goods** (I-8): unique, useful products added to each race's production menu.
4. **Path Kit 2 and Plaza Foundation** (I-12, I-13): fences, gates, benches, market stalls, flags, and a large part that flattens a plaza.
5. **Defense 2** (I-16, I-17): militia and pest-control perks, a brood-hive chain, and an optional calmer-attacks file.
6. **Balanced Pacing** (I-3): moderate timer presets that keep the first construction mission working.
7. **Runtime re-check** (I-27, I-28): retry the path tool on the current NMS.py, then try a "find my building" marker.

## How the research was done, and its gaps

Five research passes ran in parallel:
- Reddit
- Steam, the wiki and patch notes
- Nexus and the modding tools
- the libMBIN settlement structs
- post-Beacon feedback

Source coverage:
- **Reddit:** could not be read. Search, fetch and the in-app browser all refuse reddit.com. Reddit evidence is limited to about ten thread titles seen in another engine's results. The Steam Community board carries the same complaints and was read in full, so the themes hold, but frequency rankings lean towards Steam.
- **Fandom wiki:** returned HTTP 402. Wiki facts come from search snippets and are marked that way in the source notes.
- **Nexus:** pages returned 403 to the fetch tool. Mod data came from the public Nexus API and the first page of each mod's comments.
- **Press:** almost no critical coverage exists. Outlets ran launch news only.

The biggest hole is post-Beacon Reddit discussion: Autophage settlements, brood attacks, running four towns, and whether S-class is reachable now. To fill it, save Reddit threads as HTML into `scratch/` and ask for a follow-up pass.

Every factual claim in these files is paraphrased from a source listed next to it. In-game behaviour described as "to verify" has not been tested.
