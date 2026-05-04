---
id: learning-resources
title: Learning resources
sidebar_label: Learning resources
sidebar_position: 5
tags: [ unreal-engine, ue5, c++, learning-resources ]
---

# Learning resources

This knowledge base is reference material, not a tutorial — it assumes you're building something and
looking up the piece you need, not working through exercises in order. The resources below fill the
gap: structured, sequential material for going deeper than a single doc page can. Every entry here was
checked against a real listing before being included; nothing below is a guess at a title that sounds
plausible.

## Why curate this at all

Unreal's learning material is unusually fragmented across official docs, Epic's community learning
platform, third-party books, and paid courses of wildly varying quality. Without a filtered starting
list, the easiest failure mode is picking the first search result and hitting either heavily outdated
material (this engine changes fast across major versions) or content aimed at a completely different
skill level than you're at.

## Official Epic resources

- **Epic Developer Community Learning** — `dev.epicgames.com/community/learning` is Epic's own hub
  for tutorials, courses, and demos, maintained alongside the engine itself. Treat it as the first
  stop for anything editor-workflow related, since it stays current with the shipping version.
- **"Welcome to Unreal Engine" learning path** — a guided, official starting sequence covering the
  editor and major engine features, at
  `dev.epicgames.com/community/learning/paths/7a/welcome-to-unreal-engine`.
- **Unreal Engine documentation** — the reference this whole section cross-links to throughout;
  authoritative for API signatures and current behavior, weaker on "why," which is what the rest of
  this knowledge base tries to add.
- **Epic Developer Community Forums** — `forums.unrealengine.com` is Epic's own forum, including a
  community-maintained "Unreal YouTube Channels Database" thread that's a reasonable starting index
  for video creators if you prefer that format. Useful for version-specific questions and bug reports,
  since Epic staff and engine engineers participate directly.
- **Official Unreal Engine YouTube channel** — `youtube.com/c/UnrealEngine`, Epic's own channel for
  feature deep-dives, State of Unreal keynotes, and workflow walkthroughs. Good for seeing a feature
  demonstrated before reading its docs page.

## Books

:::note
Titles and authors below were verified against publisher/retailer listings before inclusion. Editions
change over time — confirm the edition against your engine version before buying.
:::

- **Stephen Ulibarri, *Unreal Engine C++ the Ultimate Developer's Handbook: Learn C++ and Unreal
  Engine by Creating a Complete Action Game*.** A project-based introduction that builds a complete
  action game while teaching both C++ fundamentals and Unreal-specific patterns. Good fit once you're
  past milestone 1 in the [mastery roadmap](./mastery-roadmap.md) and want a structured project to
  follow rather than isolated topics.
- **Jason Gregory, *Game Engine Architecture*.** Not Unreal-specific — this is a general game-engine
  architecture text (currently in its 4th edition, previously a widely-used 3rd edition) covering the
  systems every engine implements: rendering pipelines, animation systems, physics integration, the
  game loop. Read it for the *why* behind engine design decisions that Unreal's docs describe only as
  *how*.

## Community-maintained resources

- **Tom Looman's Unreal Engine C++ material** — community-maintained, not an official Epic resource.
  Includes free tutorials at `tomlooman.com` and the paid course *Professional Game Development in
  C++ and Unreal Engine*, which walks through building a third-person action game in C++ with an
  emphasis on production-oriented architecture and coding practices. Widely referenced in the UE C++
  community; useful once you want opinionated, production-flavored guidance beyond "how do I call this
  API."

## Matching resources to the roadmap

Pulling from [Mastery roadmap](./mastery-roadmap.md): don't start a book or a paid course before
milestone 1 (build and run) is done. All of the resources above assume you already have a project
that compiles and launches — they teach what to do *inside* that project, not how to get the
toolchain working in the first place, which is covered in
[01-toolchain-and-build](../01-toolchain-and-build/installation-and-versions.md) instead.

- **Stuck at milestone 1–2** (build and run, first C++ Actor): the official "Welcome to Unreal Engine"
  learning path and Epic's own documentation are enough. You don't need a book yet.
- **At milestone 3** (first playable loop): this is where Ulibarri's project-based book or Tom
  Looman's course earn their cost — both build a complete, playable slice, which is exactly the shape
  of problem you're solving at this milestone.
- **Past milestone 4, going deeper on engine internals**: Gregory's *Game Engine Architecture* pays
  off here, once you have enough Unreal-specific context to map its general concepts onto Unreal's
  actual subsystems.

## Gotchas

:::warning[Version drift is real]
Unreal Engine's API and recommended patterns change meaningfully between major versions (4.x to 5.x,
and across 5.x minor releases). A book or course written for an earlier version can teach patterns
that still compile but are no longer idiomatic, or reference APIs that have since been deprecated.
Check the target engine version on any resource before trusting it as current guidance for UE 5.7.
:::

:::caution[Prefer primary sources for anything you're about to ship]
Tutorials and books are for building a mental model. For anything that ends up in shipping code —
exact specifier behavior, a deprecated function's replacement, a platform-specific constraint — verify
against the official Unreal Engine documentation or engine source directly, not against a
secondary source's summary of it.
:::

## See also

- [Mastery roadmap](./mastery-roadmap.md) — the sequence these resources support.
- [What is Unreal Engine 5?](./what-is-unreal-engine.md) — orientation before diving into any of the
  above.
- [Epic Developer Community Learning](https://dev.epicgames.com/community/learning/) — the official
  hub referenced throughout this page.
