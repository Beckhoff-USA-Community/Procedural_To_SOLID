# Stage 1 — Procedural / monolithic

**Branches:** `stage-1-procedural`, `stage-1-broken`, `stage-1-cr1-applied`, `stage-1-cr2-applied`, `stage-1-cr3-applied`, `stage-1-complete`

## Design philosophy

Each station is a standalone Function Block. All sequencing, alarm handling, mode management, and HMI reporting lives **inside** the FB. Reuse is copy-paste.

This is how a vast amount of production TwinCAT code is actually written. It's not strawman — it's the most common style in industry, and it works for many shops, many products. The workshop respects that. What it argues is: **here are the limits, and here's what to look for to know you've hit them.**

## File structure

```
NEM2026/FillingLine/POUs/
├── FB_StationFill.TcPOU
├── FB_StationCap.TcPOU
├── FB_StationLabel.TcPOU
├── FB_StationInspect.TcPOU
└── MAIN.TcPOU
```

Five files, no helpers, no shared base. Each station is self-contained.

## Deliberate drift

Realistic codebases drift. The Stage 1 baseline preserves three deliberate inconsistencies that students should *discover* during the CR-1 exercise, not be told about up front:

| Drift | Where | Why kept |
|---|---|---|
| **R_TRIG vs level alarm-ack** | Fill / Label use `R_TRIG`; Cap / Inspect use level | Drift between copy-paste lineages |
| **Step numbering 0/100/200/300 vs 0/10/20** | Label uses 0/100/200/300; everyone else uses 0/10/20 | An earlier developer's preference that propagated |
| **Dead `ManualStep` variable** | `FB_StationInspect` declares `ManualStep : INT` and never uses it | Legacy cruft from a previous feature |

!!! warning "Don't tidy these up"
    The drift is the workshop's setup for CR-1. When students try to add Pause to all four stations, they discover that the differences make the change harder than they expected. That's the moment.

## What's in each station

Every station has roughly the same structure:

```iecst
FUNCTION_BLOCK FB_StationXxx
VAR_INPUT
    Execute, Reset    : BOOL;
    ModeAuto, ModeManual, JogForward, JogReverse : BOOL;
    PartPresent, AlarmAck : BOOL;
    // station-specific inputs
END_VAR
VAR_OUTPUT
    Busy, Done, Error : BOOL;
    ErrorID  : UDINT;
    StatusText : STRING(80);
    StateDisplay : INT;
    AlarmActive : BOOL;
    AlarmText : STRING(255);
    // station-specific outputs
END_VAR
VAR
    State : INT;
    Timeout : TON;
    AlarmLatched, AlarmCode : ...;
    ActiveMode : INT;
    // station-specific working state
END_VAR
```

The body of every station is structured:

```iecst
// 1. Mode resolution (copy-pasted across all stations)
IF ModeAuto THEN
    ActiveMode := 1;
ELSIF ModeManual THEN
    ActiveMode := 2;
ELSE
    ActiveMode := 0;
END_IF

// 2. Alarm acknowledgment (subtly different per station)
IF AlarmLatched AND AlarmAck THEN ...   // some use R_TRIG instead
    AlarmLatched := FALSE;
    ...
END_IF

// 3. Reset block
IF Reset THEN ... END_IF

// 4. State machine — the actual work
CASE State OF
    0: ...
    10: ...
    20: ...
END_CASE

// 5. HMI mapping (copy-pasted)
StateDisplay := State;
CASE State OF
    ...
END_CASE
Busy := (State <> 0) AND NOT Done;
AlarmActive := AlarmLatched;
Error := AlarmLatched;
ErrorID := AlarmCode;
```

Sections 1, 2, 3, and 5 are copy-paste-with-drift across all four files. Only section 4 (the state machine) varies meaningfully. **Roughly 40 of every 60-line station body is duplication.**

## The CR exercises

| CR | What changes | Files | Lines |
|---|---|---|---|
| [CR-1 Pause](../workshop/change-requests.md#cr-1-add-a-pause-mode) | Mode block + Pause guard, in every station, with Fill exception | **5** | +50 / −13 |
| [CR-2 Inspect quality + parallel](../workshop/change-requests.md#cr-2-inspect-non-faulting-alarm-parallel) | Inspect rewritten with quality flag + parallel state-10 | 2 | +92 / −55 |
| [CR-3 Selective logging](../workshop/change-requests.md#cr-3-selective-cycle-logging) | Identical buffer code in Fill and Inspect | 2 | +13 / −3 |

The "5 files / 25+ lines" cost on CR-1 is the gut punch. Every cross-cutting requirement has the same shape. Multiply across a year of production change orders.

## What's pedagogically powerful here

- **The drift is real.** Students recognize their own codebases.
- **The pain is felt before it's named.** No one needs to be told that copy-pasting four files is bad — they feel it when CR-1 lands.
- **The instructor reveal moment.** During the CR-1 exercise, ask the class: *"How many of you copied from Fill? How many from Cap? Are your alarm-ack behaviors the same?"* That's when the room goes quiet.

## When procedural is actually fine

Don't reflexively dismiss this stage. Procedural code is the right answer when:

- The codebase is small (one machine, one customer)
- Maintenance is by one engineer, the original author
- Cross-cutting changes are rare
- The team has no path to TDD/CI for control code

If all four are true, Stage 1 is fine. The rest of this workshop is about **what to do when one of them stops being true** — and that's most production environments at OEMs eventually.

## Branches in this stage

| Branch | What it shows |
|---|---|
| `stage-1-procedural` | Clean baseline with deliberate drift preserved |
| `stage-1-broken` | CR-1 half-applied (Pause in Fill+Cap only) — won't compile |
| `stage-1-cr1-applied` | CR-1 alone applied to baseline (single-commit diff) |
| `stage-1-cr2-applied` | CR-2 alone (Inspect quality+parallel rewrite) |
| `stage-1-cr3-applied` | CR-3 alone (logging duplicated in Fill + Inspect) |
| `stage-1-complete` | All 3 CRs applied — the procedural endgame |
