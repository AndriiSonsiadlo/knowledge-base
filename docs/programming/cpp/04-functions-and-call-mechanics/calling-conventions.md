---
id: calling-conventions
title: Calling Conventions
sidebar_label: Calling Conventions
sidebar_position: 7
tags: [c++, calling-conventions, abi, platform, assembly]
---

# Calling Conventions

A **calling convention** is the contract between a caller and a callee at the machine level: where
the arguments go (which registers, which stack slots), where the result comes back, which registers
the callee may overwrite, and who keeps the stack aligned. The C++ standard says nothing about it.
It is part of the platform [ABI](../12-low-level-and-platform/01-abi.md), and you need it when you
read compiler output, debug a crash in a backtrace, write assembly, or call across a language
boundary.

**Prerequisites:** [Function Declarations](./function-declarations.md). Reading x86-64 assembly
(registers, `mov`, `call`, `ret`) is covered in [Reading Assembly](../14-debugging-and-profiling/07-reading-assembly.md).

This page covers the two 64-bit x86 conventions you meet in practice: the **System V AMD64 ABI**
(Linux, macOS, the BSDs) and the **Microsoft x64** convention (Windows). Every listing below was
generated from the same source file with GCC 15.2 (`g++ -std=c++23 -O2 -S -masm=intel`) for System V
and Clang 21.1 (`clang++ --target=x86_64-pc-windows-msvc -O2 -S -masm=intel`) for Windows, with
assembler directives removed.

## The two x86-64 conventions at a glance

| | System V AMD64 | Microsoft x64 |
|---|---|---|
| Integer/pointer arguments | `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9` | `rcx`, `rdx`, `r8`, `r9` |
| Floating-point arguments | `xmm0`–`xmm7` | `xmm0`–`xmm3` |
| Slot assignment | Integer and FP registers counted **separately** | **Positional**: argument *n* uses slot *n*, integer or FP |
| Further arguments | Stack, first one at `[rsp+8]` on entry | Stack, first one at `[rsp+40]` on entry |
| Integer return | `rax` (second eightbyte in `rdx`) | `rax` |
| FP return | `xmm0` | `xmm0` |
| Callee-saved (non-volatile) | `rbx`, `rbp`, `r12`–`r15` | `rbx`, `rbp`, `rdi`, `rsi`, `r12`–`r15`, `xmm6`–`xmm15` |
| Space the caller must reserve | None | 32-byte **shadow space** before every call |
| Below `rsp` | 128-byte **red zone** a leaf function may use | Nothing; memory below `rsp` is not yours |
| Stack alignment | `rsp` is 16-byte aligned at the `call` instruction | Same |

Sources: the [System V x86-64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI) and Microsoft's
[x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention).
Because the two disagree on registers, a function compiled for one cannot be called directly with
the other's convention. That is one reason Linux and Windows object files don't mix.

<Diagram title="Where the arguments of mix(int i, double x, long long j, float y) go" caption="System V fills integer and FP registers independently; Microsoft x64 gives each argument position one slot." accent="blue">
  <DiagramGroup label="System V AMD64">
    <DiagramNode title="Integer registers">`i` → `edi`, `j` → `rsi`</DiagramNode>
    <DiagramNode title="FP registers" accent>`x` → `xmm0`, `y` → `xmm1`</DiagramNode>
  </DiagramGroup>
  <DiagramGroup label="Microsoft x64">
    <DiagramNode title="Slot 1, 3">`i` → `ecx`, `j` → `r8`</DiagramNode>
    <DiagramNode title="Slot 2, 4">`x` → `xmm1`, `y` → `xmm3`</DiagramNode>
  </DiagramGroup>
</Diagram>

## Arguments in registers

The test file used throughout the page:

```cpp title="cc.cpp" showLineNumbers
struct Pair { long long a, b; };
struct Big  { long long v[4]; };

long long sum7(long long a, long long b, long long c, long long d,
               long long e, long long f, long long g) {
    return a + b + c + d + e + f + g;
}
double mix(int i, double x, long long j, float y) { return i * x + j * y; }
Pair make_pair(long long a, long long b) { return {a, b}; }
Big  make_big(long long a) { return {{a, a, a, a}}; }

long long helper(long long x);          // defined in another file: forces a real call
long long caller(long long x) {
    long long kept = x * 3;             // must survive the call
    return helper(x) + kept;
}
```

`sum7` takes seven integers. System V has six integer argument registers, so only `g` goes on the
stack. Microsoft x64 has four, so `e`, `f` and `g` do:

<Tabs groupId="abi">
  <TabItem value="sysv" label="System V (GCC, Linux)">

```nasm
_Z4sum7xxxxxxx:
    add  rdi, rsi                 ; a + b
    add  rdi, rdx                 ; + c
    add  rdi, rcx                 ; + d
    add  rdi, r8                  ; + e
    lea  rax, [rdi+r9]            ; + f, result into rax
    add  rax, QWORD PTR [rsp+8]   ; + g, the 7th argument, from the stack
    ret
```

  </TabItem>
  <TabItem value="win" label="Microsoft x64 (Clang, Windows target)">

```nasm
"?sum7@@YA_J_J000000@Z":
    add  rcx, rdx                 ; a + b
    lea  rax, [r8 + r9]           ; c + d
    add  rax, rcx
    add  rax, qword ptr [rsp + 40]   ; e: 8 (return address) + 32 (shadow space)
    add  rax, qword ptr [rsp + 48]   ; f
    add  rax, qword ptr [rsp + 56]   ; g
    ret
```

  </TabItem>
</Tabs>

The first stack argument sits at `[rsp+8]` on System V because `[rsp]` holds the return address.
On Windows it sits at `[rsp+40]`: the caller also reserved 32 bytes of shadow space, one 8-byte slot
for each register argument, which the callee may use to spill `rcx`–`r9`.

`mix` shows the separate-versus-positional rule from the diagram. GCC reads `i` from `edi`, `x` from
`xmm0`, `j` from `rsi` and `y` from `xmm1`. The Windows code reads `ecx`, `xmm1`, `r8` and `xmm3`:

```nasm
; Microsoft x64
"?mix@@YANHN_JM@Z":
    cvtsi2sd  xmm0, ecx        ; (double)i         -- slot 1
    cvtsi2ss  xmm2, r8         ; (float)j          -- slot 3
    mulss     xmm2, xmm3       ; j * y             -- slot 4
    cvtss2sd  xmm2, xmm2
    mulsd     xmm0, xmm1       ; i * x             -- slot 2
    addsd     xmm0, xmm2       ; result in xmm0
    ret
```

## Return values

Scalars come back in `rax` (integers, pointers) or `xmm0` (floating point) on both platforms. The
conventions differ for class types:

- **System V** classifies a class of up to 16 bytes by its eightbytes. `Pair` (two `long long`) is
  two INTEGER eightbytes, so it returns in `rax:rdx`. Anything larger, or anything not trivially
  copyable, goes through memory.
- **Microsoft x64** returns a user-defined type in `rax` only if it is 1, 2, 4 or 8 bytes. `Pair`
  is 16 bytes, so it already goes through memory.

"Through memory" means a **hidden pointer**: the caller allocates the result object and passes its
address as an invisible first argument (`rdi` on System V, `rcx` on Windows). The callee builds the
result there and returns the same pointer in `rax`. This is the mechanism that makes guaranteed copy
elision possible: the "returned" object is constructed in the caller's storage from the start.

<Tabs groupId="abi">
  <TabItem value="sysv" label="System V (GCC, Linux)">

```nasm
_Z9make_pairxx:            ; 16 bytes: returned in registers
    mov  rax, rdi          ; .a
    mov  rdx, rsi          ; .b
    ret
_Z8make_bigx:              ; 32 bytes: hidden pointer in rdi, a in rsi
    movq        xmm0, rsi
    mov         rax, rdi   ; return the hidden pointer
    punpcklqdq  xmm0, xmm0
    movups      XMMWORD PTR [rdi], xmm0
    movups      XMMWORD PTR [rdi+16], xmm0
    ret
```

  </TabItem>
  <TabItem value="win" label="Microsoft x64 (Clang, Windows target)">

```nasm
"?make_pair@@YA?AUPair@@_J0@Z":   ; 16 bytes: hidden pointer in rcx
    mov  rax, rcx
    mov  qword ptr [rcx], rdx     ; a is now the 2nd slot
    mov  qword ptr [rcx + 8], r8  ; b is the 3rd slot
    ret
```

  </TabItem>
</Tabs>

## Who saves which registers

Registers are split into two groups. **Caller-saved** (volatile) registers may be destroyed by any
call, so a caller that needs a value in one after the call must save it first. **Callee-saved**
(non-volatile) registers must hold the same value when the callee returns, so a callee that wants to
use one saves it on entry and restores it before `ret`.

`caller` needs `kept` (or `x`) after `helper` returns. The compiler keeps it in a callee-saved
register, and so `caller` itself must save that register's old value for *its* caller:

<Tabs groupId="abi">
  <TabItem value="sysv" label="System V (GCC, Linux)">

```nasm
_Z6callerx:
    push  rbx                 ; rbx is callee-saved: preserve the caller's value
    mov   rbx, rdi            ; keep x where helper() can't touch it
    call  _Z6helperx          ; x is still in rdi, the first argument
    mov   rdx, rax            ; helper's result
    lea   rax, [rbx+rbx*2]    ; kept = x * 3
    pop   rbx                 ; restore the caller's rbx
    add   rax, rdx
    ret
```

  </TabItem>
  <TabItem value="win" label="Microsoft x64 (Clang, Windows target)">

```nasm
"?caller@@YA_J_J@Z":
    push  rsi                 ; rsi is callee-saved on Windows (volatile on System V)
    sub   rsp, 32             ; shadow space for helper
    lea   rsi, [rcx + 2*rcx]  ; kept = x * 3
    call  "?helper@@YA_J_J@Z" ; x is still in rcx
    add   rax, rsi
    add   rsp, 32
    pop   rsi
    ret
```

  </TabItem>
</Tabs>

The same instructions in the object file, disassembled with `objdump`. The call target shows as
`9` because the relocation for `helper` is filled in by the linker:

```bash
g++ -std=c++23 -O2 -fcf-protection=none -c call.cpp -o call.o
objdump -d -M intel --no-show-raw-insn -C call.o
```

```text
0000000000000000 <caller(long long)>:
   0:	push   rbx
   1:	mov    rbx,rdi
   4:	call   9 <caller(long long)+0x9>
   9:	mov    rdx,rax
   c:	lea    rax,[rbx+rbx*2]
  10:	pop    rbx
  11:	add    rax,rdx
  14:	ret
```

(`-fcf-protection=none` only drops the `endbr64` landing-pad instruction that Ubuntu's GCC adds by
default. It doesn't change the convention.)

## The stack frame during a call

<Diagram title="System V stack while helper() runs, called from caller()" caption="Addresses grow upward in this picture's top rows; the stack grows down toward the bottom." accent="violet">
  <DiagramNode title="Caller's caller frame">Its locals; any stack arguments (7th and later) for `caller`.</DiagramNode>
  <DiagramNode title="Return address into caller's caller">Pushed by the `call` that entered `caller`. `rsp` pointed here on entry.</DiagramNode>
  <DiagramNode title="Saved rbx">Pushed by `caller`'s prologue: `rbx` is callee-saved.</DiagramNode>
  <DiagramNode title="Return address into caller" accent>Pushed by `call helper`. Before the call `rsp` was 16-byte aligned.</DiagramNode>
  <DiagramNode title="helper's frame" dashed>Its own saved registers and locals; a leaf may also use the 128-byte red zone below `rsp`.</DiagramNode>
</Diagram>

`caller` has no locals in memory and no frame pointer at `-O2`: its whole frame is one saved
register. With `-O0` or `-fno-omit-frame-pointer` you also see `push rbp; mov rbp, rsp`, which links
frames into a chain that debuggers and profilers can walk.

The trace below follows `caller(4)` on System V, with `helper(x)` returning `x + 1`. Call the value
of `rsp` on entry `S`. The ABI makes `rsp` 16-byte aligned *at* the `call`, and `call` pushes 8
bytes, so `S` is always 8 more than a multiple of 16.

<Walkthrough title="caller(4) on System V, one instruction group at a time" caption="rsp values are relative to S, the stack pointer on entry to caller." accent="violet">
  <Step title="Entry">

`rdi` = 4 (the argument). `rsp` = `S`; `[S]` holds the return address into the code that called
`caller`. `rbx` holds some value the caller's caller owns.

  </Step>
  <Step title="push rbx">

`rsp` = <StepChange>`S - 8`</StepChange>, and `[S - 8]` = the old `rbx`. `rsp` is now 16-byte
aligned, which is what the upcoming `call` needs.

  </Step>
  <Step title="mov rbx, rdi">

<StepChange>`rbx` = 4</StepChange>. `x` now lives in a callee-saved register, so `helper` must give
it back unchanged. `rdi` still holds 4, ready as `helper`'s first argument.

  </Step>
  <Step title="call helper">

`call` pushes the return address (offset `0x9` in `caller`): `rsp` = <StepChange>`S - 16`</StepChange>.
Control jumps to `helper`, which sees `rdi` = 4 and returns <StepChange>`rax` = 5</StepChange>.
Its `ret` pops the return address, so `rsp` is back at `S - 8`.

  </Step>
  <Step title="Compute the result">

`mov rdx, rax` → `rdx` = 5. `lea rax, [rbx+rbx*2]` → <StepChange>`rax` = 12</StepChange> (`kept`).
`rbx` is still 4 because `helper` honoured the callee-saved rule.

  </Step>
  <Step title="pop rbx; add rax, rdx">

`pop rbx` restores the old `rbx` and sets `rsp` = <StepChange>`S`</StepChange>. `add` gives
<StepChange>`rax` = 17</StepChange>, the return value.

  </Step>
  <Step title="ret">

`ret` pops the return address: `rsp` = <StepChange>`S + 8`</StepChange> and control is back in the
caller's caller with 17 in `rax`. (Linked with a `main` that returns `caller(4)`, the program exits
with status 17.)

  </Step>
</Walkthrough>

## Variadic functions

A variadic callee such as `printf` cannot know the argument types in advance, so both conventions add
a rule:

- **System V:** the caller sets `al` to an upper bound on the number of vector registers used for
  arguments. The callee's prologue uses it to decide whether to spill `xmm0`–`xmm7`.
- **Microsoft x64:** a floating-point value passed through `...` is also copied into the matching
  integer register, so the callee can spill all four register slots into the shadow space and walk
  them as memory.

Both require a visible prototype at the call site. Calling a variadic function through a
non-variadic declaration is undefined behaviour and breaks in practice on these ABIs.

## 32-bit x86 and the convention keywords

On 32-bit x86 there was no single convention, which is where the keywords come from. All push
arguments right to left; they differ in cleanup and register use:

| Keyword | Arguments | Who pops the arguments |
|---|---|---|
| `__cdecl` | All on the stack | Caller (works with `...`) |
| `__stdcall` | All on the stack | Callee (Win32 API) |
| `__fastcall` | First two in `ecx`, `edx` | Callee |
| `__thiscall` | `this` in `ecx` (MSVC member functions) | Callee |

GCC and Clang spell these as attributes, `__attribute__((stdcall))` and so on. On x86-64 they have no
effect: there is one convention per platform, and GCC warns that the attribute is ignored. MSVC adds
`__vectorcall` on x64, which passes more values in vector registers.

`extern "C"` changes only [name mangling](../01-toolchain-and-build/name-mangling.md) and language
linkage. On x86-64 it doesn't select a different register convention: C and C++ functions already
use the same one. See [Interop with C](../12-low-level-and-platform/07-interop-c.md).

## Common mistakes

- **Assuming argument registers survive a call.** `rdi`, `rsi`, `rdx`, `rcx`, `r8`–`r11` and `rax`
  are caller-saved on System V. Hand-written assembly that keeps a value in one across a `call` reads
  garbage afterwards. Keep it in a callee-saved register, or spill it.
- **Treating `rsi`/`rdi` as scratch in Windows assembly.** They are non-volatile there, unlike on
  System V. Porting a routine without saving them corrupts the caller.
- **Misaligning the stack.** `rsp` must be a multiple of 16 at every `call`. A routine that pushes an
  odd number of 8-byte values and then calls out crashes as soon as the callee uses an aligned SSE
  store (`movaps`).
- **Forgetting the shadow space.** On Windows, calling a function without `sub rsp, 32` (plus
  alignment) lets the callee overwrite your stack data when it spills its arguments.
- **Assuming a small struct goes in registers everywhere.** `Pair` above is returned in `rax:rdx` on
  Linux and through a hidden pointer on Windows.

## Key points

- A calling convention is a platform ABI rule, not a C++ rule; the two x86-64 ones disagree on
  registers, shadow space, and which registers are callee-saved.
- System V: six integer + eight FP argument registers counted separately. Microsoft: four positional
  slots plus 32 bytes of shadow space.
- Results come back in `rax`/`xmm0`; large class types go through a caller-provided hidden pointer.
- Keep `rsp` 16-byte aligned at every `call`; values that must survive a call go in callee-saved
  registers.
- To see the convention your compiler uses, compile with `-O2 -S` or use `objdump -d` on the object
  file.
