# From Procedural to SOLID

### A 4-hour TwinCAT 3 workshop in object-oriented PLC design — NEM 2026

Students build the same 4-station filling line — **Fill → Cap → Label → Inspect** — three different ways, then apply the same three change requests to each. The branches in this repo are the workshop scoreboard: **same requirements, three methodologies, very different blast radius.**

---

## What you'll learn

The lesson lives in the diffs, not the slides:

1. **Stage 1 — Procedural / monolithic.** Each station is a standalone Function Block with copy-pasted mode/alarm/HMI logic. Realistic drift (R_TRIG vs level alarm-ack, mismatched step numbering, leftover dead variables) is preserved deliberately — the duplication problem has to feel real.
2. **Stage 2 — Inheritance via SPT-Libraries.** Stations extend `SPT_Components.FB_ComponentBase` from the [SPT-Libraries framework](https://beckhoff-usa-community.github.io/SPT-Libraries/). Mode/alarm/HMI live in a base class once. Demonstrates classic inheritance benefits — and where they break down.
3. **Stage 3 — SOLID / composition (Core libraries).** Stations are composed from small, single-responsibility FBs wired through interfaces. `I_AlarmHandler`, `I_DataLogger`, `I_ModeProvider`, etc. Behavior varies by injecting different implementations, not by overriding base methods.

The change requests are deliberately cross-cutting — they target where each methodology is weakest.

---

## The three Change Requests

| | Description | Why it hurts |
|---|---|---|
| **CR-1** | Add a **Pause** mode — but Fill must ignore Pause mid-cycle (stopping a half-filled bottle ruins the product) | Cross-cutting concern with a per-station exception |
| **CR-2** | Inspect needs a **non-faulting** alarm (quality flag, doesn't stop the line) **and** must run camera + reject-arm in **parallel** | Two axes of variation in one station, at once |
| **CR-3** | Add **cycle data logging** to Fill and Inspect only — Cap and Label don't need it | Feature that cuts across the hierarchy unevenly |

---

## Branch map

```
main
│
├── stage-1-procedural ─┬── stage-1-broken            CR-1 half-applied (won't compile)
│                       ├── stage-1-cr1-applied       CR-1 alone, Pause everywhere
│                       ├── stage-1-cr2-applied       CR-2 alone, Inspect quality+parallel
│                       ├── stage-1-cr3-applied       CR-3 alone, log buffer in Fill+Inspect
│                       └── stage-1-complete          all 3 CRs applied
│
├── stage-2-inheritance ┬── stage-2-broken            CR-2 half-applied (Inspect override mess)
│                       ├── stage-2-cr1-applied       CR-1 via base + AllowPause virtual
│                       ├── stage-2-cr2-applied       CR-2 via Inspect Monitoring override
│                       ├── stage-2-cr3-applied       CR-3 via base + LoggingEnabled virtual
│                       └── stage-2-complete          all 3 CRs applied
│
└── stage-3-composition ┬── stage-3-broken            CR-1 the WRONG way (per-station guard)
                        ├── stage-3-cr1-applied       CR-1 alone, FB_ModeManager only
                        ├── stage-3-cr2-applied       CR-2 swap (LineFault → QualityFlag,
                        │                              StepSequencer → ParallelSequencer)
                        ├── stage-3-cr3-applied       CR-3 alone, I_DataLogger DI
                        └── stage-3-complete          all 3 CRs applied
```

Each `cr*-applied` branch is **one commit** on top of its clean baseline so the diff is exactly that CR's footprint.

---

## The scoreboard

Numbers from `git diff --stat <baseline>...<cr-applied-branch>`:

| | Stage 1 (procedural) | Stage 2 (inheritance) | Stage 3 (composition) |
|---|---|---|---|
| **CR-1 Pause** | 5 files / +50 / −13 — every station modified | 3 files / +65 / −48 — `AllowPause` virtual pollutes the base for one child's exception | **2 files / +19 / −6** — one method on `FB_ModeManager`, others untouched |
| **CR-2 Inspect quality+parallel** | 2 files / +92 / −55 — inline rewrite of one CASE machine | 2 files / +121 / −48 — `Monitoring` override drops `SUPER`, mode resolution duplicated, base behavior fragile to future changes | **1 line in MAIN + ~3 internal** — alarm strategy swapped via `I_AlarmHandler`, sequencer swapped from `FB_StepSequencer` → `FB_ParallelSequencer` |
| **CR-3 Selective logging** | 2 files / +13 / −3 — buffer code duplicated in Fill and Inspect | 3 files / +64 / −25 — base carries `LogBuffer` for **every** station, only Fill/Inspect use it (dead weight in Cap/Label) | **3 files / +32 / −11** — `I_DataLogger` injected only into the stations that need it |

Side-by-side review:

```fish
# CR-1 across methodologies
git diff stage-1-procedural...stage-1-cr1-applied --stat
git diff stage-2-inheritance...stage-2-cr1-applied --stat
git diff stage-3-composition...stage-3-cr1-applied --stat

# Or view them in GitHub:
# https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-1-procedural...stage-1-cr1-applied
# https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-2-inheritance...stage-2-cr1-applied
# https://github.com/Mark-Code-Cowboys/NEM_Workshop/compare/stage-3-composition...stage-3-cr1-applied
```

---

## Running it

This is a **Beckhoff TwinCAT 3** project. There is no command-line build — TwinCAT compiles only via the XAE Visual Studio shell on Windows.

**Requirements**
- Windows host with [TwinCAT 3 XAE](https://www.beckhoff.com/en-us/products/automation/twincat/) (3.1.4026 or newer)
- The SPT-Libraries (Stage 2) and Core libraries (Stage 3) — installed via NuGet from the Beckhoff USA Community feed, or pre-resolved into `NEM2026/FillingLine/_Libraries/` (already committed)

**Open the solution**
```fish
# clone, then on a Windows box:
git switch stage-3-composition       # or any stage you want to inspect
# Open NEM2026/NEM2026.sln in Visual Studio (XAE shell)
```

The PLC project is `NEM2026/FillingLine/`. The PLC task `PlcTask` runs on a 10 ms cycle and calls `MAIN`. Each branch's `MAIN.TcPOU` shows the wire-up specific to that stage.

---

## Repo layout

```
NEM2026/
├── NEM2026.sln                    # VS solution
├── NEM2026.tspproj                # TwinCAT System project
└── FillingLine/
    ├── FillingLine.plcproj        # library refs change per branch family:
    │                              #   stage-1-*: Tc2_Standard / Tc2_System / Tc3_Module
    │                              #   stage-2-*: above + SPT_BaseTypes / SPT_Components /
    │                              #              SPT_Diagnostic / SPT_EventLogger /
    │                              #              SPT_Utilities / Tc3_EventLogger /
    │                              #              Tc3_PackML_V3
    │                              #   stage-3-*: above-base + Core / CoreComponents /
    │                              #              Tc3_EventLogger
    ├── PlcTask.TcTTO              # task: 10 ms / priority 20
    ├── POUs/                      # programs, FBs, methods (ST in XML)
    │   ├── Interfaces/            # (Stage 3 only) — SOLID contracts
    │   ├── BuildingBlocks/        # (Stage 3 only) — composable primitives
    │   ├── Stations/              # (Stage 3 only) — per-station FBs
    │   └── MAIN.TcPOU             # cyclic entry point
    ├── DUTs/                      # struct types
    └── _Libraries/                # resolved library cache (committed for offline use)
```

---

## Editing conventions

If you're contributing back:

- `.TcPOU` / `.TcDUT` / `.TcGVL` / `.TcIO` are XML envelopes around CDATA-wrapped IEC 61131-3 Structured Text. Methods and properties nest as `<Method>` / `<Property>` elements inside the parent `<POU>` (or `<Itf>` for interfaces).
- GUIDs in object headers (`Id="{...}"`) are stable identities used by XAE — don't regenerate them when editing existing files. Generate new ones for new objects (`uuidgen`).
- Type prefixes (`FB_`, `I_`, `ST_`, `E_`) on type names; **no** Hungarian on instance variables.
- Stage 1 drift is **deliberate** — don't tidy up the alarm-ack inconsistency, the 0/100/200/300 numbering in `FB_StationLabel`, or the dead `ManualStep` variable in `FB_StationInspect`. They're the setup for the CR-1 reveal.

---

## References

- [SPT-Libraries documentation](https://beckhoff-usa-community.github.io/SPT-Libraries/) — Stage 2 framework canon
- [SPT_V4_Samples](https://github.com/Beckhoff-USA-Community/SPT_V4_Samples) — working SPT examples (Stage 2 grounded against `SPT_Alarms`)
- [VFFS PackML Demo](https://github.com/Beckhoff-USA-Community/PackML_PLC_Example) — production Core library usage (Stage 3 grounded against this pattern)

For AI assistants working on this repo: see [`CLAUDE.md`](CLAUDE.md) for the architectural and pedagogical guardrails.
