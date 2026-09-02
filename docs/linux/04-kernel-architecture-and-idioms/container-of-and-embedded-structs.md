---
id: container-of-and-embedded-structs
title: "`container_of` and Embedded Structs"
sidebar_label: "container_of"
sidebar_position: 8
tags: [linux, kernel]
prerequisites:
  - linux/kernel-architecture-and-idioms/kernel-data-structures
draft: false
---

# `container_of` and Embedded Structs

The central Linux idiom derived from scratch, after which kobjects, the VFS, and the device model all become readable at once.

One macro unlocks a large fraction of the kernel's design. If the previous page's diagram made sense — link
pointers pointing at *fields* embedded inside objects, never at the objects themselves — then the next
question answers itself: given a pointer to the field, how do you get back to the object that contains it?
The answer is arithmetic, not indirection, and it's short enough to derive exactly once and then recognise
everywhere.

## The problem, concretely

Take the `struct request` from the previous page:

```c
struct request {
	int id;
	struct list_head list;
};
```

`list_for_each_entry(r, &pending_requests, list)` hands the loop body an `r` of type `struct request *` —
but every pointer the list machinery actually stores and traverses, `next` and `prev`, is a `struct
list_head *`, pointing at the `list` field, not at the `struct request` that contains it. Somewhere inside
`list_for_each_entry`, something is converting "the address of a `list_head` field" into "the address of
the `struct request` that embeds it at that field." That conversion is `container_of`, and it's worth
deriving instead of just quoting.

## Deriving it

Three small steps, each independently obvious, that compose into the whole trick.

**1. A field's offset within its type is a compile-time constant.** The compiler already knows, at compile
time, exactly how many bytes into a `struct request` the `list` field sits — that's what `offsetof` asks
for and gets, with no runtime cost:

```c
size_t off = offsetof(struct request, list);   /* a constant, known at compile time */
```

**2. The object's address is the field's address minus that offset.** If you have a `struct list_head *p`
that you know points at the `list` field of some `struct request`, then the `struct request` itself starts
`off` bytes earlier in memory:

```c
struct request *r = (struct request *)((char *)p - off);
```

**3. Wrap it so the compiler still type-checks the result.** Steps 1–2 as raw pointer arithmetic compile
and run, but they throw away every bit of type safety the compiler could otherwise give you — a caller could
pass a pointer into the wrong kind of struct entirely and nothing would complain. The kernel's actual macro
wraps the arithmetic with exactly enough type machinery to catch that:

```c
#define container_of(ptr, type, member) ({				\
	void *__mptr = (void *)(ptr);					\
	static_assert(__same_type(*(ptr), ((type *)0)->member) ||	\
		      __same_type(*(ptr), void),			\
		      "pointer type mismatch in container_of()");	\
	((type *)(__mptr - offsetof(type, member))); })
```

Read it term by term:

- `void *__mptr = (void *)(ptr);` stashes the incoming pointer in a local so the expression only evaluates
  `ptr` once, even though it's referenced twice below — important if `ptr` is itself an expression with a
  side effect, not just a plain variable.
- `static_assert(__same_type(*(ptr), ((type *)0)->member) || __same_type(*(ptr), void), ...)` is the type
  check step 3 promised: it compares the type of what `ptr` points at against the type of the named
  `member` field inside `type`, at compile time, and refuses to build if they don't match (a `void *ptr` is
  allowed through as an explicit escape hatch). This is exactly what catches "I passed a `list_head *` that
  actually belongs to a different struct" — the arithmetic in steps 1–2 would happily compute a wrong-but-
  valid-looking pointer with no such check.
- `((type *)(__mptr - offsetof(type, member)))` is steps 1 and 2, verbatim: subtract the field's offset from
  the field's address, cast the result to a pointer to the containing type.

The whole thing is wrapped in a GCC statement expression, `({ ... })`, precisely so it can perform that
intermediate `static_assert` and local-variable bookkeeping while still being usable anywhere an ordinary
expression is — the "GCC extensions in daily use" from the dialect page, put to real use.

:::note
v6.18's `include/linux/container_of.h` also defines `container_of_const()`, which does the same derivation
but preserves a `const`-qualified input pointer's constness through the cast — something a straight
`container_of()` call silently drops. The header comments now recommend `container_of_const()` for new
code; `container_of()` itself remains, unchanged, everywhere it's already used.
:::

## The three-subsystem tour

The same three-step pattern — pointer to an embedded field in hand, offset known at compile time, arithmetic
gets you the containing object — repeats across the kernel in places that look, on first read, like
unrelated subsystems.

**A driver walking a list of its own device structures.** `drivers/char/misc.c` keeps every registered
miscellaneous device on one list, `misc_list`, linked through a `list_head` embedded in `struct miscdevice`:

```c
struct miscdevice {
	int minor;
	const char *name;
	const struct file_operations *fops;
	struct list_head list;
	/* ... */
};
```

Opening a misc device by minor number is a linear scan of that list, recovering each `struct miscdevice *`
from its embedded `list` field the same way the previous page's `struct request` example did:

```c
list_for_each_entry(iter, &misc_list, list) {
	if (iter->minor != minor)
		continue;
	c = iter;
	new_fops = fops_get(iter->fops);
	break;
}
```

Nothing here calls `container_of` by name — `list_for_each_entry` does it internally, on every step of the
walk, which is exactly the point: once you can read the macro, every `list_for_each_entry` loop in the tree
is a `container_of` call you no longer have to think about consciously.

**The VFS recovering a filesystem-specific inode from a `struct inode`.** Every filesystem that needs more
per-inode state than the generic `struct inode` provides embeds a `struct inode` *inside* its own,
larger struct, rather than pointing at one separately. ext4's version:

```c
static inline struct ext4_inode_info *EXT4_I(struct inode *inode)
{
	return container_of(inode, struct ext4_inode_info, vfs_inode);
}
```

The VFS layer hands filesystem code a `struct inode *` — the generic type every filesystem shares — and
`EXT4_I()` is how ext4-specific code gets back to the full `struct ext4_inode_info` that generic pointer is
actually embedded in. Every filesystem with private per-inode state has its own version of this exact
accessor.

**A `kobject` embedded in a device structure.** `struct device` embeds a `struct kobject` as an ordinary
field:

```c
struct device {
	struct kobject kobj;
	struct device *parent;
	/* ... */
};
```

and the device model needs to go the other direction constantly — sysfs code holds a `struct kobject *` and
needs the `struct device *` that owns it:

```c
#define kobj_to_dev(__kobj)	container_of_const(__kobj, struct device, kobj)
```

This is the pattern the next page is entirely about: the kobject is the device model's generic, embeddable
"this object participates in sysfs" building block, and `container_of`/`container_of_const` is how every
subsystem that embeds one gets back to its own richer type.

## Why this instead of a `void *data` pointer

A tempting alternative design would give every "generic" struct a `void *private_data` field pointing at
whatever type-specific data the concrete implementation needs — no macro, no arithmetic, just an opaque
pointer the concrete code casts back. The kernel avoids that pattern almost everywhere it has this choice,
for reasons that hold up:

- **No extra allocation.** A `void *` field pointing at type-specific data means that data lives somewhere
  else — allocated separately, with its own lifetime to track. An embedded struct's "type-specific data" is
  the same allocation as the generic struct; there is nothing else to allocate or free.
- **No extra dereference.** Recovering the concrete object from an embedded field is one subtraction.
  Recovering it from a `void *private_data` field is a *pointer to a pointer*: dereference the generic
  struct to load `private_data`, then dereference that to reach the actual data — an extra memory access on
  a path that, in `list_for_each_entry`'s case, runs on every single list iteration.
- **Type checked at compile time.** `container_of`'s `static_assert` catches a mismatched member at compile
  time. A `void *` cast catches nothing until (if you're lucky) it crashes at runtime.
- **The object can't get separated from its links.** Because the link field and the object are the same
  allocation, there's no way to free the object while a `void *` elsewhere still points at stale data — the
  usual failure mode a separate side-pointer design has to guard against by hand.

## What actually happens

`EXT4_I()` from above is a good function to actually read as compiled code, because it's small, stable, and
does nothing but a `container_of` call:

```c
static inline struct ext4_inode_info *EXT4_I(struct inode *inode)
{
	return container_of(inode, struct ext4_inode_info, vfs_inode);
}
```

Expanding the macro by hand: `offsetof(struct ext4_inode_info, vfs_inode)` is a compile-time constant — say
it's `N` bytes, whatever ext4's actual struct layout makes it. The function body becomes, after macro
expansion and with the `static_assert` elided (it produces no code, only a compile-time check):

```c
static inline struct ext4_inode_info *EXT4_I(struct inode *inode)
{
	return (struct ext4_inode_info *)((char *)inode - N);
}
```

That's a pointer subtraction by a compile-time-known constant — and a subtraction by a *known constant* is
exactly the shape of computation a CPU's addressing modes already do for free. The compiler doesn't emit a
separate `sub` instruction and then a load; it folds the constant offset directly into the addressing mode
of whatever instruction next touches the returned pointer, the same way it would fold a struct member access
like `inode->i_mode` into a load with a small constant displacement. `container_of` is not a runtime
indirection layered on top of a plain pointer — compiled, it disappears into ordinary pointer arithmetic
that costs nothing beyond what dereferencing any struct member already costs. That's the payoff of the whole
design: an idiom that looks like it should be expensive machinery is, after compilation, exactly as cheap as
the direct field access it replaces.

## The arithmetic, laid out

```text
struct ext4_inode_info {
        ...                          offset 0
        ...
        struct inode vfs_inode;  ←── offset N            ←─┐  ptr you have:
        ...                                                 │  &ext4_i->vfs_inode
}                                                            │  (== the struct inode *
 ↑                                                           │   the VFS hands you)
 └── ptr you want: ext4_i ── (char *)&ext4_i->vfs_inode − N ┘
```

*The pointer you have, the offset the compiler knows, and the pointer you want.*

<KernelFacts
  structure={[["container_of()", "include/linux/container_of.h"], ["offsetof()", "include/linux/stddef.h"]]}
  path="pointer to an embedded member → minus offsetof(type, member) → pointer to the containing object, cast and type-checked"
  observe="include/linux/container_of.h — `container_of` (a structural macro with no runtime command; the header is twelve lines and reads faster than any command's output would explain it)"
  trap="`container_of` does not check that the pointer it's given really is inside an object of that type — it only checks that the *pointed-to type* matches the named member's type. Pass a `list_head *` that belongs to the wrong kind of struct entirely and you get a valid-looking pointer to garbage, with no fault and no warning." />

## References

- <Src file="include/linux/container_of.h" /> — the macro itself, twelve lines, worth reading in full rather
  than taking this page's term-by-term walkthrough as a substitute.
- [Driver basics](https://docs.kernel.org/driver-api/basics.html) — the kernel's own list of these
  fundamental helpers, `container_of` included, in the context they were built for.
- [The Kernel Hacker's Bookshelf: Kernel Data Structures](https://lwn.net/Articles/22195/) — a classic
  explanation of the intrusive-list model; old, but the model itself has not changed since.
