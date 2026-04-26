---
id: behavior-trees-and-blackboard
title: Behavior trees and the blackboard
sidebar_label: Behavior trees & blackboard
sidebar_position: 2
tags: [ unreal-engine, ue5, c++, behavior-tree, blackboard, ai ]
---

# Behavior trees and the blackboard

A Behavior Tree (`UBehaviorTree`) is a re-entrant tree of nodes that gets re-evaluated every tick from
the root, not a script that runs top to bottom once. Every piece of state the tree reasons about lives
outside the tree, in a `UBlackboardComponent`. Without that split understood up front, the abort
system — the mechanism that lets a low-priority branch get interrupted the instant a higher-priority
condition becomes true — looks like unpredictable magic instead of the deliberate re-evaluation model
it actually is.

## Why this matters

A naive "if enemy visible, attack, else patrol" state machine has to be hand-written to check the
enemy-visible condition constantly, everywhere it's relevant. Behavior Trees invert that: composites
express priority, decorators express conditions, and the tree's execution engine re-checks decorator
conditions on relevant blackboard changes and aborts lower-priority branches automatically. Once you
understand that a Behavior Tree is continuously re-selecting which branch is allowed to run — not
"executing a script" — the abort model, and the bugs that come from misconfiguring it, both make sense.

## Mental model

```mermaid
flowchart TD
    Root["Root"]
    Sel["Selector: Combat"]
    SeqAttack["Sequence: Attack\n(decorator: Blackboard.HasTarget)"]
    TaskAttack["Task: Attack Target"]
    SeqPatrol["Sequence: Patrol"]
    TaskMove["Task: Move To Patrol Point"]
    Service["Service: Update Nearest Enemy\n(attached to Selector)"]

    Root --> Sel
    Sel --> SeqAttack
    Sel --> SeqPatrol
    SeqAttack --> TaskAttack
    SeqPatrol --> TaskMove
    Service -.ticks while Selector is active,\nwrites Blackboard.HasTarget.-> Sel

    BB[("Blackboard\nHasTarget: bool\nTargetActor: Object\nPatrolPoint: Vector")]
    Service -->|writes| BB
    SeqAttack -->|reads via decorator| BB
    TaskAttack -->|reads TargetActor| BB
```

The Selector picks the first child that can run, highest priority first (left to right, by default).
The Service on the Selector keeps `HasTarget` current whenever that branch is active. The decorator on
`Sequence: Attack` doesn't just gate entry — depending on its **observer abort** setting, it keeps
watching `HasTarget` even while `Sequence: Patrol` is executing below it, and can rip control back to
`Sequence: Attack` the instant the value flips.

## The building blocks

### Composites: Selector, Sequence, Simple Parallel

- **Selector** (`UBTComposite_Selector`) — runs children in order until one **succeeds**; if a child
  fails, it tries the next. This is how you express priority: put the highest-priority behavior first.
- **Sequence** (`UBTComposite_Sequence`) — runs children in order until one **fails**; if a child
  succeeds, it moves to the next. This is how you express "do these steps in order, bail if any step
  can't."
- **Simple Parallel** (`UBTComposite_SimpleParallel`) — runs one main task and one background tree
  branch simultaneously (e.g. play an animation montage task while a background branch keeps checking
  a condition). It's deliberately limited to exactly one task plus one subtree, not a general
  multi-branch parallel.

### Tasks

A `UBTTaskNode` (or Blueprint `Task`) is a leaf that does something and returns `Succeeded`, `Failed`,
or `InProgress` (for tasks that finish asynchronously, e.g. movement). `UBTTask_MoveTo` and
`UBTTask_RunEQSQuery` are the built-in tasks you'll use constantly; most gameplay-specific behavior
(play a montage, fire a weapon, run a StateTree) is a custom `UBTTaskNode` subclass.

### Decorators

A `UBTDecorator` gates whether a node (or subtree) is allowed to execute, and optionally keeps
observing its condition afterward — this is the abort mechanism, covered below. Decorators can be
pure conditions (Blackboard-based, Cooldown, custom C++) or can invert their result.

### Services

A `UBTService` attaches to a composite and ticks on an interval (`Interval` / `RandomDeviation`)
**while that composite's subtree is active** — regardless of which specific child is currently
running. Services are how you keep blackboard values fresh (nearest enemy, last known location)
without every leaf task having to poll for it.

## The Blackboard

`UBlackboardComponent` is typed key/value storage, described by a `UBlackboardData` asset. Keys have
declared types — `Bool`, `Int`, `Float`, `Vector`, `Object`, `Class`, `Enum`, `Name`, `String` — and
that typing is what lets decorators and the editor validate key usage instead of you discovering a
type mismatch at runtime.

```cpp title="Reading and writing blackboard values from a custom task"
EBTNodeResult::Type UBTTask_UpdateNearestEnemy::ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory)
{
    UBlackboardComponent* BB = OwnerComp.GetBlackboardComponent();
    if (AActor* Nearest = FindNearestEnemy(OwnerComp))
    {
        BB->SetValueAsObject(TargetActorKey.SelectedKeyName, Nearest);
        BB->SetValueAsBool(HasTargetKey.SelectedKeyName, true);
        return EBTNodeResult::Succeeded;
    }

    BB->SetValueAsBool(HasTargetKey.SelectedKeyName, false);
    return EBTNodeResult::Failed;
}
```

`FBlackboardKeySelector` (`TargetActorKey`, `HasTargetKey` above) is the standard `UPROPERTY` type for
exposing a configurable blackboard key on a task/decorator/service in the editor, filtered to a
specific value type.

```cpp title="UBTTask_UpdateNearestEnemy.h"
UCLASS()
class MYGAME_API UBTTask_UpdateNearestEnemy : public UBTTaskNode
{
    GENERATED_BODY()

public:
    virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;

protected:
    UPROPERTY(EditAnywhere, Category = "Blackboard")
    FBlackboardKeySelector TargetActorKey;

    UPROPERTY(EditAnywhere, Category = "Blackboard")
    FBlackboardKeySelector HasTargetKey;
};
```

## Decorator abort modes — the #1 source of confusion

Every Blackboard-based decorator has an **Observer Aborts** setting, backed by `EBTFlowAbortMode`:

| Mode | Behavior |
|---|---|
| `None` | The decorator is only checked when the tree tries to enter that node. It never interrupts something already running. |
| `LowerPriority` | If the condition changes, abort any **currently running node with lower priority** than this decorator, so a higher-priority branch can take over. |
| `Self` | If the condition changes to fail, abort **this decorator's own subtree** if it's the one currently running. |
| `Both` | Combines `LowerPriority` and `Self` — this decorator watches its condition continuously and can abort either the branch below it or a lower-priority sibling branch, whichever is currently running. |

The trap: `None` is deceptively "safe-looking" because you never see unexpected interruptions — but
it's also why a decorator that should be reactive (e.g. "abort the patrol the instant an enemy is
seen") silently does nothing until the tree happens to re-enter that node on its own. `LowerPriority`
is what most "interrupt a lower-priority behavior when a condition becomes true" designs actually want,
and it only works because the decorator sits on a **higher**-priority sibling in a Selector — it has no
lower-priority sibling to abort if you put it in the wrong place in the tree.

:::warning Abort mode only matters if there's something to abort
`LowerPriority` and `Both` require the decorator to actually have lower-priority siblings under the
same Selector that could be running. A decorator on the only child of a Sequence, or on the
highest-priority child when nothing else is running, has nothing to interrupt — the abort mode setting
does nothing observable and the bug report becomes "my AI doesn't react," when the real issue is tree
structure, not the decorator.
:::

:::caution Services tick on an interval, not on write
A Service's `Interval`/`RandomDeviation` means the blackboard value it maintains can be up to one
interval stale. If a decorator with `LowerPriority` abort depends on a value a Service writes, the
reaction time to that condition is bounded by the Service's interval, not by decorator-checking speed —
tighten the interval if the reaction needs to feel instant, but that costs more ticks per active agent.
:::

## See also

- [Environment query system](./environment-query-system.md) — `UBTTask_RunEQSQuery` is one of the most
  common built-in tasks, and it writes its result to a blackboard key.
- [AI controller and perception](./ai-controller-and-perception.md) — perception updates are the
  typical trigger for the blackboard changes decorators react to.
- [State tree](./state-tree.md) — the newer alternative to Behavior Tree + Blackboard for some AI, with
  a comparison of when each fits better.
- [Epic — Behavior Trees](https://dev.epicgames.com/documentation/unreal-engine/behavior-trees-in-unreal-engine)
- [Epic — Behavior Tree Blackboard](https://dev.epicgames.com/documentation/unreal-engine/behavior-tree-blackboard-in-unreal-engine)
