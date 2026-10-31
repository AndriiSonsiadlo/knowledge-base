---
id: makefiles
title: Makefiles
sidebar_label: Makefiles
sidebar_position: 13
tags: [c++, make, build, automation]
---

# Makefiles

Make is the original build tool: a `Makefile` lists **rules**, each saying how to produce a target
file from its prerequisites, and `make` runs a rule's commands only when a prerequisite is newer
than the target. That timestamp check is the whole incremental-build idea that every later build
system kept. You meet Makefiles in older projects, in small Unix tools, and as one of CMake's
generator outputs. For a new multi-platform C++ project, [CMake](./build-systems-cmake.md) is the
usual choice.

**Prerequisites:** [Build Systems and CMake](./build-systems-cmake.md) (the dependency graph),
[The Compilation Pipeline](./compilation-pipeline.md).

This page covers GNU Make, the version on Linux; the reference is the
[GNU Make manual](https://www.gnu.org/software/make/manual/make.html).

## Rules

```makefile title="Makefile"
app: main.o square.o
	g++ main.o square.o -o app

main.o: main.cpp square.h
	g++ -std=c++23 -c main.cpp -o main.o

square.o: square.cpp square.h
	g++ -std=c++23 -c square.cpp -o square.o
```

Each rule is `target: prerequisites`, followed by command lines that **must start with a tab
character**, not spaces (`*** missing separator.  Stop.` means spaces). `make` with no argument
builds the first target in the file. To decide what to run, it walks the graph from `app` down: a
target is rebuilt if it does not exist or any prerequisite is newer.

The hand-written `square.h` prerequisites are the weak point: forget one and an edited header
silently does not trigger a rebuild. The compiler can generate them instead (below).

## Variables, automatic variables and pattern rules

| Syntax | Meaning |
|---|---|
| `CXX := g++` | Simple assignment, evaluated once (`=` re-evaluates on every use) |
| `$(VAR)` | Use a variable |
| `$@` | The target of the current rule |
| `$<` | The first prerequisite |
| `$^` | All prerequisites, without duplicates |
| `%.o: %.cpp` | Pattern rule: how to make any `.o` from the `.cpp` with the same stem |
| `$(wildcard src/*.cpp)` | List matching files |
| `$(SRCS:src/%.cpp=build/%.o)` | Substitute in every word of a list |
| `.PHONY: clean` | `clean` is a command, not a file; run it even if a file named `clean` exists |

Make has built-in variables with conventional meanings: `CXX` (C++ compiler), `CXXFLAGS` (compiler
flags), `CPPFLAGS` (preprocessor flags), `LDFLAGS` (linker options such as `-L`), `LDLIBS`
(libraries, `-l…`). Using them lets users override settings from the command line:
`make CXX=clang++ CXXFLAGS=-O0`.

## A complete Makefile

```makefile title="Makefile"
CXX      := g++
CXXFLAGS := -std=c++23 -Wall -Wextra -O2
CPPFLAGS := -MMD -MP
LDFLAGS  :=
LDLIBS   :=

SRC_DIR   := src
BUILD_DIR := build

SRCS   := $(wildcard $(SRC_DIR)/*.cpp)
OBJS   := $(SRCS:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
DEPS   := $(OBJS:.o=.d)
TARGET := $(BUILD_DIR)/app

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(LDFLAGS) $^ $(LDLIBS) -o $@

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@

$(BUILD_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR)

-include $(DEPS)
```

- `| $(BUILD_DIR)` is an **order-only** prerequisite: the directory must exist, but its timestamp
  (which changes whenever a file is added to it) does not force rebuilds.
- `$(LDLIBS)` comes after the objects because [library order matters](./linking.md#library-order).
- `-MMD -MP` makes the compiler write `build/main.d` alongside `build/main.o`, and `-include`
  pulls those files in on the next run (the `-` ignores them when they don't exist yet):

```text title="build/main.d"
build/main.o: src/main.cpp src/square.h
src/square.h:
```

With `src/` holding the [two-file program](./compilation-pipeline.md#tracing-a-two-file-program),
this is what GNU Make 4.4 ran:

<Walkthrough title="Incremental builds with the Makefile above" accent="green">
  <Step title="make -j4 (clean tree)">

```text
mkdir -p build
g++ -MMD -MP -std=c++23 -Wall -Wextra -O2 -c src/main.cpp -o build/main.o
g++ -MMD -MP -std=c++23 -Wall -Wextra -O2 -c src/square.cpp -o build/square.o
g++  build/main.o build/square.o  -o build/app
```

Everything is built; the two compiles may run in parallel.

  </Step>
  <Step title="touch src/square.h; make">

```text
g++ -MMD -MP -std=c++23 -Wall -Wextra -O2 -c src/main.cpp -o build/main.o
g++ -MMD -MP -std=c++23 -Wall -Wextra -O2 -c src/square.cpp -o build/square.o
g++  build/main.o build/square.o  -o build/app
```

The header is listed in <StepChange>both `.d` files</StepChange>, so both objects rebuild.

  </Step>
  <Step title="touch src/square.cpp; make">

```text
g++ -MMD -MP -std=c++23 -Wall -Wextra -O2 -c src/square.cpp -o build/square.o
g++  build/main.o build/square.o  -o build/app
```

Only <StepChange>`square.o`</StepChange> and the link.

  </Step>
  <Step title="make (nothing changed)">

```text
make: Nothing to be done for 'all'.
```

  </Step>
</Walkthrough>

## Everyday commands

```bash
make                 # build the first target
make clean           # run a named target
make -j"$(nproc)"    # parallel jobs, one per CPU
make -n              # print the commands without running them
make -B              # rebuild everything regardless of timestamps
make V=1             # (CMake-generated Makefiles) show full commands
```

## Pitfalls

- **Spaces instead of a tab** before a command: `missing separator`.
- **Missing header dependencies.** Without `-MMD` and `-include`, editing a header does not rebuild
  its users, and you get stale objects that disagree about a class's layout.
- **Changing flags does not rebuild.** Make compares file times, not command lines. After changing
  `CXXFLAGS`, run `make clean` (CMake and Ninja track command lines and do this automatically).
- **Recursive make** (`$(MAKE) -C subdir` for each directory) splits the graph, so Make cannot see
  dependencies across directories. Prefer one Makefile with `include`d fragments.
- **Portability.** GNU Make features (`:=`, `wildcard`, pattern rules) are not in BSD Make or
  Windows `nmake`.

## Key points

- A rule rebuilds a target when any prerequisite is newer; that is all Make knows.
- Let the compiler generate header dependencies (`-MMD -MP`) and `-include` them.
- Use the conventional variables (`CXX`, `CXXFLAGS`, `CPPFLAGS`, `LDFLAGS`, `LDLIBS`) and `.PHONY`.
- For cross-platform projects, generate the build files with CMake instead of writing them.
