# Instructor's guide — guided tour

This is the workshop's facilitation playbook. It works three ways:

1. **A live tour script** for running the workshop in real time
2. **A self-paced refresher** for FAEs reviewing the material weeks later
3. **A teaching kit** for FAEs running shortened versions for their own customers and teams

The audience is **Beckhoff Field Applications Engineers and customer-training staff**. They're already strong on TwinCAT — move at a good clip. They'll teach this material later — give them the *why* and the customer-conversation answers, not just the *how*.

---

## Pre-workshop preparation

### One week before

- Send attendees the [Prerequisites](workshop/prerequisites.md) page link
- Confirm everyone has cloned the repo and run `Build → Build Solution` cleanly on `stage-1-procedural`
- Ask anyone with environment problems to surface them now, not on the day

### Day before

- Pull the latest from `main` on the presenter machine: `git pull && ./serve-docs.sh build`
- Confirm the presentation laptop has all 18 branches fetched: `git fetch --all && git branch -a`
- Open these tabs in the browser:
    - <https://github.com/Mark-Code-Cowboys/NEM_Workshop>
    - The compare URLs for all nine scoreboard cells (have them bookmarked)
    - The local docs site (`http://localhost:8000`)
- Have the presentation laptop on a stand with external display
- Prep the **physical scoreboard** — a whiteboard or large sticky notes you'll fill in live

### 30 minutes before

- Re-clone the repo to a clean directory and verify the workshop runs without baked-in state
- Open `stage-1-procedural` in XAE; have the four station FBs visible in tabs
- Open `stage-3-composition` in a *second* XAE instance for late-Block-3 demonstration (saves a 60-second switch)

---

## Running the workshop

What follows is the live tour script. Each block has:

- **Wall time** — what to budget
- **Tour beats** — chronological things to do/say/show
- **Discussion prompts** — explicit "ask the room" moments where the FAE audience earns the workshop
- **Pre-emptive pushback** — questions FAEs will get from their own customers later; rehearse the answers here
- **Pacing levers** — what to cut if you're behind, what to add if you're ahead

---

### Block 0 — Welcome (5 min)

**Tour beats:**

1. Confirm everyone has the repo cloned and a working XAE. Hands up.
2. Frame the workshop in 30 seconds: *"You'll build the same filling line three different ways. Same requirements at every stage. The diffs tell the story."*
3. Show the [Branch tree on the home page](index.md). Don't dive in — just orient.
4. Set expectations: *"This is calibrated for FAEs. We move at FAE pace. But I want lots of discussion — that's where the workshop earns its time. If something feels wrong or you've seen it work differently, say so."*

**Discussion prompt:** *"Before we start — quickly: who here has shipped a 4-station-or-larger machine in the last year?"* (Answer is usually most of the room.) *"Then this workshop is calibrated for you. The pain we're going to surface is pain you've already felt."*

---

### Block 1 — Stage 1 — Procedural (85 min)

**Wall time: 85 min. Stretch zone: the CR-1 reveal.**

#### 1A — Walkthrough (15 min)

**Tour beats:**

1. `git switch stage-1-procedural` on your presenter machine. Open all four station FBs side by side.
2. Read the [paradigm theory](stages/procedural.md#the-procedural-paradigm) — but don't read it aloud. Summarize: *"This is the architecture you've been writing for 20 years. IEC 61131-3 was designed for it. There's nothing wrong with it. Today we're going to feel where it stops scaling."*
3. Walk through the structure. **Highlight the 5 sections of every station:** mode block, alarm-ack block, reset block, state machine, HMI mapping. Show that the middle (state machine) is the only meaningfully different section.
4. **The three deliberate drifts** — point them out one at a time:
    - R_TRIG vs level alarm-ack (visible by reading any two stations side-by-side)
    - 0/100/200/300 numbering in `FB_StationLabel` only
    - Dead `ManualStep : INT;` in `FB_StationInspect`
5. Don't editorialize on the drift yet. Just show them.

**Discussion prompt:** *"Look at this code. Anyone here written something that looks like this in the last six months?"* (Hands go up.) *"Anyone written exactly five files like this in the last six months?"* (Some hands stay up.) *"Anyone copied station 5 from station 4, and then had to fix four things?"* (More hands.) *"Good. Hold on to that feeling — we're about to make it worse."*

**Pre-emptive pushback (rehearse this answer):**

> *Customer:* **"This is fine. We've shipped 50 machines like this. Why are we changing it?"**
>
> *FAE answer:* **"You're right — it's fine for one machine. We're going to look at what happens when the same change has to land in four files instead of one. If that's never happened to you, this workshop won't change your mind. If it has, you'll recognize the pain."**

#### 1B — CR-1 hands-on (20 min)

**Tour beats:**

1. *"Customer's calling. They want a Pause mode. Here it is — read the requirement."* Show [the CR-1 description](workshop/change-requests.md#cr-1-add-a-pause-mode).
2. *"Half-applied state for you to start from."* `git switch stage-1-broken`. Show the compile error in MAIN.
3. *"30 seconds to read the broken state, then 15 minutes to fix it."* Set a timer.
4. Walk the room. **Don't help.** Wait until people are ~10 minutes in.

**The reveal moment (the workshop's first):**

After about 10 minutes — when most people are mid-fix — interrupt:

> *"Quick check. How many of you copied your Pause logic into Label from Cap? From Fill? From Inspect?"*

(Mixed hands.)

> *"Now — who has a level-based AlarmAck and who has an R_TRIG?"*

(The room goes quiet because some attendees realize they copied from a station with one ack style and pasted into a station with the other.)

> *"That's the procedural maintenance trap. Drift you didn't even know was there. You weren't writing buggy code; you were copying with rigorous attention. The system itself failed to enforce consistency."*

5. After they finish, `git switch stage-1-cr1-applied` and `git diff stage-1-procedural --stat` on screen. Five files, +50/-13.

**Discussion prompt:** *"Show of hands — who got Fill's mid-cycle exception right on the first try?"* Most won't. *"That's not a comment on you; it's a comment on the design. The exception is buried in the same Pause-guard logic that every other station uses. You couldn't write it once and apply it correctly four ways."*

**Pre-emptive pushback:**

> *Customer:* **"My team's careful. We use code review. Drift won't happen."**
>
> *FAE answer:* **"Code review against duplicated logic catches drift sometimes. Drift you don't catch is the kind that ships. The architecture either enforces consistency or it doesn't — and code review is your last line, not your first."**

#### 1C — CR-2 hands-on (20 min)

**Tour beats:**

1. Read the CR-2 spec aloud. *"Inspect needs a quality flag that doesn't fault the line, AND parallel camera + reject pre-arm. Both at once."*
2. *"15 minutes."* Set a timer.
3. Walk the room. The attempt will be: rewriting `FB_StationInspect`'s entire CASE machine.

**Stretch the discussion when done:**

> *"How many of you ended up with a 60+ line rewrite of one CASE machine?"* (Most.) *"Now: think about the next station that needs parallel branches. How much of what you just wrote can the next person reuse?"*

(Answer: very little. The parallel coordination logic is buried in Inspect's CASE, not extracted.)

> *"That's the second procedural cost. Not just duplication of the *base* — duplication of new patterns each time they appear. Stage 2 will help with this. Stage 3 will help even more."*

4. `git switch stage-1-cr2-applied` and show the diff. 2 files, +92/-55.

**Pre-emptive pushback:**

> *Customer:* **"Why do I care that the parallel logic isn't reusable? I only have one Inspect station."**
>
> *FAE answer:* **"Today, you do. Two years from now, you might have an Inspect station and a Test station that both need parallel branches. The procedural cost of CR-2 is a tax you pay every time a new station needs the same pattern."**

#### 1D — CR-3 hands-on (15 min)

**Tour beats:**

1. *"Easier one. Add cycle logging to Fill and Inspect only. Cap and Label don't need it."*
2. *"10 minutes."*
3. The attempt: a `LogBuffer` array + `LogIndex` on Fill and the same code on Inspect.
4. `git switch stage-1-cr3-applied` and show the diff. 2 files, +13/-3.

**Discussion prompt:** *"That looked small. Anyone want to defend it as 'fine'?"* Some will. *"Now imagine the logging requirements change in six months — say we want to write to a file instead of an in-memory buffer. Where do you change the code?"* (Two places.) *"And if you forget one of them?"* (Drift.)

**Pre-emptive pushback:**

> *Customer:* **"It's literally 13 lines. Stop making it a big deal."**
>
> *FAE answer:* **"It's 13 lines today. The cost isn't the lines; it's the duplication. Every future change to that logic happens twice. We'll show you the same feature in Stage 3 — same lines, but only one place to change."**

#### 1E — Block 1 debrief (15 min)

**Tour beats:**

1. `git switch stage-1-complete` and `git diff stage-1-procedural --stat`. 5 files, +152/-66.
2. *"That's what your codebase looks like after a year of cross-cutting CRs. Five files modified, growth concentrated in Inspect, duplication on every cross-cutting concern."*
3. **Ask the room:** *"Stage 1 isn't broken. It works. So why are we moving on?"* Take answers. The right ones surface naturally:
    - "Drift between files"
    - "Can't enforce consistency"
    - "Duplication compounds"
4. *"Right. Now we'll see what happens when we try to fix all of that with a base class. Spoiler: we'll fix some of it. We'll create new problems too."*

**Pacing lever:** If you're running long, cut the CR-3 hands-on (it's the smallest CR and the easiest one to walk through declaratively). If you're running short, extend the CR-1 reveal into a longer drift discussion.

---

### Break (10 min)

Don't shorten this. Coffee, bathroom, social conversation. The next block has the densest concept load.

---

### Block 2 — Stage 2 — Inheritance (70 min)

**Wall time: 70 min. Stretch zone: the CR-2 `SUPER`-can't-be-called moment.**

#### 2A — Refactor walkthrough (15 min)

**Tour beats:**

1. `git switch stage-2-inheritance`. Open `FB_StationBase` first, then `FB_StationFill`.
2. *"Same code. Same behavior. Different architecture."* Show that `FB_StationFill` is now ~65 lines instead of ~110. The shrinkage moved into the base.
3. **Highlight the inheritance mechanics:**
    - `EXTENDS FB_StationBase`
    - `THIS^.ExecuteSequence()` — virtual dispatch
    - `SUPER^.CyclicLogic()` — explicit base call
    - `(Name := 'Fill')` — extended FB_init at construction
4. **Highlight what got fixed:**
    - Drift gone — base uses `R_TRIG` for everyone
    - Step numbering normalized — Label's 0/100/200/300 became 0/10/20/30
    - Dead `ManualStep` dropped — wasn't on the base, doesn't propagate

**Discussion prompt:** *"What did this refactor cost?"* Take answers. Likely answers: nothing visible, lower line count, etc. **The right answer:** *"It cost an extra concept. Now you have to understand 'base class' and 'override' and 'THIS vs SUPER' to read this code. That's the real cost. Be honest about it."*

**Pre-emptive pushback:**

> *Customer:* **"My junior engineers don't know inheritance. Now they can't read my code."**
>
> *FAE answer:* **"That's a valid concern. Inheritance has a learning cost. The win is consistency enforcement — once your team learns it, drift goes away. The trade-off is real; you pick whichever fits your team's experience curve."**

#### 2B — CR-1 hands-on (15 min)

**Tour beats:**

1. *"Same Pause requirement as Stage 1. Apply it the inheritance way."*
2. *"10 minutes."*
3. The attempt: most will add `ModePause` to the base's mode logic. Then they'll hit Fill's mid-cycle exception.

**The reveal moment (the workshop's second):**

When attendees are stuck on Fill's exception, walk the room and ask:

> *"How are you handling the exception?"*

The two answers:

- **Option A:** virtual `AllowPause()` on the base, override in Fill
- **Option B:** Fill overrides `Monitoring` entirely

Both are legitimate. **Both are ugly in the same way.** Then:

> *"Option A — `AllowPause` exists for one child's exception, but Cap, Label, Inspect inherit it forever. Pollution. Option B — duplicates base mode logic. Drift risk. Pick your poison."*

4. `git switch stage-2-cr1-applied` and show the diff. 3 files, +65/-48.

**Discussion prompt:** *"Compare to Stage 1's CR-1 (5 files, +50/-13). The line counts are similar but the *kind* of code differs. Stage 2's pollution is on the base — visible to every reader, paid by every child. Stage 1's pollution was scattered — paid only by the four stations. Which is worse?"*

(There's no clear answer. **That's the point.** Inheritance trades one cost for another.)

#### 2C — CR-2 hands-on — the breaking point (25 min)

This block is the workshop's hardest moment. **Plan to slow down here.**

**Tour beats:**

1. Read CR-2 again. *"Inspect: non-faulting alarm AND parallel state-10. Same as Stage 1, but apply it via inheritance."*
2. *"15 minutes. I'll be available — this one's harder."*
3. Most attendees start by overriding `Monitoring` and adding their quality-flag logic *after* `SUPER^.Monitoring()`. This produces broken behavior — the base latches the alarm before their override can flag it as quality.

**Walk the room and ask leading questions:**

> *"When does `SUPER^.Monitoring()` latch the alarm?"* (Answer: every time `RaiseStationAlarm` is called.) *"And what does the quality flag policy say should happen?"* (Answer: don't latch.) *"So what does that imply about calling SUPER?"*

The realization:

> *"You can't call SUPER. But if you don't call it, you lose the mode resolution and alarm-ack the base does. So you have to duplicate them in your override."*

**The breaking-point reveal (workshop's third):**

> *"This is the moment. Read what you wrote. The base class that helped you in Stage 1 → Stage 2 — that compressed five files of duplicated code into a single base — has now become the constraint. Inspect can't extend the base; it has to *fight* the base."*

> *"Notice this isn't your fault. It's a property of the design. Single inheritance gives you ONE base. Whatever the base does, every child gets — unless the child reimplements that behavior in an override. There's no way to say 'inherit everything except the alarm policy.' Inheritance is all-or-nothing."*

4. `git switch stage-2-broken` and show the TODO-laden state. *"This is what mid-fix looks like in real life."*
5. `git switch stage-2-cr2-applied` and show the diff. 2 files, +121/-48. Highlight that the override is ~80 lines including duplicated mode logic and alarm-ack.

**Pre-emptive pushback (this is the most important one in the workshop):**

> *Customer:* **"Use multiple inheritance, then."**
>
> *FAE answer:* **"TwinCAT doesn't support multiple inheritance, and most languages that do (C++, Python) have ugly issues with it (the diamond problem). The composition pattern in Stage 3 solves the same need without those issues. We'll get there."**

> *Customer:* **"This is fine — I just need to remember to mirror base changes into Inspect's override."**
>
> *FAE answer:* **"That's a code-review burden you'll carry forever. Every base change is now a question of 'did we update Inspect?' Sometimes you'll forget. The architecture isn't enforcing the consistency anymore — your team's discipline is. Discipline is bounded; architecture is unbounded."**

#### 2D — CR-3 hands-on (10 min)

**Tour beats:**

1. *"Selective logging. Apply it via inheritance."*
2. *"5 minutes."*
3. The attempt: `LogBuffer` + `LoggingEnabled` virtual on the base; Fill and Inspect override to TRUE.
4. `git switch stage-2-cr3-applied` and show the diff. 3 files, +64/-25.

**Discussion prompt:** *"Where does Cap's `LogBuffer` storage live in memory?"* (Answer: in every Cap and Label instance, even though they never write to it.) *"Is that a problem?"* (Answer: in this 4-station example, no. In a 50-station factory? Yes.)

**Pre-emptive pushback:**

> *Customer:* **"100 strings × 120 chars × 2 unused stations = 24KB. Why are we obsessing about this?"**
>
> *FAE answer:* **"You're right — for this scale, the memory cost is academic. The bigger problem is *cognitive*. Every reader of `FB_StationBase` has to understand why `LogBuffer` exists when half the children don't use it. It's noise on the abstraction. As your codebase grows, that noise compounds."**

#### 2E — Block 2 debrief (5 min)

**Tour beats:**

1. `git switch stage-2-complete` and `git diff stage-2-inheritance --stat`. 4 files, +224/-65.
2. *"The base has accumulated `ModePause`, `AllowPause` virtual, `LogBuffer`, `LogIndex`, `LoggingEnabled` virtual, `LogCycleData` helper. It started clean; now it's a junk drawer."*
3. **Ask the room:** *"Stage 2 fixed real problems Stage 1 had. What new problems did it create?"* Take answers. The right ones:
    - "Base-class pollution"
    - "`SUPER`-can't-be-called fragility"
    - "Dead weight in unrelated children"
4. *"Stage 3 will keep what's good about Stage 2 — clean abstractions, consistency enforcement — and fix what's wrong. Let's go."*

**Pacing lever:** If you're behind, cut the CR-3 hands-on entirely (just show the diff). The CR-2 breakdown is the lesson; CR-3 is supplementary.

---

### Break (10 min)

This is the longer of the two breaks if you can swing it. Block 3's emotional payoff lands harder if the room comes back fresh.

---

### Block 3 — Stage 3 — Composition (70 min)

**Wall time: 70 min. Stretch zone: the CR-2 swap demo.**

#### 3A — Architecture walkthrough (20 min)

**Tour beats:**

1. `git switch stage-3-composition`. Show the file tree — 18 files in three directories.
2. *"This looks like more code. Hold that judgment for a minute."*
3. Open files in this order:
    - `I_AlarmHandler.TcPOU` — *"This is a contract. No implementation, just a shape."*
    - `FB_AlarmHandler_LineFault.TcPOU` — *"One implementation. Simple, focused."*
    - `FB_AlarmHandler_QualityFlag.TcPOU` — *"Another implementation. Same contract, opposite policy."*
    - `FB_StationFill.TcPOU` — *"A station. Implements two contracts. Composes building blocks. Receives dependencies via FB_init."*
    - `MAIN.TcPOU` — *"This is where the architecture is realized. The construction calls are the wiring diagram."*
4. **Highlight the SOLID principles concretely:**
    - **Single Responsibility:** every building block does one thing
    - **Open/Closed:** new alarm strategy = new FB; existing code untouched
    - **Liskov Substitution:** any `I_AlarmHandler` works anywhere `I_AlarmHandler` is expected
    - **Interface Segregation:** HMI sees `I_HmiReportable`, not `I_Sequenceable`
    - **Dependency Inversion:** stations depend on `I_AlarmHandler`, not on `FB_AlarmHandler_LineFault`

**Discussion prompt:** *"What's the cost of this architecture?"* The honest answer: *"More files. More concepts. More vocabulary to read this code. The win is what we're about to see — and the win compounds across the codebase's lifetime."*

**Pre-emptive pushback:**

> *Customer:* **"Eighteen files for a 4-station machine? You've got to be kidding."**
>
> *FAE answer:* **"You're right — for 4 stations, this is overkill. The architecture pays back when the codebase grows. If you're shipping one machine and walking away, Stage 1 is the right answer. If you're building a product family, Stage 3 is the prerequisite for sane long-term maintenance."**

#### 3B — CR-1 hands-on (10 min)

**Tour beats:**

1. *"Same Pause requirement. Apply it the composition way."*
2. *"5 minutes. I think you'll surprise yourselves."*
3. The realization comes fast: *just modify `FB_ModeManager`*. Don't touch any station.

**Discussion prompt:** *"Why is the Fill mid-cycle exception automatic in this architecture?"*

The answer: Fill's state-10 logic doesn't gate on `Mode.AllowRun` once started — it gates on `Accumulated >= TargetVolume`. The right gating point was already in place. **CR-1 didn't have to add new gating logic anywhere because the abstraction encoded the right behavior already.**

4. `git switch stage-3-cr1-applied` and show the diff. 2 files, +19/-6.

**Pre-emptive pushback:**

> *Customer:* **"Sure, this works for Pause because Pause maps cleanly to a mode. What about a feature that doesn't have a clean abstraction?"**
>
> *FAE answer:* **"Then you do the work to find the right abstraction. Composition isn't magic — it requires careful design. The trade is: invest in the abstraction up front, or pay the per-CR cost in every change. Stage 1 + 2 pay per-CR. Stage 3 pays up front and reaps savings."**

#### 3C — CR-2 — the headline swap demo (20 min)

This is the workshop's emotional payoff. Pace it carefully.

**Tour beats:**

1. *"CR-2. Inspect: non-faulting alarm AND parallel state-10. Same as Stage 1 (60 inline lines) and Stage 2 (the override mess). Apply it the composition way."*
2. **Demonstrate first** — on the presenter machine, before they try.
3. Open MAIN. Find: `InspectAlarm : FB_AlarmHandler_LineFault;`. Change to `FB_AlarmHandler_QualityFlag;`. Save. Build.
4. *"That's the entire alarm-policy change. One line."*
5. **Pause. Let the implication land. Don't fill the silence.**
6. After 10 seconds, ask: *"Did Inspect's behavior just change?"* (Yes — alarms are now non-latching, line keeps running on defect.) *"Did we modify any Inspect code?"* (No.) *"How is this possible?"* (Because the alarm strategy is *injected*, not hardcoded. The station depends on `I_AlarmHandler` — anything implementing that interface plugs in.)

**The reveal moment (workshop's fourth — the headline):**

> *"Compare to Stage 2's CR-2: 121 lines of override that fights the base. Compare to Stage 1's CR-2: 92 lines of inline rewrite of one CASE machine. Stage 3: ONE LINE."*

> *"This is the workshop's central claim. Same requirements, three architectures, different blast radius. The diff is the proof."*

7. **Now hands-on for the parallel sequencer part.** *"You also need parallel state-10 in Inspect. Open `FB_StationInspect.TcPOU`. Compose `FB_ParallelSequencer`. Configure for 2 branches in `FB_Init`. Rework state 10. 10 minutes."*
8. When done, `git switch stage-3-cr2-applied` and show the diff. 2 files, ~30 lines added, ~10 removed.

**Pre-emptive pushback (the customer-facing version of this conversation):**

> *Customer:* **"You're cherry-picking the example. CR-2 is designed to make composition look good."**
>
> *FAE answer:* **"It's designed to be **realistic**, not to make composition look good. Real customers ask for non-faulting alarms and parallel coordination on specific stations all the time. The point isn't that Stage 3 looks good in this CR — it's that CR-1, CR-2, and CR-3 ALL look good in Stage 3. Three different shapes of cross-cutting requirement, three different costs, every one cheaper in composition. That's not cherry-picking; that's pattern recognition."**

#### 3D — CR-3 hands-on (10 min)

**Tour beats:**

1. *"Selective logging in Fill and Inspect. Apply it the composition way."*
2. *"5 minutes."*
3. The path: add `Logger : I_DataLogger;` field + `DataLogger` `FB_Init` param to Fill and Inspect only. MAIN constructs `CycleLogger` and passes it via DI. **Cap and Label keep their original 4-arg `FB_Init` signature — don't touch them.**
4. `git switch stage-3-cr3-applied` and show the diff. 3 files, +32/-11.

**Discussion prompt:** *"Where does Cap's logger storage live now?"* (Answer: nowhere. Cap doesn't have a logger field.) *"What changes if we want to swap from in-memory buffer to file-based logger?"* (Answer: only `FB_CycleDataLogger` is replaced. Stations don't change. MAIN doesn't change.) *"Compare to Stage 2's logger refactor cost."* (Stage 2: base + every override + `LogCycleData` helper.)

#### 3E — The wrong-way branch (5 min)

**Tour beats:**

1. *"Bonus content — even Stage 3 can be applied poorly."*
2. `git switch stage-3-broken` and show the diff. *"Same CR-1 (Pause), but applied via per-station guard logic instead of via `FB_ModeManager`. Compiles. Runs. Halts Fill mid-cycle — the very failure mode CR-1 was designed to avoid."*
3. **The lesson:** *"Architecture matters, but so does discipline. Composition gives you the tools to do it right. It doesn't force you to."*

**Pre-emptive pushback:**

> *Customer:* **"So composition can be done wrong too. What's the point?"**
>
> *FAE answer:* **"Every paradigm can be done wrong. The point is which one *makes the right thing easy and the wrong thing visible*. Stage 1's right answer for cross-cutting concerns is 'modify every station' — easy to do, easy to drift. Stage 3's right answer is 'modify the shared service' — also easy, and the wrong-way alternative is loud (5-file diff) instead of quiet (1-file diff). The right architecture nudges you toward the right answer."**

---

### Block 4 — Scoreboard, discussion, take-home (20 min)

**Wall time: 20 min. Plan to overshoot — this is where the workshop cements.**

#### 4A — Scoreboard fill-in (10 min)

**Tour beats:**

1. Pull up the [Scoreboard page](workshop/scoreboard.md) on the projector. Or reveal a whiteboard with the cells pre-drawn.
2. Walk through the 9 cells, citing the actual diff numbers. The audience has now *done* every cell — this is consolidation, not introduction.
3. **Read the scoreboard's deeper lessons aloud:**
    - "CR-1 hits 5 files in procedural; 3 in inheritance; 2 in composition."
    - "CR-2 in procedural is a 92-line inline rewrite. In inheritance it's a 121-line override fight. In composition it's a 1-line swap."
    - "CR-3 looks small in procedural (13 lines) but the duplication is permanent. Inheritance fixes the duplication but adds dead weight. Composition has both proportional cost and zero dead weight."

**Discussion prompt (the most important one):** *"Walk back to your shop. What machine, codebase, or customer is each stage right for? Be specific. Name names if you can."*

Take answers. Encourage debate. The honest answers are:

- **Stage 1** — single-machine integrators, panel shops, one-engineer teams, short-lifespan code
- **Stage 2** — homogeneous machine families, mid-sized teams, long-lifespan code, medium variation
- **Stage 3** — OEMs building product families, multi-engineer teams, multi-customer variation, long lifespan, TDD goals

#### 4B — Customer-conversation rehearsal (5 min)

**Tour beats:**

1. *"You'll go back to your customers and someone will say 'this is overkill' or 'we don't have time for this' or 'just give me the procedural version.' Let's rehearse."*
2. Pick three pre-emptive pushback questions from the blocks above (the ones marked **Pre-emptive pushback**) and roleplay them with the room.
3. *"The answer isn't 'composition is always right.' The answer is 'here's how to know which fits your situation.'"*

#### 4C — Continuation kit (5 min)

**Tour beats:**

1. *"Three modes for keeping this material alive after today:"*
    - **Self-paced refresher** — `./serve-docs.sh` from the cloned repo, walk through stages in order
    - **Teaching mode** — this docs site is structured so an attendee can run a 1-2 hour version for their own team or customer; the [Instructor's guide](#) is the script, the [Patterns reference](patterns.md) is the cheat sheet
    - **Deep end** — TcUnit on a Stage 3 station, then on Stage 1; testability difference is visceral
2. *"Send me one specific machine, project, or customer this material applies to. I want to know what you'll teach it for. That's how I make this workshop better."*

**Personal recommendation per attendee** (post-workshop, optional but high-impact):

If you have time and the workshop is intimate enough (< 20 attendees), send each attendee a brief follow-up with a specific recommendation tied to their team's situation:

> *"Sarah — your shop ships motion controllers. The `I_AlarmHandler` swap is the most useful Stage 3 pattern for your test rigs. Try it on your next customer build."*
>
> *"Bob — you're maintaining a single-machine codebase. Stage 1 is fine for you. Add the Stage 3 CR-2 swap exercise to your toolkit for the next motion vendor swap — that's where you'll feel the testability win."*
>
> *"Maria — you do customer training. Run a 1-hour version of just Stage 1 → Stage 3 CR-2 (skip CR-1 and CR-3) for your next class. It's the most impactful single demo in the workshop."*

**The personal recommendation is what makes the workshop stick.** Generic advice fades; specific advice sticks.

---

## Pacing and contingency planning

### If you're 15 minutes behind by Block 2

- **Cut CR-3 in Block 2.** The Stage 2 lesson is CR-1 (pollution) and CR-2 (breaking point). CR-3's dead-weight problem is academic compared to those.
- **Tighten Block 1's debrief.** You don't need to walk every diff in detail — show the matrix on the scoreboard page and let the audience scan.

### If you're 15 minutes behind by Block 3

- **Demo CR-2 swap instead of having attendees do it.** The reveal moment is the swap on the presenter screen; the parallel-sequencer hands-on can be skipped.
- **Compress 4A to a 2-minute walk-through of the scoreboard page** rather than per-cell discussion.

### If you're ahead

- **Extend the discussion in Block 4.** Customer-conversation rehearsal can run 15+ minutes if the room is engaged.
- **Show the [Patterns reference](patterns.md) page** and walk through Strategy / Template Method / DI by name. Connect to the workshop they just did.
- **Demo `stage-3-broken`** — the CR-1-the-wrong-way branch — and walk through *why* it's wrong even though it compiles.
- **Run the unit-test demo on `stage-3-complete-tests`** (15-25 min, requires PlcTestSuite installed). The most powerful extension if the room is technically engaged. See the dedicated section below.

### Bonus — running the unit-test demo (only if class finishes early)

The [Testing (extra credit)](testing.md) page documents a working unit-test suite on the `stage-3-complete-tests` branch using [SimmelFlo's PlcTestSuite](https://github.com/SimmelFlo/PlcTestSuite). It's the most powerful demonstration of the testability advantage — but it's deliberately **not** in the core workshop schedule because:

1. **It requires a library install on the day.** PlcTestSuite is a separate `.library` file (Tools → Library Repository → Install). If attendees don't already have it, the install eats 5+ minutes per machine.
2. **It only works on Stage 3 code.** Demonstrating *why it doesn't work on Stage 1 or Stage 2* requires extra setup time the core workshop doesn't budget.
3. **It needs a running TwinCAT runtime.** Attendees who came review-only (no target controller, no local runtime) can't actually execute the tests.

**When to run it:**

- You're at least 20 minutes ahead of schedule by Block 4
- Most attendees have a running runtime (local or remote)
- The room is leaning toward "what would I actually do with this back at my shop?" — testing is the answer

**How to run it (15-25 min):**

1. *(2 min)* Pull up the [Testing page](testing.md) on the projector. Read the "Why composition is testable" section aloud — it's the architectural argument that hasn't been made explicit yet.
2. *(3 min)* Switch to `stage-3-complete-tests` on the presenter machine. Open `NEM2026/FillingLine/POUs/Tests/FB_TestRunner.TcPOU`. Walk through the file structure: 16 test methods organized into building-block tests + station integration tests.
3. *(5 min)* Show one building-block test in detail — `Test_QualityFlag_StopsLineIsFalse` is the best one. The body is six lines, but the lesson is the entire Liskov substitution principle: same interface, opposite policy, station code unaware. *"Read this test out loud. That's the contract that makes CR-2 a one-line swap."*
4. *(5 min)* Show one station integration test — `Test_FillStation_HappyPath_CompletesCycle`. Highlight the `VAR_INST` block declaring local `FB_ModeManager`, `FB_AlarmHandler_LineFault`, `FB_CycleDataLogger`, and the `FB_StationFill` constructed with all three. *"This is the testing seam: the FB takes its dependencies as constructor parameters. We can construct it with anything that satisfies the interface — including mocks."*
5. *(5 min)* If you have a runtime: build, activate, login, start. Set `RunTests := TRUE` in MAIN. Show the JUnit results file at `C:\ProgramData\Beckhoff\TwinCAT\3.1\Boot\TEST_Result.xml`.
6. *(2-5 min)* Discussion: *"What would it take to test a Stage 1 station? A Stage 2 station? Why is this only possible on Stage 3?"* The answer surfaces naturally — Stage 1 and 2 stations don't have the dependency-injection seam, so there's nowhere to plug in mocks.

**Frame the segment as:** *"This is what the rest of software engineering takes for granted. Stage 3 makes it available to control code. Composition isn't optional architecture if your shop wants to move toward CI for PLC — it's the prerequisite."*

**If you don't get to it:** that's fine. Send the [Testing page](testing.md) link in the post-workshop follow-up; attendees can read and run it on their own time. The architectural lesson lands fully without the testing demo — testing is the *cherry on top*, not the load-bearing beam.

### If a discussion is going long but is gold

**Let it.** The workshop's value is in the discussion. The schedule is a guideline. If the room is debating "where Stage 2 is the right answer" and learning by doing it, don't cut them off to make timing.

---

## Materials checklist

Day-of:

- [ ] Presenter laptop with repo cloned, all branches fetched
- [ ] Working TwinCAT XAE installation (3.1.4026+)
- [ ] Two XAE instances open: `stage-1-procedural` and `stage-3-composition`
- [ ] Browser with the [scoreboard](workshop/scoreboard.md) bookmarked
- [ ] Local docs site running (`./serve-docs.sh`) — backup if wifi fails
- [ ] Whiteboard or large sticky notes for the physical scoreboard
- [ ] Sticky notes for attendees to track files-touched and lines-changed during exercises (the **physical** scoreboard is more engaging than digital)
- [ ] Timer (phone is fine) for the timed exercises

**Optional (only bring if you're confident you'll finish ahead — the testing demo is bonus content, not workshop-core):**

- [ ] [PlcTestSuite library](https://github.com/SimmelFlo/PlcTestSuite/Releases) installed on the presenter machine *and* on attendee machines if you want hands-on
- [ ] `stage-3-complete-tests` branch fetched (`git fetch && git switch stage-3-complete-tests`)
- [ ] [Testing page](testing.md) bookmarked in the browser

Day-after:

- [ ] Send each attendee the personal recommendation (see 4C)
- [ ] Send the repo URL and the [scoreboard compare links](workshop/scoreboard.md#github-compare-links-one-per-cell) — they'll forget where to find them
- [ ] Solicit feedback in the workshop's chat / dedicated channel

---

## Running shorter versions

The full workshop is 4 hours. FAEs running customer training or internal sessions often need 1-2 hour versions. Three pre-built shapes:

### 30 minutes — "the one demo"

Show only the Stage 3 CR-2 swap demo. Three steps:

1. *"Here's a station that needs a non-faulting alarm. Watch."*
2. Switch a one-line alarm strategy in MAIN. Build. Behavior changes.
3. *"That's composition. The strategy is injected, not hardcoded. Same code, different behavior, no Inspect modification."*

Useful when you have a customer in a half-hour slot and want to plant a single seed. The seed is: **runtime swappable strategies are real and useful in TwinCAT.**

### 1 hour — "the methodology compare"

Skip Stage 2. Run Stage 1 walkthrough + CR-1 hands-on, then Stage 3 walkthrough + CR-1 demonstration. Show only the CR-1 cells of the scoreboard.

Useful when the audience is short on time but technically capable. The lesson: **same requirement, three different costs.**

### 2 hours — "the workshop, compressed"

Run the full workshop's structure but cut the CR-3 exercises in every stage. CR-1 + CR-2 cover the key lessons. CR-3 is a pacing extender for the 4-hour version.

Useful for an intermediate audience that doesn't need every cell of the scoreboard but wants the full architecture comparison.

### 4 hours — "the full workshop"

This document.

!!! note "None of the shortened versions include the testing demo"
    The unit-test demonstration on `stage-3-complete-tests` is reserved for the 4-hour version, and only when the class is running ahead of schedule. Even the full 4-hour workshop treats testing as bonus content — see the [If you're ahead → bonus testing section](#bonus-running-the-unit-test-demo-only-if-class-finishes-early) above for the rationale and the 15-25 minute facilitation script.

---

## Becoming a teacher of this material

The bar for the FAE audience is: **become believers and teachers**. The "believer" part comes from doing the workshop. The "teacher" part requires three more things:

1. **Run a shorter version yourself** — within a month of attending, run the 1-hour or 2-hour version for your own team or one customer. The first time you teach it, you'll discover what you actually understood vs. what you only nodded along to.
2. **Adapt the script to your audience** — the script in this document is calibrated for FAEs. If you're teaching controls engineers at a customer site, soften the pace; spend more time on the Stage 1 → Stage 2 transition (most controls engineers haven't deeply used inheritance). If you're teaching software engineers, skip the procedural-paradigm theory; jump to the patterns vocabulary in Stage 3.
3. **Track the customer reactions** — keep a running list of pushback questions you hear that aren't in this document. Send them back. The next version of this guide will incorporate them. **The workshop improves through being taught by many people, not just by one.**

The deepest measure of the workshop's success is when an FAE who attended teaches it, and *their* attendees recognize themselves in Stage 1's drift the way you recognized yourselves on the day you attended.
