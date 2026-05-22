# Prerequisites

Read this before the workshop. The 60 seconds you spend here will save 30 minutes of fumbling on the day.

## Hardware

| | What | Notes |
|---|---|---|
| **Required** | A Windows laptop, 16 GB RAM minimum | Workshop is hands-on; you'll be switching branches, recompiling, and running locally |
| **Recommended** | An external monitor | The TwinCAT XAE solution explorer + the docs site + this page side-by-side is worth the screen real estate |
| **Optional** | A target Beckhoff controller (CX, IPC, BX, BC) | Useful but not required — local TwinCAT runtime is enough for the workshop. If you bring one, have routes pre-configured |

You can do every exercise without a target controller. If you want to *run* the code (not just review and compile), local TwinCAT runtime on the same Windows host works.

## Software

### TwinCAT 3 XAE

**Required version:** 3.1.4026 or newer.

The workshop project's `.tspproj` is pinned at `3.1.4026.22`. Older XAE versions will offer to migrate the project — let it. They generally work but you may see warnings about features used (extended `FB_init`, property attributes) that older toolchains don't fully understand.

If you don't have XAE installed:

1. Download from [Beckhoff Engineering Software](https://www.beckhoff.com/en-us/products/automation/twincat/te1xxx-twincat-3-engineering/te1000.html)
2. Install **TE1000 — TwinCAT 3 XAE** (includes the Visual Studio shell)
3. License: a 7-day demo license is fine for the workshop; you'll be asked when you first activate a configuration

### Git client

Anything that can `clone`, `switch branches`, and `pull`:

- **Command line** (`git` on Windows, via [Git for Windows](https://git-scm.com/download/win) or `winget install Git.Git`)
- **GitKraken** — visual, very nice for navigating branch trees
- **Visual Studio's built-in Git** — works fine for switching, slightly clunky for branch comparison

You'll be switching branches a lot. Whatever client lets you do that fastest is the right one.

### Python (for the docs site only)

If you want to view the docs site locally during the workshop, you'll need Python 3.9+ on PATH. The launcher scripts handle the rest:

- **Linux/macOS:** `./serve-docs.sh`
- **Windows:** `serve-docs.cmd`

If you don't want the docs site running locally, you can read it on GitHub directly. The Markdown renders fine there too.

## Library installations

Two library families show up in the workshop:

### SPT-Libraries (used in Stage 2)

Stage 2's `FB_StationBase` derives from **`FB_ComponentBase`** in **SPT Components** — the workshop's only direct use of SPT. The Inheritance plcproj also declares `SPT Base Types`, `SPT Diagnostic`, `SPT Event Logger`, and `SPT Utilities` as placeholder references for build resolution; the example code doesn't call into them. Install the SPT family as a package — easier than picking individual libraries, and XAE resolves transitive deps for you.

Source: <https://github.com/Beckhoff-USA-Community/SPT-Libraries> (master repo + docs at <https://beckhoff-usa-community.github.io/SPT-Libraries/>)

Distribution: typically via the **Beckhoff USA Community NuGet feed**. Add the feed in XAE under `Tools → NuGet Package Manager → Package Sources`:

```
https://api.nuget.org/v3/index.json   (default)
https://nuget.beckhoff.com/v3/index.json   (Beckhoff Automation)
https://beckhoff-usa-community.github.io/PackageRepository/index.json   (USA Community)
```

### Core libraries (used in Stage 3)

- **Core** — base interfaces (`I_Cyclic`, `I_Diagnostic`)
- **CoreComponents** — component base classes

Distribution: **internal to Beckhoff USA today** — not on the public USA Community NuGet feed. The workshop ships them in `_Libraries/` for offline build. Outside this workshop, treat them as internal-only.

### You don't have to install these for the workshop

Each PLC project has its own committed `_Libraries/` cache:

- `NEM2026/FillingLine_Procedural/_Libraries/`
- `NEM2026/FillingLine_Inheritance/_Libraries/`
- `NEM2026/FillingLine_Composition/_Libraries/`

Every library any stage references is pre-resolved in there, so XAE can resolve placeholder references **offline**. The first time you open the solution, XAE may complain it doesn't recognize the libraries — point it at the appropriate `_Libraries/` and click through.

If you want to upgrade libraries later (or use SPT in your own projects), connect the public NuGet feeds — Core / CoreComponents are not available there today.

## Knowledge prerequisites

The workshop assumes:

- **Comfortable with TwinCAT 3 ST** — declaring `FUNCTION_BLOCK`, `VAR_INPUT` / `VAR_OUTPUT`, calling FBs, accessing fields with `.`
- **Comfortable with state machines** — `CASE OF`, transitions, common patterns
- **Comfortable with timers and edges** — `TON`, `TOF`, `R_TRIG`, `F_TRIG`
- **Aware of methods on FBs** — even if you haven't written one in anger
- **Basic Git** — `clone`, `branch`, `switch` (or `checkout`), `diff`

The workshop does **not** assume:

- Prior exposure to inheritance, interfaces, or `EXTENDS`
- Experience with the SPT-Libraries or Core framework
- Familiarity with software design patterns (Strategy, Visitor, etc.)
- C# / Java / Python background (helpful but not required)

If you've used `EXTENDS` in TwinCAT but never paused to think about why or when, you're in the sweet spot for this workshop.

## Setup verification

Before the workshop starts, verify your setup. Five-minute checklist:

```fish
# 1. Clone the repo
git clone https://github.com/Mark-Code-Cowboys/NEM_Workshop.git
cd NEM_Workshop

# 2. Switch to the Release baseline and verify the three PLC projects are present
git switch Release
ls NEM2026/                                         # should see FillingLine_Procedural / _Inheritance / _Composition
ls NEM2026/FillingLine_Procedural/POUs/             # should see flat FB_Station* files
ls NEM2026/FillingLine_Composition/POUs/Stations/   # should see the four station FBs (Stage 3 layout)

# 3. Open the solution in XAE
explorer NEM2026/NEM2026.sln          # Windows
```

When XAE loads:

- Solution Explorer should show **three PLC projects**: `FillingLine_Procedural`, `FillingLine_Inheritance`, `FillingLine_Composition`
- Each project's `POUs/MAIN.TcPOU` should open without errors
- `Build → Build Solution` should compile all three cleanly (warnings are OK; errors are not)

If any of those don't work, post the error message in your team chat / to the workshop organizer **before the day**. Day-of debugging eats discussion time.

## Optional but helpful

These will deepen your retention — not required, but if you have time:

- **Read the [README](https://github.com/Mark-Code-Cowboys/NEM_Workshop/blob/main/README.md)** — 10-minute overview of what we're building and why
- **Skim the [Patterns by name](../patterns.md) page** — gives you vocabulary in advance, makes the live discussion faster
- **Look at one [SPT_V4_Samples](https://github.com/Beckhoff-USA-Community/SPT_V4_Samples) project** — the `SPT_Alarms` example shows production code that uses Stage 2 patterns

If you've never touched a PLC unit-testing framework but want to see where Stage 3 leads:

- **[PlcTestSuite](https://github.com/SimmelFlo/PlcTestSuite)** — what we use in the workshop's testing extra-credit. Friendly TwinCAT 3 framework, lightest install. Stage 3's dependency injection is the prerequisite for any of these to work.
- **[TcUnit](https://github.com/tcunit/TcUnit)** — the older / better-known alternative. More setup; same architectural prerequisite.
- **A first-party Beckhoff test framework is in flight** — worth tracking for shops standardizing on Beckhoff tooling.

## What to bring on the day

- Your laptop (charged, charger packed)
- The repo cloned and verified per the checklist above
- An open mind for the parts of the workshop that contradict your current habits
- A skeptical mind for the parts that sound too good to be true

If you're unsure whether something fits in your shop's reality, **say so during the workshop**. The discussion is where the workshop earns its time. The lecture isn't.
