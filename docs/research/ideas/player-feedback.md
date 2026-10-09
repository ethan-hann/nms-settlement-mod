# Player feedback on settlements

What players complain about and ask for, grouped by theme and ranked roughly by how often each comes up. Each theme says whether Hello Games has fixed it. Sources are linked inline. "Snippet" means only a search-result summary or title was readable.

Most of the evidence is from the Steam Community board for app 275850, read in full, plus official patch notes and Nexus mod comments. Reddit could not be read (see [README.md](README.md)).

## Timeline

| Era | Settlement state |
|---|---|
| Frontiers 3.6, Sep 2021 | Settlements added. One per player, 5 visible stats, 2-option decisions, 6 features, multi-hour builds |
| 3.61 to 3.71, Sep to Oct 2021 | Bug fixes. Decisions every 15 min to 2 h (3.63). Teleporter in the overseer's office (3.66). Shops and trade terminal in the market (3.66) |
| Outlaws, Apr 2022 | A pirate-raid frequency bug hits settlements; Hello Games confirms it and patches it |
| Echoes 4.4, Aug 2023 | "A Trace of Metal" storyline with corrupted-drone raids |
| Beacon 5.7, Jun 2025 | Rework: up to 4 settlements, per-building C to S upgrades, choosable and exportable production, 18 features, 2 to 4 decision options, Autophage settlements, brood attacks, squadron pilots, reworked class formula |
| 5.71 to 6.03, Jun to Sep 2025 | Beacon regressions. Sentinel and brood attacks never fired for about three months, until 6.03 |
| Cosmos 7.0 to 7.06, Sep to Oct 2026 | 7.04 fixes the 15-month bug where higher productivity slowed production, and debt jumping to about 2 billion. 7.05 shortens the expedition milestone waits |

Sources: [Frontiers notes](https://www.nomanssky.com/frontiers-update/), [Beacon notes](https://www.nomanssky.com/beacon-update/), [5.73](https://www.nomanssky.com/2025/07/beacon-5-73/), [6.03](https://www.nomanssky.com/2025/09/voyagers-6-03/), [7.04](https://www.nomanssky.com/2026/09/cosmos-7-04/), [7.05](https://www.nomanssky.com/2026/09/cosmos-7-05/).

## 1. The economy makes no sense, and debt can't be paid

Status: **open**. 7.04 fixed the inverted production bug, but players still can't read the math.

- Production follows beds, not settlers, and happiness has no visible effect (40% vs 106%). Players were still asking about this on 2026-10-09. [Steam](https://steamcommunity.com/app/275850/discussions/0/594069606514035616/)
- Every C-class building runs at a loss. Beacon dropped existing towns to C, which sent some millions into debt and cost half their population. [Steam](https://steamcommunity.com/app/275850/discussions/0/601906562849633224/), [wiki](https://nomanssky.fandom.com/wiki/Planetary_Settlement_-_Construction_Opportunities) (snippet)
- Advertised gains arrive at less than half their value. Examples: a factory listed at 76k delivered about 29k, and a 45,767 maintenance cut applied 16,542. [Steam](https://steamcommunity.com/app/275850/discussions/0/601906666649224324/), [Steam](https://steamcommunity.com/app/275850/discussions/2/592899712937391153/)
- Overseers can't pay debt with their own units, even with hundreds of millions on hand. This has been asked since 2021 and again in 2025 and 2026. "Donate to reserves" only advances the production timer, and players call the wording misleading. [Steam 2021](https://steamcommunity.com/app/275850/discussions/0/3044984779775869023), [Steam 2025](https://steamcommunity.com/app/275850/discussions/0/532101388398797947/), [Steam suggestions](https://steamcommunity.com/app/275850/discussions/3/565911724530681775/)
- Debt keeps growing while the game is closed, so a week away means a big bill. One Corvette-era save took 40 days to clear. [Steam](https://steamcommunity.com/app/275850/discussions/0/762933704335074369/)
- Upgrade materials make no sense. One upgrade wanted 63 Dirt while the town makes 1 every 10 hours. [Steam](https://steamcommunity.com/app/275850/discussions/0/601906666649224324/)
- The building upkeep cost is not shown anywhere in the office UI. [wiki](https://nomanssky.fandom.com/wiki/Planetary_Settlement_-_Construction_Opportunities) (snippet)

## 2. Real-time timers and one upgrade at a time

Status: **open**. This is the most-cited complaint from 2021 through the September 2026 expedition.

- The largest settlement thread found (115 replies, 2021) compares the system to bad mobile city builders. A landing pad builds in seconds; a village building takes about 3 hours. [Steam](https://steamcommunity.com/app/275850/discussions/0/3044984779763072839)
- After Beacon, build phases run 1:30:00 three times, only one project can run, and decisions stop during construction. A mod page cites 13 hours for a full upgrade. [Steam](https://steamcommunity.com/app/275850/discussions/0/601906666649224324/), [Nexus 3699](https://www.nexusmods.com/nomanssky/mods/3699) (snippet)
- Requests:
  - donate all materials at once
  - auto-advance stages
  - drop the unveiling step
  - pay extra resources to shorten a timer
  - missions that speed construction
  
  [Steam](https://steamcommunity.com/app/275850/discussions/0/601907544254858498/), [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/)
- During the Cosmos expedition milestone, picking a new building blocks the one in progress. One player called it "not respecting the players time". 7.05 shortened only the expedition waits. [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734660892212/)
- Players are split on how far to go. Instant mods break the first construction mission ([Nexus 3907](https://www.nexusmods.com/nomanssky/mods/3907)), and Gumsk recommends lengthening timers. Mod comments ask for a balanced middle, such as one minute per build or 10-second builds with 2-minute decisions.

## 3. Settlements feel pointless: weak or generic rewards

Status: **partly addressed** by Beacon (production choice, export, building utilities). Players still say it.

- This is the most repeated sentiment from 2021 to 2024. Output is tiny next to scanning a plant or running frigate missions, and a maxed settlement is "eye candy". [Steam](https://steamcommunity.com/app/275850/discussions/0/2963922521568687692), [Steam](https://steamcommunity.com/app/275850/discussions/0/3830914462336139435)
- After Beacon, nothing the town makes is unique. Players suggested tritium, storage augments, frigate modules, or a crafting workshop. [Steam](https://steamcommunity.com/app/275850/discussions/0/601907544254858498/)
- A large mothership "can do exactly the same thing" and can move. Oct 2026. [Steam](https://steamcommunity.com/app/275850/discussions/0/594069369071491172/)
- Players want to preview or choose production before claiming. Beacon added choice, but for years the only way to change it was a save editor. [Nexus 2187 comments](https://www.nexusmods.com/nomanssky/mods/2187)
- Some product stacks are absurdly small, for example 1 cryogenic chamber against 10 quantum processors. [Nexus 3699 comments](https://www.nexusmods.com/nomanssky/mods/3699)
- Reaching S-class gives no buff; it is a status symbol. [Steam](https://steamcommunity.com/app/275850/discussions/0/595137443379818332) (snippet)

## 4. Attacks: too frequent, broken, or with nothing to defend with

Status: **mixed**. Frequency bugs were patched more than once. Self-defence and stuck alerts are still open.

- On Reddit this was the most common thread topic in 2022 to 2024, for example "Settlement constantly under attack" and "How to stop pirate attacks on Settlement every 5 minutes". [r/NoMansSkyTheGame titles](https://www.reddit.com/r/NoMansSkyTheGame/comments/t94wp0/) (title only)
- Players asked for laser turrets like freighters have, anti-air, defence buildings, and settlers who fight. Vy'keen warriors run back and forth during raids. [Steam](https://steamcommunity.com/app/275850/discussions/0/4362376335341287447), [Steam](https://steamcommunity.com/app/275850/discussions/3/3279194170700342055) (snippet)
- Brood attacks have no alert meter. Sentinel alerts sit at 100% for days with no raid, or show "under attack" with nobody spawned. [Steam](https://steamcommunity.com/app/275850/discussions/0/532101539723025030/), [Steam](https://steamcommunity.com/app/275850/discussions/0/595140105668148133)
- Attacks only matter if the player is present, and they want towns to defend themselves. Oct 2026. [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/)
- Mod comments ask "is there a way to stop the constant sentinel attacks?" and two maintained mods only stretch the attack interval. [Nexus 2855](https://www.nexusmods.com/nomanssky/mods/2855), [Nexus 3229](https://www.nexusmods.com/nomanssky/mods/3229)

## 5. Decisions are opaque, random or repetitive

Status: **partly addressed**. Beacon added up to 4 options and clearer disputes. 5.71 fixed "faulty goods" coming up too often, and 5.73 fixed decisions paying less than their stated values.

- Disputes with an "unknown outcome" can apply a hidden negative perk with no warning, and the game gives no feedback on whether a choice was good. [Steam](https://steamcommunity.com/app/275850/discussions/0/3044984779779833348)
- Most events are negative or boost a stat that is already maxed. [Steam](https://steamcommunity.com/app/275850/discussions/0/6741412150954783507)
- After Beacon, decisions are still called repetitive and sometimes nonsensical. Players asked for a town mission board instead of nagging. [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/), [Steam](https://steamcommunity.com/app/275850/discussions/0/590686595451070314/) (snippet)
- Players disagree about cadence. Some want more decisions, queued; others don't want a "full-time job". [Steam](https://steamcommunity.com/app/275850/discussions/0/3044984779771383347)

## 6. No building freedom inside the town

Status: **open**. The Toolkit's own origin story is this complaint.

- Players can't build their own parts or terraform inside a settlement. The standard trick is still a base computer just outside the boundary, which can crash the game or make settlers vanish. [Steam](https://steamcommunity.com/app/275850/discussions/0/3279193518787070790), [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/)
- Requests:
  - paving and roads
  - fences
  - lights, furniture, paint, flags, themes
  - cranes as landing-pad modules
  - warehouses that hold tribute
  - moving buildings "into order"
  
  [Steam](https://steamcommunity.com/app/275850/discussions/0/3044985412478132592), [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734660854004/) (snippet)
- No terrain edits are allowed within about 300u of the monument, so buildings and terminals end up buried in hills. [Steam](https://steamcommunity.com/app/275850/discussions/0/2963922521552170417) (snippet)
- Mod users ask for "normal base parts in the settlement or terraforming". [Nexus 1369 comments](https://www.nexusmods.com/nomanssky/mods/1369)
- Other players can drop base terminals or items inside your settlement. [Steam](https://steamcommunity.com/app/275850/discussions/0/594069369071491172/) (snippet)

## 7. Finding things inside the town

Status: **open**. 5.73 only labels terminals in the Analysis Visor.

- A building being upgraded gets no sky beacon, so players search the whole town. Their workarounds are save beacons, signal boosters, photo-mode drone cams, and a Workshop path-marker mod. Oct 2026. [Steam](https://steamcommunity.com/app/275850/discussions/0/594069369071491172/)
- Players want a screen listing every building with its status and class. [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/)
- The construction terminal sits at the building site, not at the office, which confuses new overseers. [Steam](https://steamcommunity.com/app/275850/discussions/0/594069100231177692/) (snippet)

## 8. Farms and facilities that do nothing

Status: **open**. No patch mentions it.

- Hydroponics trays and agri units in settlement buildings can't take plants, and the dance club's Nutrient Processor can't be used. Nov 2025. [Steam](https://steamcommunity.com/app/275850/discussions/0/5824898961045689091/)
- Players want to grow crops in grow houses for export or food, a big aquarium for caught fish, and settlement storage. Oct 2026. [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/), [Steam](https://steamcommunity.com/app/275850/discussions/0/594069369071403160/)

## 9. Class progression

Status: **reworked by Beacon**, with little feedback since.

- Before Beacon, S-class was nearly unreachable. One confirmed S took about three months at 200 population, and S towns dropped back to A for no clear reason. [Steam](https://steamcommunity.com/app/275850/discussions/0/3729575905263491542), [Steam](https://steamcommunity.com/app/275850/discussions/0/4625855174854932619)
- Beacon dropped a months-earned S town to low B. [Steam](https://steamcommunity.com/app/275850/discussions/0/601906461957751138/)

## 10. Scale and ownership

Status: **partly addressed**. Beacon raised the limit from 1 to 4.

- Until Beacon, claiming a second settlement silently wiped the first. [Steam](https://steamcommunity.com/app/275850/discussions/0/3492005739877313745)
- Players running four towns ask for 8 and for more building types. Oct 2026. [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/)
- Managing four towns is "a chore that becomes less fun over time". [Steam](https://steamcommunity.com/app/275850/discussions/0/601912361526475050/)

## 11. NPCs and life

Status: **mostly open**. Navigation glitches were patched several times.

- Settlers are passive, can't be assigned jobs, and trickle in slowly (7 in two weeks). Raising the population cap doesn't add settlers. [Steam](https://steamcommunity.com/app/275850/discussions/0/601907544254858498/), [Nexus 3662 comments](https://www.nexusmods.com/nomanssky/mods/3662)
- Players want livelier towns with more NPCs, cantina missions and tip-offs. [Steam](https://steamcommunity.com/app/275850/discussions/0/3421063428078639932)
- Mod users ask for a higher NPC cap; the Aces mod that raised it is abandoned. [Nexus 2187](https://www.nexusmods.com/nomanssky/mods/2187)

## 12. Autophage settlements

Status: **open** for reliability.

- Towns vanish or float after terrain shifts, and an S-class town lost its walls and ceiling. Oct 2025; no later patch mentions it. [Steam](https://steamcommunity.com/app/275850/discussions/0/597414091753399421/)
- Players ask for a "more fitting Autophage generator" building. [Steam](https://steamcommunity.com/app/275850/discussions/0/594068734661084460/)
- The Autophage claim offer sometimes rejects the player despite enough atlideum. [Steam](https://steamcommunity.com/app/275850/discussions/0/532101678384574154/) (snippet)

## 13. Onboarding and explanation

Status: **open**.

- Nothing explains how features, upkeep or debt work, and key stats sit in an easy-to-miss side menu. [Steam](https://steamcommunity.com/app/275850/discussions/0/3044984779779833348)
- Players say the perk system is never presented as one. Same thread.

## 14. Requests aimed at mod authors

From Nexus mod comment tabs ([mod-landscape.md](mod-landscape.md)):

- Publish the Lua and list the files you change, because every settlement mod fights over `GCSETTLEMENTGLOBALS`.
- Split the files: construction-only, decisions-only, fleet-only.
- Keep mods updated after game patches; many popular ones are abandoned.
- Offer balanced pacing, not just instant.

## Praise, for balance

Players like the Autophage visuals, procedural interiors, jukeboxes, varied attacks, four towns, and tower distress sweeps ([Steam](https://steamcommunity.com/app/275850/discussions/0/601907544254858498/)). A 2026-10-08 Steam review lists settlement management as a strength. Settlements have fans; the complaints are about depth, pacing and payoff, not the idea.
