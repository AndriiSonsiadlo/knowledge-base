# Design: Documentation specs for nlohmann/json, spdlog, fmt

## Goal

Add three new comprehensive, boost-style C++ library doc sets to the knowledge base:
`nlohmann/json`, `spdlog`, and `fmt`. This document specifies the shared conventions all
three must follow and the per-library page outline, so that writing/generating the actual
`.md` content is a mechanical follow-the-template exercise.

## Precedent

The site already has two doc sets for third-party C++ libraries at this depth:
`docs/programming/boost/` (comprehensive, 16 numbered subfolders, ~70+ pages) and
`docs/programming/cmake/` (focused, 7 numbered subfolders). The three new libraries follow
the **boost model**: numbered subfolders, one folder per top-level topic area, comprehensive
coverage including internals, pitfalls, and comparisons to alternatives.

## Shared conventions (apply to all three libraries)

### Location and top-level structure

Each library gets its own top-level folder as a sibling of `boost/`, `cmake/`, `cpp/`,
`python/`:

```
docs/programming/nlohmann-json/
docs/programming/spdlog/
docs/programming/fmt/
```

Each folder needs:
- A `_category_.json` at the folder root (sidebar label + `position` + `generated-index` link).
  New `position` values continue the existing sequence (`cpp`=2, `python`=3, `cmake`=4,
  `boost`=5) — assign 6, 7, 8 in whatever order they're added.
- A `readme.md` at the folder root that serves as the landing/overview page (mirrors
  `boost/readme.md` and `cmake/readme.md`).
- Numbered subfolders (`00-overview`, `01-basics`, ...) each with their own
  `_category_.json` (`label`, `position`, `generated-index` link) and 3-7 topic `.md` files.

### Per-page frontmatter

Every page (including `readme.md`) uses this frontmatter shape, matching existing pages
exactly:

```md
---
id: <kebab-case-id>
title: <Human Title>
sidebar_label: <short label, defaults to title if same length>
sidebar_position: <int, order within its folder>
tags: [ c++, <library-slug>, <topic-tag>, <topic-tag> ]
---
```

- `id` is optional on `readme.md`-style overview pages (existing overviews use `title` only,
  no `id`) but required on all topic pages.
- `tags` always starts with `c++` and the library slug (`nlohmann-json`, `spdlog`, `fmt`),
  followed by 1-3 topic-specific tags, all lowercase, hyphenated.
- `sidebar_position` starts at 1 within each folder; the folder's `_category_.json`
  `position` orders the folders themselves.

### Page structure

Every topic page:
1. Opens with an `# H1` matching `title`.
2. Opens with 1-2 paragraphs of prose framing *why this exists / what problem it solves*
   before any API details.
3. Uses `##` sections for each subtopic; `###` sparingly for deep sub-splits.
4. Ends with a `## See also` section: a bullet list of `<Icon icon="lucide:..." inline />`
   + relative markdown links to 3-5 related pages (siblings first, then cross-folder, then
   the library's own `readme.md`).

### Admonitions (Docusaurus)

Reuse the existing four admonition types with the existing semantics — don't invent new
ones:

| Admonition | Use for |
|---|---|
| `:::info[...]` | Framing the problem a feature solves, "why does this exist" |
| `:::tip[...]` | Idiomatic usage, when a feature shines, best-practice nudges |
| `:::danger[...]` | Undefined behavior, footguns, things that silently break |
| `:::note[...]` | "Which one should I use" guidance, migration notes, version caveats |

### Code blocks

- Always fenced ` ```cpp ` (or ` ```bash ` / ` ```cmake ` / ` ```json ` as appropriate — `json`
  is not currently in `prism.additionalLanguages`; if `nlohmann-json` pages include fenced
  ` ```json ` blocks, add `"json"` to `additionalLanguages` in `docusaurus.config.js`).
- Use `showLineNumbers` on any snippet longer than ~5 lines.
- Add `title="filename.cpp"` when the snippet represents a real standalone file worth naming.
- Snippets must compile conceptually (correct includes, no hand-waved syntax) even though
  they aren't build-tested by CI.

### Diagrams and tables

- Use a `mermaid` `flowchart` for: state machines (e.g. JSON value type variants, spdlog
  logger → sinks fan-out, async logging thread-pool flow), and decision/relationship
  diagrams (e.g. fmt vs std::format lineage, "which sink do I want").
- Use comparison tables (`| Feature | Option A | Option B |`) whenever a page's job is to
  help the reader choose between two things (e.g. `nlohmann::json` vs `boost::json`,
  `spdlog::async` vs sync, `fmt::format` vs `std::format`, header-only vs compiled mode).

### Cross-linking rules

- Link to sibling pages with relative paths (`./other-page.md`), to other folders with
  `../NN-folder/page.md`, and to the folder's own overview with `../readme.md`.
- Where a genuine relationship exists to `boost/`, `cmake/`, or `cpp/` content, link across
  folders (e.g. fmt pages link to `../../cpp/09-standard-library/...` for `std::format`
  context; nlohmann-json's build page links to `../../cmake/03-dependencies/fetchcontent.md`).
- Don't force cross-links that aren't genuinely useful — quality over connectivity.

### Overview `readme.md` contents (per library)

Following the `boost/readme.md` / `cmake/readme.md` pattern, each library's `readme.md`
contains, in order:
1. Frontmatter (`title: Overview of <Library>`, `sidebar_label: Overview`,
   `sidebar_position: 1`, `tags`).
2. A short framing paragraph: what the library is, one sentence on why it's the de facto
   standard for its niche.
3. An `:::info[How this is organised]` box explaining the folder progression.
4. A `## Sections` table: one row per numbered subfolder, with an `<Icon>` , a link to that
   folder's first page, and a one-line description of what it covers.
5. A `## Suggested reading paths` section: a `mermaid flowchart` of folder progression, plus
   2-3 bullet "if you're doing X, read these in order" paths.
7. A closing `## Quick reference` section (a compact table or short list of the most-reached
   for signatures/macros, matching the pattern seen at the end of `cmake/readme.md`).

### Writing voice

Match the existing tone: precise and technical, conversational but not casual, willing to
state opinions ("prefer X unless Y"). Favor showing *why* a design decision exists over
just documenting API surface. Every "how" should be paired with a "why" or a "when."

## Per-library outlines

### `docs/programming/nlohmann-json/` — position 6

`_category_.json` label: `"nlohmann/json"`.

- **00-overview** — `what-is-nlohmann-json.md`, `installation-and-integration.md` (single
  header vs `include/` vs CMake `find_package`/`FetchContent`, Conan, vcpkg),
  `design-philosophy.md` (STL-like container semantics, implicit conversions),
  `comparison-with-alternatives.md` (RapidJSON, Boost.JSON, simdjson — speed vs
  ergonomics trade-offs).
- **01-basics** — `parsing-json.md` (`parse` from string/stream/file, `operator""_json`),
  `creating-json-values.md` (initializer-list construction, literals), `the-json-value-type.md`
  (variant-like value: null/bool/number/string/array/object, `ordered_json`),
  `serialization-and-dumping.md` (`dump`, pretty-printing, `indent`, error handling on dump).
- **02-accessing-and-modifying** — `element-access.md` (`operator[]` vs `.at()` vs
  `.value()`, auto-vivification pitfall), `iterating-json.md` (range-for, `.items()`,
  structured bindings), `type-checking-and-conversions.md` (`is_*()`, `get<T>()`,
  `get_to()`, implicit conversion operator and its footguns), `json-pointer-and-patch.md`
  (`json_pointer`, RFC 6901, `patch`/`diff`, RFC 6902), `merging-and-comparison.md`
  (`merge_patch`, `update`, equality/ordering semantics).
- **03-custom-type-conversion** — `to_json-and-from_json.md` (ADL customization point),
  `serialization-macros.md` (`NLOHMANN_DEFINE_TYPE_INTRUSIVE`/`NON_INTRUSIVE`,
  `_WITH_DEFAULT` variants), `adl_serializer-and-templates.md` (specializing for
  third-party/template types you can't add free functions to).
- **04-advanced-features** — `sax-interface.md` (event-based parsing without building a
  DOM, `json_sax` callbacks, when to use over DOM parsing), `binary-formats.md` (CBOR,
  MessagePack, BSON, UBJSON — `to_cbor`/`from_cbor` etc., size/speed trade-offs),
  `error-handling-and-exceptions.md` (`parse_error`, `type_error`, `out_of_range`,
  `basic_json::exception` hierarchy, disabling exceptions).
- **05-numbers-memory-and-performance** — `number-handling-and-precision.md` (integer vs
  floating storage, big-number pitfalls, `number_integer_t`/`number_float_t` customization),
  `custom-allocators-and-json-types.md` (the `basic_json` template parameters — custom
  `ObjectType`/`ArrayType`/`Allocator`), `performance-and-best-practices.md` (avoiding
  copies, `emplace`/`push_back` vs `operator[]` growth, common pitfalls checklist).

### `docs/programming/spdlog/` — position 7

`_category_.json` label: `"spdlog"`.

- **00-overview** — `what-is-spdlog.md`, `installation-and-integration.md` (header-only vs
  compiled `SPDLOG_COMPILED_LIB`, CMake `find_package`/`FetchContent`, vcpkg/Conan),
  `design-philosophy.md` (fmt-based formatting, speed-first, sink architecture),
  `comparison-with-alternatives.md` (glog, Boost.Log, log4cplus — throughput/footprint
  trade-offs).
- **01-basics** — `quick-start.md` (default logger, `spdlog::info`/`warn`/`error`),
  `log-levels.md` (`trace`→`critical`, runtime vs compile-time level filtering),
  `basic-formatting.md` (fmt-style `{}` placeholders in log calls).
- **02-loggers-and-registry** — `creating-loggers.md` (`spdlog::create`, explicit
  construction), `the-registry.md` (`spdlog::get`, `register_logger`, default logger
  swapping), `logger-lifecycle.md` (shared ownership via `shared_ptr<logger>`, drop/
  shutdown), `multi-sink-loggers.md` (one logger, many sinks, per-sink levels/patterns).
- **03-sinks** — `sink-overview.md` (the `sink` interface, sink vs logger responsibilities),
  `console-sinks.md` (`stdout_color_sink`, `stderr_sink`, ANSI color control),
  `file-sinks.md` (`basic_file_sink`, truncate vs append), `rotating-and-daily-sinks.md`
  (`rotating_file_sink` size-based rotation, `daily_file_sink` time-based rotation),
  `syslog-and-platform-sinks.md` (syslog, Windows event log, Android log), `custom-sinks.md`
  (subclassing `sink_base`, thread-safety requirements).
- **04-formatting-and-patterns** — `pattern-flags.md` (`%Y`, `%l`, `%v`, `%^%$` color range,
  custom pattern strings), `custom-formatters.md` (`custom_flag_formatter`),
  `source-location-and-structured-logging.md` (`SPDLOG_LOGGER_CALL` macros capturing
  file/line/function, structured/key-value patterns).
- **05-async-logging** — `thread-pool-and-async-logger.md` (`spdlog::init_thread_pool`,
  `async_logger`), `overflow-policies.md` (`block` vs `overrun_oldest`),
  `async-vs-sync-tradeoffs.md` (latency vs throughput, when async isn't worth it).
- **06-performance-and-configuration** — `compile-time-log-level.md`
  (`SPDLOG_ACTIVE_LEVEL`, dead-code elimination of disabled levels), `backtrace-and-crash-dump.md`
  (ring-buffer backtrace, `dump_backtrace_on(level)`), `flush-policies.md`
  (`flush_on`, periodic flush thread), `global-settings-and-best-practices.md`
  (`set_default_logger`, `set_pattern` globally, common pitfalls).

### `docs/programming/fmt/` — position 8

`_category_.json` label: `"fmt"`.

- **00-overview** — `what-is-fmt.md`, `installation-and-integration.md` (header-only
  `fmt/core.h`/`fmt/format.h` vs compiled `FMT_HEADER_ONLY=0`, CMake, vcpkg/Conan),
  `relationship-to-std-format.md` (fmt as the reference implementation behind C++20
  `std::format`; what's still fmt-only), `comparison-with-printf-and-iostreams.md`
  (type safety, extensibility, performance vs both).
- **01-basics** — `format-strings-and-arguments.md` (`{}` replacement fields,
  `fmt::format`), `the-format-function-family.md` (`format`, `print`, `format_to`,
  `format_to_n`, `vformat`), `positional-and-named-arguments.md` (`{0}`, `"{name}"_a`,
  `fmt::arg`).
- **02-format-spec-mini-language** — `format-spec-syntax.md` (the
  `[[fill]align][sign][#][0][width][.precision][type]` grammar), `alignment-fill-and-width.md`,
  `sign-and-numeric-precision.md`, `type-specific-presentation.md` (`d`/`x`/`o`/`b` for
  ints, `f`/`e`/`g` for floats, `s`/`c` for strings/chars), `numeric-grouping-and-locales.md`
  (`{:L}`, thousands separators).
- **03-formatting-custom-types** — `formatter-specialization.md` (`fmt::formatter<T>`
  template specialization, `parse`/`format`), `ostream-fallback-formatting.md`
  (`fmt/ostream.h`, `operator<<` bridge), `ranges-tuples-and-containers.md` (`fmt/ranges.h`),
  `chrono-and-time-formatting.md` (`fmt/chrono.h`, strftime-style specs for
  `std::chrono` types).
- **04-compile-time-checks** — `compile-time-format-string-checking.md` (`FMT_STRING`,
  C++20 `consteval` checks on `fmt::format` directly), `error-diagnostics.md`
  (`fmt::format_error`, reading compiler errors from bad format strings).
- **05-advanced-features** — `output-iterators-and-format_to.md` (writing into buffers/
  containers without intermediate `std::string`), `memory-buffer-and-buffered-output.md`
  (`fmt::memory_buffer`, avoiding allocations), `color-and-text-styles.md`
  (`fmt::styled`, `fg`/`bg`/`emphasis`, `fmt/color.h`), `unicode-and-encoding-notes.md`
  (UTF-8 handling, width calculation caveats).
- **06-performance-and-best-practices** — `performance-characteristics.md` (benchmarks vs
  `sprintf`/iostreams/`std::format`, where the speed comes from — compile-time parsing,
  no heap for small results), `header-only-vs-compiled-mode.md` (build-time trade-off),
  `migration-from-std-format.md` (near-drop-in differences, when to still prefer fmt),
  `common-pitfalls.md` (dangling references in `fmt::format`, lifetime of `fmt::join`
  results).

## Verification

Because this repo's only correctness gate is `npm run build` (`onBrokenLinks: "throw"`), once
pages are written:
- Run `npm run build` to catch broken internal links and MDX/admonition syntax errors.
- Run `npm run lint` (Biome) for Markdown/JS consistency.
- Spot-check that every new folder's `_category_.json` `position` doesn't collide with an
  existing sibling, and that the navbar (`docusaurus.config.js`) doesn't need updates (it
  shouldn't — `programming` is already one navbar item covering all of `docs/programming/*`
  via the autogenerated sidebar).
