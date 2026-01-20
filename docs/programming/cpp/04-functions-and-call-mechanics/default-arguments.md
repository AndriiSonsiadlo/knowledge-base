---
id: default-arguments
title: Default Function Arguments
sidebar_label: Default Arguments
sidebar_position: 2
tags: [cpp, functions, default-arguments, parameters]
---

# Default Function Arguments

**Default arguments** allow function parameters to have default values when not explicitly provided by the caller.

## Basic Syntax
```cpp
// Declaration with defaults
void print(std::string msg, int count = 1, bool newline = true);

// Calls
print("Hello");              // count=1, newline=true
print("Hello", 3);           // count=3, newline=true
print("Hello", 3, false);    // count=3, newline=false
```

:::info
Default arguments must appear **rightmost** in the parameter list. Once a parameter has a default, all following parameters must also have defaults.
:::

## Rules and Restrictions
```cpp
// CORRECT: defaults are rightmost
void f1(int a, int b = 2, int c = 3);

// WRONG: non-default after default
// void f2(int a = 1, int b, int c = 3);  // Error!

// CORRECT: multiple defaults
void f3(int a, int b = 2, int c = 3, int d = 4);
```

### Declaration vs Definition
```cpp
// In header (.h)
void configure(int port, std::string host = "localhost", int timeout = 30);

// In source (.cpp) - NO defaults here!
void configure(int port, std::string host, int timeout) {
    // Implementation
}

// WRONG: defaults in both places
// void configure(int port, std::string host = "localhost", int timeout = 30) {
//     // Error!
// }
```

:::warning
Default arguments should only appear in the **declaration**, not the definition (if separated).
:::

## Common Patterns

### Pattern 1: Optional Configuration
```cpp
#include <string>

class Logger {
public:
    void log(const std::string& msg, 
             const std::string& level = "INFO",
             bool timestamp = true);
};

// Usage
logger.log("Server started");                    // INFO, with timestamp
logger.log("Error occurred", "ERROR");          // ERROR, with timestamp
logger.log("Debug info", "DEBUG", false);       // DEBUG, no timestamp
```

### Pattern 2: Builder-Style APIs
```cpp
class HttpRequest {
public:
    HttpRequest& setMethod(const std::string& method = "GET");
    HttpRequest& setTimeout(int seconds = 30);
    HttpRequest& setRetries(int count = 3);
};

// Usage
request.setMethod()           // Uses "GET"
       .setTimeout()          // Uses 30
       .setRetries(5);        // Override to 5
```

### Pattern 3: Backward Compatibility
```cpp
// Old API
void process(int value);

// New API - adds optional parameter
void process(int value, bool verbose = false);

// Old code still works!
process(42);        // verbose=false (backward compatible)
```

## Non-Constant Defaults

Default arguments are evaluated at **call time**, not declaration time:
```cpp
int getDefaultValue() {
    return 42;
}

void func(int x = getDefaultValue()) {
    std::cout << x << '\n';
}

// Each call evaluates getDefaultValue()
func();  // Calls getDefaultValue()
func();  // Calls getDefaultValue() again
```

### Member Variables as Defaults
```cpp
class Widget {
    int defaultSize_ = 100;
    
public:
    // WRONG: can't use member as default
    // void resize(int size = defaultSize_);  // Error!
    
    // CORRECT: use overload or other approach
    void resize(int size);
    void resize() { resize(defaultSize_); }
};
```

## Default Arguments vs Overloading
```cpp
// Approach 1: Default arguments
void display(std::string text, int size = 12, bool bold = false);

// Approach 2: Overloading
void display(std::string text);
void display(std::string text, int size);
void display(std::string text, int size, bool bold);
```

| Default Arguments | Overloading |
|-------------------|-------------|
| Single function | Multiple functions |
| Can't change logic per parameter | Different logic per version |
| Evaluated at call site | Can have different implementations |
| Less code | More flexibility |

## Practical Examples

### Example 1: Database Connection
```cpp
#include <string>

class Database {
public:
    bool connect(
        const std::string& host = "localhost",
        int port = 5432,
        const std::string& user = "admin",
        const std::string& password = "",
        int timeout = 30
    );
};

// Usage examples
db.connect();                                      // All defaults
db.connect("192.168.1.100");                      // Custom host
db.connect("192.168.1.100", 3306);                // Custom host and port
db.connect("192.168.1.100", 3306, "root", "pwd"); // Custom connection
```

### Example 2: File Operations
```cpp
#include <string>
#include <fstream>

class FileWriter {
public:
    void write(
        const std::string& filename,
        const std::string& content,
        bool append = false,
        bool createIfMissing = true
    ) {
        auto mode = std::ios::out;
        if (append) mode |= std::ios::app;
        if (!createIfMissing) mode |= std::ios::in;
        
        std::ofstream file(filename, mode);
        file << content;
    }
};
```

## Best Practices

:::success
**DO:**
- Use defaults for frequently-used values
- Place defaults in header files (declarations)
- Keep defaults simple (literals or simple expressions)
- Use defaults for optional configuration
  :::

:::danger
**DON'T:**
- Use defaults with complex expressions (performance)
- Mix defaults and overloading carelessly
- Use member variables as default values
- Put defaults in both declaration and definition
  :::

## Related Topics

- **[Function Declarations](function-declarations.md)** - Function signatures
- **[Overloading](overloading.md)** - Alternative approach
- **[Lambdas](lambdas.md)** - Closures with captures