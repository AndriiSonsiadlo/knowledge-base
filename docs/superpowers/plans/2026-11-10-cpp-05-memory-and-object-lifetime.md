# C++ section 05 (Memory and Object Lifetime) rewrite

Rewrite the not-yet-rewritten pages of `docs/programming/cpp/05-memory-and-object-lifetime/`
to the same standard as the already-rewritten `alignment.md` and `placement-new.md` in that
folder, and the section `04-functions-and-call-mechanics/` pages.

## Global Constraints

- Read `AUTHORING.md` (repo root) and root `CLAUDE.md` content rules before writing. They bind.
- Quality exemplars (read at least one fully before writing): `05-memory-and-object-lifetime/alignment.md`,
  `04-functions-and-call-mechanics/calling-conventions.md`.
- Keep each page's existing `id` (links depend on it). Keep frontmatter complete: `id`, `title`,
  `sidebar_label`, `sidebar_position`, `tags`. No duplicate `sidebar_position` within a folder.
- One canonical home per concept: before writing, grep `docs/programming/cpp` for the page's key
  terms; recap + link instead of re-explaining what another page owns. Within this section the
  owners are: lifetime rules → `object-lifetime`; storage durations → `storage-duration`;
  `new`/`delete` expressions and operator new → `new-and-delete`; placement new → `placement-new`;
  alignment → `alignment`; aliasing/type punning → `strict-aliasing`; init forms → `initialization/*`.
- Never invent facts. Standard wording/behaviour must match the C++ standard / cppreference; mark
  the standard version where behaviour changed (C++11/17/20/23).
- Code snippets compile as shown (test with `g++ -std=c++20 -Wall -Wextra` in a scratch dir, or
  mark explicitly as fragments). Show compiler output only if you actually ran it.
- Diagrams: `<Diagram>` component, not Mermaid, unless it's a sequence/state diagram.
- No filler; rewrite, don't pad. Remove content that is wrong or belongs to another page's home.
- Gate: `npm run build` must pass. Commit once per task: `docs: rewrite C++ <page> page`
  (one line, no trailers, no Co-Authored-By).

## Task 1: memory-model-overview.md
Rewrite `memory-model-overview.md` as the section's entry page: the C++ abstract machine's view of
memory (objects, bytes, memory locations), how storage, lifetime, alignment, and aliasing relate,
and a map linking to every other page in the folder. Must not cover the concurrency memory model
beyond a one-sentence pointer (that lives in `11-concurrency-and-memory-model`).

## Task 2: storage-duration.md
Rewrite `storage-duration.md`: automatic, static, thread, dynamic storage duration; linkage vs
storage distinction; static initialization order (zero/constant/dynamic init, static init order
fiasco, function-local statics and their thread-safe init since C++11). Decide what to do with
`stack-vs-heap.gif` (keep via `<Figure>` if it helps, else delete the file) and record the decision
in the report.

## Task 3: object-lifetime.md
Rewrite `object-lifetime.md`: when lifetime begins/ends, temporaries and lifetime extension,
dangling references, implicit object creation (C++20), `std::launder`, `std::start_lifetime_as`
(C++23). Link to `placement-new` rather than re-explaining it.

## Task 4: new-and-delete.md
Rewrite `new-and-delete.md`: new/delete expressions vs `operator new`/`operator delete`, array
forms, mismatched forms as UB, `std::nothrow`, `std::bad_alloc`, replaceable allocation functions,
sized and aligned deallocation (C++14/17). Point to smart pointers section (`06-…`) for ownership.

## Task 5: strict-aliasing.md
Rewrite `strict-aliasing.md`: the aliasing rule and allowed types, why compilers exploit it
(a demonstrable optimisation example), safe punning via `std::memcpy` and `std::bit_cast` (C++20),
`-fno-strict-aliasing`.

## Task 6: initialization/ (4 pages)
Rewrite `initialization/default-initialization.md`, `value-initialization.md`,
`aggregate-initialization.md`, `uniform-initialization.md` as one coherent set with no overlap:
each page owns its form; the uniform-initialization page owns brace-init/narrowing/
`initializer_list` overload preference and designated initializers belong to the aggregate page
(C++20). Keep the folder `_category_.json` sane.
