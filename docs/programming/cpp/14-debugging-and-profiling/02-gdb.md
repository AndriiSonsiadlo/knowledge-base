---
id: gdb
title: GDB Debugger
sidebar_label: GDB
sidebar_position: 2
tags: [gdb, debugging, breakpoints, watchpoints, backtrace]
---

# GDB Debugger

GNU Debugger (GDB) is the standard debugger for C/C++ on Linux. Allows stepping through code, inspecting variables, setting breakpoints, and analyzing crashes.

:::info Compile for Debugging
Always compile with `-g` flag: `g++ -g -O0 program.cpp -o program`
:::

## Starting GDB
```bash
# Start with program
gdb ./program

# With arguments
gdb --args ./program arg1 arg2

# Attach to running process
gdb -p <PID>

# Debug core dump
gdb ./program core

# Quiet mode (no banner)
gdb -q ./program
```

## Essential Commands

| Command    | Shortcut | Description           |
|------------|----------|-----------------------|
| `run`      | `r`      | Start program         |
| `continue` | `c`      | Continue execution    |
| `next`     | `n`      | Step over (next line) |
| `step`     | `s`      | Step into function    |
| `finish`   | `fin`    | Step out of function  |
| `quit`     | `q`      | Exit GDB              |
| `help`     | `h`      | Show help             |

## Breakpoints
```gdb
# Set breakpoint at function
(gdb) break main
(gdb) b main

# Set breakpoint at line
(gdb) break file.cpp:42
(gdb) b 42

# Conditional breakpoint
(gdb) break main if x == 5

# List breakpoints
(gdb) info breakpoints
(gdb) i b

# Delete breakpoint
(gdb) delete 1      # Delete breakpoint #1
(gdb) d 1

# Disable/enable breakpoint
(gdb) disable 1
(gdb) enable 1

# Delete all breakpoints
(gdb) delete
```

### Example Session
```gdb
$ gdb ./program
(gdb) break main
Breakpoint 1 at 0x400537: file program.cpp, line 5.

(gdb) run
Starting program: /path/to/program 
Breakpoint 1, main () at program.cpp:5

(gdb) next
6           int x = 5;

(gdb) print x
$1 = 5

(gdb) continue
Program exited normally.
```

## Examining Variables
```gdb
# Print variable
(gdb) print x
(gdb) p x

# Print with format
(gdb) p/x x        # Hexadecimal
(gdb) p/t x        # Binary
(gdb) p/d x        # Decimal

# Print array
(gdb) p arr[0]@10  # Print 10 elements starting at arr[0]

# Print structure
(gdb) p mystruct
(gdb) p mystruct.member

# Print pointer target
(gdb) p *ptr

# Print type
(gdb) ptype x
(gdb) whatis x
```

## Backtrace (Call Stack)
```gdb
# Show call stack
(gdb) backtrace
(gdb) bt

# Full backtrace
(gdb) bt full

# Show specific frames
(gdb) bt 5         # Top 5 frames

# Select frame
(gdb) frame 2
(gdb) f 2

# Move up/down stack
(gdb) up
(gdb) down
```

### Example Backtrace
```gdb
(gdb) bt
#0  crash_function () at program.cpp:10
#1  helper () at program.cpp:15
#2  main () at program.cpp:20

(gdb) frame 1
#1  helper () at program.cpp:15

(gdb) print local_var
$1 = 42
```

## Watchpoints

Break when variable changes.
```gdb
# Watch variable
(gdb) watch x

# Watch expression
(gdb) watch x > 10

# Read watchpoint
(gdb) rwatch x     # Break when x is read

# Access watchpoint
(gdb) awatch x     # Break on read or write
```

## Stepping Through Code
```gdb
# Run program
(gdb) run
(gdb) r

# Step over (next line)
(gdb) next
(gdb) n

# Step into function
(gdb) step
(gdb) s

# Step instruction (assembly)
(gdb) stepi
(gdb) si
(gdb) nexti
(gdb) ni

# Finish current function
(gdb) finish
(gdb) fin

# Continue to next breakpoint
(gdb) continue
(gdb) c
```

## Examining Memory
```gdb
# Examine memory
(gdb) x/10x ptr    # 10 hex words at ptr
(gdb) x/10i ptr    # 10 instructions at ptr
(gdb) x/s ptr      # String at ptr

# Format: x/[count][format][size] address
# format: x=hex, d=decimal, i=instruction, s=string
# size: b=byte, h=halfword, w=word, g=giant(8 bytes)

# Examples
(gdb) x/4x $sp     # 4 hex words at stack pointer
(gdb) x/20i $pc    # 20 instructions at program counter
```

## Registers
```gdb
# Show all registers
(gdb) info registers
(gdb) i r

# Show specific register
(gdb) p $rax
(gdb) p/x $rsp

# Print all general registers
(gdb) info reg
```

## Threads
```gdb
# List threads
(gdb) info threads
(gdb) i th

# Switch thread
(gdb) thread 2

# Apply command to all threads
(gdb) thread apply all bt

# Break in specific thread
(gdb) break file.cpp:42 thread 3
```

## Source Code
```gdb
# List source code
(gdb) list
(gdb) l

# List function
(gdb) list main

# List specific line
(gdb) list file.cpp:42

# Show current location
(gdb) where
```

## Changing Values
```gdb
# Set variable
(gdb) set var x = 10
(gdb) set x = 10

# Set memory
(gdb) set {int}0x12345678 = 42

# Call function
(gdb) call printf("x = %d\n", x)
```

## Core Dumps
```gdb
# Analyze core dump
$ gdb ./program core

(gdb) bt           # See where it crashed
(gdb) frame 0      # Go to crash location
(gdb) print x      # Examine variables
```

Enable core dumps:
```bash
ulimit -c unlimited
```

## GDB Scripts
```gdb
# Run commands from file
(gdb) source script.gdb

# Example script.gdb:
break main
run
print x
continue
```

### .gdbinit
```gdb
# ~/.gdbinit - Runs automatically
set pagination off
set print pretty on
set print array on
```

## TUI Mode (Text User Interface)
```bash
# Start in TUI mode
gdb -tui ./program

# Or inside GDB
(gdb) tui enable
(gdb) layout src       # Source window
(gdb) layout split     # Source + assembly
(gdb) layout asm       # Assembly window
(gdb) layout regs      # Registers

# Scroll source
Ctrl+X, A             # Toggle TUI
Ctrl+L                # Refresh screen
```

## Useful Tricks
```gdb
# Skip boring functions
(gdb) skip function std::.*

# Save breakpoints
(gdb) save breakpoints bp.txt

# Load breakpoints
(gdb) source bp.txt

# Conditional execution
(gdb) command 1       # After breakpoint 1 hits:
>print x
>continue
>end

# Catch exceptions
(gdb) catch throw
(gdb) catch catch

# Catch syscalls
(gdb) catch syscall write
```

## Debugging Optimized Code
```gdb
# With -O2, variables may be optimized away
(gdb) p x
$1 = <optimized out>

# Build with -Og (optimize for debugging)
g++ -g -Og program.cpp

# Or disable optimizations for specific function
__attribute__((optimize("O0")))
void debug_this() { ... }
```

## Quick Reference Card
```gdb
# Starting
r                    # run
r arg1 arg2         # run with args

# Breakpoints
b main              # break at main
b file.cpp:42       # break at line
b func if x==5      # conditional

# Execution
n                   # next (step over)
s                   # step (step into)
fin                 # finish (step out)
c                   # continue

# Examination
p x                 # print x
bt                  # backtrace
info locals         # show local vars
info args           # show arguments

# Common
q                   # quit
h                   # help
```

## Summary
:::info
**Start**: `gdb ./program`, compile with `-g -O0`.
**Breakpoints**: `b main`, `b file.cpp:42`.
**Execution**: `r` (run), `n` (next), `s` (step), `c` (continue).
**Examine**: `p var` (print), `bt` (backtrace), `info locals`.
**Watchpoints**: `watch x` (break on change).
**Threads**: `info threads`, `thread 2`.
**Core dumps**: `gdb ./program core`, `bt`.
**TUI**: `gdb -tui`, `layout src`.
:::info

```cpp
// Memory aid: "RBWP" (Run Break Watch Print)
// R = Run (r, c, n, s)
// B = Breakpoints (b, info b, delete)
// W = Watch (watch var, rwatch, awatch)
// P = Print (p, bt, info locals)

// Typical workflow:
// 1. gdb ./program
// 2. b main
// 3. r
// 4. n (step through)
// 5. p var (examine)
// 6. bt (if crash)
// 7. q (quit)
```