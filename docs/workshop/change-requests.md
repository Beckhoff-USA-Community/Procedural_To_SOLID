# The three Change Requests

The same three CRs are issued at every stage. They're chosen specifically because they target where each methodology is weakest.

---

## CR-1 — Add a Pause mode

> "Add a global Pause input. When `ModePause` is TRUE, every station should hold. **Exception:** the Fill station must ignore Pause mid-cycle — pausing a half-filled bottle ruins the product."

### Why it hurts

- **Cross-cutting:** every station needs the new input
- **Has an exception:** Fill must behave differently from the others
- **Feels small:** the new requirement is one English sentence

In procedural code it ripples through every station file. In inheritance it forces a virtual flag on the base class that exists only to serve Fill's exception. In composition it's six lines on the mode manager.

### How each stage handles it

=== "Stage 1 (procedural)"

    Five files modified, ~25 lines added. Each station gets a `ModePause` input and the same Pause guard duplicated four times. Fill's exception is a `State <> 10` check on the guard.

    [→ stage-1-cr1-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-1-procedural...stage-1-cr1-applied)

=== "Stage 2 (inheritance)"

    Three files modified, ~30 lines. Base gets a virtual `AllowPause()` method (default `TRUE`). Fill overrides to return `(State <> 10)`. The `AllowPause()` virtual exists *only* to serve Fill — the other three stations carry it as inherited dead weight forever.

    [→ stage-2-cr1-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-2-inheritance...stage-2-cr1-applied)

=== "Stage 3 (composition)"

    Two files modified, ~6 lines. `FB_ModeManager` gets a `ModePause` input and a `Mode = 3` branch. Stations are *not* touched — they only consult `Mode.AllowRun`, which already returns `FALSE` when paused. Fill's exception is automatic because Fill's state-10 logic doesn't gate on `AllowRun` once started.

    [→ stage-3-cr1-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-3-composition...stage-3-cr1-applied)

---

## CR-2 — Inspect: non-faulting alarm + parallel

> "The Inspect station needs to flag visual defects **without stopping the line** — those defects feed downstream sortation, not a fault chain. **And** Inspect must trigger the camera at the same time as it pre-arms the reject pusher, not sequentially. Both changes apply only to Inspect; the other stations stay as-is."

### Why it hurts

- **Two axes of variation at once** — alarm policy *and* sequencer topology
- **Only applies to Inspect** — has to coexist with the other three stations' patterns
- **The "don't stop the line" requirement is policy, not behavior** — implementations have to communicate that policy somehow

### How each stage handles it

=== "Stage 1 (procedural)"

    One file modified, ~70 lines. Inspect's `CASE` machine is rewritten with `CameraDone` / `RejectDone` flags inside step 10, plus a new `RejectDelay` timer. New `QualityFlag` / `QualityCode` / `QualityText` outputs parallel the existing alarm fields. `AlarmActive` output now `OR`s the two sources together. The HMI now needs station-aware logic to interpret alarms.

    [→ stage-1-cr2-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-1-procedural...stage-1-cr2-applied)

=== "Stage 2 (inheritance)"

    One file modified, ~80 lines. Inspect overrides `Monitoring` **without calling SUPER** because the base would latch the alarm and stop the line — wrong behavior for a quality flag. The cost: every line of mode-resolution and alarm-ack logic gets duplicated into Inspect's override. Future additions to base `Monitoring` won't auto-propagate. **The base class that helped Stage 1 → Stage 2 is now the constraint.**

    [→ stage-2-cr2-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-2-inheritance...stage-2-cr2-applied)

=== "Stage 3 (composition)"

    One line in `MAIN`, three lines internal to Inspect. The line in MAIN: `InspectAlarm : FB_AlarmHandler_QualityFlag;` (was `LineFault`). Both implementations satisfy `I_AlarmHandler` — Inspect's code never knew which it had. The internal change: compose `FB_ParallelSequencer` alongside `FB_StepSequencer`, configure for two branches, rework state 10. **No other stations touched.**

    [→ stage-3-cr2-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-3-composition...stage-3-cr2-applied)

!!! tip "This is the headline demonstration"
    CR-2 is where the methodology comparison lands hardest. Three files vs. one alarm-handler swap is the moment students recognize what composition actually buys them.

---

## CR-3 — Selective cycle logging

> "We need to log cycle completion data — station name, step number, cycle time — but only for Fill and Inspect. Cap and Label don't need logging."

### Why it hurts

- **Feature affects some children but not all** — uniform abstractions struggle with this
- **Looks trivial** — the temptation is to put it in the base class and gate on a flag, which creates dead weight for the children that don't use it
- **Logger implementation will probably change later** — file vs. database vs. Tc3 EventLogger vs. test stub. The architecture should make swapping easy

### How each stage handles it

=== "Stage 1 (procedural)"

    Two files modified, identical buffer code duplicated in Fill and Inspect. ~10 lines of `LogBuffer ARRAY[0..99] OF STRING(120) + LogIndex INT` plus the write call at each station's Complete state. Two places to maintain — when the logging requirement evolves, both must be updated.

    [→ stage-1-cr3-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-1-procedural...stage-1-cr3-applied)

=== "Stage 2 (inheritance)"

    Three files modified, ~30 lines. `FB_StationBase` gets `LogBuffer` + `LogIndex` storage and a virtual `LoggingEnabled` flag. Fill and Inspect override `LoggingEnabled` to return `TRUE`. **Cap and Label silently inherit the storage** — they pay for memory they never use. The base trades duplication for dead weight in unrelated children.

    [→ stage-2-cr3-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-2-inheritance...stage-2-cr3-applied)

=== "Stage 3 (composition)"

    Three files modified, ~25 lines. Fill and Inspect each grow an `I_DataLogger` field and accept it via `FB_Init`. MAIN constructs a `CycleLogger` and passes it only to Fill and Inspect. **Cap and Label don't have a logger field, don't take a logger init param, don't pay any cost.** When the logger implementation changes — file → database → telemetry — only `FB_CycleDataLogger` is replaced; nothing else moves.

    [→ stage-3-cr3-applied diff](https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-3-composition...stage-3-cr3-applied)

---

## What the three CRs share

All three are **realistic**. None of them are contrived to make composition look good — every one is a real shape of requirement that controls engineers see in production.

- CR-1 is "add a global mode with a per-machine carve-out"
- CR-2 is "this one station needs to behave differently from the others"
- CR-3 is "we need this feature in two places but not the rest"

If you've never hit any of these in production, this workshop is too early for your career. If you've hit all three (most senior controls engineers have), the scoreboard will not surprise you — but the *vocabulary* for explaining why composition handles them better will.
