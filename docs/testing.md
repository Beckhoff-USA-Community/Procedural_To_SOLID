# Unit testing — extra credit

The deepest payoff of Stage 3's composition isn't visible in the diff scoreboard. It's in **testability**. PLC code that depends on its dependencies via construction (instead of reaching for globals or instantiating its own actuators) is unit-testable in a way Stage 1 and Stage 2 code fundamentally cannot be.

This page demonstrates that with a working test suite for `stage-3-complete`, built on top of [SimmelFlo's PlcTestSuite](https://github.com/SimmelFlo/PlcTestSuite) — a friendly TwinCAT 3 testing framework that lowers the TDD barrier for control-code engineers.

PlcTestSuite was picked because it's the **lightest install** — a single library file, demoable in a workshop slot. [TcUnit](https://github.com/tcunit/TcUnit) is the older, better-known alternative; a **first-party Beckhoff test framework is also in flight** and will be worth tracking for shops standardizing on Beckhoff tooling. Whichever framework you pick later, the architectural prerequisite is the same: dependency injection. Stage 1 and Stage 2 stations don't have it, so none of these frameworks can test them in isolation.

The branch `stage-3-complete-tests` carries the test suite. The mainline `stage-3-complete` branch deliberately does not — testing is extra credit, not a workshop prerequisite.

## Why composition is testable

A station in Stage 1 or Stage 2 is **structurally tied to its environment**:

```iecst
(* Stage 1 *)
StationFill();   (* the FB has its own alarm machinery, mode logic,
                    HMI mapping. To test it you would need to drive
                    every input and assert against every output. The
                    FB has no seam where you can substitute a mock. *)
```

A station in Stage 3 is **structurally tied to abstractions**:

```iecst
(* Stage 3 *)
StationFill : FB_StationFill(ModeRef     := SomeMode,        (* anything that IS a FB_ModeManager *)
                             AlarmHandler := SomeAlarm,      (* anything that IMPLEMENTS I_AlarmHandler *)
                             DataLogger   := SomeLogger);    (* anything that IMPLEMENTS I_DataLogger *)
```

In a test, `SomeMode` / `SomeAlarm` / `SomeLogger` can be **anything that satisfies the contract**. The framework instances. Mock implementations. Spy implementations that record what was called. The station can't tell — and shouldn't be able to.

That's the **dependency injection seam**. PlcTestSuite gives you the assertion machinery to use it.

## PlcTestSuite at a glance

PlcTestSuite is a single TwinCAT 3 library (`[Tc3_PlcTestSuite]`, version 1.1.2 at time of writing). It provides:

- **`Tc3_PlcTestSuite.TestSuite`** — global instance, accessed from anywhere
- **`TestSuite.Test('test-id').ExecuteTest() : BOOL`** — gating predicate; returns `TRUE` exactly once per test run, on the cycle the test should execute
- **`TestSuite.Test('test-id').AssertEqual(Expected, Actual)`** — generic assertion; supports `BOOL`, `INT`/`DINT`/`UDINT`, `STRING`, `REAL`/`LREAL` (with epsilon)
- **`TestSuite.TestSuiteName`** — set the suite display name
- **`TestSuite.ReRunTests()`** — re-execute all tests on next scan
- **`TestSuite.ReRunIndividualTest('test-id')`** — re-execute one test

Test results land in JUnit XML format at `C:\ProgramData\Beckhoff\TwinCAT\3.1\Boot\TEST_Result.xml` — feedable to any CI system that consumes JUnit.

The framework's idiomatic test method:

```iecst
METHOD Test_Something
VAR_INST                                  (* state persists between cycles *)
    Local : FB_UnitUnderTest;
END_VAR

IF Tc3_PlcTestSuite.TestSuite.Test(__POUNAME()).ExecuteTest() THEN
    (* drive the unit, capture results *)
    Local.SetSomeInput(42);

    (* assert *)
    Tc3_PlcTestSuite.TestSuite.Test(__POUNAME()).AssertEqual(42, Local.SomeOutput);
END_IF
```

`__POUNAME()` is a TwinCAT compile-time pragma that resolves to the pou+method path (e.g., `FB_TestRunner.Test_Something`), so the framework can track tests by stable identity.

## Installing the framework

1. Clone the framework repo somewhere on your Windows host:
    ```cmd
    git clone https://github.com/SimmelFlo/PlcTestSuite.git
    ```
2. In XAE, install the library file from `PlcTestSuite/Releases/TestSuite_V1.1.2.library`:
    - Open **Tools → Library Repository...**
    - **Install** → navigate to the `.library` file → confirm
3. The library is now installed system-wide; switch to `stage-3-complete-tests` and the placeholder reference in `FillingLine.plcproj` will resolve automatically.

## Running the suite

```fish
git switch stage-3-complete-tests
explorer NEM2026/NEM2026.sln
```

Build, activate, login, start the runtime. In MAIN's online view:

```iecst
RunTests := TRUE;
```

This triggers `Tc3_PlcTestSuite.TestSuite.TestSuiteName := 'FillingLine — Stage 3 SOLID';` and calls `TestRunner();`, which dispatches all 16 test methods. Each test runs once per "test run" — the framework's `ExecuteTest()` predicate is the gate.

To re-run all tests (e.g., after editing one):

```iecst
TestSuite.ReRunTests();   (* in MAIN's online view, write TRUE to a hooked variable *)
```

To re-run a single test:

```iecst
TestSuite.ReRunIndividualTest('FB_TestRunner.Test_FillStation_HappyPath_CompletesCycle');
```

Results land at `C:\ProgramData\Beckhoff\TwinCAT\3.1\Boot\TEST_Result.xml`.

## The test list

The 16 tests in `FB_TestRunner.TcPOU` are organized in two tiers — **building-block tests** (no real time, instant state) and **station integration tests** (drive the unit-under-test through multiple `Execute()` calls in a synchronous loop).

### Building-block tests

| Test | What it proves |
|---|---|
| `Test_ModeManager_AutoModeAllowsRun` | Auto mode → `AllowRun = TRUE`, `CurrentMode = 1` |
| `Test_ModeManager_PauseOverridesAuto` | **CR-1**: Pause input takes priority over Auto; mode resolves to `3`, `AllowRun = FALSE` |
| `Test_ModeManager_IsPausedProperty` | **CR-1**: `IsPaused` returns TRUE only in Pause mode |
| `Test_LineFault_LatchesOnRaise` | Strategy A: `RaiseAlarm` → `HasActiveAlarm = TRUE` |
| `Test_LineFault_StopsLineIsTrue` | Strategy A policy declaration: `StopsLine = TRUE` |
| `Test_LineFault_AcknowledgeOnRisingEdge` | R_TRIG behavior: held-high `AckInput` doesn't re-clear |
| `Test_QualityFlag_FlagsOnRaise` | Strategy B: same interface, flags but doesn't latch |
| `Test_QualityFlag_StopsLineIsFalse` | **The Liskov substitution proof**: same interface, opposite policy via `StopsLine` |
| `Test_StepSequencer_TransitionUpdatesStepName` | `TransitionTo` updates both `CurrentStep` and `StepName` |
| `Test_StepSequencer_MarkCompleteSetsFlag` | Sequencer's complete flag drives station's `IsComplete` |
| `Test_ParallelSequencer_AllBranchesComplete` | All branches must be marked done before `AllBranchesComplete` flips |
| `Test_CycleDataLogger_IsEnabled` | Default state is enabled |

### Station integration tests

These tests exercise the dependency-injection seam — they construct a `FB_StationFill` (or `FB_StationInspect`) with test-scope dependencies and drive it through synchronous `Execute()` calls.

| Test | What it proves |
|---|---|
| `Test_FillStation_HappyPath_CompletesCycle` | A complete Idle → Filling → Complete cycle succeeds; `IsComplete = TRUE`, `IsFaulted = FALSE` |
| `Test_FillStation_NoFlow_RaisesAlarm` | When `FlowRate < 0.1` during Filling, the injected `LineFault` strategy raises an alarm and `IsFaulted = TRUE` |
| `Test_FillStation_PauseBlocksNewCycle` | **CR-1 integration**: with Pause asserted on the `FB_ModeManager`, the station never leaves state 0 |
| `Test_InspectStation_QualityFlagDoesNotFault` | **CR-2 integration**: with `FB_AlarmHandler_QualityFlag` injected, an alarm yields `HasActiveAlarm = TRUE` but `StopsLine = FALSE` (the contract that drives `IsFaulted`) |

## What's deliberately not tested

Some scenarios require **real-time PLC scan progression** to test correctly — `TON` timers (`CapSettle`, `CameraDelay`, `RejectDelay`, `Watchdog.Duration`) won't advance in a synchronous test loop because they depend on wall-clock elapsed time. We skip:

- `FB_StationCap` full-cycle test (state 10 needs `T#500MS` of `CapSettle`)
- `FB_StationLabel` full-cycle test (state 10/20 need `ApplySettle`)
- `FB_StationInspect` full-cycle test through state 10's parallel branches (`CameraDelay` / `RejectDelay`)
- `FB_TimeoutWatchdog.TimedOut` firing test (needs `T#10S` real time)

Production-grade testing of these requires either:

1. **Time-virtualization** — wrap `TON`/`TOF` in an injected `IClock` that the test can advance synchronously. (Not implemented here; would be the next architectural extension.)
2. **Asynchronous test orchestration** — multi-cycle test methods that step through scans across PLC iterations, asserting at the end. PlcTestSuite supports this via `VAR_INST` state but it requires writing more test infrastructure.

For workshop purposes, the 16 tests above demonstrate the principle. **The architectural lesson — composition makes testing structurally possible — lands at this scale just as well as it would at 100 tests.**

## How this would extend to CI

In a production OEM shop:

1. **Set up a TwinCAT runtime in a container or VM** that mirrors the target controller
2. **Hook the JUnit XML output** to your CI system (Jenkins, GitHub Actions self-hosted runner, GitLab CI, Azure DevOps — they all consume JUnit)
3. **Drive `TestSuite.ReRunTests()` over ADS** from the CI orchestrator after each `mkdocs build`-style PLC build
4. **Fail the build on any test failure**

This is **what TDD for PLC code looks like in 2026**. The reason it's not industry-standard yet is exactly the architectural problem this workshop teaches: most PLC code isn't structured to be testable. Stage 3 is. Once your shop is on Stage 3, CI for PLC code is a deployment problem, not an architecture problem.

## What to take away

For the workshop:

- **The diff scoreboard** shows the *blast radius* benefit of composition. Cheap.
- **The unit tests** show the *long-tail* benefit. Compounding.

For your shop:

- If you write Stage-3-style PLC code, **you can adopt PlcTestSuite tomorrow** and start pushing toward CI.
- If you write Stage-1 / Stage-2 PLC code, **you cannot** — the architecture isn't testable, no matter how many CI tools you bolt on.

That's the deeper structural argument. Composition is a prerequisite for the test infrastructure that the rest of software engineering takes for granted.

## References

- [SimmelFlo/PlcTestSuite](https://github.com/SimmelFlo/PlcTestSuite) — the framework's repo, including releases and CLAUDE.md
- [TcUnit](https://github.com/tcunit/TcUnit) — alternative TwinCAT testing framework, more established but heavier setup
- A **first-party Beckhoff test framework is in flight** — no public link yet; track Beckhoff InfoSys for the announcement
- This repo's `stage-3-complete-tests` branch — `NEM2026/FillingLine/POUs/Tests/FB_TestRunner.TcPOU`
