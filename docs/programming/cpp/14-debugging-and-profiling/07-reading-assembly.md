---
id: reading-assembly
title: Reading Assembly Output
sidebar_label: Reading Assembly
sidebar_position: 7
tags: [assembly, optimization, disassembly, performance]
---

# Reading Assembly Output

Understanding compiler-generated assembly helps verify optimizations, debug performance issues, and understand low-level behavior.

:::info Why Read Assembly?
**Verify optimizations**, debug weird performance, understand compiler decisions, learn CPU architecture. Not needed daily, but invaluable when needed.
:::

## Generating Assembly
```bash
# Generate assembly file
g++ -S -O2 program.cpp -o program.s

# With Intel syntax (more readable)
g++ -S -O2 -masm=intel program.cpp -o program.s

# Optimized assembly
g++ -S -O3 -march=native program.cpp -o program.s

# Disassemble existing binary
objdump -d program > program.asm
objdump -d -M intel program > program.asm  # Intel syntax

# Compiler Explorer (online)
# https://godbolt.org - instant assembly view
```

## AT&T vs Intel Syntax
```asm
# AT&T syntax (GCC default)
movl $5, %eax          # Source, Destination
addl %ebx, %eax        # Add ebx to eax

# Intel syntax (more readable)
mov eax, 5             # Destination, Source
add eax, ebx           # Add ebx to eax
```

**Use Intel syntax**: Easier to read.

## Basic x86-64 Registers

| Register | Purpose | 64-bit | 32-bit | 16-bit | 8-bit |
|----------|---------|--------|--------|--------|-------|
| **Accumulator** | Math/return | RAX | EAX | AX | AL |
| **Base** | Base pointer | RBX | EBX | BX | BL |
| **Counter** | Loop counter | RCX | ECX | CX | CL |
| **Data** | Data | RDX | EDX | DX | DL |
| **Stack Pointer** | Stack top | RSP | ESP | SP | SPL |
| **Base Pointer** | Stack frame | RBP | EBP | BP | BPL |
| **Source Index** | String ops | RSI | ESI | SI | SIL |
| **Dest Index** | String ops | RDI | EDI | DI | DIL |
| **R8-R15** | General | R8-R15 | R8D-R15D | R8W-R15W | R8B-R15B |

**Special registers:**
- `rip` = Instruction pointer
- `rflags` = Flags (zero, carry, etc.)

## Common Instructions
```asm
# Data movement
mov   rax, rbx         # Move: rax = rbx
lea   rax, [rbx + 8]   # Load effective address
push  rax              # Push to stack
pop   rax              # Pop from stack

# Arithmetic
add   rax, rbx         # rax = rax + rbx
sub   rax, rbx         # rax = rax - rbx
imul  rax, rbx         # rax = rax * rbx (signed)
idiv  rbx              # rax = rdx:rax / rbx (signed)
inc   rax              # rax++
dec   rax              # rax--

# Bitwise
and   rax, rbx         # rax = rax & rbx
or    rax, rbx         # rax = rax | rbx
xor   rax, rbx         # rax = rax ^ rbx
not   rax              # rax = ~rax
shl   rax, 2           # rax << 2
shr   rax, 2           # rax >> 2 (logical)
sar   rax, 2           # rax >> 2 (arithmetic, sign-extend)

# Comparison
cmp   rax, rbx         # Compare (sets flags)
test  rax, rax         # AND and set flags (often: is zero?)

# Control flow
jmp   label            # Unconditional jump
je    label            # Jump if equal (ZF=1)
jne   label            # Jump if not equal (ZF=0)
jl    label            # Jump if less (SF≠OF)
jg    label            # Jump if greater
call  function         # Call function
ret                    # Return
```

## Reading Simple Functions
```cpp showLineNumbers
int add(int a, int b) {
    return a + b;
}
```
```asm
# Intel syntax
add:
    lea eax, [rdi + rsi]    # eax = rdi + rsi (a + b)
    ret                      # Return (result in eax)

# Explanation:
# rdi = first argument (a)
# rsi = second argument (b)
# eax = return value
# lea = load effective address (fast add)
```

## Function Call Convention (x86-64 System V)

**Arguments** (in order):
1. `rdi`
2. `rsi`
3. `rdx`
4. `rcx`
5. `r8`
6. `r9`
7. Stack (if more than 6)

**Return value**: `rax`

**Caller-saved**: `rax`, `rcx`, `rdx`, `r8-r11`  
**Callee-saved**: `rbx`, `rbp`, `r12-r15`
```cpp showLineNumbers
int func(int a, int b, int c, int d, int e, int f, int g) {
    return a + b + c + d + e + f + g;
}
```
```asm
func:
    # a=rdi, b=rsi, c=rdx, d=rcx, e=r8, f=r9
    add edi, esi           # a += b
    add edi, edx           # a += c
    add edi, ecx           # a += d
    add edi, r8d           # a += e
    add edi, r9d           # a += f
    mov eax, DWORD PTR [rsp+8]  # g from stack
    add eax, edi           # result
    ret
```

## Optimization Examples

### Loop Unrolling
```cpp showLineNumbers
void zero_array(int* arr, int n) {
    for (int i = 0; i < n; ++i) {
        arr[i] = 0;
    }
}
```
```asm
# -O0: Simple loop with increment

# -O3: Vectorized + unrolled
zero_array:
    test    esi, esi
    jle     .L1
    pxor    xmm0, xmm0         # Zero vector register
.L3:
    movdqu  [rdi], xmm0        # Store 16 bytes at once
    movdqu  [rdi+16], xmm0     # Store another 16
    add     rdi, 32            # Advance pointer
    sub     esi, 8             # Decrement counter (8 ints)
    jg      .L3                # Loop
.L1:
    ret
```

**Optimized**: Processes 8 ints per iteration with SIMD.

### Constant Folding
```cpp showLineNumbers
int compute() {
    return 10 * 20 + 5;
}
```
```asm
# -O0: Actual math at runtime
# -O2: Computed at compile time
compute:
    mov eax, 205        # Result precomputed!
    ret
```

### Inlining
```cpp showLineNumbers
inline int square(int x) {
    return x * x;
}

int use_square(int n) {
    return square(n) + 1;
}
```
```asm
# -O2: Function inlined, no call
use_square:
    imul edi, edi       # n * n (inlined)
    lea eax, [rdi + 1]  # result + 1
    ret
```

## Identifying Bottlenecks
```asm
# Good: Fast operations
mov eax, ebx            # 1 cycle
add eax, 5              # 1 cycle
lea eax, [rbx + 8]      # 1 cycle

# Slow: Division
idiv ecx                # ~20-40 cycles

# Slow: Memory access (if cache miss)
mov eax, [rbx]          # 1 cycle (L1), ~200 cycles (RAM)

# Good: Vectorized
movdqu xmm0, [rdi]      # Load 16 bytes at once
```

## Stack Frame
```cpp showLineNumbers
void function(int x) {
    int local = x + 5;
    // ...
}
```
```asm
function:
    push    rbp              # Save old base pointer
    mov     rbp, rsp         # New base pointer
    sub     rsp, 16          # Allocate stack space
    
    mov     DWORD PTR [rbp-4], edi   # Store x
    mov     eax, DWORD PTR [rbp-4]
    add     eax, 5
    mov     DWORD PTR [rbp-8], eax   # Store local
    
    leave                    # Restore rbp, rsp
    ret
```

**Stack layout:**
```
High addresses
+----------------+
| Return address |  <- rsp on entry
+----------------+
| Old rbp        |  <- rbp points here after push
+----------------+
| Local variable |  <- rbp-4, rbp-8, etc.
+----------------+
Low addresses
```

## Compiler Explorer (Godbolt)

Online tool for instant assembly viewing.

**URL**: https://godbolt.org
```cpp
// Paste code, see assembly instantly
int add(int a, int b) {
    return a + b;
}
```

**Features:**
- Compare compilers (GCC, Clang, MSVC)
- Compare optimization levels
- Color-coded source ↔ assembly mapping
- Share links

## Reading Disassembled Binary
```bash
# Disassemble specific function
objdump -d -M intel program | grep -A 20 "^[0-9a-f]* <main>:"

# Disassemble with source interleaved
objdump -S -M intel program

# GDB disassembly
gdb ./program
(gdb) disassemble main
(gdb) disas /m main      # With source
```

## Common Patterns

### Null Check
```cpp
if (ptr == nullptr) return;
```
```asm
test rdi, rdi       # Test if rdi is zero
je   .L_return      # Jump if zero
```

### Loop
```cpp
for (int i = 0; i < n; ++i)
```
```asm
    xor eax, eax      # i = 0
.L_loop:
    cmp eax, esi      # Compare i with n
    jge .L_done       # Jump if i >= n
    # ... loop body ...
    inc eax           # i++
    jmp .L_loop
.L_done:
```

### Function Call
```cpp
int result = func(a, b, c);
```
```asm
mov  edi, eax       # First arg (a)
mov  esi, ebx       # Second arg (b)
mov  edx, ecx       # Third arg (c)
call func           # Call function
mov  [result], eax  # Store return value
```

## Summary

**Generate**: `g++ -S -O2 -masm=intel`. **Registers**: `rax` (return), `rdi/rsi/rdx/rcx/r8/r9` (args). **Common**: `mov` (copy), `add/sub` (math), `cmp` (compare), `jmp/je/jne` (branch), `call/ret` (function). **Optimizations**: Inlining (no call), constant folding (precompute), vectorization (SIMD), unrolling (fewer iterations). **Tools**: Compiler Explorer (godbolt.org), `objdump -d`. Focus on hot paths, not every line.
```asm
; Memory aid: "MACJ" (Mov Add Cmp Jmp)
; M = mov (data movement)
; A = add/sub (arithmetic)
; C = cmp/test (comparison)
; J = jmp/je/call (control flow)

; Reading assembly:
; 1. Find function entry
; 2. Identify prologue (push rbp, mov rbp rsp)
; 3. Track register usage (rdi=arg1, rsi=arg2, rax=return)
; 4. Follow control flow (jmp, je, call)
; 5. Find epilogue (leave, ret)
```