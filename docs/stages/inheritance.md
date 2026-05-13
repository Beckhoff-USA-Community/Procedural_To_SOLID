# Stage 2 — Inheritance

**Branches:** `stage-2-inheritance`, `stage-2-broken`, `stage-2-cr1-applied`, `stage-2-cr2-applied`, `stage-2-cr3-applied`, `stage-2-complete`

---

## The OOP-inheritance paradigm

### Origin and theory

Object-oriented programming was conceived in **Simula 67** at the Norwegian Computing Center in the late 1960s. Ole-Johan Dahl and Kristen Nygaard introduced the concept of a **class** as a template for objects, and **inheritance** as a way for one class to be a "kind of" another. **Smalltalk** at Xerox PARC in the 1970s formalized message-passing and dynamic dispatch. C++ (1985) and Java (1995) brought OOP to mainstream industry.

The core inheritance idea is the **IS-A relationship**:

> *"A `FB_StationFill` IS-A `FB_StationBase`. So everything `FB_StationBase` knows how to do, `FB_StationFill` also knows how to do — except where it overrides specifically."*

This is enormously powerful. If you have a hundred objects that share 80% of their behavior and differ in 20%, inheritance lets you write the 80% once on a base class and the 20% on derived classes. Polymorphism (specifically **late binding** via virtual methods) means a caller holding a `FB_StationBase` reference can invoke methods that automatically resolve to the right derived implementation at runtime.

The 1994 *"Design Patterns"* book by the **Gang of Four** codified the *Template Method* pattern — base class defines the algorithm skeleton, subclasses fill in the gaps via virtual hooks. That's the canonical inheritance use, and it's exactly what `FB_StationBase` does in this stage.

### The inheritance mental model

When you write inheritance code, you're thinking:

> *"Same shape, different details. Capture the shape on the base; let children specialize the details. The framework calls the right method at the right time."*

In Stage 2, the "shape" is the lifecycle — initialize → cyclic check → execute sequence → reset. Every station shares this shape. The "details" are the specific sequence each station runs. So `FB_StationBase` defines the shape (`CyclicLogic` is the template), and `FB_StationFill` / `FB_StationCap` / `FB_StationLabel` / `FB_StationInspect` fill in the blanks via `ExecuteSequence` and `GetStepName`.

### Where TwinCAT inheritance comes from

TwinCAT 3 added OOP to IEC 61131-3 in the 2010s — `EXTENDS`, `IMPLEMENTS`, `METHOD`, `PROPERTY`, `THIS^`, `SUPER^`. **All methods are virtual by default** unless declared `FINAL`. Visibility is controlled by `PUBLIC` / `PROTECTED` / `PRIVATE` / `INTERNAL`. The framework can layer on top: SPT-Libraries (Beckhoff USA Community), the older `FB_PackML_BaseModule` from Tc3_PackML_V3, custom shop-specific bases.

The Stage 2 of this workshop sits on top of the **SPT-Libraries' `FB_ComponentBase`**, which is itself a Template Method base. The SPT framework defines:

- **`Initialize`** — called once on first scan, returns `BOOL` (multi-cycle init pattern)
- **`CyclicLogic`** — the cyclic entry point; calls `Initialize` then `Monitoring` then user-overrides
- **`Monitoring`** — for raising alarms based on conditions
- **`Reset`** — clears errors, multi-cycle
- **`CreateEvents`** — initialization of `FB_TcAlarm` arrays for production alarm wiring
- Built-in fields: `_InitComplete`, `_Error`, `_ErrorID`, `_Busy`, `_CurrentAlarmSeverity`, `Name`

Our `FB_StationBase` extends this and adds station-specific shape: a `State` integer, a `Timeout` TON, alarm latching, mode resolution, an `ExecuteSequence` virtual hook, a `GetStepName` virtual hook.

### Critical TwinCAT-specific mechanics

Three idioms you must understand to read Stage 2:

**1. `THIS^` and `SUPER^`** — method calls inside an FB

```iecst
THIS^.ExecuteSequence();   // calls THIS instance's ExecuteSequence
                           // — virtual dispatch, finds the most-derived override
SUPER^.CyclicLogic();      // calls the BASE class's CyclicLogic explicitly
                           // — bypasses virtual dispatch, used to call up the chain
```

If `FB_StationBase` overrides `Monitoring` and `FB_StationInspect` overrides `Monitoring` further, then `THIS^.Monitoring()` from anywhere calls Inspect's version. `SUPER^.Monitoring()` from inside Inspect's override calls `FB_StationBase`'s version. The `^` is dereference (these are pointers to the FB instance).

**2. The Initialize idiom** — multi-cycle init

```iecst
METHOD PUBLIC CyclicLogic
    IF NOT _InitComplete THEN
        _InitComplete := Initialize();   // returns FALSE while still initializing
        RETURN;                          // skip cyclic logic until init done
    END_IF
    SUPER^.CyclicLogic();
    THIS^.ExecuteSequence();
END_METHOD
```

`Initialize` may need multiple scans to complete (registering child components, setting up alarms, etc.). The `_InitComplete` gate ensures we don't run cyclic logic until initialization is fully done.

**3. The `(Name := 'X')` instantiation idiom** — extended `FB_init`

```iecst
StationFill : FB_StationFill := (Name := 'Fill');
```

This passes `'Fill'` to `FB_StationFill`'s extended `FB_init` method. The SPT base uses `Name` for diagnostic prefixes ("Fill: Timeout") and event-logger string parameters. **Every station instance gets a unique name** so its alarm events are distinguishable in the event log.

---

## How inheritance is constructed in this workshop

### File layout (6 files)

```
NEM2026/FillingLine/POUs/
├── FB_StationBase.TcPOU       ~165 lines — abstract base
├── FB_StationFill.TcPOU       ~65 lines — extends Base
├── FB_StationCap.TcPOU        ~75 lines — extends Base
├── FB_StationLabel.TcPOU      ~75 lines — extends Base
├── FB_StationInspect.TcPOU    ~85 lines — extends Base
└── MAIN.TcPOU                 ~80 lines — instantiates and drives all four
```

Total: ~545 lines. Roughly the same as Stage 1 — the inheritance refactor compresses duplication but introduces the base class. **The win isn't in lines; the win is in eliminating the cross-station drift.**

### `FB_StationBase` — the Template Method

```iecst
FUNCTION_BLOCK FB_StationBase EXTENDS SPT_Components.FB_ComponentBase
VAR_INPUT
    Execute      : BOOL;
    ModeAuto     : BOOL;
    ModeManual   : BOOL;
    PartPresent  : BOOL;
    AlarmAck     : BOOL;
END_VAR
VAR_OUTPUT
    Done         : BOOL;
    StatusText   : STRING(80);
    StateDisplay : INT;
    AlarmActive  : BOOL;
    AlarmText    : STRING(255);
END_VAR
VAR
    State        : INT;
    Timeout      : TON;
    AlarmLatched : BOOL;
    AlarmAckEdge : R_TRIG;            // standardized for everyone — drift fixed
    AlarmCode    : UDINT;
    ActiveMode   : INT;
END_VAR
```

The methods, with their roles:

| Method | Visibility | Override expectation | Purpose |
|---|---|---|---|
| `CyclicLogic` | PUBLIC | Children may override but usually shouldn't | The cyclic entry point — calls Initialize, then framework chain (Monitoring etc), then ExecuteSequence + UpdateHmiStatus |
| `Monitoring` | PROTECTED | Children may override to add station-specific alarm conditions; should call `SUPER^.Monitoring()` | Mode resolution + alarm-ack (lives here once, instead of in every station) |
| `Reset` | PUBLIC | Children may override to add station-specific reset behavior; should call `SUPER^.Reset()` | Multi-cycle clear of state + alarms |
| `ExecuteSequence` | PROTECTED | **Children must override** | Empty default — concrete station provides the CASE state machine |
| `GetStepName` | PROTECTED | **Children should override** | Returns 'Idle' / 'Running' generically; child returns step-specific names |
| `RaiseStationAlarm(Code, Text)` | PROTECTED | Helper — children call it | Latches alarm, sets `_Error` |
| `TransitionTo(NextStep)` | PROTECTED | Helper — children call it | Single point for state transitions |
| `UpdateHmiStatus` | PROTECTED | Children rarely override | HMI string mapping using `GetStepName` |

### `FB_StationFill` — example child

The child is now tiny:

```iecst
FUNCTION_BLOCK FB_StationFill EXTENDS FB_StationBase
VAR_INPUT
    FlowRate     : LREAL;
    TargetVolume : LREAL;
END_VAR
VAR_OUTPUT
    OpenFillValve : BOOL;
END_VAR
VAR
    Accumulated  : LREAL;
END_VAR

METHOD PROTECTED ExecuteSequence    // OVERRIDE — the only thing Fill does differently
    CASE State OF
        0:
            OpenFillValve := FALSE;
            Accumulated   := 0.0;
            IF Execute AND PartPresent AND ActiveMode = 1 THEN
                THIS^.TransitionTo(10);
            END_IF
        10:
            OpenFillValve := TRUE;
            Timeout(IN := TRUE, PT := T#10S);
            IF Timeout.Q THEN
                THIS^.RaiseStationAlarm(1000, 'Fill: Timeout');
            END_IF
            IF FlowRate < 0.1 THEN
                THIS^.RaiseStationAlarm(1001, 'Fill: No flow detected');
            END_IF
            Accumulated := Accumulated + (FlowRate * 0.001);
            IF Accumulated >= TargetVolume THEN
                THIS^.TransitionTo(20);
            END_IF
        20:
            OpenFillValve := FALSE;
            Timeout(IN := FALSE);
            Done := TRUE;
    END_CASE
END_METHOD

METHOD PROTECTED GetStepName : STRING(40)    // OVERRIDE
    CASE State OF
        0:  GetStepName := 'Idle';
        10: GetStepName := 'Filling';
        20: GetStepName := 'Complete';
    ELSE
        GetStepName := 'Unknown';
    END_CASE
END_METHOD
```

Just 65 lines. Mode logic, alarm acknowledgment, HMI mapping, the lifecycle — all inherited. **The state machine is the only thing that varies.** That's the inheritance win.

### MAIN's invocation pattern

```iecst
StationFill    : FB_StationFill    := (Name := 'Fill');
StationCap     : FB_StationCap     := (Name := 'Cap');
StationLabel   : FB_StationLabel   := (Name := 'Label');
StationInspect : FB_StationInspect := (Name := 'Inspect');

(* in Implementation: *)
StationFill(
    Execute      := Execute,
    ModeAuto     := ModeAuto,
    ModeManual   := ModeManual,
    PartPresent  := PartFill,
    AlarmAck     := AlarmAck,
    FlowRate     := FlowRate,
    TargetVolume := TargetVolume);
StationFill.CyclicLogic();
```

**Two-step station call:** the FB body call (which populates `VAR_INPUT`s) and then `.CyclicLogic()` (which runs the framework lifecycle). This is a standard SPT pattern.

---

## Cost / benefit analysis

### When inheritance is the right answer

Inheritance is **the correct architectural choice** when:

- **Stations form a homogeneous family** — every station does the same shape of work, with only data differences
- **The lifecycle is genuinely shared** — every station has the same `init / cycle / monitor / reset` rhythm
- **The base class can be authored once and rarely change** — adding capability happens via new overrides, not base modifications
- **Cross-cutting concerns are *additive*, not *exceptional*** — every station should get the new feature; none should opt out
- **Your team is medium-sized** (3-10 engineers) and you want the consistency that a shared base enforces
- **The codebase will be maintained 3-10 years** — long enough that the consistency win compounds

If those are true, inheritance gives you **real wins**:

- **Drift elimination** — base-class shared logic can't drift between stations because it's the same code
- **Easier onboarding** — a new engineer reads the base, then reads a child, and understands a station in 20 minutes
- **Consistency enforcement** — every station has the same shape because it inherits the shape
- **Reasonable testability** — you can subclass the base for tests, override the work-doing methods, and exercise the lifecycle (better than Stage 1, worse than Stage 3)

### When inheritance starts to hurt

Inheritance breaks down when **any** of the following stops being true:

| Symptom | Root cause | What you're feeling |
|---|---|---|
| "Adding a feature for this *one* station forces a virtual flag on the base" | The base class becomes the dumping ground for per-child exceptions | Inheritance pollution — `AllowPause()` exists for one child but lives on the base forever |
| "I had to override `Monitoring` without calling `SUPER` because the base does the wrong thing" | The base's behavior contradicts a specific child's needs | The Liskov Substitution Principle is violated: this child is *not* substitutable for the base |
| "Every change to the base requires re-checking every child" | Coupling between base and children is bidirectional | The base class is a single point of failure — and a single point of consideration |
| "Two stations want to share half a feature, but inherit different bases" | Single-inheritance can't combine traits | TwinCAT (and most OOP languages) only allow one base class — this corner is permanent |
| "I want to test stations with mocked alarms but I can't" | Alarm strategy is hardcoded into base behavior | No seam for injecting different implementations at runtime |

The first symptom — the **virtual-flag-pollution** smell — is the canonical inheritance breakdown. It's what CR-1 demonstrates. The second — the **`SUPER`-can't-be-called** problem — is the harder breakdown that CR-2 demonstrates.

### What CR-2 reveals about inheritance limits

CR-2 has two axes of variation that hit Inspect simultaneously:

1. **Different alarm policy** (non-latching, doesn't stop the line)
2. **Different sequencing topology** (parallel branches in step 10)

Inheritance can handle one of these. Both at once *forces* the override of `Monitoring` to drop `SUPER` (because `SUPER` would do the wrong thing on the alarm policy), which means duplicating mode resolution and alarm-ack from the base into Inspect's override.

The cost compounds permanently:

- **Every future addition to base `Monitoring` must be manually mirrored** into Inspect's override, or Inspect silently misses it
- **HMI consumers need station-aware logic** because Inspect now exposes `QualityFlag` / `QualityCode` / `QualityText` parallel to the base's alarm fields
- **Inspect is no longer Liskov-substitutable for the base** — code that operates on `FB_StationBase` references can't safely call `.Monitoring()` and expect the documented behavior

This is **the fundamental limit of single inheritance**: you can't carve out arbitrary subsets of base behavior to keep, drop, or replace without violating substitutability. The base either does what every child needs, or it does the wrong thing for some child.

### What CR-3 reveals about inheritance limits

CR-3 — selective logging in Fill and Inspect only — exposes a different inheritance smell: **the base accumulating dead weight**.

To make selective logging work via inheritance, you put `LogBuffer` and `LogIndex` on the base, plus a virtual `LoggingEnabled : BOOL` flag (default `FALSE`). Fill and Inspect override `LoggingEnabled` to return `TRUE`. **Cap and Label inherit storage they never use.**

This is a memory cost (100 × 120 bytes per Cap and Label instance) and a cognitive cost (every reader of `FB_StationBase` has to understand why those fields exist when they don't apply to two of the four children). It compounds: the next selective-feature CR adds another field to the base, another virtual flag, another piece of dead weight in unrelated children.

This is **a fundamental limit of inheritance for cross-cutting features that don't apply uniformly**: the base ends up as the union of every child's needs, even when no single child needs everything.

### The diff numbers (your blast radius scoreboard)

| CR | Files | Lines added | Lines removed | What it touched |
|---|---|---|---|---|
| **CR-1 Pause** | 3 | 65 | 48 | Base + `AllowPause` virtual + Fill override + MAIN |
| **CR-2 Inspect quality + parallel** | 2 | 121 | 48 | Inspect `Monitoring` override (no SUPER) + parallel hack |
| **CR-3 Selective logging** | 3 | 64 | 25 | Base storage (dead weight in 2 children) + 2 child overrides |

Compared to Stage 1:

- **CR-1** is **slightly more** lines than Stage 1 (3 files vs 5, but the 65 vs 50 line count is similar) — the inheritance pollution shows up in *kind* (a virtual flag the base doesn't need) more than *quantity*
- **CR-2** is **more** lines than Stage 1 (121 vs 92) because the `Monitoring` override duplicates base behavior — and far more fragile because future base changes won't propagate
- **CR-3** is roughly **2x** lines than Stage 1 (64 vs 13), but the cost is now spread: real code on the base + dead weight in unrelated children

The inheritance scoreboard tells a more nuanced story than the procedural one. **Inheritance fixes some problems Stage 1 has (drift, duplication of mode/alarm/HMI) and creates new ones (pollution, fragility, dead weight in unrelated children).**

---

## Complete how-to walkthrough

### Step 1 — Survey the refactor

```fish
git switch stage-2-inheritance
explorer NEM2026/NEM2026.sln
```

Open `FB_StationBase` first. Read it top-to-bottom. **Notice the variables that used to be in every Stage 1 station are now here once.** That's the duplication-elimination win, made physical.

Now open `FB_StationFill`. Notice it's tiny — ~65 lines vs. ~110 in Stage 1. The `EXTENDS FB_StationBase` line on the FB declaration is the link. The two methods (`ExecuteSequence`, `GetStepName`) are the only things Fill does differently.

Cap, Label, Inspect — same shape. Read all four side-by-side and notice the **structural symmetry**. Stage 1's drift between stations is gone because the shared parts are inherited, not copy-pasted.

!!! tip "Pause and ask yourself"
    What if you wanted to add a 5th station now? You'd write a new FB extending the base, override `ExecuteSequence` and `GetStepName`, done. **The 5th station costs maybe 60 lines of new code** — not 110+ of mostly-duplicated boilerplate. *That's the inheritance win.*

### Step 2 — Run the line

`F7` to build, then activate / login / start as in Stage 1. Drive the same inputs. The behavior should be identical to Stage 1's behavior — same outputs, same timing, same alarms.

The architectural change doesn't change runtime behavior in this clean baseline. **It only changes what happens next**, when CRs land.

### Step 3 — Apply CR-1 the inheritance way

```fish
git switch stage-2-broken
```

Open `FB_StationInspect`. **Notice the override of `Monitoring`** with its non-latching quality-flag logic and the half-finished TODO comments. This is what CR-2 looks like half-applied — and it compiles, unlike Stage 1's broken state. **The room can run this code; the smell isn't a compile error, it's an architectural smell.**

But first, CR-1. Switch to:

```fish
git switch stage-2-inheritance
```

**Exercise:** add `ModePause` to the base. Update `Monitoring` to handle Pause (`IF ModePause THEN ActiveMode := 3 ...`). Now: how do you make Fill ignore Pause mid-cycle?

Two options surface naturally:

- **Option A (cleaner)** — add a virtual `AllowPause()` method to the base. Default returns `TRUE`. `FB_StationFill` overrides to return `(State <> 10)`. The base's `Monitoring` becomes `IF ModePause AND THIS^.AllowPause() THEN ActiveMode := 3 END_IF`.
- **Option B (uglier)** — Fill overrides the *entire* `Monitoring` method, duplicating base mode logic.

Pick A — write it. When done:

```fish
git switch stage-2-cr1-applied
git diff stage-2-inheritance --stat
```

3 files, +65/-48. **Notice the pollution:** `AllowPause` exists for Fill's exception, but Cap, Label, Inspect inherit it forever, never override it, never need it. The base's interface has grown by one method that serves one child.

### Step 4 — Apply CR-2 — feel inheritance break

```fish
git switch stage-2-inheritance
```

CR-2 — Inspect needs non-faulting alarms AND parallel state-10.

**Exercise:** modify `FB_StationInspect` only. The non-faulting alarm has to bypass the base's latching `Monitoring` behavior. **Try to extend Monitoring properly first** — add the quality-flag logic *after* `SUPER^.Monitoring()` runs:

```iecst
METHOD PROTECTED Monitoring   // OVERRIDE
    SUPER^.Monitoring();      // base latches alarms — wait
    // now add quality flag logic ...
END_METHOD
```

You'll discover this doesn't work. The base latches `AlarmLatched := TRUE` when `RaiseStationAlarm` is called, and the quality flag *should not latch*. To override the policy, you must NOT call `SUPER^.Monitoring()`. Which means you must *re-implement* mode resolution and alarm-ack from scratch in your override.

You've now hit the **inheritance breaking point.** Reach for `stage-2-broken` to see what this state looks like with TODOs in place. Then look at the answer:

```fish
git switch stage-2-cr2-applied
git diff stage-2-inheritance --stat
```

2 files, +121/-48. **Notice the cost is invisible in the line count.** The override duplicates 8 lines of base mode logic. Future base changes won't propagate to Inspect's override. **Every code review on the base now needs an explicit "did we mirror this into Inspect?" step.**

This is the moment that justifies Stage 3.

### Step 5 — Apply CR-3 the inheritance way

```fish
git switch stage-2-inheritance
```

CR-3: selective logging in Fill and Inspect only.

**Exercise:** add `LogBuffer` and `LogIndex` to the base. Add a virtual `LoggingEnabled : BOOL` (default FALSE). Fill and Inspect override to return TRUE. Add a `LogCycleData(Note)` helper to the base that's gated on `LoggingEnabled()`.

When done:

```fish
git switch stage-2-cr3-applied
git diff stage-2-inheritance --stat
```

3 files, +64/-25. **Notice the dead weight:** every `FB_StationCap` and `FB_StationLabel` instance now carries 100 × 120 = 12000 bytes of `LogBuffer` storage that will never be written. The cost is invisible at compile time but real at runtime memory.

### Step 6 — See the all-3-CRs end state

```fish
git switch stage-2-complete
```

Compare to baseline:

```fish
git diff stage-2-inheritance stage-2-complete --stat
```

4 files modified, +224/-65. The base has accumulated `ModePause` + `AllowPause` virtual + `LogBuffer` + `LogIndex` + `LoggingEnabled` virtual + `LogCycleData` helper. **The base is no longer a clean abstraction — it's a junk drawer of cross-cutting concerns.**

### Step 7 — Reflect

Before moving to Stage 3, ask yourself:

1. **Did CR-1's `AllowPause` virtual feel right?** It works, but Cap / Label / Inspect inherit it forever for no reason.
2. **What would a 4th alarm policy do to the base?** (E.g., a stop-then-restart-after-confirm policy.) Probably another override in the relevant child, with another duplication of base behavior.
3. **What's the testability story now?** You can subclass the base in a PlcTestSuite test — better than Stage 1 — but you can't swap alarm policies at runtime; that's still hardcoded into base + override structure.

The transition to Stage 3 is justified when you can articulate why CR-2's `SUPER`-can't-be-called and CR-3's dead-weight-in-base feel like *fundamental* limits, not just inconveniences.

---

## Branches in this stage

| Branch | Role | Forks from | One-line summary |
|---|---|---|---|
| `stage-2-inheritance` | Clean baseline | `main` | `FB_StationBase` extending `SPT_Components.FB_ComponentBase` + 4 children |
| `stage-2-broken` | Pedagogical CR-2 half-applied | `stage-2-inheritance` | Inspect's `Monitoring` override is mid-rewrite with TODOs — compiles but unfinished |
| `stage-2-cr1-applied` | CR-1 answer key | `stage-2-inheritance` | `AllowPause` virtual added to base + Fill override |
| `stage-2-cr2-applied` | CR-2 answer key | `stage-2-inheritance` | Inspect overrides `Monitoring` without SUPER + parallel hack in `ExecuteSequence` |
| `stage-2-cr3-applied` | CR-3 answer key | `stage-2-inheritance` | Base gets `LogBuffer` + `LoggingEnabled` virtual + Fill/Inspect overrides |
| `stage-2-complete` | All 3 CRs end state | `stage-2-inheritance` | The inheritance endgame — base is now a junk drawer |
