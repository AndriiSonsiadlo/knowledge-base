---
id: include-guards-and-pragma-once
title: Include Guards and #pragma once
sidebar_label: Include Guards
sidebar_position: 11
tags: [c++, include-guards, pragma-once, preprocessor, headers]
---

# Include Guards and `#pragma once`

In a real project the same header reaches a translation unit along several paths: `main.cpp`
includes `button.h` and `widget.h`, and both of those include `component.h`. Because `#include` is
text pasting, `component.h` would appear twice, and its class definition would be a redefinition
error. An **include guard** makes the second and later inclusions in the same TU produce nothing.
There are two ways to write one, and every header needs one of them.

**Prerequisites:** [Preprocessing](./preprocessing.md), [Headers and Includes](./headers-and-includes.md).

## The problem

```cpp title="widget.h (no guard)"
class Widget { int value; };
```

```cpp title="twice.cpp"
#include "widget.h"
#include "widget.h"
int main() {}
```

```text
In file included from twice.cpp:2:
widget.h:1:7: error: redefinition of ‘class Widget’
    1 | class Widget { int value; };
      |       ^~~~~~
In file included from twice.cpp:1:
widget.h:1:7: note: previous definition of ‘class Widget’
```

Nobody writes the same include twice on purpose. It happens through the include graph:

<Diagram title="Diamond include" caption="component.h is reached along two paths in one TU." accent="amber">
  <DiagramNode icon="file-text" title="main.cpp" />
  <DiagramArrow label="#include" />
  <DiagramRow>
    <DiagramNode icon="file-text" title="button.h" />
    <DiagramNode icon="file-text" title="widget.h" />
  </DiagramRow>
  <DiagramArrow label="both #include" />
  <DiagramNode icon="file-text" title="component.h" accent>Pasted twice without a guard</DiagramNode>
</Diagram>

Guards work **per translation unit**. They do nothing about the same header being included in two
different `.cpp` files, which is normal and required; that case is governed by the
[One Definition Rule](./translation-units.md#the-one-definition-rule).

## Two ways to guard a header

<Tabs groupId="guard">
  <TabItem value="macro" label="Macro guard (standard)">

```cpp title="mylib/widget.h"
#ifndef MYLIB_WIDGET_H
#define MYLIB_WIDGET_H

class Widget {
    int value;
};

#endif  // MYLIB_WIDGET_H
```

  </TabItem>
  <TabItem value="pragma" label="#pragma once">

```cpp title="mylib/widget.h"
#pragma once

class Widget {
    int value;
};
```

  </TabItem>
</Tabs>

<Walkthrough title="A macro guard on the second inclusion" accent="amber">
  <Step title="First #include">

`MYLIB_WIDGET_H` is not defined, so `#ifndef` is true. The preprocessor
<StepChange>defines `MYLIB_WIDGET_H`</StepChange> and emits `class Widget { … };`.

  </Step>
  <Step title="Second #include">

The file is opened again, but `MYLIB_WIDGET_H` <StepChange>is now defined</StepChange>, so
everything up to `#endif` is skipped. The TU contains `Widget` once.

  </Step>
</Walkthrough>

`#pragma once` asks the compiler to remember the **file** instead of a macro: once a file marked
this way has been included, later `#include`s that resolve to the same file are ignored.

| | Macro guard | `#pragma once` |
|---|---|---|
| Standard C++ | Yes | No, but supported by GCC, Clang, MSVC and other mainstream compilers |
| Identity check | A macro name you choose | The compiler's idea of "the same file" |
| Can collide | Yes: two headers using the same macro name hide each other | No names involved |
| Can be typoed | Yes (GCC warns, see below) | No |
| Speed | GCC and Clang recognise the guard pattern and skip reopening the file ([GCC: Once-Only Headers](https://gcc.gnu.org/onlinedocs/cpp/Once-Only-Headers.html)), so there is no reliable difference | |

Either is fine; pick one per project and use it in every header. Most new code uses
`#pragma once`; code that must work on unusual compilers, or that is copied into other projects'
trees, uses macro guards. Combining both in one file buys nothing.

## When "the same file" is ambiguous

`#pragma once` depends on how the compiler decides two paths are the same file. A test with a
symlink and with an identical copy in another directory (GCC 15 and Clang 21):

```cpp
#include "real.h"
#include "link.h"        // symlink to real.h
#include "copy/real.h"   // byte-identical copy of real.h
```

| Case | GCC 15 | Clang 21 |
|---|---|---|
| Symlink to the same file | Included once | Included once |
| Identical copy at a different path | Included once (GCC also compares contents and timestamp) | **Included twice**: `error: redefinition of 'P'` |

So the two compilers disagree on copies, which do occur: a header installed system-wide and also
vendored in the source tree, or generated into two build directories. A macro guard with a unique
name behaves the same everywhere in these cases. Without one, make sure each header exists at only
one path on the include search path.

## Naming macro guards

The name must be unique across every header that might end up in the same TU, including
third-party ones. Derive it from the path under the include root:

| Header path | Guard |
|---|---|
| `include/mylib/widget.h` | `MYLIB_WIDGET_H` |
| `include/mylib/net/socket.h` | `MYLIB_NET_SOCKET_H` |

Avoid names that start with an underscore followed by a capital letter (`_WIDGET_H`) or contain a
double underscore: those are reserved for the implementation. Generic names such as `UTIL_H` are how
two libraries end up silently hiding each other's headers.

## Common mistakes

- **Mismatched names.** GCC catches the typo:

  ```text
  typo.h:1: warning: header guard ‘WIDGET_H’ followed by ‘#define’ of a different macro [-Wheader-guard]
      1 | #ifndef WIDGET_H
  typo.h:2: note: ‘WIDGTE_H’ is defined here; did you mean ‘WIDGET_H’?
  ```

  The guard never takes effect, so the header behaves as if unguarded.
- **Content outside the guard.** Anything after `#endif` is pasted every time.
- **A missing `#endif`**: `error: unterminated #ifndef` in every file that includes the header.
- **Copy-pasted guards.** A new header created from an old one keeps the old guard name; whichever
  is included second disappears. Lint for it (clang-tidy `llvm-header-guard`) or use `#pragma once`.
- **Expecting a guard to fix `multiple definition` link errors.** Those come from one definition in
  *several* TUs; guards only work within one. See
  [Linking](./linking.md#reading-linker-errors).

## Key points

- Every header needs a guard; without one, a diamond in the include graph is a redefinition error.
- Guards act within one translation unit only.
- `#pragma once` is simpler; macro guards are standard and immune to "same file?" ambiguity.
- Name macro guards after the header's path; let `-Wheader-guard` or a linter catch typos.
