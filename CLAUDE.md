# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Beckhoff TwinCAT 3 workshop project — **"From Procedural to SOLID: Object-Oriented PLC Design in TwinCAT 3"** (4-hour course, NEM 2026). Students see the same 4-station filling line implemented three ways side-by-side, then watch three change requests propagate through each implementation to compare blast radius.

### Current canonical layout: `Release` branch — three PLC projects in one solution

As of 2026-05-21, the workshop ships as a single TwinCAT solution containing three parallel PLC projects:

- **`FillingLine_Procedural/` — Procedural / monolithic.** Plain ST + `Tc2_Standard` / `Tc2_System` / `Tc3_Module`. Each station is a standalone FB with deliberately copy-pasted drift (R_TRIG vs level alarm-ack, 0/100/200/300 vs 0/10/20 step numbering, dead `ManualStep` var) — the drift is pedagogical and must be preserved.
- **`FillingLine_Inheritance/` — Inheritance.** Stations extend `FB_StationBase` and SPT base classes from the **SPT-Libraries** framework (Beckhoff Automation LLC — `SPT Base Types`, `SPT Components`, `SPT Diagnostic`, `SPT Event Logger`, `SPT Utilities`). Canonical design guide: **https://beckhoff-usa-community.github.io/SPT-Libraries/** — follow that style guide for FB/method naming, component lifecycle (`Cyclic`, `Init`/`Reset`), and diagnostic conventions.
- **`FillingLine_Composition/` — SOLID / composition.** Stations are composed from small FBs wired via interfaces, on the **Core** libraries (`Core`, `CoreComponents`) — currently internal Beckhoff USA libraries, the lower-layer foundation the public SPT-Libraries is built on top of. `I_Cyclic`, `I_Diagnostic`, component pattern. No inheritance from station base classes; behavior varies by injecting different implementations of `I_AlarmHandler`, `I_DataLogger`, etc.

All three PLCs run concurrently on their own system task in the same runtime, so attendees can attach an online view / HMI to any of them. The Procedural → Inheritance → Composition progression is the whole point — keep state machines minimal and let the framework comparison do the teaching.

### Branch model

```
Release            ← 3-PLC baseline (pre-class start state)
  ├── cr1-applied  ← CR-1 applied across all 3 PLCs
  ├── cr2-applied  ← CR-2 applied across all 3 PLCs
  └── cr3-applied  ← CR-3 applied across all 3 PLCs
complete           ← merge of cr1+cr2+cr3 (post-class end state)
```

The diffing exercise is: take any single CR and compare its application across the three PLC projects within a branch. That's the workshop scoreboard.

### Legacy branches (historical, do not modify)

Pre-2026-05-21 the workshop was organized as 20 separate branches with a single PLC project per branch (`stage-1-procedural`, `stage-1-broken`, `stage-1-cr1-applied`, …, `stage-3-complete-tests`). These are kept as a historical record + source for extracting the per-paradigm CR diffs into the new `Release`-derived structure. They should not be edited; new work happens on `Release` and the CR branches sprouting from it.

## Project layout

```
NEM2026/
├── NEM2026.sln                       # TcXaeShell-format solution; 3 PLC GUIDs in build-config rows
├── NEM2026.tsproj                    # System project: 3 tasks, 3 <Plc> instances
├── NEM2026.tspproj                   # Legacy stub (Vision DataType cruft) — unused, not referenced by .sln
├── _Boot/                            # XAE activation output — gitignored
├── FillingLine_Procedural/
│   ├── FillingLine_Procedural.plcproj
│   ├── PlcTask_Pr.TcTTO              # task: 10 ms cycle, priority 20, calls MAIN
│   ├── POUs/                         # programs, FBs, methods (ST in XML)
│   └── _Libraries/                   # resolved library cache (committed for offline use)
├── FillingLine_Inheritance/
│   ├── FillingLine_Inheritance.plcproj
│   ├── PlcTask_In.TcTTO              # 10 ms / priority 21
│   ├── POUs/
│   └── _Libraries/
└── FillingLine_Composition/
    ├── FillingLine_Composition.plcproj
    ├── PlcTask_Co.TcTTO              # 10 ms / priority 22
    ├── DUTs/                         # ST_LogEntry etc.
    ├── POUs/{Interfaces,BuildingBlocks,Stations}/
    └── _Libraries/
```

Each PLC project declares empty folders `DUTs/`, `GVLs/`, `VISUs/`, `POUs/` — place new objects in the matching folder so they're picked up by XAE conventions.

### Per-PLC identity

| PLC project | Project GUID | PLC AmsPort | Task name | Task prio | Task AmsPort | Instance Id |
|---|---|---|---|---|---|---|
| Procedural  | `{64827A5F-3A2D-4879-934C-C9ADE5CB19FC}` (heir of original FillingLine) | 851 | `PlcTask_Pr` | 20 | 350 | `#x08502000` |
| Inheritance | `{DEB50AD9-4D5C-4AAA-99B3-6A5E7542C762}` | 852 | `PlcTask_In` | 21 | 351 | `#x08502001` |
| Composition | `{7B5FD20B-C248-43BF-8C66-E30773564D03}` | 853 | `PlcTask_Co` | 22 | 352 | `#x08502002` |

Don't regenerate these GUIDs casually — XAE keys off them for project identity. If a PLC instance must be added or removed, ensure all PLC-level GUIDs (`<ProjectGuid>`, `<Application>`, `<TypeSystem>`, `<Implicit_Task_Info>`, `<Implicit_KindOfTask>`, `<Implicit_Jitter_Distribution>`, `<LibraryReferences>`) stay unique across the solution.

## Library reference policy (per PLC project)

Each PLC project carries only the placeholder references its code actually uses — keeps each PLC's project tree clean and makes the framework distinction visible across the solution:

| PLC project | Libraries the example code uses |
|---|---|
| `FillingLine_Procedural`  | `Tc2_Standard`, `Tc2_System`, `Tc3_Module` |
| `FillingLine_Inheritance` | above + `SPT Base Types`, `SPT Components`, `SPT Diagnostic`, `SPT Event Logger`, `SPT Utilities` |
| `FillingLine_Composition` | above-base + `Core`, `CoreComponents` |

The Core / CoreComponents libraries (`FillingLine_Composition`) are currently internal Beckhoff USA libraries — the lower-layer foundation that the public SPT-Libraries is built on top of. The workshop ships them in each PLC project's committed `_Libraries/` cache so attendees can read and build the Stage 3 code; they aren't on the public USA Community NuGet feed and aren't intended for general customer redistribution today. Stage 2 builds on the SPT layer; Stage 3 builds directly on Core's component model (`I_Cyclic`, `I_Diagnostic`).

The `Inheritance` and `Composition` plcprojs currently still declare `Tc3_EventLogger` and `Tc3_PackML_V3` as placeholder references, but no example code touches either — they're dead refs and can be pruned independently. `MechatronicsCore` is not declared in any plcproj despite older docs suggesting it.

Each PLC project's `_Libraries/` on disk holds resolved copies of every library XAE may need (Core/SPT/Mc3/XTS/Tc2/Tc3) so placeholders resolve offline — do not delete entries from `_Libraries/` even when pruning placeholder references.

## Build / run

No CLI build on Linux — TwinCAT projects build only via XAE on Windows. Open `NEM2026/NEM2026.sln` in the TcXaeShell (or Visual Studio shell with the TwinCAT XAE extensions installed); activate configuration / login / run from the IDE. There is no `dotnet` / `npm` / `pytest` equivalent. **When asked to "build" or "run tests" from this Linux checkout, say so explicitly** — don't run MSBuild against the `.tsproj`; it'll fail without the XAE extensions. Tests, when added, would use TcUnit and run on each PLC.

Each PLC runs as an independent instance — you can login to one, observe state, and leave the others idle. AmsPort 851/852/853 distinguish them.

## Editing conventions for TwinCAT files

- `.TcPOU` / `.TcDUT` / `.TcGVL` / `.TcIO` are XML envelopes around CDATA-wrapped ST. Keep the XML structure intact: `<Declaration>` for the `VAR` block / signature, `<Implementation><ST>` for the body. Methods and properties nest as `<Method>` / `<Property>` elements inside the parent `<POU>` (or `<Itf>` for interfaces). XAE re-parses these on load and rejects malformed envelopes.
- GUIDs in object headers (`Id="{...}"`) are stable identities used by XAE — don't regenerate them when editing existing files. New objects need fresh GUIDs (use `uuidgen`).
- The same source POU often lives in two or three PLC projects (e.g. `FB_StationFill.TcPOU`) — they are *not* shared. Each is an independent file with its own GUIDs and the paradigm-specific implementation. Edits to one do not propagate; intentional.
- Compiler warnings **410** and **5410** are disabled project-wide (see `DisabledWarningIds` in each plcproj). `CalcActiveTransOnly` is `True`.

## Course-specific guardrails

- **Preserve drift in `FillingLine_Procedural`.** Don't "tidy up" the alarm-ack edge/level inconsistency, the 0/100/200/300 numbering in Label, or the dead `ManualStep` in Inspect — they're the setup for CR-1 and the "how many of you copied from Fill?" reveal.
- **Match SPT API to https://beckhoff-usa-community.github.io/SPT-Libraries/** for `FillingLine_Inheritance` (FB names, method signatures, namespace prefixes). If unsure of an exact symbol against the installed library version in `_Libraries/`, flag it inline so a Windows reviewer can fix in XAE.
- **CR application is per-PLC, not blanket.** A CR may be trivial in Composition and a heavy refactor in Procedural — that asymmetry is the lesson. Don't normalize the diff across PLCs.
- The legacy `stage-*` branches still encode the original "wrong way" demos (e.g. `stage-1-broken` deliberately doesn't compile; `stage-2-broken` has the Inspect-override mess). Cherry-pick from those when authoring a new broken/teaching variant on top of `Release`, rather than starting from scratch.
