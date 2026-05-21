# Patterns by name

Most controls engineers use these every day without naming them. The workshop's quiet payoff is the vocabulary — once you have names for the patterns, you can:

- Read Beckhoff's framework code (it uses these)
- Talk to software engineers without translating
- Recognize the same shapes in C# / Java / Python
- Cite the design rationale in code reviews

This page names what you saw. Demonstrated patterns first, then adjacent ones worth knowing about.

---

## Demonstrated in this codebase

### Strategy

> *Same contract, swappable implementations, picked at construction.*

The CR-2 demonstration is the textbook example. Two FBs both implement `I_AlarmHandler`:

| `FB_AlarmHandler_LineFault` | `FB_AlarmHandler_QualityFlag` |
|---|---|
| Latches `_Latched := TRUE` on `RaiseAlarm` | Sets `_Flagged := TRUE`, doesn't latch |
| `R_TRIG` edge detection on `Acknowledge.AckInput` | `Acknowledge` is a no-op |
| `StopsLine := TRUE` | `StopsLine := FALSE` |

The station code is **identical** for both. It calls `Alarm.RaiseAlarm(...)`, reads `Alarm.HasActiveAlarm`, consults `Alarm.StopsLine` for `IsFaulted`. Which strategy it has is a MAIN-construction-time decision:

```iecst
// FillingLine_Composition on Release (default)
InspectAlarm : FB_AlarmHandler_LineFault;

// FillingLine_Composition on cr2-applied (the swap)
InspectAlarm : FB_AlarmHandler_QualityFlag;
```

**One-line swap, zero station code change.** That's the GoF Strategy pattern in 4 IEC characters.

The same shape applies elsewhere in the codebase:

- `I_DataLogger` could have multiple implementations: `FB_CycleDataLogger` (production), `FB_NullLogger` (no-op for tests), `FB_FileLogger` (writes via `SysFile`), `FB_TcEventLogger` (publishes via Tc3 EventLogger). Today only one exists, but adding more requires no station changes.
- The `FB_StepSequencer` ↔ `FB_ParallelSequencer` swap inside Inspect is also Strategy at the building-block level.

**When you reach for it:** any time a class needs to change behavior at runtime based on configuration, environment (test vs. production), or data type. Strategy is one of the most useful patterns in PLC code because the test/production split is so common.

---

### Template Method

> *Base class defines the skeleton; subclasses fill in the gaps.*

Stage 2's `FB_StationBase` is the canonical Template Method:

```iecst
METHOD PUBLIC CyclicLogic   // the TEMPLATE
    IF NOT _InitComplete THEN
        _InitComplete := Initialize();
        RETURN;
    END_IF
    SUPER^.CyclicLogic();        // framework Monitoring etc.
    THIS^.ExecuteSequence();     // ← virtual hook (children fill in)
    THIS^.UpdateHmiStatus();
END_METHOD

METHOD PROTECTED ExecuteSequence  // VIRTUAL — empty default
END_METHOD

METHOD PROTECTED GetStepName : STRING(40)  // VIRTUAL — generic default
    CASE State OF
        0:  GetStepName := 'Idle';
    ELSE
        GetStepName := 'Running';
    END_CASE
END_METHOD
```

`CyclicLogic` is the *template* — it defines the order of operations. `ExecuteSequence` and `GetStepName` are *hooks* that concrete stations override.

This is what classic OOP teaching means by "favor inheritance for IS-A relationships." A `FB_StationFill` IS-A `FB_StationBase` — it just specializes the sequence and step names.

**When Template Method is the right answer:** when the behavior of a family of classes shares a fixed skeleton and only varies in specific phases. Lifecycle hooks (`Init`, `Cyclic`, `Reset`, `Exit`) are the canonical place. Beckhoff's `FB_ComponentBase` and `FB_PackML_BaseModule` are full of Template Method — `Starting`, `Aborting`, `Holding`, `Resetting`, etc. are all virtual hooks the framework calls in a fixed order.

**When it's the wrong answer:** when classes need to vary behavior in *unexpected* ways or *combine* multiple variations. CR-2 (Inspect quality + parallel) is exactly that case — it has two axes of variation that don't fit the Template Method skeleton, which is why Stage 2 cracks under it.

---

### Dependency Injection

> *What you need arrives at construction. Don't reach for it.*

Stage 3's stations declare what they need via `FB_Init`:

```iecst
METHOD FB_Init : BOOL
VAR_INPUT
    bInitRetains  : BOOL;          // standard TwinCAT
    bInCopyCode   : BOOL;          // standard TwinCAT
    ModeRef       : REFERENCE TO FB_ModeManager;   // injected
    AlarmHandler  : I_AlarmHandler;                // injected
    DataLogger    : I_DataLogger;                  // injected (CR-3)
END_VAR
```

MAIN provides those dependencies at instance declaration:

```iecst
StationFill : FB_StationFill(ModeRef     := ModeManager,
                             AlarmHandler := FillAlarm,
                             DataLogger   := CycleLogger);
```

Beckhoff calls this **"extended FB_Init"** in the documentation; the rest of software engineering calls it **constructor injection**. They're the same thing.

**Why it matters:** the station has no globals to hunt down, no Service Locator to query, no implicit assumptions about which alarm handler is in scope. What it needs is **declared in its signature** and **provided at construction**. That makes the station:

- **Trivially testable** — pass mock implementations in a test rig
- **Trivially swappable** — change the strategy without touching the consumer
- **Self-documenting** — read the `FB_Init` signature, you know what the station depends on

**When DI is overkill:** for FBs that don't have variant dependencies (a `TON` doesn't need DI). For FBs whose dependencies never change. The cost of DI is one extra line per dependency at construction; if you'll never swap, the cost is wasted.

In practice, controls engineers underuse DI. The cost is small and the testability win is large.

---

### State pattern

> *Every CASE OF State pattern you've ever written.*

The PLC dialect of the GoF State pattern is the flat `CASE State OF` table:

```iecst
CASE State OF
    0:  // Idle
        IF Execute THEN State := 10; END_IF
    10: // Filling
        OpenFillValve := TRUE;
        IF Accumulated >= TargetVolume THEN State := 20; END_IF
    20: // Complete
        OpenFillValve := FALSE;
        Done := TRUE;
END_CASE
```

The GoF version would create one class per state with a polymorphic `Transition` method. The PLC version uses a flat integer because:

- PLCs love deterministic scan times — the `CASE` compiles to a jump table
- You can see the whole machine on one page
- Debugging is faster — set a breakpoint at `State := X` and you've found the transition

**Both versions are correct.** Knowing the GoF name helps when you watch C# / Java engineers do the same problem differently — they'll talk about `IState` interfaces and state transitions; you should be able to translate "that's just a flat CASE in PLC."

The State pattern lives at the heart of every station in this workshop. Stage 1 and Stage 2 use plain CASE. Stage 3 introduces `FB_StepSequencer` (which owns the State variable + names the steps) — that's a step toward the GoF version, but still flat at heart.

---

### Interface Segregation

> *Don't make a client depend on methods it doesn't use.*

Stage 3 splits station behavior into two interfaces:

- `I_Sequenceable` — `Execute`, `Reset`, `Abort` + `IsComplete` / `IsFaulted` / `StateName`
- `I_HmiReportable` — `StatusText` / `StateNumber` / `AlarmActive` / `AlarmMessage`

A station implements both. But a consumer that only displays state on the HMI **only takes `I_HmiReportable`** — it can't accidentally call `Execute` or `Reset`. That's Interface Segregation.

This shows up in production when you have multiple HMI screens, a recipe management system, and a fault diagnostic dashboard all looking at the same stations. Each screen sees only the interface relevant to its role. **Privacy via type, enforced at compile time.**

---

### Open-Closed Principle

> *Open for extension, closed for modification.*

Adding a new alarm policy in Stage 3:

```iecst
FUNCTION_BLOCK FB_AlarmHandler_RetryWithExponentialBackoff
    IMPLEMENTS I_AlarmHandler
    // ... new behavior, new code
END_FUNCTION_BLOCK
```

**Existing code doesn't change.** Stations don't know about the new strategy. MAIN can opt into it for one station without affecting others. The `I_AlarmHandler` interface is **closed** to modification (you don't change it) but the system is **open** to extension (you add new implementations).

Compare to Stage 2: adding a fundamentally new alarm policy means modifying the base class (which all children inherit) — **modification**, not extension.

---

## Adjacent patterns worth knowing

These aren't demonstrated as branches but live in the same neighborhood. Beckhoff's own libraries use them, and they'll come up in production if your codebase grows.

### Visitor

> *Do operation X across a heterogeneous collection without modifying the elements.*

The Beckhoff Core libraries use Visitor heavily — patterns like `ChangeStateOnAllSubModules`, `SetOverrideVisitor`, `HmiEnableDisableAllVisitor`, and `ForceVisitor` are the canonical shape.

The mental model: an aggregator FB walks the parent module's child components and applies an operation. Useful for:

- "Compute total alarm severity across all stations"
- "Flush all data loggers at end-of-shift"
- "Reset every `I_Sequenceable` in the line"

**Why we don't demo it in this workshop:** Visitor needs a way to enumerate the children (an array, a parent module's component list, etc.). Our 4 stations are flat-named instances in MAIN; adding the enumeration plumbing would be an extra layer the workshop doesn't have time for. If you want to extend the workshop, `FB_AlarmSnapshotVisitor` is the natural follow-up.

### Adapter

> *Make a vendor FB look like your interface.*

You'll need this the first time you wire a third-party library to your `I_Sequenceable` or `I_AlarmHandler` contract. Wrap the vendor's FB in an FB that implements your interface and translates calls:

```iecst
FUNCTION_BLOCK FB_ThirdPartyMotionAdapter IMPLEMENTS I_Sequenceable
VAR
    _vendor : ThirdParty_PositionerFB;
END_VAR
METHOD Execute : BOOL
    _vendor.bStart := TRUE;
    _vendor();
    Execute := _vendor.bDone;
END_METHOD
```

Adapter is what makes vendor lock-in survivable. Switch vendors, write a new adapter, the rest of your code doesn't move.

### Observer

> *One event, many listeners.*

The Tc3 `Tc3_EventLogger` library is essentially Observer — components publish events, listeners (HMI screens, fault diagnostic dashboards, telemetry exporters) subscribe.

In production, Observer shows up when one event needs to fan out: an alarm should update the HMI, log to disk, send a Tc3 message, and possibly trigger downstream rejection. Observer keeps the publisher unaware of who's listening.

We don't demo this directly — the Tc3 EventLogger machinery handles it.

### Singleton

> *One instance, project-wide access.*

`FB_ModeManager` in our Stage 3 design behaves like a Singleton: one instance in MAIN, every station references it. This is a controlled use — modes really are project-wide.

Singleton is **as much an antipattern as a pattern** when overused. The temptation is to make everything a singleton ("I'll just put it in a global"), which kills testability. Use sparingly, and prefer DI even when there's only one instance.

---

## What this means for a controls engineer

You already know the moves. The patterns above aren't replacements for what you do — they're **names** for choices you make every day.

The big idea isn't that composition is morally superior to procedural code. The big idea is that **composition is a tool that pays for itself when your codebase outgrows what one engineer can hold in their head**. The scoreboard tells you when that's happened.

If your shop is moving toward TDD/CI for control code, composition isn't optional anymore — it's the prerequisite for testable PLC. If your shop is shipping one-off integrations, procedural is probably fine.

Knowing the names lets you have the conversation about which is right for your situation.
