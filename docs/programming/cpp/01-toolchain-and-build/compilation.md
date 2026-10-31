---
id: compilation
title: Compilation
sidebar_label: Compilation
sidebar_position: 3
tags: [c++, compiler, optimization, assembly]
---

# Compilation

Compilation proper is stage 2 of the [pipeline](./compilation-pipeline.md): it takes one
preprocessed translation unit and turns it into assembly for the target CPU. This is the only stage
that understands C++. It is where syntax and type errors come from, where templates are
instantiated, and where the optimiser decides what your code actually does at run time. It is also,
by a wide margin, the stage where build time goes.

**Prerequisites:** [The Compilation Pipeline](./compilation-pipeline.md),
[Preprocessing](./preprocessing.md).

## Inside the compiler

<Diagram title="Front end, middle end, back end" caption="GCC and Clang are both structured this way; only the IR differs (GIMPLE/RTL vs LLVM IR)." accent="green">
  <DiagramRow>
    <DiagramNode icon="file-text" title="Front end">Tokens → syntax tree. Name lookup, overload resolution, templates, type checks. All C++ errors come from here.</DiagramNode>
    <DiagramArrow direction="right" label="IR" />
    <DiagramNode icon="gauge" title="Optimiser" accent>Language-independent passes on an intermediate representation: inlining, constant folding, loop transforms.</DiagramNode>
    <DiagramArrow direction="right" label="IR" />
    <DiagramNode icon="cpu" title="Back end">Instruction selection, register allocation, scheduling for `-march`. Writes `.s`.</DiagramNode>
  </DiagramRow>
</Diagram>

You can look at each layer with Clang. For `int add(int a, int b) { return a + b * 2; }`:

<Tabs>
  <TabItem value="ast" label="Syntax tree">

```bash
clang++ -std=c++23 -Xclang -ast-dump -fsyntax-only add.cpp
```

```text
`-ReturnStmt <col:22, col:33>
  `-BinaryOperator 'int' '+'
    |-ImplicitCastExpr 'int' <LValueToRValue>
    | `-DeclRefExpr 'int' lvalue ParmVar 'a' 'int'
    `-BinaryOperator 'int' '*'
      |-ImplicitCastExpr 'int' <LValueToRValue>
      | `-DeclRefExpr 'int' lvalue ParmVar 'b' 'int'
      `-IntegerLiteral 'int' 2
```

Precedence is already resolved: `*` sits below `+`. (Node addresses removed.)

  </TabItem>
  <TabItem value="ir" label="LLVM IR (-O1)">

```bash
clang++ -O1 -S -emit-llvm add.cpp -o -
```

```text
define dso_local noundef i32 @_Z3addii(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = shl nsw i32 %1, 1
  %4 = add nsw i32 %3, %0
  ret i32 %4
}
```

The optimiser already replaced `* 2` by a shift. `nsw` ("no signed wrap") records that signed
overflow is undefined, which later passes are allowed to rely on.

  </TabItem>
</Tabs>

Everything the front end does is language semantics, covered in the language sections: overload
resolution in [Overloading](../04-functions-and-call-mechanics/overloading.md), templates in
[Function Templates](../08-templates-and-metaprogramming/function-templates.md). What matters for
the toolchain is the consequence: **templates are instantiated in every translation unit that uses
them**, so their definitions must be visible there (see
[Translation Units](./translation-units.md#templates-and-inline-functions)).

## Optimisation levels

| Flag | What it does (per [GCC: Optimize Options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)) | Use for |
|---|---|---|
| `-O0` | Default. No optimisation; every variable lives in memory, so the debugger sees everything | Debugging |
| `-Og` | Optimisations that don't interfere with debugging | Debug builds you still want to run at a reasonable speed |
| `-O1` | Basic optimisations without large compile-time cost | Rarely chosen directly |
| `-O2` | Nearly all optimisations that don't trade size for speed | The usual release level |
| `-O3` | `-O2` plus more aggressive inlining and vectorisation; can grow code | Hot numeric code; measure it |
| `-Os` / `-Oz` | Optimise for size | Embedded, caches |

`-O3` is not automatically faster than `-O2`. Measure your own program before choosing it.

### The same loop at `-O0` and `-O2`

```cpp title="sum_to.cpp"
int sum_to(int n) {
    int total = 0;
    for (int i = 1; i <= n; ++i) total += i;
    return total;
}
```

<Tabs groupId="opt">
  <TabItem value="o0" label="GCC 15 -O0">

```nasm
_Z6sum_toi:
	push	rbp
	mov	rbp, rsp
	mov	DWORD PTR -20[rbp], edi      # n spilled to the stack
	mov	DWORD PTR -8[rbp], 0         # total = 0
	mov	DWORD PTR -4[rbp], 1         # i = 1
	jmp	.L2
.L3:
	mov	eax, DWORD PTR -4[rbp]
	add	DWORD PTR -8[rbp], eax       # total += i
	add	DWORD PTR -4[rbp], 1         # ++i
.L2:
	mov	eax, DWORD PTR -4[rbp]
	cmp	eax, DWORD PTR -20[rbp]
	jle	.L3
	mov	eax, DWORD PTR -8[rbp]
	pop	rbp
	ret
```

  </TabItem>
  <TabItem value="o2" label="GCC 15 -O2">

```nasm
_Z6sum_toi:
	test	edi, edi
	jle	.L4
	lea	ecx, 1[rdi]
	xor	edx, edx
	and	edi, 1
	mov	eax, 1
	je	.L3
	mov	eax, 2
	mov	edx, 1
	cmp	eax, ecx
	je	.L1
.L3:
	lea	edx, 1[rdx+rax*2]            # two iterations per pass
	add	eax, 2
	cmp	eax, ecx
	jne	.L3
.L1:
	mov	eax, edx
	ret
.L4:
	xor	edx, edx
	mov	eax, edx
	ret
```

  </TabItem>
  <TabItem value="clang" label="Clang 21 -O2">

```nasm
_Z6sum_toi:
	test	edi, edi
	jle	.LBB0_1
	lea	eax, [rdi - 1]
	lea	ecx, [rdi - 2]
	imul	rcx, rax
	shr	rcx
	lea	eax, [rcx + 2*rdi]
	dec	eax
	ret
.LBB0_1:
	xor	eax, eax
	ret
```

  </TabItem>
</Tabs>

All three were produced with `-S -masm=intel -fno-asynchronous-unwind-tables` (GCC also
`-fcf-protection=none`), with directives removed. At `-O0` every access goes through the stack. At
`-O2`, GCC keeps everything in registers and unrolls by two; Clang recognises the arithmetic series
and computes it in closed form with no loop at all. Two compilers, same source, same flag, different
code: claims like "the compiler turns this into a formula" are compiler-specific and need checking.
[Compiler Explorer](https://godbolt.org) shows the output of many compilers side by side.

Optimisations you will see in output like this: **inlining** (copying a callee's body into the
caller, which enables everything else), **constant folding** (`3 + 4 * 5` becomes `23`), **dead code
elimination**, **strength reduction** (`x * 2` to a shift or `lea`), **loop unrolling**, and
**vectorisation** (SIMD instructions at `-O2`/`-O3`). The optimiser may assume undefined behaviour
never happens, which is why code with UB can change meaning between `-O0` and `-O2`; see
[Undefined Behavior](../10-error-handling-and-safety/06-undefined-behavior.md).

## Warnings

Warnings are the front end telling you that code is valid but probably wrong. Turn them on for every
build ([GCC: Warning Options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html)):

```bash
g++ -std=c++23 -Wall -Wextra -Wpedantic -Wconversion -Wshadow main.cpp
```

| Flag | Catches (examples) |
|---|---|
| `-Wall` | Unused variables, `if (x = 5)`, missing `return`, misleading indentation. Despite the name, not "all" |
| `-Wextra` | Unused parameters, signed/unsigned comparisons in C++ |
| `-Wpedantic` | Non-standard extensions (VLAs, GNU syntax) |
| `-Wconversion` | Implicit narrowing: `int` → `short`, `double` → `int` |
| `-Wshadow` | A local hiding another variable of the same name |
| `-Werror` | Turn warnings into errors (common in CI; risky in released build scripts, since a new compiler version adds warnings) |

Example from GCC 15 with `-Wall`:

```text
w.cpp:3:11: warning: comparison of integer expressions of different signedness: ‘unsigned int’ and ‘int’ [-Wsign-compare]
```

The bracket names the flag, so you can look it up or disable that one warning locally.

## Inspecting compiler output

```bash
g++ -O2 -S -masm=intel main.cpp -o main.s       # assembly
g++ -O2 -S -fverbose-asm main.cpp -o main.s     # assembly annotated with variable names
g++ -O2 -save-temps -c main.cpp                 # keep .ii, .s and .o
clang++ -O2 -S -emit-llvm main.cpp -o main.ll   # LLVM IR
g++ -O2 -fopt-info-vec-missed main.cpp          # report loops that were NOT vectorised
g++ -ftime-report -c main.cpp                   # where compile time went
```

## Reducing compile time

The compiler re-parses every included header in every TU, so most compile-time fixes reduce how
much text each TU contains:

- **Include less.** Forward-declare types you only use by pointer or reference, and include what
  you use: [Headers and Includes](./headers-and-includes.md#forward-declarations).
- **Precompiled headers.** Parse a stable set of headers once and reuse the result
  ([details](./headers-and-includes.md#precompiled-headers)).
- **Explicit instantiation.** `extern template class Box<int>;` in a header stops every TU from
  instantiating `Box<int>`; one `.cpp` provides `template class Box<int>;`.
- **Modules** *(C++20)*: compile an interface once and import it: [Modules](./modules.md).
- **Parallel and incremental builds**, which the build system provides:
  [Build Systems](./build-systems-cmake.md).

## Pitfalls

- **Benchmarking a `-O0` build.** It measures memory traffic the release build will not have.
- **`-march=native` in shipped binaries.** It targets the build machine's CPU. The binary may crash
  with an illegal instruction on an older CPU. Use it only for code that runs where it is built.
- **Believing `inline` controls inlining.** At `-O2` the compiler inlines by its own cost model.
  The keyword's real meaning is about the One Definition Rule
  ([Inline Functions](../04-functions-and-call-mechanics/inline-functions.md)).
- **Debugging optimised code without `-g`.** `-O2 -g` is valid and common; variables may show as
  `<optimized out>`, but stack traces and line numbers work.

## Key points

- Front end (C++ semantics, all errors) → optimiser (IR) → back end (target assembly).
- `-O2` is the normal release level; `-O3` and `-march=native` are choices to measure and justify.
- Different compilers optimise the same code differently. Read the assembly before claiming what it
  does.
- Compile time is mostly header text; reduce what each translation unit includes.
