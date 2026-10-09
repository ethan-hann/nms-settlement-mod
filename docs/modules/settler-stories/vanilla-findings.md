# Settler Stories: what vanilla data shows

Read 2026-10-09 from `scratch/extracted` (`gcsettlementglobals.MXML`, `metadata/reality/tables/rewardtable.MXML`, `metadata/simulation/missions/tables/sentinelsettlementmissiontable.MXML`). This answers the two "To verify offline" items in [plan.md](plan.md). Nothing here has been tested in game yet.

## Summary

- Every vanilla chain stays inside `CustomJudgements`, and no random-pool judgement chains at all. So follow-ups belong in `CustomJudgements`, which the random draw never touches.
- The open question moves: can a random-pool dilemma hand off to a custom one? Vanilla never does it, so it needs one test session.
- Judgements have no race field. Vanilla targets a race only through a mission, and does exactly that for its Autophage story.

## 1. Keeping follow-ups out of the random pool

The two lists:
- `Judgements`: 36 random-pool entries, weights 0.1 to 2.5. None has a `ChainedJudgementID`.
- `CustomJudgements`: 13 entries addressed by `ID` (`J_SENT_MISS_1`, `J_BUI_VISITOR`, `J_DEBRIEF_POS` and so on). All 8 non-empty `ChainedJudgementID` values point from one custom entry to another (`J_SENT_MISS_1` to `J_SENT_MISS_1B`, `J_SENT_MISS_3` to `3B` or `3C`, `J_SENT_MISS_4*` to `4B` or `4C`).

A custom entry wraps the same `GcSettlementJudgementData` as a pool entry, plus `CustomCostText` and `CustomMissionObjectiveText`. Custom entries carry a `Weighting`, but nothing suggests the random draw reads them.

Vanilla starts the first step of a custom chain in three ways:
- A mission reward, `GcRewardSettlementCustomJudgement`, with `CustomJudgement`, `DisplaySettlementJudgementAlert`, `CanOverrideNonCustomJudgement` and `AwardToClosestSettlement`. The Sentinel storyline uses this for `J_SENT_MISS_1`, `_3` and `J_SENT_4_LEGS`.
- The mini-expedition: `MiniMissionSuccessJudgement` and `MiniMissionFailJudgement` name `J_DEBRIEF_POS` and `J_DEBRIEF_NEG`.
- A judgement option starting a mission: the `J_BUI_VISITOR` options list `AdditionalRewards` `R_J_BUI_VISITOR`, a `SettlementTable` reward entry that gives `GcRewardMission` `SETTLE_BUI_J`.

**Result:** the `Weighting` 0 idea is not needed. Follow-ups go in `CustomJudgements`.

**Still unproven:** a story's first step comes from the random pool, and vanilla has no pool entry that chains. Two routes, in order of preference:
- **A.** Set `ChainedJudgementID` on a pool option to a custom ID. Same option struct, so it may just work.
- **B.** Put a `SettlementTable` reward entry in `AdditionalRewards` that gives `GcRewardSettlementCustomJudgement`. Both halves exist in vanilla, but never joined like this.

If neither works, a story can open with a custom judgement fired by a mission, which is the vanilla route and brings a mission into scope.

## 2. Targeting a race

- `GcSettlementJudgementData` has no race field. The only race-related fields are `DilemmaTextIsAlien` (49 uses) and `JudgementSpecificRacePartyChance` (parties only).
- `GcMissionConditionHasSettlement` takes `SpecificAlienRace`. Vanilla sets it to `Builders` (Autophage) in `SETTLE_BUI_SE` and `SETTLE_BUI_J`, the Autophage visitor storyline that ends in `J_BUI_VISITOR`.
- A separate `GcMissionConditionHasSettlementLocal` exists. That suggests `HasSettlement` means "owns one anywhere", not "is standing in one". If so, a race-gated story could fire at a settlement of a different race. `AwardToClosestSettlement` on the reward might help; not checked.

**Result:** race targeting is possible only through a mission, the way vanilla does it for the Autophage. Without one, stories must fit any race.

## Other things noticed

- An option slot (`Option1List` to `Option4List`) is a list, and 4 vanilla slots hold more than one variant. The game probably picks one at random. That could give a dilemma variety without adding entries; behaviour unconfirmed.
- `SettlementTable` holds 8 vanilla reward entries (`R_SETTL_LIST1` to `3`, `R_SETTL_UPLIST1` to `3`, `R_SETTL_NAVDATA`, `R_SETTL_PROG`). Item, nanite and standing rewards would be new entries in that bucket.
- `CanOverrideNonCustomJudgement` suggests a fired custom judgement replaces a pending random one rather than queueing behind it.
