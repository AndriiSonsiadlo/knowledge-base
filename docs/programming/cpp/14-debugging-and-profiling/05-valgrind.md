---
id: valgrind
title: Valgrind
sidebar_label: Valgrind
sidebar_position: 5
tags: [valgrind, memory-leaks, profiling, debugging]
---

# Valgrind

Dynamic analysis tool suite for memory debugging, leak detection, and profiling. More thorough than sanitizers but much slower (10-50x).

:::info When to Use Valgrind
**Sanitizers can't find it?** Try Valgrind. Better leak detection, more thorough checks. Trade-off: 10-50x slower.
:::

## Valgrind Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| **Memcheck** | Memory errors, leaks | Default, most common |
| **Cachegrind** | Cache profiling | Performance analysis |
| **Callgrind** | Call graph profiling | Function call costs |
| **Helgrind** | Thread errors | Race detection |
| **Massif** | Heap profiling | Memory usage over time |

## Memcheck (Memory Errors)
```bash
# Basic usage
valgrind ./program

# With leak checking
valgrind --leak-check=full ./program

# Show leak details
valgrind --leak-check=full --show-leak-kinds=all ./program

# Track origins of uninitialized values
valgrind --track-origins=yes ./program

# Verbose output
valgrind -v --leak-check=full ./program
```

### What Memcheck Detects
```cpp showLineNumbers
// 1. Invalid read/write
int arr[10];
int x = arr[10];  // ❌ Invalid read of size 4

// 2. Use of uninitialized value
int x;
if (x == 5) {}  // ❌ Conditional jump depends on uninitialized value

// 3. Invalid free
int* p = new int;
delete p;
delete p;  // ❌ Invalid free() / delete

// 4. Memory leak
void leak() {
    int* p = new int[100];
    // No delete[]  // ❌ 400 bytes in 1 blocks definitely lost
}

// 5. Mismatched free/delete
int* p = new int[10];
delete p;  // ❌ Mismatched free() / delete / delete[]
```

### Valgrind Output
```
==12345== Invalid write of size 4
==12345==    at 0x400567: main (program.cpp:10)
==12345==  Address 0x5203050 is 0 bytes after a block of size 40 alloc'd
==12345==    at 0x4C2E0EF: operator new[](unsigned long)
==12345==    by 0x400557: main (program.cpp:8)

==12345== LEAK SUMMARY:
==12345==    definitely lost: 400 bytes in 1 blocks
==12345==    indirectly lost: 0 bytes in 0 blocks
==12345==      possibly lost: 0 bytes in 0 blocks
==12345==    still reachable: 0 bytes in 0 blocks
==12345==         suppressed: 0 bytes in 0 blocks
```

## Leak Types

| Type | Meaning |
|------|---------|
| **Definitely lost** | Memory leak, no pointers to it |
| **Indirectly lost** | Lost via definitely lost block |
| **Possibly lost** | Pointer to middle of block |
| **Still reachable** | Pointer exists but not freed |
| **Suppressed** | Ignored via suppressions file |

## Cachegrind (Cache Profiling)

Simulates CPU cache behavior.
```bash
# Run with cachegrind
valgrind --tool=cachegrind ./program

# Produces cachegrind.out.<pid>
# View with:
cg_annotate cachegrind.out.12345

# Show top functions
cg_annotate --auto=yes cachegrind.out.12345
```

**Output shows:**
- Instruction cache misses
- Data cache misses
- Branch mispredictions

## Callgrind (Call Graph Profiling)

Records call graph and call counts.
```bash
# Run with callgrind
valgrind --tool=callgrind ./program

# Produces callgrind.out.<pid>
# Visualize with KCachegrind (GUI)
kcachegrind callgrind.out.12345

# Or text view
callgrind_annotate callgrind.out.12345
```

**Shows:**
- Function call counts
- Inclusive/exclusive costs
- Call relationships

## Helgrind (Thread Errors)

Detects thread synchronization errors.
```bash
# Run with helgrind
valgrind --tool=helgrind ./program
```
```cpp showLineNumbers
#include <thread>

int shared = 0;  // Not protected

void thread1() { shared = 1; }  // ❌ Possible data race
void thread2() { shared = 2; }  // ❌ Possible data race

int main() {
    std::thread t1(thread1);
    std::thread t2(thread2);
    t1.join();
    t2.join();
}
```

**Helgrind reports:**
```
==12345== Possible data race during read of size 4 at 0x601060 by thread #1
==12345== This conflicts with a previous write of size 4 by thread #2
```

## Massif (Heap Profiling)

Tracks heap memory usage over time.
```bash
# Run with massif
valgrind --tool=massif ./program

# Produces massif.out.<pid>
# View with:
ms_print massif.out.12345

# Or GUI
massif-visualizer massif.out.12345
```

**Shows:**
- Heap usage over time
- Peak memory usage
- Where allocations happen

## Common Options
```bash
# Detailed leak checking
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --verbose \
         --log-file=valgrind.log \
         ./program

# Suppress known issues
valgrind --suppressions=my.supp ./program

# Generate suppressions
valgrind --gen-suppressions=all ./program
```

## Suppression File
```
# my.supp
{
   ignore_std_string_leak
   Memcheck:Leak
   ...
   fun:*std::string*
}

{
   ignore_known_library_issue
   Memcheck:Addr4
   obj:/usr/lib/libfoo.so
}
```
```bash
# Use suppression file
valgrind --suppressions=my.supp ./program
```

## Performance Tips
```bash
# Faster (less accurate)
valgrind --expensive-definedness-checks=no ./program

# Even faster
valgrind --partial-loads-ok=yes ./program

# Limit trace depth
valgrind --num-callers=12 ./program  # Default: 12

# For large programs
valgrind --time-stamp=yes ./program
```

## Debugging with Valgrind
```bash
# Start program paused
valgrind --vgdb=yes --vgdb-error=0 ./program

# In another terminal, attach GDB
gdb ./program
(gdb) target remote | vgdb
(gdb) continue
```

## Common False Positives
```cpp showLineNumbers
// Uninitialized value (intentional)
std::vector<int> v(100);  // Valgrind: uninitialized
// Values are uninitialized but that's OK here

// Still reachable (not a leak)
static std::string global = "hello";
// Valgrind: still reachable at exit
// Not freed, but not a leak (program ending)
```

## Valgrind vs Sanitizers

| Feature | Valgrind | Sanitizers |
|---------|----------|------------|
| **Speed** | 10-50x slower | 2-3x slower |
| **Coverage** | More thorough | Fast enough for CI |
| **Leak detection** | Excellent | Good (ASan) |
| **Uninitialized reads** | Yes | MSan only |
| **Thread errors** | Helgrind | TSan (better) |
| **Setup** | No recompile | Needs recompile |

## When to Use What
```bash
# Daily development: Sanitizers
g++ -fsanitize=address,undefined program.cpp

# Can't reproduce with sanitizers: Valgrind
valgrind --leak-check=full ./program

# Performance profiling: Cachegrind/Callgrind
valgrind --tool=callgrind ./program

# Thread debugging: TSan first, then Helgrind
g++ -fsanitize=thread program.cpp  # Try first
valgrind --tool=helgrind ./program  # If TSan doesn't find it
```

## Real-World Example
```cpp showLineNumbers
// leak.cpp
#include <iostream>

void leak() {
    int* p = new int[100];
    // Forgot delete[]
}

int main() {
    leak();
    std::cout << "Done\n";
    return 0;
}
```
```bash
# Compile
g++ -g leak.cpp -o leak

# Run with Valgrind
valgrind --leak-check=full ./leak

# Output shows:
# 400 bytes in 1 blocks are definitely lost
# at operator new[](unsigned long)
# by leak() (leak.cpp:5)
```

## CI Integration
```bash
# Run tests with Valgrind
#!/bin/bash
valgrind --leak-check=full \
         --error-exitcode=1 \
         --errors-for-leak-kinds=definite,possible \
         ./test_suite

# Exit code 1 if leaks found → CI fails
```

## Summary

:::info
Valgrind = dynamic analysis tool suite.
- **Memcheck** (default): memory errors, leaks, uninitialized values.
- **Cachegrind**: cache profiling.
- **Callgrind**: call graph.
- **Helgrind**: thread errors.
- **Massif**: heap profiling.
---
- Much slower than sanitizers (10-50x) but more thorough.
- Use `--leak-check=full` for leak detection.
- Good for finding bugs sanitizers miss.
- Not for production (too slow).
:::

```bash
# Most common usage:
valgrind --leak-check=full --show-leak-kinds=all ./program

# Profile:
valgrind --tool=callgrind ./program
kcachegrind callgrind.out.*

# Threads:
valgrind --tool=helgrind ./program
```