# Workshop overview

## Audience

This workshop is sized for **controls engineers with moderate TwinCAT/ST proficiency**. Specifically, you should be comfortable with:

- Writing `CASE OF` state machines
- Declaring Function Blocks with `VAR_INPUT` / `VAR_OUTPUT`
- Using `TON` / `TOF` timers and `R_TRIG` / `F_TRIG` edge detectors

You **do not** need prior exposure to interfaces, dependency injection, or design patterns. That's the point — the workshop teaches by feel before naming.

## Format

Four hours, three blocks, two breaks:

| Block | Duration | Content |
|---|---|---|
| 1 | 90 min | Stage 1 — Procedural walkthrough → CR-1, CR-2, CR-3 exercises |
| Break | 10 min | |
| 2 | 75 min | Stage 2 — Inheritance refactor → CR-1, CR-2, CR-3 exercises |
| Break | 10 min | |
| 3 | 75 min | Stage 3 — Composition rebuild → CR-1, CR-2, CR-3 exercises |
| 4 | 20 min | Scoreboard review, side-by-side diffs, Q&A |

## Course narrative

You build the same 4-station filling line three different ways. At each stage the instructor issues the same three Change Requests. The class tracks **files touched, lines changed, and regression risk** on a visible scoreboard. By the end the scoreboard tells the story.

The core argument is empirical, not aesthetic: composition wins on every axis that matters in production code, but the win only becomes obvious *after you've felt the procedural pain*.

## What students walk out with

1. **Vocabulary** for what they already do every day — Strategy, Template Method, Dependency Injection, State pattern. They didn't need names to do good work, but the names let them talk to the rest of software engineering.
2. **An opinion** about when each methodology fits. Procedural is fine for one-off panels; inheritance is fine until the cross-cutting concerns hit; composition pays for itself when the codebase outgrows what one engineer can hold in their head.
3. **A reference repo** with the entire matrix already populated. The diffs in this repo are evidence; students can cite them in design reviews back at their own shops.

## What this isn't

- **Not a TwinCAT tutorial.** Students need to come in already comfortable with ST and FBs.
- **Not a sales pitch.** The narrative explicitly acknowledges that procedural code is the right call for some workloads. The workshop respects that.
- **Not a SOLID religion class.** SOLID is named where useful (Stage 3) and dropped where it would obscure (Stages 1 and 2).
