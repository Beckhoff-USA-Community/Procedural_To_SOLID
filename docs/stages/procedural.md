# Stage 1 — Procedural / monolithic

**Branches:** `stage-1-procedural`, `stage-1-broken`, `stage-1-cr1-applied`, `stage-1-cr2-applied`, `stage-1-cr3-applied`, `stage-1-complete`

---

## The procedural paradigm

### Origin and theory

Procedural programming is the oldest of the three paradigms in this workshop. Its roots go back to **structured programming** in the 1960s — Dijkstra's *"Go To Considered Harmful"* (1968), the elimination of arbitrary jumps, the rise of `IF/THEN/ELSE` and `FOR`/`WHILE` as the only control-flow primitives. By the 1970s it crystallized in Pascal and C, where the program is a tree of **procedures** (functions, subroutines) that take inputs, return outputs, and operate on data structures passed in.

IEC 61131-3 — the ladder/ST/FBD standard the entire PLC industry is built on — bakes procedural programming in as the default. A `FUNCTION_BLOCK` is essentially a procedure with persistent state: data goes in via `VAR_INPUT`, comes out via `VAR_OUTPUT`, and the FB body runs once per scan.

The two procedural axioms IEC 61131-3 enforces:

1. **Data + behavior are coupled inside the FB.** No "free functions" with mutable state — state lives inside an FB and only that FB modifies it.
2. **Scan-based reasoning.** The FB body is invoked once per scan; everything must be expressible as "given inputs at scan N, compute outputs and update state by end of scan N."

These axioms are enormously powerful for control systems. They make scan timing predictable, eliminate races (because there's no concurrency within a single PLC task), and let an engineer reason about behavior by reading the code top-to-bottom.

### The procedural mental model

When you write a procedural FB, you're thinking:

> *"This is a self-contained black box. Wire its inputs, scan it, read its outputs. The next scan repeats."*

Every station in Stage 1 is a black box of that shape. Mode goes in, alarms come out, the actuators get driven. Nothing about a station knows about any other station except via shared HMI globals in MAIN. **The lack of coupling between stations is the procedural style's greatest strength.**

### Why procedural code looks the way it does in TwinCAT

Three patterns recur in every procedural TwinCAT codebase:

1. **The CASE-of-INT state machine.** A single `INT` variable named `State` (or `Step`) tracks where the FB is in its sequence. The body is one big `CASE State OF`. Transitions are explicit assignments to `State`. This is the PLC dialect of the GoF State pattern — flat, table-driven, deterministic.

2. **The mode block at the top.** Almost every station opens by deriving an `ActiveMode` from its mode inputs. This block tends to be 3-7 lines and is **almost identical in every FB** because the requirements are almost identical.

3. **The HMI mapping at the bottom.** After the state machine runs, another `CASE State OF` translates `State` (an INT) into `StatusText` (a STRING) for the operator screen. Also nearly identical across stations.

The middle of every station — the actual sequence logic — is genuinely different. The top and bottom are duplicated.

---

## How procedural code is constructed in this workshop

### File layout (5 files)

```
NEM2026/FillingLine/POUs/
├── FB_StationFill.TcPOU      ~110 lines — fills a bottle
├── FB_StationCap.TcPOU       ~110 lines — picks a cap, torques it down
├── FB_StationLabel.TcPOU     ~115 lines — picks a label, applies it
├── FB_StationInspect.TcPOU   ~120 lines — triggers camera, rejects if defect
└── MAIN.TcPOU                 ~80 lines — instantiates and drives all four
```

Total: ~535 lines. No helpers, no shared base, no library code beyond `Tc2_Standard` (`TON`, `R_TRIG`).

### Station structure (every station follows the same template)

```iecst
FUNCTION_BLOCK FB_StationXxx
VAR_INPUT
    Execute, Reset                        : BOOL;          // common
    ModeAuto, ModeManual                  : BOOL;          // common
    JogForward, JogReverse                : BOOL;          // common
    PartPresent, AlarmAck                 : BOOL;          // common
    StationSpecificInput1, etc            : LREAL/BOOL;    // varies per station
END_VAR
VAR_OUTPUT
    Busy, Done, Error, ErrorID            : BOOL/UDINT;    // common
    StatusText, StateDisplay              : STRING/INT;    // common
    AlarmActive, AlarmText                : BOOL/STRING;   // common
    StationSpecificActuator1, etc         : BOOL;          // varies per station
END_VAR
VAR
    State                                 : INT;
    Timeout                               : TON;
    AlarmLatched, AlarmCode, AlarmText    : ...;
    AlarmAckEdge                          : R_TRIG;        // (Fill, Label only — drift!)
    ActiveMode                            : INT;
END_VAR

(* body *)
// 1. Mode block (copy-pasted with subtle drift)
IF ModeAuto THEN ActiveMode := 1; ELSIF ModeManual THEN ActiveMode := 2; ELSE ActiveMode := 0; END_IF

// 2. Alarm acknowledge (copy-pasted with subtle drift)
//    Fill / Label use R_TRIG; Cap / Inspect use level — the kept drift
IF AlarmLatched AND AlarmAck THEN AlarmLatched := FALSE; ... END_IF
//   or:
AlarmAckEdge(CLK := AlarmAck);  IF AlarmLatched AND AlarmAckEdge.Q THEN ... END_IF

// 3. Reset block (mostly identical)
IF Reset THEN ... END_IF

// 4. State machine — the only meaningfully different section
CASE State OF
    0:  // idle, transition into work on Execute + ActiveMode = 1
        IF Execute AND PartPresent AND ActiveMode = 1 THEN State := 10; END_IF
    10: // doing the actual work
        ...
        IF done_condition THEN State := 20; END_IF
    20: // complete
        Done := TRUE;
END_CASE

// 5. HMI mapping (copy-pasted)
StateDisplay := State;
CASE State OF 0: StatusText := 'Idle'; 10: ... END_CASE
Busy := (State <> 0) AND NOT Done;
AlarmActive := AlarmLatched;
Error := AlarmLatched;
ErrorID := AlarmCode;
```

Sections 1, 2, 3, and 5 are roughly **40 of every 60-line station body** — and they're duplicated four times across files with **deliberate, realistic drift**:

| Drift | Where | Pedagogical reason |
|---|---|---|
| `R_TRIG` vs level alarm-ack | Fill/Label use edge; Cap/Inspect use level | Realistic copy-paste lineage divergence |
| Step numbering 0/10/20/30 vs 0/100/200/300 | Label uses 0/100/200/300 | Earlier developer's preference that propagated |
| Dead `ManualStep` variable | `FB_StationInspect` declares it, never uses it | Legacy cruft from a previous feature |

!!! warning "These drifts are deliberately preserved across the procedural branches"
    They're the setup for CR-1's reveal moment. Don't tidy them up. The drift is realistic — it's what controls engineers actually inherit from previous developers — and the workshop's pedagogical power depends on the room recognizing themselves in it.

### MAIN's instantiation pattern

Every station is wired identically in MAIN:

```iecst
StationFill(
    Execute      := Execute,
    Reset        := Reset,
    ModeAuto     := ModeAuto,
    ModeManual   := ModeManual,
    PartPresent  := PartFill,
    AlarmAck     := AlarmAck,
    FlowRate     := FlowRate,
    TargetVolume := TargetVolume);

StationCap(   ...wires the same shared signals... );
StationLabel( ...same... );
StationInspect( ...same... );
```

There's no shared service, no central mode manager, no alarm aggregator. **Each station receives its inputs, runs its body, returns its outputs. MAIN is the orchestrator.**

---

## Cost / benefit analysis

### When procedural code is the right answer

Procedural is **the correct architectural choice** when:

- **Your team is small** (one or two engineers maintaining the code)
- **The codebase is small** (one machine, one customer, under ~5000 lines)
- **Cross-cutting concerns are rare** — you don't need to add features that touch every station
- **You don't need testability** in the unit-test sense — you'll commission and validate on the real machine
- **The code lifespan is short to medium** — under 5 years of active development
- **The team has no path toward CI/CD for control code** — and isn't planning to build one

If all six are true, **don't refactor to inheritance or composition.** Procedural will outperform OOP code on these dimensions:

- **Scan time** — no virtual dispatch, no interface vtables, no reference indirection
- **Read-line debugging** — set a breakpoint, watch values change, no abstraction layers in the way
- **Customer hand-off** — a maintenance engineer who knows ST can read your station file and grasp the whole machine in 20 minutes
- **Build time** — fewer files, no library dependencies, faster compile

These are **real advantages** that the rest of the workshop will not offer.

### When procedural starts to hurt

The procedural style breaks down predictably when **any one** of the conditions above stops being true. The breakdowns each have their own signature:

| Symptom | Root cause | What you're feeling |
|---|---|---|
| "I changed alarm behavior in three of four stations and missed the fourth" | Cross-cutting drift — every duplicated copy of mode/alarm/HMI logic is its own version | Procedural can't enforce consistency across files |
| "Adding station 5 took 2 days of copy-paste-then-fix" | Reuse-by-copy doesn't scale | Procedural has no abstraction for "the next station" |
| "I need to write tests but I can't because my FBs touch I/O directly" | No dependency injection, no seams to insert mocks | Procedural code is fundamentally tied to its environment |
| "The HMI now needs station-specific alarm info" | HMI consumers reaching into station internals | No interface boundary protecting either side from the other |

The Stage 1 → Stage 2 jump is justified when **two or more** of these symptoms have surfaced in your codebase. Until they have, the cost of OOP isn't worth paying.

### The diff numbers (your blast radius scoreboard)

The price of procedural code is paid every time a cross-cutting concern shows up. Here's what each CR cost in raw `git diff --stat`:

| CR | Files | Lines added | Lines removed | What it touched |
|---|---|---|---|---|
| **CR-1 Pause** | 5 | 50 | 13 | All 4 stations (each got `ModePause` + Pause guard) + MAIN (variable + 4 wires) |
| **CR-2 Inspect quality + parallel** | 2 | 92 | 55 | Inspect rewritten with quality flag + parallel state-10; MAIN gets one new wire |
| **CR-3 Selective logging** | 2 | 13 | 3 | Identical buffer code duplicated in Fill and Inspect |

The **shape** of these numbers tells the deeper story:

- CR-1 hit five files. The next 50 cross-cutting CRs will also hit roughly five files each.
- CR-2's "92 lines added" is *one inline rewrite of one station's CASE machine*. There's no abstraction to share with the other three stations, so the change can't be cheaper than that.
- CR-3 looks small (only 13 lines) but **those 13 lines are duplicated identically in Fill and Inspect**. Two places to maintain forever.

That's the procedural cost surface, made concrete.

---

## Complete how-to walkthrough

A step-by-step path through Stage 1 you can follow alone, with an instructor, or as a refresher months later.

### Step 1 — Survey the baseline

```fish
git switch stage-1-procedural
explorer NEM2026/NEM2026.sln
```

In XAE, open all four station FBs side by side (drag tabs into split panes, or `Window → New Vertical Tab Group`). Look at:

- **The mode block at the top.** Notice it's identical in 4-line shape but the surrounding context differs.
- **The alarm-ack block.** **Notice the drift** — Fill and Label use `R_TRIG`-edge ack; Cap and Inspect use level-based ack.
- **The state numbering.** **Notice another drift** — `FB_StationLabel` uses 0/100/200/300; everyone else uses 0/10/20/30.
- **The dead variable.** `FB_StationInspect` has `ManualStep : INT;` declared but **never referenced**. Legacy cruft. Search for `ManualStep` to confirm.

!!! tip "Pause and ask yourself"
    **Why didn't anyone notice these drifts before they shipped?** Because in production, you read one station file at a time, not four side-by-side. The drift hides in plain sight unless you look across files. *That's the procedural maintenance trap.*

### Step 2 — Run the line

```fish
# Make sure you have a TwinCAT runtime configured (local or target)
# In XAE: Build → Build Solution; should compile cleanly
```

Activate, login, start. In MAIN's online view, write:

```iecst
ModeAuto     := TRUE
Execute      := TRUE
PartFill     := TRUE
FlowRate     := 1.0
TargetVolume := 250.0
```

Watch `StationFill.OpenFillValve` go true, `Accumulated` rise, `Done` go true at 250.

Then drive Cap, Label, Inspect with their inputs (`PartCap := TRUE; CapFeederReady := TRUE; TorqueActual := 5.5;` etc.). Each station runs independently. **There is no concept of "the line as a whole" in this design — each station is its own world.**

### Step 3 — Apply CR-1 the procedural way

```fish
git switch stage-1-broken
```

This branch fails to compile. Open MAIN — you'll see `ModePause := bModePause` wired to all four stations, but **only Fill and Cap have `ModePause` as a `VAR_INPUT`**. Compile error: *"ModePause is not an input variable for FB_StationLabel."*

This is the realistic CR-1 starting point — an earlier developer started the work, got pulled away, left it half-applied. Your job is to finish.

**Exercise:** add `ModePause` to `FB_StationLabel` and `FB_StationInspect`. The mode block needs a Pause branch (`ELSIF ModePause THEN ActiveMode := 3`). The state machine needs a guard against `ActiveMode = 3`.

**Trap:** Fill must *ignore* Pause mid-cycle. Notice that the trap requires not just adding code, but reading carefully through Fill's existing state-10 logic to understand where to gate.

When you're done (or stuck), peek at the answer:

```fish
git switch stage-1-cr1-applied
git diff stage-1-procedural --stat
```

5 files, +50/-13. Compare what you wrote.

### Step 4 — Apply CR-2 the procedural way

```fish
git switch stage-1-procedural   # back to clean baseline
```

CR-2 says: Inspect needs a non-faulting quality flag, AND camera + reject pre-arm need to run in parallel.

**Exercise:** modify `FB_StationInspect` only. You'll need to add:

- `QualityIssueDetected : BOOL` as a `VAR_INPUT`
- `QualityFlag : BOOL` and `QualityCode : UDINT` and `QualityText : STRING(255)` as `VAR_OUTPUT`s
- A new `RejectDelay : TON` so camera and reject can run on independent timers
- `CameraDone : BOOL` and `RejectDone : BOOL` flags to coordinate the parallel branches in step 10
- An OR in the `AlarmActive` output so HMI sees either source

When done, peek at the answer:

```fish
git switch stage-1-cr2-applied
git diff stage-1-procedural --stat
```

2 files, +92/-55. Notice that Inspect's body grew by ~70 lines because there's no abstraction to share parallel-coordination logic with anyone else who might need it later.

### Step 5 — Apply CR-3 the procedural way

```fish
git switch stage-1-procedural
```

CR-3: log cycle data on Fill and Inspect only. Cap and Label don't need it.

**Exercise:** add a log buffer (`LogBuffer : ARRAY[0..99] OF STRING(120); LogIndex : INT;`) and a write call at each station's terminal "Complete" state. Apply to Fill and Inspect only.

When done:

```fish
git switch stage-1-cr3-applied
```

2 files, +13/-3. Notice that **the buffer code is byte-identical between Fill and Inspect**. If logging requirements change, you have two places to update.

### Step 6 — See the all-3-CRs end state

```fish
git switch stage-1-complete
```

This is what Stage 1 looks like after the customer has issued every CR in the workshop. Compare to the original baseline:

```fish
git diff stage-1-procedural stage-1-complete --stat
```

5 files modified, +152/-66. **The growth is concentrated in Inspect** (CR-2 + CR-3 both hit it), and **the duplication has compounded** (CR-1 + CR-3 each added near-identical code across multiple files). This is what a procedural codebase looks like after a year of cross-cutting CRs.

### Step 7 — Reflect

Before moving to Stage 2, ask yourself:

1. Which CR was hardest to apply? (Most engineers say CR-1 because of the mid-cycle exception.)
2. Which CR's *blast radius* surprised you? (Most often CR-3 — looks small, but the duplication is permanent.)
3. If a 5th station gets added next year, which CRs do you have to *re-think* for the new station? (Answer: all three.)

The transition to Stage 2 is justified when you can articulate why the procedural cost of these CRs feels wrong, even though the absolute line counts are still small.

---

## Branches in this stage

| Branch | Role | Forks from | One-line summary |
|---|---|---|---|
| `stage-1-procedural` | Clean baseline | `main` | Four monolithic stations with deliberate drift |
| `stage-1-broken` | Pedagogical CR-1 half-applied | `stage-1-procedural` | Pause added to Fill+Cap; MAIN wires it to all 4 → won't compile |
| `stage-1-cr1-applied` | CR-1 answer key | `stage-1-procedural` | Pause everywhere with Fill mid-cycle exception |
| `stage-1-cr2-applied` | CR-2 answer key | `stage-1-procedural` | Inspect quality flag + parallel state-10 |
| `stage-1-cr3-applied` | CR-3 answer key | `stage-1-procedural` | Log buffer duplicated in Fill and Inspect |
| `stage-1-complete` | All 3 CRs end state | `stage-1-procedural` | The procedural endgame |
