---
id: headers-and-includes
title: Headers and Include Mechanism
sidebar_label: Headers & Includes
sidebar_position: 10
tags: [c++, headers, includes, organization, preprocessor]
---

# Headers and Include Mechanism

Headers (.h, .hpp) contain declarations that are shared across multiple source files. The `#include` directive copies header contents into source files during preprocessing.

:::info Purpose of Headers
Headers declare interfaces (what exists), while source files define implementations (how it works). This separation enables code reuse and organization.
:::

## Header vs Source File

```cpp showLineNumbers 
// math.h (Header - declarations)
#pragma once

int add(int a, int b);
int multiply(int a, int b);

class Calculator {
    int value;
public:
    Calculator(int v);
    int getValue() const;
    void setValue(int v);
};
```

```cpp showLineNumbers 
// math.cpp (Source - definitions)
#include "math.h"

int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}

Calculator::Calculator(int v) : value(v) {}

int Calculator::getValue() const {
    return value;
}

void Calculator::setValue(int v) {
    value = v;
}
```

Headers declare the API; source files implement it.

---

## Include Syntax

### Angle Brackets vs Quotes

```cpp showLineNumbers 
#include <iostream>      // System/standard headers
#include <vector>        // Search: /usr/include, etc.

#include "myheader.h"    // User headers
#include "utils/math.h"  // Search: current dir first, then system
```

**Angle brackets `< >`**: Standard library and system headers  
**Quotes `" "`**: Your project headers

**Search order for `" "`**:
1. Current directory
2. Directories specified with `-I` flag
3. System include paths

---

## What Goes in Headers?

### ✅ Should Include

```cpp showLineNumbers 
// Declarations
class Widget;
void function(int);
extern int global_var;

// Complete class definitions
class Button {
    int x, y;
public:
    Button(int x, int y);
    void click();
};

// Inline functions (definition required)
inline int square(int x) {
    return x * x;
}

// Templates (definition required)
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

// Constants
constexpr int MAX_SIZE = 1000;
const double PI = 3.14159;
```

### ❌ Should NOT Include

```cpp showLineNumbers 
// ❌ Function definitions (unless inline)
void function() {
    // implementation
}

// ❌ Variable definitions (unless const/constexpr)
int global_var = 42;

// ❌ using namespace (pollutes all files that include this)
using namespace std;

// ❌ Implementation details
static void internal_helper() {}
```

**Rule**: Headers declare interfaces, sources provide implementations.

---

## Include Organization

### Typical Project Structure

```
project/
├── include/           # Public headers
│   └── mylib/
│       ├── api.h
│       └── utils.h
├── src/               # Source files and private headers
│   ├── api.cpp
│   ├── utils.cpp
│   └── internal.h   # Private header
└── tests/
    └── test_api.cpp
```

### Include Order (Best Practice)

```cpp showLineNumbers 
// widget.cpp
#include "widget.h"      // 1. Corresponding header FIRST

#include <iostream>      // 2. Standard library
#include <vector>
#include <algorithm>

#include "utils.h"       // 3. Project headers
#include "logger.h"

#include <boost/shared_ptr.hpp>  // 4. Third-party libraries
```

**Why header first?** Ensures the header is self-contained (doesn't depend on headers included before it).

---

## Self-Contained Headers

Headers should include everything they need:

```cpp showLineNumbers 
// ❌ Bad: Depends on iostream being included first
// widget.h
class Widget {
public:
    void print() {
        std::cout << "Widget\n";  // Uses cout but doesn't include iostream!
    }
};

// ✅ Good: Self-contained
// widget.h
#include <iostream>  // Includes what it needs

class Widget {
public:
    void print() {
        std::cout << "Widget\n";
    }
};
```

**Test**: The header should compile on its own:

```bash
g++ -c widget.h  # Should work without errors
```

---

## Forward Declarations

Avoid including headers when forward declarations suffice:

```cpp showLineNumbers 
// ❌ Unnecessary include
// widget.h
#include "database.h"  // Includes entire database header

class Widget {
    Database* db;  // Only uses pointer
};

// ✅ Better: Forward declare
// widget.h
class Database;  // Forward declaration

class Widget {
    Database* db;  // Pointer/reference OK with forward declaration
};

// widget.cpp (only here include full header)
#include "database.h"
```

**When forward declaration works**:
- Pointers: `Database*`
- References: `Database&`
- Function parameters: `void process(Database&)`

**When full definition needed**:
- Member variables (by value): `Database db;`
- Inheritance: `class Widget : public Database`
- Templates: `std::vector<Database>`
- Calling methods: `db->query()`

---

## Include What You Use (IWYU)

Don't rely on transitive includes:

```cpp showLineNumbers 
// ❌ Bad: Relies on widget.h including vector
// main.cpp
#include "widget.h"  // Happens to include <vector>

int main() {
    std::vector<int> v;  // Works by accident!
}

// ✅ Good: Explicit includes
// main.cpp
#include <vector>    // Explicitly include what you use
#include "widget.h"

int main() {
    std::vector<int> v;
}
```

**Why?** If widget.h stops including vector, your code breaks.

---

## Precompiled Headers

Speed up compilation for stable headers:

```cpp showLineNumbers 
// pch.h - Rarely changing headers
#include <iostream>
#include <vector>
#include <map>
#include <algorithm>
#include <string>
```

```bash
# Precompile once
g++ -x c++-header pch.h -o pch.h.gch

# Use in compilation (much faster)
g++ -include pch.h main.cpp
```

Precompiled headers compile once and reuse the compiled result. Can speed builds by 30-50%.

---

## Header-Only Libraries

Libraries with only headers (no .cpp files):

```cpp showLineNumbers 
// math.h - Header-only library
#pragma once

namespace math {
    inline int square(int x) {
        return x * x;
    }
    
    template<typename T>
    T max(T a, T b) {
        return a > b ? a : b;
    }
}

// Usage - just include
#include "math.h"
int result = math::square(5);
```

**Advantages**:
- Easy to integrate (just copy header)
- No linking needed
- Good for templates

**Disadvantages**:
- Longer compilation (code compiled in every TU)
- Larger object files

---

## Circular Dependencies

Avoid circular includes:

```cpp showLineNumbers 
// ❌ Circular dependency
// a.h
#include "b.h"
class A {
    B b;
};

// b.h
#include "a.h"  // Circular!
class B {
    A a;
};
```

**Solution**: Forward declarations and pointers:

```cpp showLineNumbers 
// ✅ Fixed with forward declarations
// a.h
class B;  // Forward declaration
class A {
    B* b;  // Pointer
};

// b.h
class A;  // Forward declaration
class B {
    A* a;  // Pointer
};
```

---

## Include Paths

```bash
# Add include directory
g++ -I./include -I./third_party main.cpp

# Multiple paths
g++ -I/usr/local/include -I./mylib/include main.cpp

# Show include search paths
g++ -E -x c++ -v - < /dev/null
```

**Project structure**:
```bash
project/
├── include/
│   └── mylib/
│       └── api.h
└── src/
    └── main.cpp

# Compile with:
g++ -I./include src/main.cpp

# Include as:
#include "mylib/api.h"  # Not "api.h"
```

---

## Common Pitfalls

### Using namespace in Headers

```cpp showLineNumbers 
// ❌ header.h
using namespace std;  // Pollutes every file that includes this!

class Widget {
    vector<int> data;  // Now std::vector everywhere
};
```

**Solution**: Always use fully qualified names in headers:

```cpp showLineNumbers 
// ✅ header.h
class Widget {
    std::vector<int> data;
};
```

### Forgetting Include Guards

```cpp showLineNumbers 
// ❌ No include guard
// widget.h
class Widget {};

// main.cpp
#include "widget.h"
#include "widget.h"  // ❌ Error: redefinition of 'Widget'
```

**Solution**: See next section (include guards).

---

## Summary

Headers:
- **Declare interfaces**: Classes, functions, constants
- **Include what you use**: Don't rely on transitive includes
- **Self-contained**: Include dependencies
- **Forward declare** when possible to reduce dependencies
- **Never** put `using namespace` in headers

**Best practices**:
```cpp showLineNumbers 
// Good header structure
#pragma once                    // Include guard

#include <system_headers>       // Dependencies
#include "project_headers"

class MyClass {                 // Declarations
    // ...
};

inline int helper() {           // Inline definitions OK
    // ...
}

template<typename T>            // Template definitions OK
T process(T value) {
    // ...
}
```

Headers enable code reuse, separate interface from implementation, and speed compilation through separate compilation of translation units.