# Settler Stories: rough plan

Rough outline, written 2026-10-09. Not a spec yet.

## Goal

An optional module, `OverseersToolkit-SettlerStories`, that adds new settlement decisions. Some are single dilemmas and some are short stories that unfold over two or three decisions. Every outcome is shown before the player chooses, and most outcomes are good or mixed.

The research behind it is idea I-1 in [../../research/ideas/module-ideas.md](../../research/ideas/module-ideas.md). It answers these complaints from [player-feedback.md](../../research/ideas/player-feedback.md):
- decisions feel repetitive, random or punishing (F5)
- there is little to do in a settlement (F3)
- settlers feel passive (F11)

## Scope

In:
- New dilemmas appended to the random pool.
- Short chained stories through `ChainedJudgementID`.
- New perks for story outcomes.
- Race-flavoured text for Gek, Korvax, Vy'keen and Autophage towns.
- Rewards beyond stats where the data allows them: standing, alien words, nanites, items.

Out:
- New missions or mission givers. That is idea I-2.
- New build parts.
- Any edit to vanilla dilemmas beyond what appending needs.

## Design rules

- Never hide an outcome: set `HidePerkInJudgement` to false.
- Mostly positive or mixed outcomes; any negative perk is named on the option.
- Rewards split about 50-50 between the player (items, nanites, standing, words) and the settlement (stats, perks), counted across the pack. Where it fits, a dilemma can make that the choice itself: keep the reward, or put it back into the town.
- Keep weightings low so new dilemmas mix in with vanilla ones rather than crowd them out. Aim for roughly one Settler Stories decision in every four or five.
- Text goes through `LocTable.MXML` keys, in English first.
- The module stands alone. It does not depend on core, Defense or SettlementDecor.

## What the tooling needs

`tools/gen_settlement.py` already appends judgements and perks for Defense. It has two gaps:

1. It refuses source judgements whose options chain (`ChainedJudgementID`), and it never sets a chain. Stories need it to write chains between the module's own dilemmas, probably as `CustomJudgements` entries addressed by ID.
2. It clears `AdditionalRewards`. Item, nanite and standing rewards need reward-table entries (the `SettlementTable` bucket) and a way to reference them from the spec.

Both changes start with a failing test, per the plan's TDD rules.

## Decisions

Decided 2026-10-09:

1. **Stories never start halfway through.** A follow-up dilemma must only ever fire from its chain, never from the random pool. This is a requirement, not a preference. If the data can't guarantee it, stories are dropped in favour of single dilemmas (see Risks).
2. **Race-specific stories if the game allows it.** Write stories for a specific race when the data can target one. Otherwise write them to fit any race.
3. **The first release has 6 single dilemmas and 3 stories** of two or three steps.
4. **The first release is race-neutral.** Judgements have no race field, and no mission condition reads the race of the settlement the player is at: `HasSettlement` with a race means "owns one anywhere" ([vanilla-findings.md](vanilla-findings.md)). A race-gated mission could only work for players whose settlements are all one race, and it rests on untested fields. Race flavour comes from `%RACE%` text and race gifts if the session shows they work.
5. **No new reward-table entries in the shipped module.** Options use vanilla reward IDs, because whole-file reward-table mods would erase appended entries. Other mods may change those payouts; that is accepted.
6. **Follow-up steps have `Weighting` 0,** as vanilla's debrief judgements do, so the random draw can never pick one.

## To verify offline

Answered from game data on 2026-10-09; see [vanilla-findings.md](vanilla-findings.md) and [build-plan.md](build-plan.md). In short: follow-ups go in `CustomJudgements` (weighted 0, as vanilla's debriefs are), but whether a random-pool dilemma can hand off to one needs a test session. Race can't be read from the settlement the player is at; missions can only test ownership. The original questions:

1. **Keeping follow-ups out of the random pool.** Two candidate mechanisms:
   - `ChainedJudgementID` points at a `CustomJudgements` ID, which is never drawn at random.
   - The follow-up sits in the main pool with `Weighting` 0. TestTuning zeroes vanilla judgements this way, but whether a zero-weight entry is ever drawn is unproven.
   
   Read vanilla chained options in `GCSETTLEMENTGLOBALS` to see which list their targets live in.
2. **Targeting a race.** No race field is known on random judgements; `JudgementSpecificRacePartyChance` only covers parties. The one known route is a mission:
   - `GcMissionConditionHasSettlement` takes `SpecificAlienRace`.
   - `GcRewardSettlementCustomJudgement` can then fire a story's first dilemma.
   
   That would bring a mission into scope, which the Out list currently excludes. It also needs checking whether the condition tests the settlement the player is at or any settlement they own. If this route is the only option, a mission has to be worth the extra scope.

## Rough steps

1. Settle the "To verify offline" items from vanilla data (`GCSETTLEMENTGLOBALS`, the reward table, the mission tables). Run `tools/extract.py` on the PC with the game installed.
2. Extend `gen_settlement.py` to support chains and reward references, tests first.
3. Write a spec, `specs/OverseersToolkit-SettlerStories.json`, with two or three dilemmas and one chained story as a vertical slice.
4. Test session: TestTuning makes decisions fire within minutes. Confirm that the dilemmas appear, the chain follows, rewards arrive, and nothing crashes.
5. Write the rest of the stories and balance the weightings.
6. Package it, add it to COMPATIBILITY.md, the README and CHANGES.md.

## Risks

- **Chaining:** if follow-ups can't be kept out of the random pool, the 3 stories become single dilemmas with richer outcomes. Stories that start halfway through are not acceptable.
- **Race targeting:** if no route exists, every story is written to fit any race. Race flavour then comes only through text that suits all of them.
- **Shared file:** `GCSETTLEMENTGLOBALS` is the file every settlement mod patches. Appending to the judgement lists should merge cleanly, but test alongside a timer mod.
- **Repeats:** no condition checks whether a perk is already owned, so a perk-granting dilemma can come up again (the known Defense limit).
