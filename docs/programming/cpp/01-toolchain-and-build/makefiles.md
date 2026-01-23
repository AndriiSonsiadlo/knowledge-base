---
id: makefiles
title: Makefiles
sidebar_label: Makefiles
sidebar_position: 13
tags: [c++, make, build, automation]
---

# Makefiles

Makefiles define rules for building projects using the Make build system. They specify dependencies and commands to compile source code incrementally.

:::info Unix Build Standard
Make has been the standard Unix build tool since 1976. Simple for small projects, but CMake is preferred for cross-platform development.
:::

## Basic Makefile Structure
```makefile
# Target: Dependencies
#     Command (must be indented with TAB)

app: main.o utils.o
	g++ main.o utils.o -o app

main.o: main.cpp utils.h
	g++ -c main.cpp -o main.o

utils.o: utils.cpp utils.h
	g++ -c utils.cpp -o utils.o

clean:
	rm -f *.o app
```

**How it works:**
- Target depends on dependencies
- If dependency newer than target, run command
- Recursively checks dependencies

## Variables
```makefile
CXX = g++
CXXFLAGS = -std=c++20 -Wall -Wextra -O2
LDFLAGS = -lpthread

SRCS = main.cpp utils.cpp math.cpp
OBJS = $(SRCS:.cpp=.o)

app: $(OBJS)
	$(CXX) $(OBJS) $(LDFLAGS) -o app

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@
```

**Special variables:**
- `$@` - target name
- `$<` - first dependency
- `$^` - all dependencies
- `%` - pattern matching

## Pattern Rules
```makefile
# Generic rule: any .cpp -> .o
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# All .cpp files in directory
SRCS = $(wildcard src/*.cpp)
OBJS = $(SRCS:src/%.cpp=build/%.o)
```

## Phony Targets
```makefile
.PHONY: clean all install

all: app

clean:
	rm -f $(OBJS) app

install: app
	cp app /usr/local/bin/
```

`.PHONY` marks targets that aren't actual files.

## Common Make Commands
```bash
make              # Build default target (first in file)
make clean        # Run clean target
make app          # Build specific target
make -j8          # Parallel build (8 jobs)
make -n           # Dry run (show commands)
make -B           # Force rebuild all
```

## Complete Example
```makefile
# Compiler settings
CXX := g++
CXXFLAGS := -std=c++20 -Wall -Wextra -O2
LDFLAGS := -lpthread -lm

# Directories
SRC_DIR := src
BUILD_DIR := build
BIN_DIR := bin

# Files
SRCS := $(wildcard $(SRC_DIR)/*.cpp)
OBJS := $(SRCS:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
TARGET := $(BIN_DIR)/app

# Targets
all: $(TARGET)

$(TARGET): $(OBJS) | $(BIN_DIR)
	$(CXX) $(OBJS) $(LDFLAGS) -o $@

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(BUILD_DIR) $(BIN_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)

.PHONY: all clean
```

## Automatic Dependencies

Track header dependencies automatically:
```makefile
# Generate dependency files
DEPS := $(OBJS:.o=.d)

-include $(DEPS)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@
```

`-MMD -MP` flags generate `.d` files tracking which headers each `.cpp` includes.

## When to Use Make

**Use Make when:**
- Unix-only project
- Simple build requirements
- Want minimal dependencies
- Familiar with Make syntax

**Use CMake instead when:**
- Cross-platform needed
- Complex project structure
- Managing external libraries
- Want IDE integration

## Summary

Makefiles define build rules for Make:
- **Target: dependencies** structure
- **Incremental builds** - only rebuild changed files
- **Pattern rules** - generic compilation rules
- **Variables** - avoid repetition
- **Parallel builds** - `-j` flag

**Simple Makefile:**
```makefile
CXX = g++
CXXFLAGS = -std=c++20 -Wall

app: main.o utils.o
	$(CXX) $^ -o $@

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $

clean:
	rm -f *.o app

.PHONY: clean
```

Make is perfect for small Unix projects but CMake is recommended for most modern C++ development.