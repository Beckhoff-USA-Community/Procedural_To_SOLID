# From Procedural to SOLID

### A 4-hour TwinCAT 3 workshop in object-oriented PLC design

**NEM 2026** — Beckhoff Automation North American Engineering Meeting

---

## The setup

You are going to build the same 4-station filling line — **Fill → Cap → Label → Inspect** — three different ways. At each stage, the instructor will issue the same three change requests. You'll track files touched, lines changed, and regression risk on a visible scoreboard.

By the end, the scoreboard will tell the story without anyone needing to argue it.

!!! tip "The lesson lives in the diffs, not the slides"
    Every claim this workshop makes about "blast radius" is a real `git diff --stat` you can run yourself. The branches in this repo are the workshop scoreboard.

## The three stages

| Stage | Approach | Framework |
|---|---|---|
| **1** | [Procedural / monolithic](stages/procedural.md) | Plain ST + `Tc2_Standard` |
| **2** | [Inheritance](stages/inheritance.md) | [SPT-Libraries](https://beckhoff-usa-community.github.io/SPT-Libraries/) — `FB_ComponentBase` |
| **3** | [SOLID / composition](stages/composition.md) | Beckhoff Core libraries — interfaces + DI |

## The three change requests

| | Description | Why it hurts |
|---|---|---|
| **CR-1** | Add a **Pause** mode — but Fill must ignore Pause mid-cycle | Cross-cutting with a per-station exception |
| **CR-2** | Inspect needs **non-faulting** alarms **and** parallel camera + reject | Two axes of variation in one station |
| **CR-3** | Add **cycle data logging** to Fill and Inspect only | Feature that cuts across the hierarchy unevenly |

[See the full CR rationale →](workshop/change-requests.md){ .md-button }

## What this isn't

This isn't a sales pitch for object-oriented PLC programming. It's an honest comparison of three architectural choices against the same set of forces.

You already know how to write state machines. You already know how to copy a station file. You already use [Strategy and Template Method patterns](patterns.md) — you just don't have names for them. **The workshop's quiet payoff is the vocabulary.**

## Where to start

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **First time here?**

    ---

    Read the [getting-started](getting-started.md) page for prerequisites and how to navigate the branches.

    [→ Getting started](getting-started.md)

-   :material-school:{ .lg .middle } **Running the workshop?**

    ---

    The [instructor's guide](instructor.md) has facilitation notes, audience-fit guidance, and the timing breakdown.

    [→ Instructor's guide](instructor.md)

-   :material-chart-line:{ .lg .middle } **Just here for the scoreboard?**

    ---

    The [scoreboard](workshop/scoreboard.md) shows the actual line counts from `git diff --stat` for every cell of the matrix.

    [→ Scoreboard](workshop/scoreboard.md)

-   :material-bookmark:{ .lg .middle } **Want pattern names?**

    ---

    The [patterns reference](patterns.md) names what the workshop teaches — Strategy, Template Method, Dependency Injection, State.

    [→ Patterns reference](patterns.md)

</div>

## Credits

Workshop material © **Beckhoff Automation LLC**. Authored for the **NEM 2026** North American Engineering Meeting and hosted by the [Beckhoff USA Community](https://github.com/Beckhoff-USA-Community) GitHub organization.

The frameworks each stage builds on are © Beckhoff Automation:

- **Stage 1** — plain IEC 61131-3 Structured Text on **TwinCAT 3** (`Tc2_Standard`, `Tc2_System`, `Tc3_Module`).
- **Stage 2** — the public **[SPT-Libraries](https://beckhoff-usa-community.github.io/SPT-Libraries/)** (`SPT Base Types`, `SPT Components`, `SPT Diagnostic`, `SPT Event Logger`, `SPT Utilities`). Sample code that uses the same conventions: **[SPT_V4_Samples](https://github.com/Beckhoff-USA-Community/SPT_V4_Samples)**.
- **Stage 3** — the internal Beckhoff USA **`Core`** and **`CoreComponents`** libraries — the lower-layer foundation that the public SPT-Libraries is built on top of.
