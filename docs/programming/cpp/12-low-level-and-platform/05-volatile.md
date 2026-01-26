---
id: volatile
title: volatile Keyword
sidebar_label: volatile
sidebar_position: 5
tags: [cpp, volatile, hardware, optimization, memory-mapped]
---

# volatile Keyword

`volatile` tells compiler that a variable can change unexpectedly (hardware, interrupts, other threads). Prevents certain optimizations. **Not for thread synchronization** - use atomics instead.

:::danger Not for Threading
`volatile` ≠ thread-safe. Use `std::atomic` for multi-threading. `volatile` is for hardware/interrupts only.
:::

## What volatile Does
```cpp showLineNumbers
volatile int hardware_register;

// Without volatile: compiler might optimize away "redundant" reads
int x = hardware_register;
int y = hardware_register;  // Compiler might reuse x (wrong!)

// With volatile: forces actual reads
volatile int hardware_register;
int x = hardware_register;  // Read from hardware
int y = hardware_register;  // Read again (different value possible)
```

**Guarantee**: Every access actually touches memory - no optimization.

## volatile Prevents

### Optimization Away
```cpp showLineNumbers
// Without volatile
int status;
while (status == 0) {
    // Wait
}
// Compiler: "status never changes in loop, optimize to infinite loop"
// while (true) {}  ❌

// With volatile
volatile int status;
while (status == 0) {
    // Compiler must read status each iteration ✅
}
```

### Read/Write Reordering
```cpp showLineNumbers
volatile int* port = (int*)0x40000000;

*port = 1;
*port = 2;

// Compiler must not:
// - Eliminate first write
// - Reorder writes
// Both writes happen in order ✅
```

### Register Caching
```cpp showLineNumbers
// Without volatile
int sensor_value;
for (int i = 0; i < 1000; ++i) {
    if (sensor_value > 100) break;
}
// Compiler caches sensor_value in register ❌

// With volatile
volatile int sensor_value;
for (int i = 0; i < 1000; ++i) {
    if (sensor_value > 100) break;  // Reads from memory each time ✅
}
```

## Use Cases

### 1. Memory-Mapped I/O
```cpp showLineNumbers
// Hardware register at fixed address
volatile uint32_t* const UART_STATUS = (uint32_t*)0x40001000;
volatile uint32_t* const UART_DATA   = (uint32_t*)0x40001004;

void send_byte(uint8_t byte) {
    while (*UART_STATUS & 0x01) {  // Wait for ready
        // Must read UART_STATUS each iteration
    }
    *UART_DATA = byte;  // Write to hardware
}
```

### 2. Interrupt Service Routines (ISR)
```cpp showLineNumbers
volatile bool data_ready = false;

void interrupt_handler() {
    // Called by hardware
    data_ready = true;  // ISR modifies
}

void main_loop() {
    while (!data_ready) {
        // Wait for interrupt
        // Must read data_ready each time
    }
    process_data();
}
```

### 3. Signal Handlers (POSIX)
```cpp showLineNumbers
#include <signal.h>

volatile sig_atomic_t interrupted = 0;

void signal_handler(int sig) {
    interrupted = 1;  // Signal handler modifies
}

int main() {
    signal(SIGINT, signal_handler);
    
    while (!interrupted) {
        // Do work
        // Must read interrupted each iteration
    }
}
```

## What volatile Does NOT Do

### Not Thread-Safe
```cpp showLineNumbers
// ❌ WRONG: volatile doesn't make this thread-safe!
volatile int counter = 0;

void thread_func() {
    for (int i = 0; i < 1000; ++i) {
        counter++;  // ❌ RACE CONDITION!
    }
}

// ✅ CORRECT: Use atomic
std::atomic<int> counter{0};

void thread_func() {
    for (int i = 0; i < 1000; ++i) {
        counter++;  // ✅ Thread-safe
    }
}
```

### No Memory Barriers
```cpp showLineNumbers
// ❌ volatile doesn't prevent reordering across variables
volatile int flag;
int data;

void producer() {
    data = 42;       // These can be reordered!
    flag = 1;
}

// ✅ Atomic provides proper synchronization
std::atomic<int> flag;
int data;

void producer() {
    data = 42;
    flag.store(1, std::memory_order_release);  // ✅ Proper sync
}
```

### No Atomicity Guarantee
```cpp showLineNumbers
// ❌ Not atomic on all platforms
volatile long long value;
value = 0x123456789ABCDEF0;  // May be two separate writes!

// ✅ Guaranteed atomic
std::atomic<long long> value;
value = 0x123456789ABCDEF0;  // Atomic write
```

## volatile vs atomic vs mutex

| Need | Use |
|------|-----|
| **Hardware registers** | `volatile` |
| **ISR to main communication** | `volatile` + `sig_atomic_t` |
| **Multi-threading** | `std::atomic` |
| **Complex critical sections** | `std::mutex` |
```cpp showLineNumbers
// Hardware I/O
volatile uint32_t* hardware = (uint32_t*)0x40000000;

// Thread communication
std::atomic<bool> ready{false};

// Complex data structure
std::mutex mtx;
std::vector<int> shared_data;
```

## volatile Pointer vs Pointer to volatile
```cpp showLineNumbers
// Pointer to volatile data
volatile int* ptr;
// *ptr is volatile, ptr is not
// ptr can be cached, *ptr cannot

// Volatile pointer
int* volatile ptr;
// ptr is volatile, *ptr is not
// *ptr can be cached, ptr cannot

// Both volatile
volatile int* volatile ptr;
// Neither can be cached

// Common usage
volatile uint32_t* const hw_register = (uint32_t*)0x40000000;
// hw_register address is constant
// *hw_register is volatile
```

## Real-World Example: Embedded System
```cpp showLineNumbers
// Hardware registers
struct UART {
    volatile uint32_t STATUS;
    volatile uint32_t DATA;
    volatile uint32_t CONTROL;
};

volatile UART* const uart = (UART*)0x40001000;

void uart_send(const char* str) {
    while (*str) {
        // Wait for transmit ready
        while (!(uart->STATUS & 0x01)) {
            // Must read STATUS each time
        }
        
        // Send character
        uart->DATA = *str++;
    }
}

void uart_receive(char* buffer, size_t size) {
    for (size_t i = 0; i < size; ++i) {
        // Wait for receive ready
        while (!(uart->STATUS & 0x02)) {
            // Must read STATUS each time
        }
        
        // Read character
        buffer[i] = uart->DATA;
    }
}
```

## C++ Memory Model Position
```cpp showLineNumbers
// C++ standard: volatile has no thread synchronization semantics
// Java/C#: volatile has memory barrier semantics (different!)

// ❌ C++: Don't use for threading
volatile bool flag;

// ✅ C++: Use atomic for threading
std::atomic<bool> flag;

// ✅ volatile only for hardware
volatile int* hardware_register;
```

## Summary

:::info Volatile
`volatile` prevents compiler from optimizing away memory accesses - forces actual reads/writes every time.
- Memory aid: "Hardware Only, Not Threads"
- Use for: Hardware registers, ISRs, signal handlers
- Don't use for: Threading (use std::atomic)
- Prevents: Read/write optimization, caching, reordering
- Doesn't provide: Atomicity, memory barriers, thread safety
:::

```cpp
// Interview answer:
// "volatile prevents compiler optimizations on variable access -
// forces actual memory read/write every time. Use for hardware
// registers, ISRs, signal handlers where value can change
// unexpectedly outside normal program flow. NOT for threading -
// use std::atomic instead. volatile doesn't provide atomicity
// or memory barriers. Mainly for embedded/systems programming,
// rarely used in application code."
```