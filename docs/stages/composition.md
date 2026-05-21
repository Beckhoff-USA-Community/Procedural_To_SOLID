# Stage 3 — SOLID / composition

**Where this lives:** `NEM2026/FillingLine_Composition/` in the `Release` solution. Diff against `Release` on the `cr1-applied` / `cr2-applied` / `cr3-applied` / `complete` branches to see CR application costs.

**Historical reference:** the single-PLC iteration lives on the legacy branches `stage-3-composition` / `stage-3-broken` / `stage-3-cr{1,2,3}-applied` / `stage-3-complete`. The walkthrough below was authored against those branches and they still exist — switching to `stage-3-broken` for the wrong-way CR-1 demo still works.

---

## The composition / SOLID paradigm

### Origin and theory

Composition as an architectural principle traces to the **1994 *Design Patterns* book** by the Gang of Four (Gamma, Helm, Johnson, Vlissides). Their famous edict — **"favor composition over inheritance"** — was a direct response to the inheritance overuse they'd seen in early-1990s OOP code. The argument: inheritance is rigid (one base, fixed at compile time), composition is flexible (many small pieces, swappable at runtime).

The **SOLID** principles (Robert C. Martin, codified in the early 2000s) made this concrete:

- **S — Single Responsibility.** A class should have one reason to change.
- **O — Open/Closed.** Open for extension, closed for modification.
- **L — Liskov Substitution.** Subtypes must be substitutable for their base types.
- **I — Interface Segregation.** Clients shouldn't depend on methods they don't use.
- **D — Dependency Inversion.** Depend on abstractions (interfaces), not concrete implementations.

The five principles, applied together, push you away from "inherit a kitchen-sink base" and toward "compose small, focused pieces with explicit contracts."

The core composition idea is the **HAS-A relationship**:

> *"A `FB_StationFill` HAS-A `Mode` (it consults one), HAS-A `Alarm` (it raises through one), HAS-A `Sequencer` (it tracks state with one). It IS-A Sequenceable thing, and IS-A HmiReportable thing — but those are contracts (interfaces), not parent classes."*

Compare to Stage 2's IS-A: a station IS-A `FB_StationBase`, *therefore* it has alarm/mode/HMI behavior whether or not those make sense for that station. In Stage 3, a station HAS-A whatever it needs and IS-A whatever it offers to outside callers.

### The composition mental model

When you write composition code, you're thinking:

> *"What does this thing **need**? Inject those. What does this thing **offer**? Implement those interfaces. The wiring happens at construction; behavior emerges from how the pieces talk to each other."*

In Stage 3, a station NEEDS a `FB_ModeManager` (to know if it's allowed to run), an `I_AlarmHandler` (to raise alarms), and optionally an `I_DataLogger` (to record cycle data). It OFFERS `I_Sequenceable` (Execute / Reset / Abort lifecycle) and `I_HmiReportable` (read-only display surface). The needs and offers are explicit in the FB declaration. The implementation is a thin coordinator that wires its inputs into building blocks.

### Where composition syntax comes from in TwinCAT

TwinCAT 3 supports interfaces and dependency injection via standard IEC 61131-3 + Beckhoff extensions:

- `INTERFACE I_Foo ... END_INTERFACE` — an interface declaration
- `FUNCTION_BLOCK FB_Bar IMPLEMENTS I_Foo` — an FB that satisfies an interface
- `MyVar : I_Foo;` — a variable typed as an interface (assignment with `:=`)
- `MyRef : REFERENCE TO FB_X;` — a reference to a specific FB (assignment with `REF=`)
- `METHOD FB_init` with extra `VAR_INPUT` parameters — extended FB_init for **constructor-like dependency injection**

The constructor-call syntax:

```iecst
StationFill : FB_StationFill(
    ModeRef     := ModeManager,        // REFERENCE TO assignment
    AlarmHandler := FillAlarm,         // interface assignment
    DataLogger   := CycleLogger);      // interface assignment
```

This invokes `FB_StationFill`'s extended `FB_init` method at construction time, passing `ModeManager` / `FillAlarm` / `CycleLogger` as the dependencies. **Inside `FB_init`, the FB stores those references for later use.**

### Critical TwinCAT-specific mechanics

**1. `REF=` vs `:=` for references and interfaces**

```iecst
Mode REF= ModeRef;     // REFERENCE TO assignment — must use REF=, not :=
Alarm := AlarmHandler; // interface assignment — uses :=
```

The `REF=` operator binds a reference variable to a target. The target's address is captured. Subsequent reads/writes through `Mode.SomeField` access the original instance, not a copy.

Interfaces are *also* references under the hood, but the assignment syntax is `:=` for historical reasons.

**2. Property syntax** for read-only outputs

```iecst
PROPERTY IsComplete : BOOL
    GET => IsComplete := Sequencer.Complete;
```

Properties look like fields to callers (`StationFill.IsComplete`) but execute code on access. The `{attribute 'monitoring' := 'call'}` directive above a property declaration tells the HMI binding to call the property each scan rather than caching the value.

**3. Building-block FBs have empty bodies but rich methods**

```iecst
FUNCTION_BLOCK FB_AlarmHandler_LineFault IMPLEMENTS I_AlarmHandler
VAR
    _Latched     : BOOL;
    _ActiveCode  : UDINT;
    _ActiveText  : STRING(255);
    _AckEdge     : R_TRIG;
END_VAR

(* body is empty — all behavior is in methods *)

METHOD RaiseAlarm : BOOL
VAR_INPUT
    Code : UDINT; Text : STRING(255);
END_VAR
    _Latched := TRUE;
    _ActiveCode := Code;
    _ActiveText := Text;
    RaiseAlarm := TRUE;
END_METHOD
```

The FB body running once per scan does nothing. Behavior is invoked explicitly via method calls. **Building blocks are passive holders of behavior, activated by the composer.** This is opposite to Stage 1, where the FB body *is* the behavior and method calls are rare.

---

## How composition is constructed in this workshop

### File layout (18 source files)

```
NEM2026/FillingLine_Composition/POUs/
├── Interfaces/                                  ~5 files, ~100 lines total
│   ├── I_Sequenceable.TcPOU                     Execute / Reset / Abort + props
│   ├── I_AlarmHandler.TcPOU                     RaiseAlarm / Acknowledge / Clear + props
│   ├── I_HmiReportable.TcPOU                    StatusText / StateNumber / AlarmActive
│   ├── I_ModeProvider.TcPOU                     CurrentMode / AllowRun / AllowJog
│   └── I_DataLogger.TcPOU                       LogCycleData / Flush + IsEnabled
├── BuildingBlocks/                              ~7 files, ~400 lines total
│   ├── FB_ModeManager.TcPOU                     implements I_ModeProvider
│   ├── FB_AlarmHandler_LineFault.TcPOU          latching alarm strategy
│   ├── FB_AlarmHandler_QualityFlag.TcPOU        non-latching alarm strategy
│   ├── FB_StepSequencer.TcPOU                   sequential CASE coordinator
│   ├── FB_ParallelSequencer.TcPOU               N-branch concurrent coordinator
│   ├── FB_TimeoutWatchdog.TcPOU                 TON wrapper
│   └── FB_CycleDataLogger.TcPOU                 implements I_DataLogger
├── Stations/                                    ~4 files, ~700 lines total
│   ├── FB_StationFill.TcPOU                     ~210 lines — implements 2 interfaces
│   ├── FB_StationCap.TcPOU                      ~180 lines
│   ├── FB_StationLabel.TcPOU                    ~180 lines
│   └── FB_StationInspect.TcPOU                  ~210 lines
├── MAIN.TcPOU                                   ~95 lines — wires everything
└── DUTs/
    └── ST_LogEntry.TcDUT                        the log buffer record type
```

Total: ~1300 lines across 18 files. **Roughly 2.5x the line count of Stage 1, distributed across many small focused files.** The line-count growth is the up-front composition cost. The CR-handling savings come back fast.

### The interfaces (SOLID contracts)

```iecst
INTERFACE I_Sequenceable
    METHOD Execute    : BOOL                        // run one scan of work
    METHOD Reset      : BOOL                        // clear state, multi-cycle
    METHOD Abort      : BOOL                        // stop immediately, drop state
    PROPERTY IsComplete : BOOL                      // GET — Sequencer.Complete
    PROPERTY IsFaulted  : BOOL                      // GET — Alarm.HasActive AND StopsLine
    PROPERTY StateName  : STRING(40)                // GET — Sequencer.StepName

INTERFACE I_AlarmHandler
    METHOD RaiseAlarm   : BOOL  VAR_INPUT Code, Text   // queue an alarm
    METHOD Acknowledge  : BOOL  VAR_INPUT AckInput     // R_TRIG inside (if latching)
    METHOD Clear        : BOOL                          // unconditional clear
    PROPERTY HasActiveAlarm : BOOL                       // GET
    PROPERTY AlarmText      : STRING(255)                // GET
    PROPERTY StopsLine      : BOOL                       // GET — POLICY (key bit)

INTERFACE I_HmiReportable
    PROPERTY StatusText    : STRING(80)                  // GET
    PROPERTY StateNumber   : INT                         // GET
    PROPERTY AlarmActive   : BOOL                        // GET
    PROPERTY AlarmMessage  : STRING(255)                 // GET

INTERFACE I_ModeProvider
    PROPERTY CurrentMode : INT                            // GET — 0 idle / 1 auto / 2 manual / 3 paused
    PROPERTY AllowRun    : BOOL                            // GET — (Mode = 1)
    PROPERTY AllowJog    : BOOL                            // GET — (Mode = 2)

INTERFACE I_DataLogger
    METHOD LogCycleData : BOOL  VAR_INPUT StationName, StepNumber, CycleTimeMs
    METHOD Flush        : BOOL
    PROPERTY IsEnabled  : BOOL
```

The most important detail across these interfaces is `I_AlarmHandler.StopsLine`. **It's a policy declaration, not a behavior.** `LineFault.StopsLine = TRUE` says "if I have an active alarm, the line should stop." `QualityFlag.StopsLine = FALSE` says "if I have an active alarm, just flag it; the line keeps running." The station code consults `Alarm.HasActiveAlarm AND Alarm.StopsLine` to compute `IsFaulted` — and the runtime distinction between alarm strategies happens at the boundary, not inside the station.

### The building blocks

| FB | Implements | One-line role |
|---|---|---|
| `FB_ModeManager` | `I_ModeProvider` | Resolves `Auto`/`Manual`/`Pause`/`Idle` from input booleans |
| `FB_AlarmHandler_LineFault` | `I_AlarmHandler` | Latching alarm; `StopsLine = TRUE` |
| `FB_AlarmHandler_QualityFlag` | `I_AlarmHandler` | Non-latching defect; `StopsLine = FALSE` |
| `FB_StepSequencer` | — | CurrentStep + step-name table + Complete flag |
| `FB_ParallelSequencer` | — | N-branch concurrent coordinator (up to 8 branches) |
| `FB_TimeoutWatchdog` | — | TON wrapper (`Enable` / `Duration` / `TimedOut` / `Reset`) |
| `FB_CycleDataLogger` | `I_DataLogger` | Ring-buffered `ST_LogEntry` storage |

Each is small (most under 60 lines), single-purpose, and trivially testable in isolation — write a test, instantiate the block, drive its inputs, assert its outputs.

### A composed station

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
    Mode      : REFERENCE TO FB_ModeManager;     // injected
    Alarm     : I_AlarmHandler;                  // injected
    Sequencer : FB_StepSequencer;                // composed
    Watchdog  : FB_TimeoutWatchdog;              // composed
    _Accumulated : LREAL;
END_VAR

METHOD FB_Init : BOOL
VAR_INPUT
    bInitRetains  : BOOL;
    bInCopyCode   : BOOL;
    ModeRef       : REFERENCE TO FB_ModeManager;   // dependency
    AlarmHandler  : I_AlarmHandler;                // dependency
END_VAR
    Mode  REF= ModeRef;
    Alarm := AlarmHandler;
    Sequencer.SetStepName(0,  'Idle');
    Sequencer.SetStepName(10, 'Filling');
    Sequencer.SetStepName(20, 'Complete');
    FB_Init := TRUE;
END_METHOD

METHOD Execute : BOOL                              // I_Sequenceable
    Watchdog.CyclicUpdate();
    IF Watchdog.TimedOut THEN
        Alarm.RaiseAlarm(Code := 1000, Text := 'Fill: Timeout');
        RETURN;
    END_IF
    CASE Sequencer.CurrentStep OF
        0:
            OpenFillValve := FALSE;
            _Accumulated  := 0.0;
            Watchdog.Reset();
            IF Mode.AllowRun AND PartPresent THEN
                Sequencer.TransitionTo(10);
                Watchdog.Enable := TRUE;
                Watchdog.Duration := T#10S;
            END_IF
        10:
            OpenFillValve := TRUE;
            IF FlowRate < 0.1 THEN
                Alarm.RaiseAlarm(Code := 1001, Text := 'Fill: No flow detected');
            END_IF
            _Accumulated := _Accumulated + (FlowRate * 0.001);
            IF _Accumulated >= TargetVolume THEN
                Sequencer.TransitionTo(20);
            END_IF
        20:
            OpenFillValve := FALSE;
            Watchdog.Enable := FALSE;
            Sequencer.MarkComplete();
    END_CASE
    Execute := TRUE;
END_METHOD

(* Reset / Abort methods + 7 property GETs delegating to Sequencer / Alarm *)
```

The station is a **thin coordinator** that wires its inputs into the building blocks and exposes the right interfaces. The actual sequencing logic is small because the building blocks do the heavy lifting.

### MAIN's wiring

```iecst
PROGRAM MAIN
VAR
    // shared services
    ModeManager  : FB_ModeManager;

    // per-station alarm strategies — different policies for different stations
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

**The construction is the architecture.** What gets injected into each station determines how it behaves. Swapping `InspectAlarm` from `LineFault` to `QualityFlag` changes the entire alarm policy of the Inspect station — the station code never changes.

---

## Cost / benefit analysis

### When composition is the right answer

Composition is **the correct architectural choice** when:

- **Stations need different runtime behaviors that share an interface** — different alarm policies, different sequencer topologies, different logger destinations
- **Your team is multi-engineer** (5+) over a multi-year horizon — interface contracts protect against drift between teams
- **Test-driven development is a goal** — composition is the prerequisite for unit-testable PLC code via mock injection
- **The codebase is a product, not a project** — multiple machines / customers / configurations, each combining the same primitives differently
- **Customer-driven requirement variation** is high — different sites / SKUs / regulatory contexts demand swappable behavior

If those are true, composition gives you wins inheritance can't:

- **No base-class dead weight** — Cap and Label don't carry `LogBuffer` storage if they don't need logging
- **Runtime-swappable strategies** — change alarm policy via instantiation, not subclassing
- **Liskov-substitutability is automatic** — any `I_AlarmHandler` works anywhere `I_AlarmHandler` is expected; no carve-out children
- **Testability is structural, not opt-in** — every station accepts its dependencies; mocks fit the same contracts as real implementations
- **Adding a new strategy is purely additive** — write a new FB implementing the interface; no existing code is touched

### When composition is overkill

Composition is **the wrong choice** when:

- **Single-customer integration** — you're customizing one machine; nobody will ever swap a strategy
- **Tiny codebase** (< 1000 lines) — the interface ceremony costs more than it saves
- **Solo engineer** — there's nobody to drift away from; composition's enforcement value is wasted
- **Short lifespan** (< 2 years to decom) — composition's compounding-time savings don't get to compound
- **Team unfamiliar with OOP** — reading a Stage 3 codebase requires understanding interfaces, REFERENCE TO, FB_init params; if your team isn't there yet, the cognitive cost is real

For those use cases, **Stage 1 (procedural) or Stage 2 (inheritance) is the right answer.** The workshop respects this; it's not advocating composition universally.

### What CR-2 reveals about composition's strength

CR-2 — Inspect needs non-latching alarm AND parallel state-10 — was the breaking point in Stage 2. In Stage 3 it's a 4-line change:

1. **In MAIN** (1 line): `InspectAlarm : FB_AlarmHandler_QualityFlag;` (was `LineFault`)
2. **Inside `FB_StationInspect`** (3 lines + state-10 rework): compose `FB_ParallelSequencer`, configure for 2 branches, rework state 10 to use it

**No other stations are touched.** Cap, Label, Fill don't know any of this happened. The Strategy pattern (alarm) and the internal sequencer change are completely hidden behind interfaces. The HMI boundary is unaffected because all stations still expose `I_HmiReportable` with the same property shape.

The architectural property that makes this possible is **the Open/Closed principle**: the system is open to extension (adding `FB_AlarmHandler_QualityFlag` is purely additive — no existing code changed) but closed to modification (`I_AlarmHandler` doesn't change shape, no station code is rewritten).

### What CR-1 reveals about composition's elegance

CR-1 — add Pause with Fill mid-cycle exception — costs 6 lines on `FB_ModeManager` and 1 wire in MAIN. **Stations are not touched.**

```iecst
// FB_ModeManager — full diff for CR-1
+ ModePause : BOOL;          // VAR_INPUT
+ IF ModePause THEN _Mode := 3; ELSIF ...   // CyclicUpdate
+ PROPERTY IsPaused : BOOL    // optional opt-in
+ GET => IsPaused := (_Mode = 3);
```

The Fill mid-cycle exception is **automatic** because Fill's state-10 logic doesn't gate on `Mode.AllowRun` once started — it gates on `Accumulated >= TargetVolume`. **The abstraction handled the exception correctly without any per-station code.**

This is the deeper composition lesson: **good interface contracts encode the right behavior so callers don't have to.** `Mode.AllowRun` returning `FALSE` when paused prevents new cycles from starting. Once started, a cycle isn't checking `AllowRun` again — it's making progress. The right gating point was already where it needed to be; CR-1 didn't have to add new gating logic anywhere.

### What CR-3 reveals about composition's symmetry

CR-3 — selective logging in Fill and Inspect only — costs:

- 1 field + 1 FB_init param on Fill (1 station, ~3 lines)
- 1 field + 1 FB_init param on Inspect (1 station, ~3 lines)
- 1 instance + 2 wires in MAIN (~3 lines)

**Cap and Label pay nothing.** They don't carry a logger field, don't take a logger init param, don't allocate buffer memory, don't update FB_init signatures. The cost is exactly proportional to what's used.

When the logger implementation changes — file storage → ADS database → MQTT telemetry — only `FB_CycleDataLogger` is replaced. The stations and MAIN don't move. **The Strategy pattern has saved a future refactor that would be expensive in Stage 1 (refactor all logging-using stations) or Stage 2 (refactor the base + every override).**

### The diff numbers (your blast radius scoreboard)

| CR | Files | Lines added | Lines removed | What it touched |
|---|---|---|---|---|
| **CR-1 Pause** | 2 | 19 | 6 | `FB_ModeManager` + MAIN; stations untouched |
| **CR-2 Inspect quality + parallel** | 2 | ~30 | ~10 | One MAIN line + Inspect's internal sequencer swap; other stations untouched |
| **CR-3 Selective logging** | 3 | 32 | 11 | Fill + Inspect (logger DI) + MAIN; Cap and Label untouched |

Compared to Stage 2:

- **CR-1**: 19 vs 65 lines (3.4x cheaper, 0 station risk vs full base-class pollution)
- **CR-2**: ~30 vs 121 lines (4x cheaper, 0 base-class drift vs `SUPER`-can't-be-called fragility)
- **CR-3**: 32 vs 64 lines (2x cheaper, 0 dead weight vs 12KB of unused buffer per Cap and Label)

**The composition scoreboard wins on every cell.** But the scoreboard wins matter most when you can articulate *why* — the wins aren't accidents; they're properties of the interface contracts and the Open/Closed principle.

---

## Complete how-to walkthrough

### Step 1 — Survey the architecture

```fish
git switch stage-3-composition
explorer NEM2026/NEM2026.sln
```

Open the solution. Note the **18 source files** organized into `Interfaces/`, `BuildingBlocks/`, `Stations/`. Compare to Stage 1's 5 files and Stage 2's 6 — there's more *number* of files, but each is *smaller and focused*.

Open files in this order:

1. **An interface** — `I_AlarmHandler.TcPOU`. Notice: METHOD declarations + PROPERTY declarations, no implementations. Just contracts.
2. **A building block** — `FB_AlarmHandler_LineFault.TcPOU`. Notice: tiny FB (~50 lines), implements `I_AlarmHandler`, body is empty, all behavior is in methods.
3. **The other strategy** — `FB_AlarmHandler_QualityFlag.TcPOU`. Notice: same shape, opposite policy. `StopsLine := FALSE`. Look at its `Acknowledge` — it's a no-op because quality flags auto-clear.
4. **A station** — `FB_StationFill.TcPOU`. Notice: implements two interfaces, has `Mode` and `Alarm` as injected dependencies, composes `Sequencer` and `Watchdog` internally, and all properties delegate to those building blocks.
5. **MAIN** — see how the construction wires everything together.

!!! tip "Pause and ask yourself"
    What if you wanted to add a 5th alarm strategy (say, a stop-then-confirm-restart policy)? You'd write `FB_AlarmHandler_StopThenConfirm` implementing `I_AlarmHandler`. You wouldn't touch any stations, any other alarm handlers, or the interface itself. **That's the Open/Closed principle made concrete.**

### Step 2 — Run the line

`F7` to build, then activate / login / start. Same inputs drive the same workflow as Stages 1 and 2. **Runtime behavior is the same; the architecture is what changed.**

### Step 3 — Apply CR-1 the composition way

```fish
git switch stage-3-composition
```

CR-1: add Pause with Fill mid-cycle exception.

**Exercise:** add `ModePause` to `FB_ModeManager`. That's it. Stations are not touched. Don't even open them.

Edit `FB_ModeManager.TcPOU`:

- Add `ModePause : BOOL` to the `VAR_INPUT`
- Add `ELSIF ModePause THEN _Mode := 3;` to `CyclicUpdate`
- Optionally add a `PROPERTY IsPaused : BOOL` returning `(_Mode = 3)` — useful for stations that want to opt in

Then in MAIN:

- Add `ModePause : BOOL;` to `VAR`
- Add `ModeManager.ModePause := ModePause;` to the cyclic implementation

Build. Done.

```fish
git switch stage-3-cr1-applied
git diff stage-3-composition --stat
```

2 files, +19/-6. **Notice: zero station files modified.** The Fill mid-cycle exception is automatic — Fill's state-10 doesn't gate on `Mode.AllowRun`, so once started it keeps going regardless of pause.

This is the moment a thoughtful FAE pauses and feels the architectural difference. **Compare to Stage 2's `AllowPause` virtual + Fill override** (3 files, +65/-48). Same requirement, very different diffs.

### Step 4 — Apply CR-2 — the headline swap demo

```fish
git switch stage-3-composition
```

CR-2: Inspect needs non-latching alarm + parallel state-10.

**Exercise (Part A — the strategy swap):** Open MAIN. Find:

```iecst
InspectAlarm : FB_AlarmHandler_LineFault;
```

Change it to:

```iecst
InspectAlarm : FB_AlarmHandler_QualityFlag;
```

That's the entire alarm-policy change. **One line.**

Build. The compile passes. The Inspect station's alarm behavior has *fundamentally changed* — alarms now flag without latching, and `IsFaulted` returns FALSE because `QualityFlag.StopsLine = FALSE`. **No Inspect code was modified.**

This is the workshop's headline moment. Pause here. Let the implication sink in. **Then ask: did you write any new code? Did Inspect's behavior change? Yes — because the alarm strategy is injected, not hardcoded.**

**Exercise (Part B — the parallel sequencer):** Inspect also needs parallel state-10. Open `FB_StationInspect.TcPOU`:

- Add `Parallel : FB_ParallelSequencer;` to `VAR`
- In `FB_Init`, after the existing logic, add `Parallel.Configure(NumberOfBranches := 2);`
- In `Execute`'s `CASE Sequencer.CurrentStep OF`, find state 10 (single-branch camera trigger) and rework it to use `Parallel.MarkBranchDone(BranchIndex := 0)` for camera and `MarkBranchDone(BranchIndex := 1)` for reject pre-arm; transition to state 20 when `Parallel.AllBranchesComplete`

When done:

```fish
git switch stage-3-cr2-applied
git diff stage-3-composition --stat
```

2 files, ~30 added / ~10 removed. **Notice: only Inspect and MAIN are modified.** Cap, Label, Fill are completely untouched. The change is internal to Inspect (sequencer swap) and external at the construction boundary (alarm strategy).

This is **what the workshop is selling**: same requirements as Stage 2, ~25% the line count, zero risk to other stations.

### Step 5 — Apply CR-3 the composition way

```fish
git switch stage-3-composition
```

CR-3: selective logging in Fill and Inspect only.

**Exercise:** add `Logger : I_DataLogger;` field to Fill and Inspect (only). Update their `FB_Init` signatures to accept `DataLogger : I_DataLogger`. Add the `Logger.LogCycleData(...)` call at each station's terminal "Complete" state.

In MAIN:

- Add `CycleLogger : FB_CycleDataLogger;` to `VAR`
- Update Fill's instantiation: `StationFill : FB_StationFill(ModeRef := ..., AlarmHandler := ..., DataLogger := CycleLogger);`
- Same for Inspect
- **Don't touch Cap or Label.** They keep their original 4-arg `FB_Init` signature.

When done:

```fish
git switch stage-3-cr3-applied
git diff stage-3-composition --stat
```

3 files, +32/-11. **Notice: Cap and Label are byte-for-byte unchanged.** They don't carry the logger field; their FB_Init signature didn't grow; they don't pay any cost.

### Step 6 — See the broken-the-wrong-way branch

```fish
git switch stage-3-broken
```

This branch shows what happens when you apply CR-1 *the wrong way* in Stage 3 — by adding `ModePause` to every station's `VAR_INPUT` and per-station guard logic in `Execute`. Compiles fine. Behavior is *worse* than the right way: Fill halts mid-cycle (the very failure mode CR-1 was supposed to avoid), and the change is now five files instead of one.

```fish
git diff stage-3-composition stage-3-broken --stat
# 5 files, +33 lines
```

**The lesson:** even composition can be applied poorly if you don't trust the abstraction. The right answer is to extend the shared service (`FB_ModeManager`), not to scatter logic across stations.

This is the moment to highlight: **architecture matters, but so does discipline.**

### Step 7 — See the all-3-CRs end state

```fish
git switch stage-3-complete
```

```fish
git diff stage-3-composition stage-3-complete --stat
# 4 files, +52 lines added, ~15 removed
```

`FB_ModeManager` has Pause. `FB_StationFill` and `FB_StationInspect` have logger DI. MAIN has the logger instance and the additional wires. **No interface ever changed. No existing strategy was modified.** The system grew purely by adding new capabilities at the boundaries.

### Step 8 — Reflect

Before declaring victory, ask yourself:

1. **What's the line count for the entire CR-1 + CR-2 + CR-3 diff in Stage 3 vs. Stage 1?** Stage 3: ~70 lines net. Stage 1: ~150 lines net. Roughly half — but the *kind* of change is what matters. Stage 3's lines are pure additions; Stage 1's lines are scattered modifications.

2. **What would adding station 5 cost?** Roughly 200 lines for a new station FB (composing the same building blocks Fill / Cap / Label / Inspect already use), plus 1 alarm strategy instance + 1 station instance + 1 wire in MAIN. **No existing code is modified.** Compare to Stage 1's "copy-paste-then-fix" cost.

3. **What's the testability story?** A PlcTestSuite test can `FB_StationFill(ModeRef := MockMode, AlarmHandler := MockAlarm, DataLogger := MockLogger)` — every dependency is a mock. Drive the inputs, assert the outputs. **Real test isolation, on real PLC code, with real semantics.** That's what composition buys that inheritance can't.

---

## When to apply each pattern by name

The patterns this stage demonstrates are documented in detail on the [Patterns by name](../patterns.md) page. A quick reference for what's where:

| Pattern | Where it lives in this stage |
|---|---|
| **Strategy** | `I_AlarmHandler` with two implementations; `FB_StepSequencer` ↔ `FB_ParallelSequencer` swap |
| **Template Method** | (Not used in Stage 3 — Stage 2's territory) |
| **Dependency Injection** | `FB_Init` extended params on every station |
| **Interface Segregation** | `I_Sequenceable` vs `I_HmiReportable` — different consumers see different surfaces |
| **Open-Closed Principle** | Adding a new alarm strategy = new FB implementing the interface; existing code unchanged |
| **State** | `FB_StepSequencer` owns `CurrentStep` + step-name table — the GoF State pattern, flat-table dialect |

The workshop teaches these by doing first, then names them. The names matter for one reason: **you'll talk to software engineers, customers, and reviewers about these designs, and the vocabulary is universal across software engineering.**

---

## Branches in this stage

**Current structure (`Release` family) — Stage 3 lives in `FillingLine_Composition/`:**

| Branch | What FillingLine_Composition shows |
|---|---|
| `Release` | Full architecture; Inspect uses `LineFault` + `StepSequencer` like other stations |
| `cr1-applied` | `FB_ModeManager` only — 6 lines + 1 wire |
| `cr2-applied` | 1 line in MAIN + ~3 lines internal Inspect — the headline swap demo |
| `cr3-applied` | Logger DI to Fill + Inspect only |
| `complete` | The composition endgame — all 3 CRs cumulative |

To compare a CR's cost on this paradigm only:
```fish
git diff Release...cr2-applied --stat -- NEM2026/FillingLine_Composition/
```

**Legacy single-PLC branches (still present as a historical record, used by the walkthrough above):**

| Branch | Role | Forks from | One-line summary |
|---|---|---|---|
| `stage-3-composition` | Clean baseline | `main` | Full architecture; Inspect uses `LineFault` + `StepSequencer` like other stations |
| `stage-3-broken` | Pedagogical CR-1 wrong way | `stage-3-composition` | Per-station Pause guard duplicated 4 times — compiles, halts Fill mid-cycle |
| `stage-3-cr1-applied` | CR-1 answer key | `stage-3-composition` | `FB_ModeManager` only — 6 lines + 1 wire |
| `stage-3-cr2-applied` | CR-2 swap demo | `stage-3-composition` | 1 line in MAIN + ~3 lines internal Inspect — the headline |
| `stage-3-cr3-applied` | CR-3 answer key | `stage-3-composition` | Logger DI to Fill + Inspect only |
| `stage-3-complete` | All 3 CRs end state | `stage-3-composition` | The composition endgame |
