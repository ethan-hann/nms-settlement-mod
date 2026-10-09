# Settler Stories: build plan

Written 2026-10-09 after the second research pass in [vanilla-findings.md](vanilla-findings.md). Covers steps 2 to 4 of [plan.md](plan.md): extend the tooling, build a small vertical slice, and test it in one session. Writing the full pack (step 5) and packaging (step 6) wait for the session results.

## What the session has to settle

The data leaves these open, and the slice is built to answer them all in one creative-save session:

1. **Route A:** can a pool option's `ChainedJudgementID` point at a custom judgement? Vanilla never does it. Stories depend on this or on route B.
2. **Route B:** can a pool option fire a custom judgement through a reward entry? Also never done in vanilla. Fallback only.
3. **Follow-ups stay hidden.** Does a custom judgement ever show up without its parent? The data says no, but nothing states it.
4. **`%RACE%` in judgement text.** If the dilemma screen fills it in, stories can name the town's race with no mission.
5. **`UseGiftReward`.** Does it give the settlement race's own gift? If so, that's race-flavoured rewards for free.
6. **Rewards and perks.** Do vanilla reward IDs and new perks arrive from the module's options?

## Decisions

Decided 2026-10-09.

1. **Defense output must not change.** `test_generated_files_match_the_spec` in `tests/test_modules.py` already regenerates every spec module and compares it byte for byte with the committed files, so the committed Defense folder is the snapshot. It only checks files the generators still write, so `test_generated_modules_hold_only_generated_files` closes that gap: a fully generated module may hold no file the generators don't write. Probes is exempt because it mixes in hand-written probe patches. Any generator change that alters Defense fails one of the two, unless the Defense folder is regenerated, and that would show in the PR diff under `mod/OverseersToolkit-Defense/`.
2. **Spec format.** These additions; existing keys keep their meaning:
   - `custom_judgements`: same fields as `judgements`, minus `type` and `weighting`, plus `id`. `copy_from` names a vanilla custom judgement by ID, for example `J_DEBRIEF_POS`. They are appended to `CustomJudgements`.
   - On any option: `chain` (a custom judgement ID), `rewards` (a list of existing reward IDs) and `gift` (sets `UseGiftReward`).
3. **Custom judgements get `Weighting` 0.** Vanilla's two debrief judgements are weighted 0 and still fire when awarded directly. A weight of 0 costs nothing and guards against the random draw ever picking a follow-up, which plan.md decision 1 forbids.
4. **Source options never pass on a chain or rewards.** The copy's chain, rewards and gift flag are always cleared, and only the spec sets them, the same way perks and stat changes work today. This replaces the current rule that rejects chaining sources, because almost every vanilla custom judgement chains.
5. **The generator enforces "never start halfway through".** Build errors for:
   - a `chain` that names anything but a custom judgement;
   - a custom judgement in the spec that no option reaches;
   - a chain loop.
6. **No new reward-table entries in the shipped module.** Two installed mods ship the whole reward table, and either would erase anything appended to it. Options use vanilla reward IDs, plus `gift` for race-flavoured gifts. Another mod can change those payouts, which is acceptable. Route B needs a new reward entry, so it is tested from the test-only Probes module and not built into the generator unless route A fails.
7. **IDs and text.** IDs use the `OT_SS_` prefix and stay at 15 characters or fewer. The type is 16 bytes, but whether it needs a terminator is unknown. Text keys use `OT_SS_` too, at 31 characters or fewer, and go through the spec's `text` block as today. That writes English and USEnglish, where vanilla's judgement text lives.
8. **Race-neutral first release.** No data condition can read the race of the settlement the player is at. A race-gated mission could only work by excluding players who own settlements of more than one race, and it rests on untested fields. Race flavour comes from `%RACE%` text and `gift`, if the session shows they work. Race-gated missions stay a later probe.

## Behaviours to test

Each one gets a failing test before any implementation, per the TDD rules in [../../plan.md](../../plan.md).

Custom judgements:
- appended to `CustomJudgements` under their own `_id` and `ID`, with `Weighting` 0, and the wrapper fields copied from the source
- an unknown source custom judgement is an error
- an ID already in vanilla, appearing twice in the spec, or longer than 15 characters is an error
- the copy's options keep no chain, rewards or gift flag from the source

Options:
- `chain` writes `ChainedJudgementID`, on pool and custom options alike
- a chain to an unknown ID or to anything but a custom judgement is an error
- `rewards` writes `AdditionalRewards` in order
- a reward ID that isn't in the vanilla reward table is an error
- `gift` sets `UseGiftReward`

Chain checks:
- a custom judgement that nothing reaches is an error
- a chain loop is an error

Unchanged:
- Defense output stays byte-identical (the two module checks above)
- every existing `test_gen_settlement.py` test still passes, except the one that rejects chaining sources, which decision 4 changes

Session support, in `tools/save_inspect.py`:
- reports each settlement's race, pending custom judgement and last judgement time, so session results can be read from save copies

## Vertical slice

A new `specs/OverseersToolkit-SettlerStories.json`, kept small:

- **Pool dilemma P1** (type `Request`), with `%RACE%` in its text:
  - Option A chains to custom step `A2`.
  - Option B has no chain; it is the control.
- **`A2`:**
  - one option gives a vanilla reward (`R_J_GIFTITEM1`, units) plus a new perk;
  - the other has `gift` set.
- **Probes module, test-only:** one more pool dilemma, P2. Its option gives a hand-written reward entry that fires custom step `B2` (route B).

Placeholder text, clearly marked. Real stories come in step 5.

## Test session

Creative test slot only, via `testmode.py`. Install SettlerStories, Probes and TestTuning, without Defense, whose fortify request is also a `Request`.

1. Watch for P1. Does the `%RACE%` text show the town's race?
2. Choose option A. Does `A2` appear, and how soon: right away, or after the normal wait?
3. On `A2`, pick the reward option. Do the units and the perk arrive? On the next run, pick the gift option. What arrives, and does it match the town's race?
4. When P2 appears, choose its option. Does `B2` appear?
5. Over the whole session, does `A2` or `B2` ever appear without its parent? It must not.
6. Any crash, hang or broken text.

Results go into `docs/progress.md`, `vanilla-findings.md` and plan.md:
- **Route A works:** stories use it, and route B is dropped.
- **Only B works:** the generator gains reward entries, and the reward-table conflict is documented.
- **Neither works:** stop and decide between missions and single dilemmas.

## Order of work

1. Close the dropped-file gap in the existing byte-for-byte module check.
2. Custom judgements in the generator, test by test.
3. Option `chain`, `rewards` and `gift`.
4. Chain checks.
5. `save_inspect.py` fields for the session.
6. The slice spec and the Probes additions, built and checked with `merge_preview.py` against the pinned MBINCompiler.
7. Session checklist, then the session, then the results recorded.

Each step records its observed red in the commit message. Work stays on `settler-stories` and reaches `main` through a PR.

## Out of scope here

- Writing the 6 dilemmas and 3 stories, balancing weightings, packaging.
- Missions, including race-gated ones. That would be a later probe: one mission that fires only when every owned settlement is the same race, using `AwardToClosestSettlement` true, as vanilla's seasonal BEACON mission does.
- Option-slot variants (several entries in one `OptionNList`). The generator still rejects them.
