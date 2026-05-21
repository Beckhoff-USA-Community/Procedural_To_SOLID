# The scoreboard

These numbers are the literal output of `git diff --stat` against each branch. No estimates, no theory — every cell is a clickable diff you can audit.

!!! info "Two ways to look at every cell"
    Each scoreboard cell can be reproduced either against the **legacy single-PLC branches** (the historical single-`FillingLine/` iteration) or against the **current 3-PLC structure** (`Release` → `crN-applied` with a path filter to one PLC). Both produce the same line counts because the underlying source files are byte-identical.

## The matrix

| | Stage 1 (procedural) | Stage 2 (inheritance) | Stage 3 (composition) |
|---|---|---|---|
| **CR-1 Pause** | 5 files / +50 / −13 | 3 files / +65 / −48 | **2 files / +19 / −6** |
| **CR-2 Inspect quality + parallel** | 2 files / +92 / −55 | 2 files / +121 / −48 | **1 line MAIN + ~3 internal** |
| **CR-3 Selective logging** | 2 files / +13 / −3 | 3 files / +64 / −25 | **3 files / +32 / −11** |
| | | | |
| Risk surface | Every station, every change | Base + affected children | Only touched files |
| Cross-station coupling | High (copy-paste drift) | Medium (inheritance fragility) | Low (interface contracts) |
| Testability | Hard — entangled with I/O | Medium — base class hooks | High — inject mocks via DI |

## Verify any cell

### Against the current 3-PLC structure (recommended)

From the repo root, each CR's per-paradigm cost is one diff against `Release` with a path filter:

```fish
# CR-1 — Pause across methodologies
git diff Release...cr1-applied --stat -- NEM2026/FillingLine_Procedural/
git diff Release...cr1-applied --stat -- NEM2026/FillingLine_Inheritance/
git diff Release...cr1-applied --stat -- NEM2026/FillingLine_Composition/

# CR-2 — Inspect quality + parallel
git diff Release...cr2-applied --stat -- NEM2026/FillingLine_Procedural/
git diff Release...cr2-applied --stat -- NEM2026/FillingLine_Inheritance/
git diff Release...cr2-applied --stat -- NEM2026/FillingLine_Composition/

# CR-3 — Selective logging
git diff Release...cr3-applied --stat -- NEM2026/FillingLine_Procedural/
git diff Release...cr3-applied --stat -- NEM2026/FillingLine_Inheritance/
git diff Release...cr3-applied --stat -- NEM2026/FillingLine_Composition/
```

For full file content drop `--stat`. The cumulative end state is on `complete`:

```fish
git diff Release...complete --stat
```

### Against the legacy single-PLC branches (historical)

The same cells reproduce against the older one-PLC-per-branch layout:

```fish
git diff stage-1-procedural...stage-1-cr1-applied --stat
git diff stage-2-inheritance...stage-2-cr1-applied --stat
git diff stage-3-composition...stage-3-cr1-applied --stat
# ...and so on for CR-2, CR-3
```

## GitHub compare links (one per cell)

Drop these straight into your slide deck or facilitator notes — they show the diff side-by-side in the browser:

| | Stage 1 | Stage 2 | Stage 3 |
|---|---|---|---|
| **CR-1** | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-1-procedural...stage-1-cr1-applied) | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-2-inheritance...stage-2-cr1-applied) | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-3-composition...stage-3-cr1-applied) |
| **CR-2** | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-1-procedural...stage-1-cr2-applied) | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-2-inheritance...stage-2-cr2-applied) | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-3-composition...stage-3-cr2-applied) |
| **CR-3** | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-1-procedural...stage-1-cr3-applied) | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-2-inheritance...stage-2-cr3-applied) | [compare](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-3-composition...stage-3-cr3-applied) |

## Reading the numbers

The raw line counts tell part of the story; the *shape* of the change tells the rest.

!!! note "Stage 1 wins on raw lines for CR-3 and CR-1 size"
    Stage 1's CR-3 is "smallest" in lines (only 13 added) but those 13 lines are *duplicated identically* in Fill and Inspect. Stage 3 has more lines but the cycle logger is shared — the duplicate is at the integration layer, not the implementation layer.

!!! warning "Stage 2's CR-2 line count understates the cost"
    Stage 2 CR-2 only adds ~80 lines, but those 80 lines include re-implementing mode resolution and alarm-ack from scratch in Inspect's `Monitoring` override. The "lines" are cheap; the *fragility* is expensive — every future change to base `Monitoring` won't propagate. That's not visible in `--stat`.

The right frame is **blast radius**, not lines:

- **Stage 1 blast radius:** every change to a cross-cutting concern touches every station. CR-1 hit 5 files; the next 50 changes will hit ~5 files each.
- **Stage 2 blast radius:** changes to the *common* parts hit the base; changes to the *station-specific* parts hit one child. Until a child needs to opt out, in which case the base gets polluted.
- **Stage 3 blast radius:** changes to a building block hit one file. Changes to wiring hit MAIN. Stations themselves rarely change after initial composition.

## The deeper benefit (testability)

The scoreboard tracks the visible cost of CRs. The invisible cost the scoreboard *can't* show is testability. Stage 1 and Stage 2 stations are entangled with their I/O — you can't unit-test them without spinning up the whole framework.

Stage 3 stations accept their dependencies at construction. In a PlcTestSuite test you can:

```iecst
VAR
    MockMode    : FB_ModeManager;
    MockAlarm   : FB_AlarmHandler_QualityFlag;   // never latches, easy to verify
    Logger      : FB_CycleDataLogger;            // can inspect buffer after each cycle
    UnitUnder   : FB_StationFill(ModeRef     := MockMode,
                                 AlarmHandler := MockAlarm,
                                 DataLogger   := Logger);
END_VAR
```

Then drive `MockMode.ModeAuto := TRUE`, set `PartPresent := TRUE`, call `UnitUnder.Execute()` repeatedly, and assert against `Logger._Buffer`. **No real I/O, no real alarms, deterministic test.**

That's the workshop's quiet long-tail value: composition makes test-driven PLC development feasible. If your shop is moving toward CI for control code, this isn't optional anymore — it's the prerequisite.
