---
id: scheduling-theory
title: Scheduling Theory for Firmware
sidebar_label: Scheduling Theory
sidebar_position: 7
tags: [embedded, real-time, scheduling, rate-monotonic, edf, response-time-analysis, timing]
---

# Scheduling Theory for Firmware

Most firmware priority assignments are opinions. Somebody decided the safety task was the most important thing in the system and gave it the highest priority, somebody else discovered the display flickered and bumped its task up, and three years later nobody can say whether the 1 kHz control loop meets its deadline — only that it seems to. Real-time scheduling theory replaces that with arithmetic. Given each task's execution time, its period and its deadline, it answers "does every task always meet its deadline" with a proof rather than a measurement campaign.

The mental model: **a periodic task set is a resource-allocation problem with a closed-form answer, and the answer depends on the priority assignment.** Liu and Layland's 1973 result is that for the standard model — periodic tasks, deadlines equal to periods, independent tasks, one preemptive processor — the *best possible* fixed-priority assignment is the one that orders tasks by rate: shorter period, higher priority. That is not a heuristic. It is optimal in the strict sense that if any fixed-priority assignment can schedule the set, rate-monotonic can.

The second thing to internalise, because it is where nearly every write-up on this subject goes wrong: **the famous utilisation bound is a sufficient condition, not a necessary one.** Passing it proves the set is schedulable. Failing it proves nothing at all. Half the systems in the field run above the bound and meet every deadline, and this page shows one of them and proves it.

:::info[Prerequisites]
[What "Real-Time" Actually Means](./real-time-definitions.md) establishes deadlines, classes, and why the worst case is the only case that matters. [Worst-Case Execution Time](./wcet.md) is where the `C` values below come from — everything here is arithmetic on numbers that page has to produce first. [Scheduling](../../computer-science/operating-systems/scheduling.md) owns the general theory of schedulers, including the non-real-time algorithms this page does not cover.
:::

## The model, and the assumptions inside it

Every result below is stated for the Liu and Layland model. Write the assumptions down, because on real firmware most of them are violated somewhere and each violation has a specific repair.

| Assumption | What real firmware does | Repair |
|---|---|---|
| Tasks are periodic with period `T` | Some events are aperiodic | Model as **sporadic**: use the minimum interarrival time as `T` |
| Deadline `D` equals period `T` | Sometimes `D < T` | Use **deadline-monotonic** priority order; response-time analysis still applies unchanged |
| Tasks are independent — no shared resources | They share buffers and peripherals | Add a **blocking term** `B` (see below) |
| Preemption is instantaneous and free | Context switch costs cycles | Fold the switch cost into each `C` |
| One processor, fully preemptive | Interrupts sit *above* every task | Model each ISR as a task with a period equal to its minimum interarrival time |

That last row is the one specific to firmware and the one most often forgotten. On a Cortex-M every interrupt handler preempts every RTOS task, regardless of task priorities — the NVIC does not know the scheduler exists. Handler execution time is therefore interference on *everything*, and it belongs in the analysis as a set of highest-priority tasks. [Priorities and Nesting](./interrupt-priorities-and-nesting.md) covers the mechanism; this page treats handlers as tasks with very short periods.

Notation used throughout: `C` is worst-case execution time, `T` is period, `D` is deadline, `R` is worst-case response time, and `U` is utilisation, the sum of `C/T` over all tasks.

## Rate-monotonic priority assignment

Order tasks by period. Shortest period gets the numerically highest priority in whatever the scheduler's convention is. Do not order by importance, by criticality, by how loudly the customer complained, or by which subsystem the author owns.

The reason this is optimal rather than merely sensible is the **critical-instant** result: a task's worst-case response occurs when it is released at the same moment as every higher-priority task, with all of them then re-arriving as fast as their periods allow. Under that alignment, the interference a task suffers is entirely determined by how many times each higher-priority task can run inside its response window — which is set by their periods. Giving the frequently-arriving task a lower priority maximises exactly the term you are trying to minimise.

## The utilisation bound

For `n` tasks under rate-monotonic priorities, Liu and Layland proved a least upper bound on utilisation:

**U ≤ n(2^(1/n) − 1)**

If total utilisation is at or below that value, the set is schedulable. Full stop, no further work. The bound decreases with `n` and converges to ln 2 ≈ 0.6931:

| `n` | Bound `n(2^(1/n) − 1)` |
|---|---|
| 1 | 1.0000 |
| 2 | 0.8284 |
| 3 | **0.7798** |
| 4 | 0.7568 |
| 5 | 0.7435 |
| 10 | 0.7177 |
| → ∞ | 0.6931 (ln 2) |

*Computed from the closed form above; verify any row with a calculator before quoting it.*

The rule of thumb that fell out of this — "keep a fixed-priority system under about 69% CPU" — is genuinely useful as a design target, because it means you never have to do any further analysis. It is also, taken as a hard limit, wrong, and the rest of this page is about why.

## A worked task set

Three tasks on a NUCLEO-F411RE at 100 MHz. All times in microseconds; the `C` values are worst-case execution times obtained as described in [Worst-Case Execution Time](./wcet.md), not averages.

| Task | Job | `T` (µs) | `C` (µs) | Priority (RM) | `U = C/T` |
|---|---|---|---|---|---|
| τ1 | Current-control loop, 1 kHz | 1000 | 300 | highest | 300/1000 = **0.30** |
| τ2 | IMU read and sensor fusion, 400 Hz | 2500 | 900 | middle | 900/2500 = **0.36** |
| τ3 | Host protocol and logging, 100 Hz | 10000 | 1000 | lowest | 1000/10000 = **0.10** |
| | | | | | **U = 0.76** |

Utilisation is 0.30 + 0.36 + 0.10 = **0.76**. The bound for `n` = 3 is 3(2^(1/3) − 1) = **0.7798**. Since 0.76 ≤ 0.7798, **this task set is schedulable under rate-monotonic priorities** and there is nothing further to prove. Every task always meets its deadline.

Worth noticing how much slack the bound throws away even here. Response-time analysis on the same set gives τ3 a worst-case response of 4000 µs against a 10 000 µs deadline — 60% margin — while the bound was within 0.02 of refusing to certify it at all.

## Sufficient, not necessary

Now the comms task grows. Someone adds a checksum over a larger frame and `C3` goes from 1000 µs to 2500 µs.

| Task | `T` (µs) | `C` (µs) | `U = C/T` |
|---|---|---|---|
| τ1 | 1000 | 300 | 0.30 |
| τ2 | 2500 | 900 | 0.36 |
| τ3 | 10000 | 2500 | 0.25 |
| | | | **U = 0.91** |

U = 0.91, and the bound is 0.7798. **The bound says nothing.** It does not say the set is unschedulable — it says this particular sufficient test cannot certify it. Those are entirely different statements, and treating the first as the second is the misreading that causes teams to redesign systems that were fine.

Even a tighter sufficient test declines. The hyperbolic bound (Bini, Buttazzo and Buttazzo, 2003) certifies a set when the product of `U_i + 1` over all tasks is at most 2. Here that product is 1.30 × 1.36 × 1.25 = **2.21**, which exceeds 2, so it too fails to certify. (For the earlier set it was 1.30 × 1.36 × 1.10 = 1.9448 ≤ 2, consistent with the utilisation bound's verdict.)

To get an actual answer you need an exact test.

## Response-time analysis

For fixed-priority preemptive scheduling with deadlines no greater than periods, response-time analysis is **necessary and sufficient**: it computes the true worst-case response time, so if `R ≤ D` for every task the set is schedulable, and if any `R > D` it genuinely is not.

The worst-case response time of task *i* is the fixed point of

```text
R = C_i + SUM over all higher-priority tasks j of  ceil(R / T_j) * C_j
```

Read it as: my own execution time, plus one full execution of every higher-priority task for every release of it that can fall inside my response window. The ceiling is what makes it a fixed point — a longer `R` admits more releases, which makes `R` longer. Solve by iteration, starting from the sum of `C` values at this priority and above, and stop when two successive values are equal. If the value ever exceeds `D`, stop early: the task misses.

**τ1** has nothing above it, so R1 = C1 = **300 µs** ≤ 1000 µs. Passes.

**τ2**, interfered with by τ1:

```text
R⁰ = 300 + 900                             = 1200
R¹ = 900 + ceil(1200/1000)·300 = 900 + 2·300 = 1500
R² = 900 + ceil(1500/1000)·300 = 900 + 2·300 = 1500   ← fixed point
```

R2 = **1500 µs** ≤ 2500 µs. Passes, with 1000 µs of slack.

**τ3**, interfered with by both. This is the one worth doing slowly, because the interference terms step up at different points:

```text
R⁰ = 300 + 900 + 2500                                            = 3700
R¹ = 2500 + ceil(3700/1000)·300 + ceil(3700/2500)·900
   = 2500 + 4·300 + 2·900 = 2500 + 1200 + 1800                   = 5500
R² = 2500 + ceil(5500/1000)·300 + ceil(5500/2500)·900
   = 2500 + 6·300 + 3·900 = 2500 + 1800 + 2700                   = 7000
R³ = 2500 + ceil(7000/1000)·300 + ceil(7000/2500)·900
   = 2500 + 7·300 + 3·900 = 2500 + 2100 + 2700                   = 7300
R⁴ = 2500 + ceil(7300/1000)·300 + ceil(7300/2500)·900
   = 2500 + 8·300 + 3·900 = 2500 + 2400 + 2700                   = 7600
R⁵ = 2500 + ceil(7600/1000)·300 + ceil(7600/2500)·900
   = 2500 + 8·300 + 4·900 = 2500 + 2400 + 3600                   = 8500
R⁶ = 2500 + ceil(8500/1000)·300 + ceil(8500/2500)·900
   = 2500 + 9·300 + 4·900 = 2500 + 2700 + 3600                   = 8800
R⁷ = 2500 + ceil(8800/1000)·300 + ceil(8800/2500)·900
   = 2500 + 9·300 + 4·900                                        = 8800   ← fixed point
```

R3 = **8800 µs** ≤ 10 000 µs. **Every task meets its deadline at U = 0.91, well above the 0.7798 bound.** The point is now demonstrated rather than asserted: exceeding the utilisation bound does not make a task set unschedulable, and the only correct response to failing a sufficient test is to run an exact one.

It also shows what "above the bound" really costs you: 1200 µs of slack on a 10 000 µs deadline, 12%. That is thin. It is enough for a shipping product only if the `C` values are genuine worst cases rather than measured maxima, which is the entire argument of the WCET page.

Two more facts that follow the same shape:

- **Harmonic task sets reach U = 1 under rate-monotonic priorities.** With T = 1000, 2000 and 10 000 µs — each period an exact multiple of the shorter ones — take C = 300, 500 and 4500 µs, so U = 0.30 + 0.25 + 0.45 = **1.00**. Response-time analysis converges to R3 = 10 000 µs, exactly the deadline: schedulable. Deliberately choosing harmonic periods is one of the cheapest real-time design decisions available, and it is free at design time and impossible later.
- **The iteration always terminates when U ≤ 1**, and diverges past the deadline when it does not. In practice you cap it: stop when `R > D` and report the miss.

## Blocking, and where the extra terms go

Real tasks share things. When a lower-priority task holds a resource a higher-priority task needs, the higher-priority task is *blocked*, and unlike preemption this is interference from below. Under an unbounded protocol it is unbounded — the classic priority inversion. Under priority inheritance or an immediate ceiling protocol it is bounded, and the bound enters response-time analysis as a single additive term:

```text
R = C_i + B_i + SUM over higher-priority j of  ceil(R / T_j) * C_j
```

`B_i` is the longest single critical section that a lower-priority task can hold on a resource task *i* can request. [Shared Data and Race Conditions](./shared-data-and-race-conditions.md) covers the mechanics of the sharing; [Concurrency and Synchronization](../../computer-science/operating-systems/concurrency-and-synchronization.md) owns the protocol theory. What matters here is that it is one more term in the same equation, and that a system with unbounded blocking has no `R` at all — the analysis does not merely give a large answer, it gives no answer.

Interrupt handlers slot in the same way: as tasks at the top of the priority order, with `T` set to their minimum interarrival time. An ISR that takes 20 µs and can arrive every 200 µs contributes 10% utilisation and appears in every task's interference sum.

## Earliest deadline first

EDF assigns priority dynamically: at any instant, the ready task with the nearest absolute deadline runs. Liu and Layland's other major result is that on a single preemptive processor with deadlines equal to periods, EDF is schedulable **if and only if U ≤ 1**. That is both a sufficient and a necessary condition, and it is the best any algorithm can do — no scheduler can do better than 100% of a processor.

So EDF dominates rate-monotonic on utilisation, by a wide margin at large `n`. It is nonetheless rare in firmware, for reasons worth knowing:

- **No mainstream small RTOS implements it.** FreeRTOS and Zephyr are fixed-priority preemptive schedulers. Using EDF means writing or porting a scheduler, which is a large amount of code to trust in exchange for utilisation you can usually buy with a faster part.
- **The runtime cost is per-release, not per-design.** Every release must compute an absolute deadline and the scheduler must order by it, rather than reading a static priority field. On a small MCU that is real overhead in the one place you least want it.
- **Overload behaviour is much worse.** Under transient overload, rate-monotonic degrades predictably: the longest-period tasks miss first and the urgent short-period ones keep running. EDF has no such ordering — a task that has already missed has the nearest deadline of all, so it is scheduled first, and it can cascade into a domino effect where nearly everything misses. For a system whose overload behaviour has to be defensible, "the logging task misses" is a far better failure mode than "something misses, we cannot say what".

The honest summary: EDF is theoretically better and rate-monotonic is what you will ship. Knowing the EDF bound is still useful, because U ≤ 1 tells you whether the *processor* is the problem. If your set fails response-time analysis but U is 0.6, the problem is the priority assignment or the blocking, not the CPU.

:::warning[The priority assignment made by importance, which fails at the same utilisation]
Take the exact task set proved schedulable above — τ1 at 1000/300, τ2 at 2500/900, τ3 at 10 000/2500, U = 0.91 — and assign priorities by importance instead of by rate. The host protocol task "is the most important thing in the product, it's what the customer sees", so τ3 goes on top, then τ2, then the control loop τ1 at the bottom.

Nothing about the code changes. Utilisation is still 0.91. Response-time analysis:

- τ3 (now highest): R = 2500 µs ≤ 10 000 µs. Passes.
- τ2: R⁰ = 900 + 2500 = 3400; R¹ = 900 + ceil(3400/10000)·2500 = 900 + 2500 = 3400, fixed point. **R2 = 3400 µs against a 2500 µs deadline — misses.**
- τ1: R⁰ = 3700; R¹ = 300 + ceil(3700/2500)·900 + ceil(3700/10000)·2500 = 300 + 1800 + 2500 = 4600; R² = 300 + ceil(4600/2500)·900 + ceil(4600/10000)·2500 = 300 + 1800 + 2500 = 4600, fixed point. **R1 = 4600 µs against a 1000 µs deadline — the 1 kHz control loop is 4.6× over.**

The symptom on the bench is not a missed-deadline error, because nothing detects one. It is a control loop that runs at an average rate near 1 kHz with occasional 4–5 ms gaps whenever a host frame arrives, which presents as motor torque ripple, or a PID loop that is unstable only when the operator has the diagnostic tool connected. Weeks get spent tuning gains. The tell is correlation with an unrelated subsystem's activity: if the control behaviour changes when you plug in the USB cable, the problem is scheduling, not control. **Priority is assigned by rate. Importance is expressed by which deadlines you make hard, never by priority order.**
:::

## Applying it without a spreadsheet

The analysis is worth doing on paper for the four or five tasks that have real deadlines, and not worth doing at all for the rest. A workable discipline:

1. **List only tasks with deadlines.** Everything else is background and goes at the lowest priority, where it cannot interfere with anything.
2. **Include every ISR** as a top-priority task with its minimum interarrival time.
3. **Make periods harmonic** where you have the freedom. 1, 2, 10 ms beats 1, 3, 7 ms for nothing.
4. **Get `C` values honestly.** A measured maximum is not a worst case, and response-time analysis is exact only with respect to the numbers you feed it.
5. **Re-run it when `C` changes.** The set above went from comfortable to 12% margin because one checksum got longer. Nobody re-ran the analysis, because nobody had written it down.

Step 5 is the one that decides whether any of this survives contact with a product. Keep the table in the repository next to the code, with the source of every `C`, and treat it as something the build breaks over.

## See also

- [What "Real-Time" Actually Means](./real-time-definitions.md) — deadline classes and arrival patterns, which are the inputs this page's arithmetic consumes.
- [Worst-Case Execution Time](./wcet.md) — where the `C` values come from, and what it takes to defend one as a worst case rather than a maximum observed.
- [Priorities and Nesting](./interrupt-priorities-and-nesting.md) — how the priority order derived here is expressed in NVIC priority numbers on a Cortex-M.
- [Scheduling](../../computer-science/operating-systems/scheduling.md) — the general theory of schedulers, including the throughput-oriented algorithms this page deliberately ignores.
- [Bare Metal, RTOS, or Linux](../00-overview/bare-metal-vs-rtos-vs-linux.md) — whether you need a preemptive scheduler at all before any of this applies.

## References

- C. L. Liu and J. W. Layland — [***Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment***](https://dl.acm.org/doi/10.1145/321738.321743), *Journal of the ACM* 20(1):46–61, January 1973. The rate-monotonic optimality proof, the critical-instant argument, and the derivation of the least upper bound `n(2^(1/n) − 1)` in the fixed-priority section; the deadline-driven (EDF) section proves that U ≤ 1 is necessary and sufficient there. Everything on this page traces back to this paper. ACM Digital Library.
- M. Joseph and P. Pandya — ***Finding Response Times in a Real-Time System***, *The Computer Journal* 29(5):390–395, 1986. The original response-time formulation, which is the exact test used above and the reason the utilisation bound can be treated as a shortcut rather than a limit.
- N. C. Audsley, A. Burns, M. Richardson, K. Tindell and A. J. Wellings — ***Applying New Scheduling Theory to Static Priority Pre-emptive Scheduling***, *Software Engineering Journal* 8(5):284–292, 1993. The iterative fixed-point solution as it is actually applied, plus the extensions this page summarises: blocking terms, release jitter, and deadlines shorter than periods.
- E. Bini, G. C. Buttazzo and G. M. Buttazzo — ***Rate Monotonic Analysis: The Hyperbolic Bound***, *IEEE Transactions on Computers* 52(7):933–942, 2003. The tighter sufficient test used above (the product of `U_i + 1` at most 2), and a clear discussion of why any sufficient test necessarily rejects schedulable sets.
- L. Sha, R. Rajkumar and J. P. Lehoczky — ***Priority Inheritance Protocols: An Approach to Real-Time Synchronization***, *IEEE Transactions on Computers* 39(9):1175–1185, 1990. Where the blocking term `B` comes from, and the protocols that make it bounded rather than arbitrary.
- Giorgio Buttazzo — ***Hard Real-Time Computing Systems***, Springer, 3rd edition, 2011. Chapters 4 and 6 work through rate-monotonic and EDF with full proofs, and Chapter 9 covers the overload behaviour that makes EDF a poor default for firmware. A purchase.
