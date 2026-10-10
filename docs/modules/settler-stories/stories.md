# Settler Stories: story draft

Draft, 2026-10-09. The content for the first release, written before Session 3 results are in. How a story step links to the next (route A chain or route B reward) does not change the content, so only the spec wiring waits on the session.

Conventions:
- Strengths follow the game's sign: `Positive` is good for the settlement, `Negative` is bad. For example, `Debt NegativeSmall` adds debt, and `Alert PositiveMedium` lowers the Sentinel alert.
- Every outcome is shown before the choice (`HidePerkInJudgement` false); costs are named in the option text.
- Text is race-neutral. `%RACE%` goes in only if Session 3 shows the dilemma screen fills it in.
- Player rewards use vanilla reward IDs: `R_J_GIFTITEM1` (500-600 nanites), `R_J_GIFTITEM2` (100,000-300,000 units), `R_J_BOUNTY` (200-500 quicksilver), `R_SETTL_NAVDATA` (1-5 navigation data), `R_J_GIFTITEM24` (salvaged technology), `R_J_GIFTITEM30` (a rare procedural item).
- Settlement rewards are stat changes, new perks, and `R_SET_FW_PARTY` (a fireworks party).

## Single dilemmas

### D1. The Night Market (Policy)

> Traders want to run a night market in the plaza once the work shifts end. It would keep the place lively, and the stalls could pay a fee to the Overseer.

- **Let it run free.** Happiness PositiveSmall, Production PositiveSmall.
- **Charge a stall fee.** Player: `R_J_GIFTITEM2` (units). Happiness NegativeSmall.

### D2. Salvage Rights (Request)

> Scouts found a cargo pod from a wrecked freighter half buried outside the walls. Its seals still hold.

- **Claim the salvage yourself.** Player: `R_J_GIFTITEM24` (salvaged technology).
- **Strip it for parts for the settlement.** Production PositiveMedium, Upkeep PositiveSmall.

### D3. A Fevered Traveller (StrangerVisit)

> A traveller staggers in with a fever, asking for a bed until it breaks. They have little to offer but a trinket from their pack.

- **Give them a bed.** MaxPopulation PositiveSmall, Happiness NegativeSmall ("the settlers worry about the fever").
- **Trade medicine for the trinket and send them on.** Player: `R_J_GIFTITEM30` (rare item).

### D4. The Buried Beacon (Request)

> Builders digging a new foundation hit an old survey beacon. It still hums, and its memory is full of coordinates.

- **Download the coordinates.** Player: `R_SETTL_NAVDATA` (navigation data).
- **Wire it into the perimeter sensors.** Alert PositiveMedium, Sentinels PositiveSmall.

### D5. Festival of Lights (Policy)

> The settlers ask for a festival to mark the end of the building season: lanterns, music, fireworks over the rooftops.

- **Fund a full festival (adds debt).** `R_SET_FW_PARTY`, Happiness PositiveMedium, Debt NegativeSmall.
- **Keep it small.** Happiness PositiveSmall.

### D6. The Wage Dispute (Conflict)

> Two workers stand before the Overseer. One says the foreman has been short-changing the night crew. The foreman says the crew has been short-changing the work.

- **Side with the crew (adds debt).** Happiness PositiveMedium, Debt NegativeSmall.
- **Side with the foreman.** Production PositiveMedium, Happiness NegativeSmall.

## Stories

### S1. The Stranger at the Gate (StrangerVisit, three steps)

**Step 1, A Stranger at the Gate.**

> A stranger in worn armour asks for shelter. They give a name, but nothing else about where they have come from.

- **Let them stay.** Leads to step 2.
- **Turn them away.** Alert PositiveSmall.

**Step 2, Rumours.**

> The stranger has worked hard and kept to themselves. Now a passing pilot claims they are a deserter from a mercenary crew, and that the crew pays well for deserters.

- **Keep their secret.** Leads to step 3.
- **Hand them over for the bounty.** Player: `R_J_BOUNTY` (quicksilver). Happiness NegativeSmall.

**Step 3, The Crew Comes Looking.**

> A dropship lands at the edge of the settlement. The crew wants their deserter back, and they are not asking politely.

- **Stand together.** New perk **Sanctuary**: Happiness PositiveMedium, Alert NegativeSmall ("the settlement draws more attention").
- **Pay the crew to leave (adds debt).** Debt NegativeMedium, Production PositiveSmall ("the deserter stays on as a worker").

### S2. The Seed Vault (Request, two steps)

**Step 1, A Sealed Vault.**

> A farmer clearing a cave found a sealed vault of ancient seeds. Collectors would pay well for it unopened.

- **Open it carefully.** Leads to step 2.
- **Sell it unopened.** Player: `R_J_GIFTITEM2` (units).

**Step 2, The Old Seeds.**

> Most of the seeds are dust, but a handful are alive: a crop nobody alive has ever grown.

- **Plant them for the settlement.** New perk **Ancient Orchard**: Production PositiveMedium, Happiness PositiveSmall.
- **Keep the best for yourself, plant the rest.** Player: `R_J_GIFTITEM30` (rare item). Production PositiveSmall.

### S3. The Lost Survey (Request, three steps)

**Step 1, Overdue.**

> A survey team left two days ago to map the ridge. They should have been back yesterday.

- **Send a search party.** Leads to step 2.
- **Light a beacon and wait.** Production PositiveSmall, Happiness NegativeSmall.

**Step 2, Shelter in the Ruins.**

> The search party found them sheltering in old ruins after a storm, unhurt. The walls around them are covered in relics nobody recognises.

- **Bring them home, with the relics.** Leads to step 3.
- **Bring them home and leave the relics.** Happiness PositiveMedium.

**Step 3, The Relics.**

> The relics are back in the settlement, and everyone has an opinion about them.

- **Put them on display.** New perk **Relic Hall**: Happiness PositiveSmall, Production PositiveSmall.
- **Hand them to the Overseer.** Player: `R_J_GIFTITEM1` (nanites).

## Balance, to finish after Session 3

- **Player and settlement split.** 8 options pay the player and about 14 pay the settlement, roughly 35/65 against the 50/50 aim. Candidates to shift: word and standing rewards, if a probe shows the generic `WORD` and `STANDING` rewards (race `None`) resolve to the settlement's race; or one or two settlement options turned into player rewards.
- **Weightings.** Estimate, assuming the game picks a type by `JudgementSelectionWeights` among types that have judgements, then a judgement by `Weighting` within the type (inferred, not stated in the data). Vanilla totals per type: Conflict 9.0 (6 entries), Policy 7.0 (7), StrangerVisit 6.0 (7), Request 4.01 (4). With this draft's nine pool entries (4 Request, 2 Policy, 2 StrangerVisit, 1 Conflict) at weighting 1.0 each, about 1 decision in 5 is a Settler Stories one while no building choice is on offer, and about 1 in 10 while one is (BuildingChoice weighs 1.6). That meets the one-in-four-or-five aim at weighting 1.0. Four new Request entries would make up half of all Requests, so moving one Request story start to another type is worth considering.
- **New perks.** Sanctuary, Ancient Orchard and Relic Hall copy vanilla `SENT_QUAR` as Defense's perk does. Like every perk grant, they can come up again once owned.
