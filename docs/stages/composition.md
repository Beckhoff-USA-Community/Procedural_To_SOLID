# Stage 3 — SOLID / composition

**Branches:** `stage-3-composition`, `stage-3-broken`, `stage-3-cr1-applied`, `stage-3-cr2-applied`, `stage-3-cr3-applied`, `stage-3-complete`

## Design philosophy

Stations are composed from small, single-responsibility Function Blocks wired through interfaces. Each building block has one job. Behavior varies by **swapping implementations**, not by overriding base methods.

This is the architecture Beckhoff's USA team builds production code with — see the [VFFS PackML Demo](https://github.com/Beckhoff-USA-Community/PackML_PLC_Example) for a real example. The Core libraries (`Core`, `CoreComponents`, `MechatronicsCore`) provide the framework primitives.

## File structure

```
NEM2026/FillingLine/POUs/
├── Interfaces/
│   ├── I_Sequenceable.TcPOU
│   ├── I_AlarmHandler.TcPOU
│   ├── I_HmiReportable.TcPOU
│   ├── I_ModeProvider.TcPOU
│   └── I_DataLogger.TcPOU
├── BuildingBlocks/
│   ├── FB_ModeManager.TcPOU
│   ├── FB_AlarmHandler_LineFault.TcPOU
│   ├── FB_AlarmHandler_QualityFlag.TcPOU
│   ├── FB_StepSequencer.TcPOU
│   ├── FB_ParallelSequencer.TcPOU
│   ├── FB_TimeoutWatchdog.TcPOU
│   └── FB_CycleDataLogger.TcPOU
├── Stations/
│   ├── FB_StationFill.TcPOU
│   ├── FB_StationCap.TcPOU
│   ├── FB_StationLabel.TcPOU
│   └── FB_StationInspect.TcPOU
├── MAIN.TcPOU
└── DUTs/
    └── ST_LogEntry.TcDUT
```

5 interfaces, 7 building blocks, 4 stations, 1 DUT, plus MAIN. **Eighteen source files** but each is small (most under 80 lines) and focused.

## The interfaces (SOLID contracts)

```iecst
INTERFACE I_Sequenceable
    METHOD Execute    : BOOL
    METHOD Reset      : BOOL
    METHOD Abort      : BOOL
    PROPERTY IsComplete : BOOL  // GET
    PROPERTY IsFaulted  : BOOL  // GET
    PROPERTY StateName  : STRING(40)  // GET

INTERFACE I_AlarmHandler
    METHOD RaiseAlarm    : BOOL  // VAR_INPUT Code, Text
    METHOD Acknowledge   : BOOL  // VAR_INPUT AckInput
    METHOD Clear         : BOOL
    PROPERTY HasActiveAlarm : BOOL
    PROPERTY AlarmText      : STRING(255)
    PROPERTY StopsLine      : BOOL  // policy bit — distinguishes strategies

INTERFACE I_HmiReportable
    PROPERTY StatusText    : STRING(80)
    PROPERTY StateNumber   : INT
    PROPERTY AlarmActive   : BOOL
    PROPERTY AlarmMessage  : STRING(255)

INTERFACE I_ModeProvider
    PROPERTY CurrentMode : INT  // 0=Idle, 1=Auto, 2=Manual, 3=Paused
    PROPERTY AllowRun    : BOOL
    PROPERTY AllowJog    : BOOL

INTERFACE I_DataLogger
    METHOD LogCycleData : BOOL  // VAR_INPUT StationName, StepNumber, CycleTimeMs
    METHOD Flush        : BOOL
    PROPERTY IsEnabled  : BOOL
```

The key bit on `I_AlarmHandler` is the `StopsLine` property — it's a **policy declaration**. `FB_AlarmHandler_LineFault` returns `TRUE`; `FB_AlarmHandler_QualityFlag` returns `FALSE`. Stations consult `Alarm.HasActiveAlarm AND Alarm.StopsLine` to decide whether to fault, and the runtime distinction between alarm strategies happens at the boundary, not inside the station.

## The building blocks

| FB | Implements | Responsibility |
|---|---|---|
| `FB_ModeManager` | `I_ModeProvider` | Resolve `Auto`/`Manual`/`Pause`/`Idle` from input booleans |
| `FB_AlarmHandler_LineFault` | `I_AlarmHandler` | Latching alarm — `StopsLine = TRUE` |
| `FB_AlarmHandler_QualityFlag` | `I_AlarmHandler` | Non-latching defect signal — `StopsLine = FALSE` |
| `FB_StepSequencer` | — | CurrentStep + step-name table + Complete/Faulted flags |
| `FB_ParallelSequencer` | — | N-branch concurrent coordinator (up to 8 branches) |
| `FB_TimeoutWatchdog` | — | TON wrapper with `Enable` / `Duration` / `TimedOut` / `Reset` |
| `FB_CycleDataLogger` | `I_DataLogger` | Ring-buffered `ST_LogEntry` array |

Each building block is small (most under 60 lines), single-purpose, and trivially testable. Compose them differently to get different stations.

## What stations look like now

```iecst
FUNCTION_BLOCK FB_StationFill IMPLEMENTS I_Sequenceable, I_HmiReportable
VAR_INPUT
    PartPresent  : BOOL;
    FlowRate, TargetVolume : LREAL;
END_VAR
VAR_OUTPUT
    OpenFillValve : BOOL;
END_VAR
VAR
    // injected dependencies (set in FB_Init)
    Mode      : REFERENCE TO FB_ModeManager;
    Alarm     : I_AlarmHandler;

    // composed building blocks
    Sequencer : FB_StepSequencer;
    Watchdog  : FB_TimeoutWatchdog;

    _Accumulated : LREAL;
END_VAR

METHOD FB_Init : BOOL
VAR_INPUT
    bInitRetains  : BOOL;
    bInCopyCode   : BOOL;
    ModeRef       : REFERENCE TO FB_ModeManager;
    AlarmHandler  : I_AlarmHandler;
END_VAR
    Mode  REF= ModeRef;
    Alarm := AlarmHandler;
    Sequencer.SetStepName(0, 'Idle');
    Sequencer.SetStepName(10, 'Filling');
    Sequencer.SetStepName(20, 'Complete');
    FB_Init := TRUE;

METHOD Execute : BOOL
    Watchdog.CyclicUpdate();
    IF Watchdog.TimedOut THEN
        Alarm.RaiseAlarm(Code := 1000, Text := 'Fill: Timeout');
        RETURN;
    END_IF
    CASE Sequencer.CurrentStep OF
        0:  IF Mode.AllowRun AND PartPresent THEN
                Sequencer.TransitionTo(10);
                Watchdog.Enable := TRUE;
                Watchdog.Duration := T#10S;
            END_IF
        10: ...
        20: Sequencer.MarkComplete();
    END_CASE
    Execute := TRUE;

// I_Sequenceable / I_HmiReportable property GETs delegate to Sequencer/Alarm
```

The station is a **thin coordinator** that wires its inputs into the building blocks and exposes the right interfaces. The actual sequencing logic is small because the building blocks do the heavy lifting.

## Construction in MAIN

```iecst
PROGRAM MAIN
VAR
    // shared services
    ModeManager  : FB_ModeManager;

    // per-station alarm strategies
    FillAlarm    : FB_AlarmHandler_LineFault;
    CapAlarm     : FB_AlarmHandler_LineFault;
    LabelAlarm   : FB_AlarmHandler_LineFault;
    InspectAlarm : FB_AlarmHandler_LineFault;     // ← swapped on stage-3-cr2-applied

    // stations composed via FB_Init dependency injection
    StationFill    : FB_StationFill(ModeRef := ModeManager, AlarmHandler := FillAlarm);
    StationCap     : FB_StationCap(ModeRef := ModeManager, AlarmHandler := CapAlarm);
    StationLabel   : FB_StationLabel(ModeRef := ModeManager, AlarmHandler := LabelAlarm);
    StationInspect : FB_StationInspect(ModeRef := ModeManager, AlarmHandler := InspectAlarm);
END_VAR
```

The construction syntax `FB_StationXxx(ModeRef := ..., AlarmHandler := ...)` invokes the FB's extended `FB_Init` with the named arguments. This is **Dependency Injection** — the station never reaches for a global; what it needs arrives at construction.

## The CR exercises — where composition shines

### CR-1 Pause — 6 lines, zero station risk

Add `ModePause` input + `Mode = 3` branch + `IsPaused` property to `FB_ModeManager`. **That's it.** Stations are not modified.

```iecst
// FB_ModeManager — full diff
VAR_INPUT
    ModeAuto, ModeManual : BOOL;
    ModePause : BOOL;        // NEW (CR-1)
END_VAR

METHOD CyclicUpdate
    IF ModePause THEN
        _Mode := 3;          // NEW
    ELSIF ModeAuto THEN
        _Mode := 1;
    ELSIF ModeManual THEN
        _Mode := 2;
    ELSE
        _Mode := 0;
    END_IF

PROPERTY IsPaused : BOOL    // NEW
    GET => IsPaused := (_Mode = 3);
```

Plus one variable + one wire in MAIN. **Six lines, one file (plus MAIN), zero station risk.**

Fill's "ignore Pause mid-cycle" requirement is automatic: Fill's state-10 logic doesn't gate on `Mode.AllowRun` once started, so pausing the line mid-fill simply blocks the next cycle from starting, not the current one. **No exception logic needed because the abstraction handles it correctly.**

[→ stage-3-cr1-applied](https://github.com/Mark-Code-Cowboys/NEM_Workshop/tree/stage-3-cr1-applied)

!!! tip "This is the Strategy pattern at work"
    `Mode.AllowRun` is `TRUE` only when `_Mode = 1`. Adding a new mode (`Pause`) doesn't change the logic — `AllowRun` automatically returns `FALSE`. The station's contract with the mode service is **the property's semantics**, not the implementation. Composition lets the contract carry the burden.

### CR-2 Inspect quality + parallel — the headline

Two changes:

1. **In MAIN — one line:**
   ```iecst
   InspectAlarm : FB_AlarmHandler_LineFault;   // before
   InspectAlarm : FB_AlarmHandler_QualityFlag; // after
   ```

2. **Inside `FB_StationInspect` — three lines** (compose `FB_ParallelSequencer`, configure for 2 branches, rework state 10):
   ```iecst
   VAR
       Parallel : FB_ParallelSequencer;
   END_VAR
   // FB_Init: Parallel.Configure(NumberOfBranches := 2);
   // ExecuteSequence step 10: parallel coordinator (CameraDone + RejectDone)
   ```

**Other stations: not touched.** Cap, Label, and Fill don't know any of this happened. The Strategy pattern (alarm) and the internal sequencer change are completely hidden behind interfaces.

[→ stage-3-cr2-applied](https://github.com/Mark-Code-Cowboys/NEM_Workshop/tree/stage-3-cr2-applied)

This is **the headline demonstration of the workshop.** Compare:

- Stage 1: 70 lines of CASE machine rewriting in one station
- Stage 2: 80 lines of `Monitoring` override duplication that fights the base
- Stage 3: 4 lines of editing total

### CR-3 Selective logging — DI to the stations that need it

Add `Logger : I_DataLogger` field + `DataLogger` `FB_Init` param to **only Fill and Inspect**. MAIN constructs a `CycleLogger` instance and passes it via DI. Cap and Label keep their original 4-arg `FB_Init` signature unchanged.

```iecst
// MAIN
VAR
    CycleLogger : FB_CycleDataLogger;       // NEW shared logger
    StationFill    : FB_StationFill(ModeRef := ModeManager,
                                    AlarmHandler := FillAlarm,
                                    DataLogger   := CycleLogger);   // CR-3
    StationCap     : FB_StationCap(ModeRef := ModeManager,
                                   AlarmHandler := CapAlarm);        // unchanged
    StationLabel   : FB_StationLabel(ModeRef := ModeManager,
                                     AlarmHandler := LabelAlarm);    // unchanged
    StationInspect : FB_StationInspect(ModeRef := ModeManager,
                                       AlarmHandler := InspectAlarm,
                                       DataLogger   := CycleLogger); // CR-3
END_VAR
```

**Cap and Label pay nothing.** They don't carry a logger field, don't take a logger init param, don't allocate buffer memory they never use.

When the logger implementation needs to change — file storage → ADS database → MQTT telemetry — only `FB_CycleDataLogger` is replaced. The stations and MAIN don't move.

[→ stage-3-cr3-applied](https://github.com/Mark-Code-Cowboys/NEM_Workshop/tree/stage-3-cr3-applied)

## Patterns this stage names

The workshop teaches these by feel, then names them once students have done them:

- **[Strategy](../patterns.md#strategy)** — `I_AlarmHandler` with two implementations selected at MAIN composition. Sequencer swap inside Inspect is the same pattern.
- **[Dependency Injection](../patterns.md#dependency-injection)** — `FB_Init` extended params for `ModeRef` / `AlarmHandler` / `DataLogger`.
- **[Interface Segregation](../patterns.md#interface-segregation)** — separate `I_Sequenceable` for sequence control vs. `I_HmiReportable` for read-only display. HMI doesn't get accidental access to internal state.
- **[Open/Closed Principle](../patterns.md#open-closed-principle)** — adding a new alarm strategy means adding a new FB that implements `I_AlarmHandler`. Existing code is **closed** to modification but **open** to extension.

## When composition is overkill

Don't reflexively reach for Stage 3. It's the right answer when:

- Multiple stations need **different runtime behaviors** that share an interface (alarm strategies, sequencer topologies)
- The codebase will be **maintained by multiple engineers over time**
- You want **TDD/CI for control code** — composition is a prerequisite for testable PLC code
- You're building a **family of similar machines** for an OEM, not a one-off integration

If you're customizing one machine for one customer and shipping it, Stage 3's complexity is not worth the testability win. Stage 1 or 2 is the right answer for that workload.

## Branches in this stage

| Branch | What it shows |
|---|---|
| `stage-3-composition` | Clean baseline — full architecture, all stations on `LineFault` + `StepSequencer` |
| `stage-3-broken` | CR-1 the WRONG way — per-station Pause guard, defeats the lesson |
| `stage-3-cr1-applied` | CR-1 alone — `FB_ModeManager` + MAIN wire only |
| `stage-3-cr2-applied` | CR-2 swap — Inspect uses `QualityFlag` + `ParallelSequencer` |
| `stage-3-cr3-applied` | CR-3 alone — Logger DI to Fill + Inspect only |
| `stage-3-complete` | All 3 CRs applied — the composition endgame |
