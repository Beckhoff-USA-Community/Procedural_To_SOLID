# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project type

This is a **Beckhoff TwinCAT 3** automation project (XAE / Visual Studio shell), not a typical software project. Source files are IEC 61131-3 (Structured Text) wrapped in XML containers (`.TcPOU`, `.TcDUT`, `.TcGVL`, `.TcTTO`, etc.). The repo currently contains scaffolding — `POUs/MAIN.TcPOU` is an empty `PROGRAM MAIN` skeleton — so most "code reading" right now is project/library configuration rather than logic.

TwinCAT version pinned by the project: `3.1.4026.22` (see `Machine3Ways.plcproj`, `_Boot/TargetDescription.xml`).

## Build / run

There is **no command-line build available in this Linux working environment**. TwinCAT projects build only via the Beckhoff XAE toolchain on Windows:

- Open `NEM2026/NEM2026.sln` in Visual Studio with the TwinCAT XAE shell installed.
- Solution platforms target multiple runtimes — `TwinCAT OS (ARMV7-A | ARMV7-M | ARMV8-A | x64 | x64-E)` and `TwinCAT RT (x64 | x86)` — in both `Debug` and `Release`. The compiled boot artifacts checked in (`NEM2026/_Boot/TwinCAT OS (ARMV7-A)/Plc/Port_851.app`, `Port_851_boot.tizip`, etc.) show this project was last built for **ARMV7-A** (likely a Beckhoff CX ARM controller).
- To deploy / run, activate configuration on the target device from XAE (Activate Configuration → Login → Run). There is no equivalent CLI.
- There is no test framework wired into this project. If tests are added later they would typically use TcUnit and run on the PLC; do not assume `dotnet test` / `pytest` / etc. apply here.

When asked to "build" or "run tests" from this Linux checkout, say so explicitly — don't attempt to execute MSBuild against `.tspproj` / `.plcproj`; it will not work without the TwinCAT extensions.

## Repository layout

```
NEM2026/
├── NEM2026.sln                    # VS solution
├── NEM2026.tspproj                # TwinCAT System project (I/O, tasks, devices, routes)
├── _Boot/                         # Compiled boot artifacts for the target (committed)
└── Machine3Ways/                  # PLC project
    ├── Machine3Ways.plcproj       # PLC project file — library refs live here
    ├── PlcTask.TcTTO              # Task definition: 10 ms cycle, priority 20, calls MAIN
    ├── POUs/                      # Programs, FBs, methods (IEC 61131-3 ST in XML)
    ├── _Libraries/                # Resolved library copies (Beckhoff + SPT + System)
    └── _CompileInfo/              # Build cache (large; do not edit)
```

The `.plcproj` declares **empty folders** for `DUTs/`, `GVLs/`, `VISUs/`, `POUs/` — when adding code, place new objects in the matching folder so they are picked up by XAE conventions (DUTs = structs/enums, GVLs = global variable lists, VISUs = TwinCAT HMI visualizations, POUs = programs and function blocks).

## Architectural context (the part not obvious from a single file)

The PLC project is built on top of the **Beckhoff "SPT" (Standardized Programming Templates) framework** plus the Mc3 motion stack, not bare Tc2/Tc3 libraries. The placeholder references in `Machine3Ways.plcproj` form a stack roughly like this:

- **Foundation**: `Tc2_Standard`, `Tc2_System`, `Tc3_Module` (system-library).
- **Beckhoff Automation LLC framework**: `Core`, `CoreComponents`, `MechatronicsCore` — application framework / lifecycle / component model.
- **Motion**: `CoreMotionMc3` and `CoreMotionNc2` (the MC3 vs NC2 split is intentional — both are wired up); `SPT Motion Control`, `SPT Kinematics`.
- **SPT machine-template libs**: `SPT Base Types`, `SPT Components`, `SPT Diagnostic`, `SPT EtherCat`, `SPT Event Logger`, `SPT Utilities`.
- **XTS**: `XtsCore` is referenced — this project is set up to drive a Beckhoff XTS (eXtended Transport System) linear-motor track. The project name "Machine3Ways" most plausibly refers to a 3-way XTS routing/diverter machine; treat XTS-related code paths as load-bearing rather than incidental.
- **VISU runtime libs** are pinned via `PlaceholderResolution` entries (`VisuElems`, `VisuElemMeter`, `VisuNativeControl`, …) — keep those in sync if a visualization is added.

When designing new code, prefer SPT/Core idioms (component pattern, SPT event logger, SPT diagnostic states) over hand-rolled equivalents — the libraries are already wired in and the rest of the codebase is expected to follow that style.

Compiler suppressions configured in `.plcproj`: warnings **410** and **5410** are disabled project-wide (see `DisabledWarningIds`). `CalcActiveTransOnly` is `True`.

## Editing conventions specific to TwinCAT files

- `.TcPOU` / `.TcDUT` / `.TcGVL` are XML envelopes around CDATA-wrapped ST source. When editing, keep the XML structure intact (`<Declaration>` for the `VAR` block / signature, `<Implementation><ST>` for the body) — XAE re-parses these on load and will reject malformed envelopes.
- GUIDs in object headers (`Id="{...}"`) are stable identities used by XAE; do not regenerate them when editing existing files. New objects need fresh GUIDs.
- `_CompileInfo/` and `_Boot/` are build outputs; don't hand-edit. They are committed in this repo (intentional), but regenerated by XAE on build.

## Known repo quirks

- A duplicate `gitignore` file (no leading dot) exists alongside `.gitignore` and differs from it. Likely accidental — flag it before relying on either.
- `README.md` is a one-line stub.
