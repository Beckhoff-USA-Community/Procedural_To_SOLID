# Stage 2 — Inheritance

**Branches:** `stage-2-inheritance`, `stage-2-broken`, `stage-2-cr1-applied`, `stage-2-cr2-applied`, `stage-2-cr3-applied`, `stage-2-complete`

## Design philosophy

Extract the duplication from Stage 1 into a base class. Children override virtual methods for station-specific behavior. Mode management, alarm latch+ack, HMI mapping, and the cyclic lifecycle live on the base **once**.

This is the standard refactor when controls engineers first reach for object-oriented design. It's also the design Beckhoff's own [SPT-Libraries framework](https://beckhoff-usa-community.github.io/SPT-Libraries/) is built on, so we use that framework directly.

## Framework: SPT-Libraries

Stations extend `SPT_Components.FB_ComponentBase`, which provides:

- **Lifecycle methods** — `CyclicLogic` (PUBLIC entry), `Initialize` (PROTECTED, multi-cycle init), `Monitoring` (PROTECTED, alarm conditions), `Reset` (PUBLIC, multi-cycle clear), `CreateEvents` (PROTECTED, FB_TcAlarm wiring)
- **Built-in fields** — `_InitComplete`, `_Error`, `_ErrorID`, `_Busy`, `_CurrentAlarmSeverity`, `Name`
- **Component-tree integration** — `RegisterWithParent(THIS^)` for hierarchical composition
- **Diagnostic interfaces** — automatic propagation of error severity to parent modules

The workshop simplifies one thing for clarity: instead of using SPT's full `FB_TcAlarm` + `TC_Events` configurator workflow, it uses plain `STRING` + `UDINT` for alarm text/code. Production code should use the full SPT alarm machinery — but that requires the events configurator, which would obscure the inheritance lesson.

## File structure

```
NEM2026/FillingLine/POUs/
├── FB_StationBase.TcPOU       # NEW — abstract base
├── FB_StationFill.TcPOU       # EXTENDS FB_StationBase
├── FB_StationCap.TcPOU        # EXTENDS FB_StationBase
├── FB_StationLabel.TcPOU      # EXTENDS FB_StationBase
├── FB_StationInspect.TcPOU    # EXTENDS FB_StationBase
└── MAIN.TcPOU
```

`FillingLine.plcproj` references the SPT placeholders: `SPT Base Types`, `SPT Components`, `SPT Diagnostic`, `SPT Event Logger`, `SPT Utilities`, plus their Tc3 prerequisites (`Tc3_EventLogger`, `Tc3_PackML_V3`).

## What `FB_StationBase` provides

```iecst
FUNCTION_BLOCK FB_StationBase EXTENDS SPT_Components.FB_ComponentBase
VAR_INPUT
    Execute, ModeAuto, ModeManual, PartPresent, AlarmAck : BOOL;
END_VAR
VAR_OUTPUT
    Done, AlarmActive : BOOL;
    StatusText : STRING(80);
    StateDisplay : INT;
    AlarmText : STRING(255);
END_VAR
VAR
    State : INT;
    Timeout : TON;
    AlarmLatched : BOOL;
    AlarmAckEdge : R_TRIG;     // standardized — drift fixed
    AlarmCode : UDINT;
    ActiveMode : INT;
END_VAR

METHOD PUBLIC CyclicLogic
    // ensures init, calls SUPER, then ExecuteSequence + UpdateHmiStatus

METHOD PROTECTED Monitoring  // OVERRIDE
    // mode resolution + alarm-ack (lives here once)

METHOD PUBLIC Reset : BOOL   // OVERRIDE
    // clears state, calls SUPER for multi-cycle base reset

METHOD PROTECTED ExecuteSequence  // VIRTUAL — children override
METHOD PROTECTED GetStepName : STRING(40)  // VIRTUAL — children override

METHOD PROTECTED RaiseStationAlarm(Code, Text)
METHOD PROTECTED TransitionTo(NextStep)
METHOD PROTECTED UpdateHmiStatus
```

## What stations look like now

Each station shrinks dramatically:

```iecst
FUNCTION_BLOCK FB_StationFill EXTENDS FB_StationBase
VAR_INPUT
    FlowRate, TargetVolume : LREAL;
END_VAR
VAR_OUTPUT
    OpenFillValve : BOOL;
END_VAR
VAR
    Accumulated : LREAL;
END_VAR
```

Methods overridden: `ExecuteSequence` (the CASE machine) and `GetStepName` (status mapping). That's it. Mode/alarm/HMI lives on the base.

The genuine wins from Stage 1 → Stage 2:

- **Mode logic** written once, not four times
- **Alarm-ack inconsistency standardized** — base uses `R_TRIG` for everyone (Stage 1 had R_TRIG vs level drift)
- **Step numbering normalized** — Label's 0/100/200/300 becomes 0/10/20/30 like everyone else
- **Dead `ManualStep` dropped** — wasn't on the base, doesn't propagate
- **HMI mapping written once** — shared `UpdateHmiStatus` + per-station `GetStepName` override

## The CR exercises — where inheritance shows its limits

This is the part where the workshop earns its name.

### CR-1 Pause — virtual flag pollution

The "right" fix in inheritance terms requires Fill to opt out of Pause mid-cycle. Two options:

**Option A — virtual `AllowPause()` on the base:**

```iecst
// added to FB_StationBase
METHOD PROTECTED AllowPause : BOOL    // VIRTUAL
    AllowPause := TRUE;       // default: yes
END_METHOD

// updated Monitoring:
IF ModePause AND THIS^.AllowPause() THEN
    ActiveMode := 3;
END_IF

// FB_StationFill overrides:
METHOD PROTECTED AllowPause : BOOL    // OVERRIDE
    AllowPause := (State <> 10);  // not during fill
END_METHOD
```

**Option B — override `Monitoring` entirely on Fill** (duplicates the base's mode logic).

Both are ugly. Option A adds a virtual method to the base that exists *only* to serve Fill's exception — Cap, Label, and Inspect inherit `AllowPause` as forever-dead weight on their interface. Option B duplicates mode logic and creates drift the moment the base changes.

**This is the inheritance pollution problem named.** Every per-child exception forces an addition to the base that all children carry forever.

[→ stage-2-cr1-applied](https://github.com/Mark-Code-Cowboys/NEM_Workshop/tree/stage-2-cr1-applied) (uses Option A)

### CR-2 Inspect quality + parallel — the breaking point

This is where inheritance breaks on **two axes at once**.

**Axis 1 — alarm policy.** Inspect needs a non-faulting quality flag. The base's `Monitoring` latches `AlarmLatched` and flips `_Error`, which stops the line. Override `Monitoring` to fix it:

```iecst
// FB_StationInspect — Monitoring override
METHOD PROTECTED Monitoring
    // CANNOT call SUPER^.Monitoring() — it would latch the alarm.
    // Must reimplement mode resolution and alarm-ack from scratch.

    IF ModeAuto THEN ActiveMode := 1;
    ELSIF ModeManual THEN ActiveMode := 2;
    ELSE ActiveMode := 0;
    END_IF

    AlarmAckEdge(CLK := AlarmAck);
    IF AlarmLatched AND AlarmAckEdge.Q THEN
        AlarmLatched := FALSE;
        // ... etc, duplicated from base
    END_IF

    IF QualityIssueDetected THEN
        QualityFlag := TRUE;       // non-latching, doesn't touch _Error
        QualityCode := 4002;
        QualityText := 'Inspect: Visual defect';
    END_IF

    // SUPER intentionally NOT called — see comment
END_METHOD
```

**The cost is permanent.** Any future addition to base `Monitoring` (new alarm condition, new diagnostic hook) won't propagate to Inspect. Every base change becomes a code-review burden: *"did we remember to mirror this into Inspect's override?"*

**Axis 2 — parallel sequencing.** Camera + reject pre-arm need to run concurrently in step 10. The base's `ExecuteSequence` virtual is fine (each child writes its own), but the assumption of linear progression in `OnStepEntry` / `OnStepExit` doesn't hold for parallel branches. Solution: jam `CameraDone` / `RejectDone` flags into the same CASE-of-INT machine and gate transitions on `IF CameraDone AND RejectDone THEN`.

It works. It also makes Inspect's body the most complex of any station, with shadowed alarm vars (`QualityFlag` / `QualityCode` / `QualityText`) that parallel the base's `AlarmLatched` / `AlarmCode` / `AlarmText` and force the HMI to read both.

[→ stage-2-cr2-applied](https://github.com/Mark-Code-Cowboys/NEM_Workshop/tree/stage-2-cr2-applied)

!!! warning "The base class that helped Stage 1 → Stage 2 has now become the constraint"
    This is the inheritance breaking point students should feel viscerally. The same abstraction that compressed five files of duplicated code is now forcing one child to fight against it.

### CR-3 Selective logging — base dead weight

Add `LogBuffer` + `LogIndex` to the base, plus a virtual `LoggingEnabled : BOOL` (default `FALSE`). Fill and Inspect override `LoggingEnabled` to return `TRUE`. Cap and Label inherit `FALSE` — and the buffer storage they never write to.

```iecst
// FB_StationBase
VAR
    LogBuffer : ARRAY[0..99] OF STRING(120);   // every child carries this
    LogIndex : INT;
END_VAR

METHOD PROTECTED LoggingEnabled : BOOL   // VIRTUAL
    LoggingEnabled := FALSE;
END_METHOD

METHOD PROTECTED LogCycleData(Note : STRING(120))
    IF NOT THIS^.LoggingEnabled() THEN RETURN; END_IF
    LogBuffer[LogIndex] := Note;
    LogIndex := (LogIndex + 1) MOD 100;
END_METHOD
```

Fill and Inspect override `LoggingEnabled` to TRUE and call `THIS^.LogCycleData(...)` at MarkComplete. Cap and Label silently carry 100 × 120 bytes of `LogBuffer` storage they will never write to. **Dead weight in unrelated children — the inheritance cost of CR-3.**

[→ stage-2-cr3-applied](https://github.com/Mark-Code-Cowboys/NEM_Workshop/tree/stage-2-cr3-applied)

## When inheritance is actually right

Stage 2 isn't strawman — it's a real gain over Stage 1 for many use cases:

- The base **does** eliminate genuine duplication of mode/alarm/HMI
- The lifecycle hooks (`Monitoring`, `Initialize`, `Reset`) **are** the right shape for most stations
- The drift gets **fixed** as a side effect of the refactor

If your station family is **homogeneous** — every station does the same shape of work, with only data differences — inheritance is a fine choice and Stage 3's complexity isn't worth it. The Stage 2 → Stage 3 jump is justified specifically when:

- Stations need **different alarm policies** (latching vs. non-latching, line-stopping vs. flagging)
- Stations need **different sequencing topologies** (linear vs. parallel vs. event-driven)
- You want **per-station optional features** without paying base-class storage for them

If none of those hit, Stage 2 is the right answer for your codebase.

## Branches in this stage

| Branch | What it shows |
|---|---|
| `stage-2-inheritance` | Clean baseline — `FB_StationBase` + 4 children |
| `stage-2-broken` | CR-2 half-applied — Inspect override mess with TODOs |
| `stage-2-cr1-applied` | CR-1 alone — `AllowPause` virtual + Fill override |
| `stage-2-cr2-applied` | CR-2 alone — Inspect `Monitoring` override (no SUPER) |
| `stage-2-cr3-applied` | CR-3 alone — base buffer + `LoggingEnabled` virtual |
| `stage-2-complete` | All 3 CRs applied — the inheritance endgame |
