---
id: assembling
title: Assembling Phase
sidebar_label: Assembling
sidebar_position: 4
tags: [c++, assembler, object-files, machine-code]
---

# Assembling Phase

The assembler converts human-readable assembly code into binary machine code (object files). Each assembly instruction becomes actual CPU instructions.

:::info Binary Translation
Assembly is the last human-readable format. After this phase, everything is binary machine code.
:::

## Assembly to Machine Code

**Input**: Assembly file (`.s`)  
**Output**: Object file (`.o` or `.obj`)  
**Tool**: `as` (GNU assembler), or `g++` which calls it

```bash
# Assemble to object file
as main.s -o main.o

# Or using g++ (stops after assembly)
g++ -c main.cpp -o main.o
```

---

## Object File Structure

Object files contain:

```
.text section:    Machine code (executable instructions)
.data section:    Initialized global/static variables
.bss section:     Uninitialized global/static variables
.rodata section:  Read-only data (string literals, const)
Symbol table:     Function/variable names and addresses
Relocation table: Where linker needs to patch addresses
Debug info:       Source line mappings (if -g flag)
```

### Example Object File Content

```cpp
// source.cpp
int global = 42;           // .data section
int uninit;                // .bss section
const char* msg = "Hi";    // .rodata section

int add(int a, int b) {    // .text section
    return a + b;
}
```

Inspect with:
```bash
# View sections
objdump -h main.o

# View machine code
objdump -d main.o

# View symbols
nm main.o

# View all info
readelf -a main.o  # Linux
otool -tv main.o   # macOS
```

---

## Machine Code Example

```asm
# Assembly
mov    eax, 5
add    eax, 3
ret

# Machine code (hexadecimal bytes)
B8 05 00 00 00    # mov eax, 5
83 C0 03          # add eax, 3
C3                # ret
```

Each assembly instruction maps to 1-15 bytes of machine code. The CPU reads these bytes directly.

---

## Symbol Table

The symbol table maps names to addresses and tracks which symbols are defined/undefined:

```bash
nm main.o

# Output:
0000000000000000 T main          # T = defined in .text
                 U std::cout     # U = undefined (from library)
0000000000000008 D global_var    # D = defined in .data
0000000000000000 B uninit_var    # B = defined in .bss
```

**Symbol Types**:
- `T` = Function defined in .text
- `D` = Variable in .data (initialized)
- `B` = Variable in .bss (uninitialized)
- `U` = Undefined (needs linking)
- `W` = Weak symbol (can be overridden)

---

## Relocation

Object files have **relative addresses** that need fixing during linking:

```cpp
extern int external_var;

int foo() {
    return external_var;  // Address unknown at assembly time!
}
```

The assembler marks this as needing relocation:
```bash
objdump -r main.o

# Output:
RELOCATION RECORDS FOR [.text]:
OFFSET   TYPE              VALUE
00000005 R_X86_64_PC32     external_var-0x4
```

The linker will patch the address when it knows where `external_var` lives.

---

## Position-Independent Code (PIC)

Code that works at any memory address - required for shared libraries:

```bash
# Compile position-independent code
g++ -fPIC -c main.cpp -o main.o

# For shared library
g++ -shared -fPIC utils.o -o libutils.so
```

PIC uses relative addressing instead of absolute addresses, allowing the code to be loaded anywhere in memory.

---

## Summary

Assembling:
- Converts **assembly → binary machine code**
- Creates **object files** (.o) with sections
- Generates **symbol table** for linking
- Marks **relocations** for address patching
- Fast phase (< 1% of build time)

The object file is not executable yet - it needs linking to resolve external symbols and create the final binary.