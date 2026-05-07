# Workshop overview

A four-hour deep dive in object-oriented PLC design for an audience that already writes good procedural code. Three methodologies, three change requests, one running scoreboard, and one persistent question: **when does each architectural choice pay off?**

## The story arc

The workshop is structured around a deliberate narrative, not a feature list. Each stage builds on the previous stage's pain.

### Act 1 — Procedural pain (90 min)

You build the same 4-station filling line you've been building for years. You get three change requests that hurt in three different ways. You feel the duplication problem. **You're not told it's a problem; you discover it by doing it.**

This act is the most important. If the room doesn't feel the procedural pain by the end of Block 1, the rest of the workshop is academic.

### Act 2 — Inheritance hopes and limits (75 min)

You refactor the procedural stations into a class hierarchy on top of the SPT-Libraries' `FB_ComponentBase`. The duplication evaporates. You're a hero — for about 20 minutes. Then CR-2 lands and you discover the base class you just built is now the constraint.

This act is the trickiest to facilitate. Inheritance has real wins; don't dismiss them. But the audience has to feel where it stops working, not just be told.

### Act 3 — Composition release (75 min)

You rebuild the line from interface-typed building blocks. CR-2 — the killer requirement that broke Stage 2 — becomes a one-line swap. You see the same code shape in Beckhoff USA's own production samples. The patterns you just used get names.

This act is the emotional payoff. Pace it so the room has time to *feel* the win, not just observe it.

### Act 4 — Scoreboard, discussion, take-home (20 min)

The numbers from the diffs go on the board. Discussion: when does each stage fit your real workload? What's the next step in your shop? The vocabulary they'll take to customer conversations starts here.

## Schedule

The schedule below is honest, not aspirational. The "stretch" entries are where good discussions usually run over.

| Block | Wall time | Content | Stretch zones |
|---|---|---|---|
| **0** Welcome | 5 min | Audience check, repo confirmation | — |
| **1** Stage 1 — Procedural | 85 min | Walkthrough → CR-1 → CR-2 → CR-3 → debrief | "How many copied from Fill?" reveal can run +10 min |
| Break | 10 min | | |
| **2** Stage 2 — Inheritance | 70 min | Refactor walkthrough → CR-1 → CR-2 → CR-3 → debrief | The CR-2 override mess discussion is the workshop's hardest moment |
| Break | 10 min | | |
| **3** Stage 3 — Composition | 70 min | Architecture walkthrough → CR-1 → CR-2 swap demo → CR-3 → debrief | The CR-2 swap demo lands in 90 seconds; let the silence happen |
| **4** Scoreboard + Q&A | 20 min | Side-by-side diffs, methodology fit discussion, post-workshop continuation | Plan to overshoot — this is where FAEs cement what they'll teach |
| **Total** | 4 h 30 min | | Plan for 4:30 to land in 4:00 cleanly |

## Audience

This workshop is calibrated for **Beckhoff Field Applications Engineers and customer-training staff**. That changes the bar:

- **You're already strong on TwinCAT.** Move at a good clip; don't dwell on syntax.
- **You'll teach this material later** to your own customers. The workshop should arm you with the *why's*, the *how to defend it's*, and the *here's what to say when X*.
- **You'll get pushback** from controls engineers who've shipped procedural code for 20 years. Pre-empt that pushback. The discussions in this workshop are dress rehearsal for those customer conversations.

The workshop's not aimed at:

- Junior engineers — they need to feel procedural pain in production first
- Single-machine integrators — Stage 3's payoff is multi-machine; show them the testability angle as a takeaway
- Software engineers crossing into controls — they know the patterns; they need TwinCAT vocabulary, which this workshop provides as a side effect

## What students will walk out with

| What | Where it sticks |
|---|---|
| **Vocabulary** for Strategy, Template Method, DI, ISP, Open-Closed | The [Patterns reference](../patterns.md) |
| **An honest opinion** on when each methodology fits | The cost/benefit sections of each [stage](../stages/index.md) |
| **A reference repo** with the entire matrix populated | <https://github.com/Mark-Code-Cowboys/NEM_Workshop> |
| **Customer-conversation answers** for common pushback ("composition is overkill" / "inheritance is enough" / "we don't need testability") | The [Instructor's guide](../instructor.md) → "Common pushback" section |
| **Self-paced refresher** — these docs work as workshop replay | This site, runnable via `./serve-docs.sh` from the repo |

## What this workshop is *not*

- **Not a TwinCAT tutorial.** Students need to come in already comfortable with ST, FBs, and CASE state machines. See [Prerequisites](prerequisites.md).
- **Not a sales pitch for OOP.** Procedural code is the right answer for plenty of workloads. The workshop explicitly acknowledges this. Each stage page has a **"when this stage is actually right"** section that respects the trade-offs honestly.
- **Not a SOLID religion class.** SOLID is named where useful (Stage 3) and quietly absent where it would obscure (Stages 1 and 2). The patterns serve the lesson, not the other way around.
- **Not Beckhoff marketing.** The framework grounding (SPT-Libraries for Stage 2, Core for Stage 3) is real because that's what's available locally and used in production at Beckhoff USA. The lesson is the same with any other component framework.

## Pre-reading

Mandatory:

- [Prerequisites](prerequisites.md) — verify your environment before the day
- [Change Requests](change-requests.md) — read so you're not seeing them cold

Recommended:

- [README](https://github.com/Mark-Code-Cowboys/NEM_Workshop/blob/main/README.md) — 10-minute orientation
- [Patterns by name](../patterns.md) — gives you the vocabulary in advance; makes live discussion faster

For the curious:

- One sample from [SPT_V4_Samples](https://github.com/Beckhoff-USA-Community/SPT_V4_Samples) (`SPT_Alarms` is the closest to Stage 2)
- The [VFFS PackML Demo](https://github.com/Beckhoff-USA-Community/PackML_PLC_Example) for production Stage-3 patterns

## After the workshop

The workshop ends; the material doesn't have to. Three modes for continued learning:

1. **Self-paced refresher.** Re-run the docs site (`./serve-docs.sh`) any time. Walk through the stages in order. Re-read the per-CR diffs against the workshop scoreboard.
2. **Teaching mode.** The [Instructor's guide](../instructor.md) is structured so an FAE who attended can run a shorter version (1-2 hours) for their own team or customer. The "Tour script" section is the live narration; the "Pre-emptive pushback" section is the customer-conversation cheat sheet.
3. **Deep-end.** Read the Beckhoff USA samples. Try TcUnit on a Stage 3 station — it'll work because of DI; try the same on Stage 1 and watch it not work — there's the testability lesson made visceral.
