# Instructor's guide

Practical notes for facilitating the workshop. Most of this won't fit on a slide — it's the kind of thing you learn after running the session a few times.

---

## Audience fit

Be honest with yourself about who's in the room. The workshop lands very differently based on experience:

| Audience | Recommendation | Why |
|---|---|---|
| Senior controls engineers at OEMs (machine builders) | **Run the full workshop** | They've felt the procedural pain. The scoreboard hits them in the gut. |
| Plant integrators / single-line shops | **Run Stage 1 + Stage 3 only** | The inheritance critique matters less; testability lands universally. |
| Mid-level controls engineers, 3-7 years | **Run the full workshop**, keep Stage 2 tight | They've felt enough pain to recognize it; might still believe inheritance is the answer. |
| Junior engineers, < 2 years | **Skip this workshop** | They need to feel the procedural pain first. Show them Stage 1 + the scoreboard as a 30-min session, not as a workshop. |
| Software engineers crossing into controls | **Run an abbreviated version** | They know the patterns; they need the PLC dialect. Skip pattern explanation, focus on TwinCAT-specific syntax. |

Mixed audiences are the hardest. If you have both senior and junior in the room, **target the seniors** — the juniors will get something out of watching the seniors recognize themselves in Stage 1.

---

## Tone

Three things to be *very* careful about:

### 1. Don't lecture

Controls engineers are conservative for **good reasons** — when their code crashes, equipment crashes and people get hurt or production loses money. Don't sell composition as a cleverness improvement. Sell it as **risk reduction**.

> *"Less duplication = less drift = fewer field bugs at 2am."*

That framing earns the room's attention. The aesthetic-purity framing loses it.

### 2. Respect what they already do

The patterns this workshop names aren't innovations. **Most of the room is already using them**, just without the vocabulary. Frame the patterns section as *"you already do this — here's the name"*, not *"here's something new to learn."*

### 3. Acknowledge when each stage is right

Don't dismiss Stage 1. Many controls problems are correctly solved with procedural code. The workshop's argument isn't "always use composition" — it's "**know which to use when**." Closing line that lands well:

> *"Procedural is the right answer for one machine, one customer. Composition is the right answer for a family of machines that will be maintained over years by people who aren't you. The scoreboard tells you which side of the line your codebase is on."*

---

## Pacing

The schedule on the [overview](workshop/overview.md) is what fits in 4 hours, but it's tight. Watch for these slippage risks:

### Block 1 (Stage 1) — usually finishes early

Stage 1 doesn't have surprises. Engineers know how to write CASE machines. **Use the saved time to make the drift discovery deliberate.** Walk between students during CR-1 and ask "show me your alarm-ack — is it edge or level?" Don't reveal the drift; let them find it.

### Block 2 (Stage 2) — usually runs over

Stage 2 has the most concept density. SPT-Libraries vocabulary, lifecycle methods, `SUPER` calls, virtual overrides — even engineers who use Beckhoff's framework daily haven't all named these things. If you're running short, **collapse the inheritance walkthrough** and use the saved time on CR-2 (which is where the inheritance limit shows up).

### Block 3 (Stage 3) — emotional payoff but technical density

Stage 3 students feel the win on CR-1 (six lines!) but get confused on the *why*. Don't let the win slip past — pause after CR-1, run the diff in front of the room:

```fish
git diff stage-1-cr1-applied stage-3-cr1-applied --stat
```

That side-by-side is the killer slide that doesn't need a slide.

### Q&A — protect this

The 20-minute Q&A is the most valuable part of the workshop. Engineers need to test their understanding against you. **Don't let pacing of earlier blocks eat the Q&A** — it's where the patterns vocabulary actually settles into their heads.

---

## The reveals — when to land them

These moments make the workshop. Plant them in your facilitation notes:

### Reveal 1: The Stage 1 drift (during CR-1 exercise)

After students have spent 10 minutes adding `ModePause` to their stations, ask:

> *"How many of you copied your Pause logic from Fill? From Cap? From Label?"* (Hands go up scattered.) *"Now — who has a level-based AlarmAck and who has an R_TRIG?"*

The room goes quiet. The drift was already there before the CR. They'd just been working around it without naming it.

### Reveal 2: The Stage 2 base-class trap (during CR-2 exercise)

When students hit the `cannot SUPER` problem in Inspect's `Monitoring` override:

> *"The base class that helped you in Stage 1 → Stage 2 is now the constraint. Notice this isn't your fault — it's a property of the design choice."*

This is the inheritance breaking-point students need to feel. Don't rescue them from it too quickly.

### Reveal 3: The Stage 3 1-line swap (during CR-2 exercise)

After students complete the Stage 3 CR-2 swap (one line in MAIN, three lines internal):

> *"The change you just made compiled and ran without touching Fill, Cap, or Label. None of those stations know that Inspect's alarm policy changed."*

Then run:

```fish
git diff stage-3-composition stage-3-cr2-applied --stat
# 2 files changed, ~30 insertions, ~10 deletions
```

vs.

```fish
git diff stage-2-inheritance stage-2-cr2-applied --stat
# 2 files changed, ~120 insertions, ~50 deletions
```

The factor-of-4 difference is the point.

### Reveal 4 (closing): The composition isn't a moral upgrade

After the Q&A, close with:

> *"Composition isn't a moral upgrade over procedural code. It's a tool. Pays for itself when your codebase outgrows what one engineer can hold in their head. The scoreboard tells you when you've crossed that line. Until then, procedural is fine."*

That respects the room and stops the workshop from becoming dogma.

---

## Common questions and how to handle them

**Q: "Doesn't all this composition slow down scan time?"**
A: Honest answer — it adds method-call overhead, but the framework FBs (`FB_StepSequencer`, `FB_TimeoutWatchdog`) are tiny and TwinCAT inlines aggressively. Measure if you're concerned. In practice, station scan time in Stage 3 is well under the 10ms budget on a CX5000-class controller. **Show the actual scan time on the runtime if you can.**

**Q: "What about TcUnit? Can I actually unit-test these?"**
A: Yes, that's the long-tail value of Stage 3. Show the [scoreboard's testability section](workshop/scoreboard.md#the-deeper-benefit-testability) — DI lets you inject mocks and drive the FB deterministically. If you have time and the audience is interested, run a TcUnit example as bonus material.

**Q: "Is this what Beckhoff's USA team builds with?"**
A: Yes. The [VFFS sample](https://github.com/Beckhoff-USA-Community/PackML_PLC_Example) is production code that uses exactly the patterns in Stage 3. Show the source.

**Q: "When should I NOT use Stage 3?"**
A: Single-customer, single-machine integrations. Codebases under ~5000 lines. Teams of one engineer. **Don't dismiss procedural — sometimes it's the right answer.** This question is a gift; the audience is showing you they're thinking critically.

**Q: "How do I sell this to my boss?"**
A: The scoreboard. Show the line counts. Argue ROI: every cross-cutting change comes 4-10x cheaper. Argue testability: composition is a prerequisite for CI on control code, which is where the industry is moving. **Don't argue aesthetics.**

---

## Materials checklist

For each session, bring:

- [ ] Local clone of the repo on the presenter machine
- [ ] TwinCAT XAE installed and tested (don't discover problems during the workshop)
- [ ] At least one stage's project loadable in XAE — `stage-3-composition` is best
- [ ] Browser open to <https://github.com/Mark-Code-Cowboys/NEM_Workshop> for the compare URLs
- [ ] Whiteboard or shared screen for the scoreboard
- [ ] Sticky notes / paper for students to track files-touched and lines-changed during exercises (the **physical** scoreboard is more engaging than digital)
- [ ] Backup: this docs site running locally (`mkdocs serve`) in case wifi fails

---

## Post-workshop — what to leave behind

Send each attendee:

1. **The repo URL** — they can clone and reference forever
2. **The compare URL list** from the [scoreboard page](workshop/scoreboard.md#github-compare-links-one-per-cell)
3. **The patterns reference** — [docs page](patterns.md) or its README equivalent
4. **One specific recommendation per attendee**, based on their team's situation. *"Sarah, your shop ships motion controllers — focus on the I_AlarmHandler swap for test rigs. Bob, you're maintaining a legacy single-machine codebase — Stage 1 is fine for you, just add the Stage 3 CR-2 swap exercise to your toolkit for the next motion vendor swap."*

The personal recommendation is what makes the workshop stick. Generic advice fades; specific advice sticks.
