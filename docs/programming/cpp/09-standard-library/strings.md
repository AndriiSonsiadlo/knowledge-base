---
id: strings
title: String Handling
sidebar_label: Strings
sidebar_position: 5
tags: [c++, strings, string-view, text]
---

# Strings and String Operations

C++ provides `std::string` for dynamic text storage and manipulation, along with `std::string_view` (C++17) for non-owning string references. Rich API for searching, modifying, and converting text data.

:::info String Types
**std::string** = owned, mutable text (dynamic allocation)  
**std::string_view** = non-owning view (no allocation, no copies)  
**C strings** = const char* (legacy, manual memory)
:::

## Creating Strings

Different ways to construct and initialize strings.

```cpp showLineNumbers 
#include 

// Default constructor - empty string
std::string s1;

// From C string literal
std::string s2 = "Hello";
std::string s3("World");

// From another string
std::string s4 = s2;
std::string s5(s2);

// Substring
std::string s6(s2, 1, 3);  // "ell" (from position 1, length 3)

// Repeated character
std::string s7(5, 'x');  // "xxxxx"

// From iterators
std::string s8(s2.begin(), s2.begin() + 3);  // "Hel"

// C++11 raw string literals (no escape sequences)
std::string s9 = R"(C:\path\to\file.txt)";  // Backslashes literal

// C++14 string literals
using namespace std::string_literals;
auto s10 = "Hello"s;  // std::string, not const char*
```

## Accessing Characters

Multiple ways to access individual characters with different safety guarantees.

```cpp showLineNumbers 
std::string str = "Hello";

// Subscript operator (no bounds check)
char c1 = str[0];      // 'H'
str[0] = 'h';          // "hello"

// at() method (throws if out of bounds)
char c2 = str.at(1);   // 'e'
// str.at(100);        // throws std::out_of_range

// Front and back
char first = str.front();  // 'h'
char last = str.back();    // 'o'

// Data pointer (C++11)
const char* cstr = str.data();  // null-terminated C string
char* ptr = str.data();         // can modify (C++17)

// c_str() - null-terminated C string
const char* cstr2 = str.c_str();
```

**Best practice:** Use `at()` when safety matters, `[]` for performance-critical code where bounds are guaranteed.

## String Properties

Query string state and characteristics.

```cpp showLineNumbers 
std::string str = "Hello, World!";

// Size and capacity
size_t len = str.size();      // 13
size_t len2 = str.length();   // 13 (same as size())
bool empty = str.empty();     // false
size_t cap = str.capacity();  // >= 13 (implementation-defined)

// Maximum size
size_t max = str.max_size();  // Very large number

// Reserve capacity (optimization)
str.reserve(100);  // Pre-allocate space
// Doesn't change size, only capacity

// Shrink to fit
str.shrink_to_fit();  // Reduce capacity to size (request, not guarantee)

// Clear content
str.clear();  // Empty string, capacity may remain
```

## Modifying Strings

Rich set of operations for adding, removing, and changing content.

### Appending

```cpp showLineNumbers 
std::string str = "Hello";

// append method
str.append(" World");    // "Hello World"
str.append(3, '!');      // "Hello World!!!"

// += operator
str += " ";
str += "C++";            // "Hello World!!! C++"

// push_back - single character
str.push_back('!');      // "Hello World!!! C++!"

// Efficient concatenation (C++11)
std::string result = str + " " + "Programming";

// Chaining
std::string msg;
msg.append("Error: ").append("File not found");
```

### Inserting

```cpp showLineNumbers 
std::string str = "Hello World";

// Insert at position
str.insert(5, ",");      // "Hello, World"
str.insert(6, " beautiful");  // "Hello, beautiful World"

// Insert character repeated
str.insert(0, 3, '*');   // "***Hello, beautiful World"

// Insert from another string
std::string prefix = "Greetings: ";
str.insert(0, prefix);
```

### Erasing

```cpp showLineNumbers 
std::string str = "Hello, World!";

// Erase range
str.erase(5, 2);         // "HelloWorld!" (erase ", ")

// Erase from position to end
str.erase(5);            // "Hello"

// Erase single character
str.erase(str.begin());  // "ello"

// pop_back - remove last character
str.pop_back();          // "ell"

// Clear all
str.clear();             // ""
```

### Replacing

```cpp showLineNumbers 
std::string str = "Hello, World!";

// Replace range
str.replace(7, 5, "C++");     // "Hello, C++!"

// Replace with repeated character
str.replace(0, 5, 3, 'H');    // "HHH, C++!"

// Replace using iterators
str.replace(str.begin(), str.begin() + 3, "Goodbye");
```

### Resizing

```cpp showLineNumbers 
std::string str = "Hello";

// Increase size (fill with null bytes or specified char)
str.resize(10);          // "Hello\0\0\0\0\0"
str.resize(15, 'x');     // "Hello\0\0\0\0\0xxxxx"

// Decrease size (truncate)
str.resize(3);           // "Hel"
```

## Searching

Find substrings, characters, and patterns.

### Basic Search

```cpp showLineNumbers 
std::string str = "Hello, World! Hello, C++!";

// Find substring (first occurrence)
size_t pos = str.find("Hello");   // 0
size_t pos2 = str.find("World");  // 7
size_t pos3 = str.find("xyz");    // std::string::npos (not found)

// Check if found
if (pos3 == std::string::npos) {
    std::cout << "Not found\n";
}

// Find from position
size_t pos4 = str.find("Hello", 1);  // 14 (second occurrence)

// Find character
size_t pos5 = str.find('W');  // 7

// Find last occurrence (reverse search)
size_t last = str.rfind("Hello");  // 14
```

### Character Set Search

```cpp showLineNumbers 
std::string str = "Hello, World!";

// Find first of any character in set
size_t pos = str.find_first_of("aeiou");  // 1 ('e')

// Find first not of set
size_t pos2 = str.find_first_not_of("Helo");  // 5 (',')

// Find last of set
size_t pos3 = str.find_last_of("aeiou");  // 8 ('o' in World)

// Find last not of set
size_t pos4 = str.find_last_not_of("!");  // 11 ('d')

// Use case: trim whitespace
std::string trimmed = str;
size_t start = trimmed.find_first_not_of(" \t\n");
size_t end = trimmed.find_last_not_of(" \t\n");
if (start != std::string::npos) {
    trimmed = trimmed.substr(start, end - start + 1);
}
```

## Substrings and Comparison

Extract parts and compare strings.

### Substring Extraction

```cpp showLineNumbers 
std::string str = "Hello, World!";

// Get substring
std::string sub1 = str.substr(0, 5);   // "Hello"
std::string sub2 = str.substr(7);      // "World!" (to end)
std::string sub3 = str.substr(7, 5);   // "World"

// Copy to buffer
char buffer[100];
str.copy(buffer, 5, 0);  // Copy 5 chars from position 0
buffer[5] = '\0';        // Null-terminate
```

### String Comparison

```cpp showLineNumbers 
std::string s1 = "apple";
std::string s2 = "banana";
std::string s3 = "apple";

// Comparison operators
bool equal = (s1 == s3);      // true
bool not_equal = (s1 != s2);  // true
bool less = (s1 < s2);        // true (lexicographical)
bool greater = (s2 > s1);     // true

// compare method (returns <0, 0, or >0)
int cmp = s1.compare(s2);
if (cmp < 0) {
    std::cout << s1 << " comes before " << s2;
}

// Compare substring
int cmp2 = s1.compare(0, 3, s3, 0, 3);  // Compare first 3 chars

// Case-insensitive comparison (manual)
auto toLower = [](std::string str) {
    std::transform(str.begin(), str.end(), str.begin(), ::tolower);
    return str;
};
bool caseInsensitiveEqual = (toLower(s1) == toLower(s3));
```

### String Prefix/Suffix (C++20)

```cpp showLineNumbers 
std::string str = "Hello, World!";

// Check prefix
bool hasHello = str.starts_with("Hello");   // true
bool hasHi = str.starts_with("Hi");         // false

// Check suffix
bool endsExclaim = str.ends_with("!");      // true
bool endsQuestion = str.ends_with("?");     // false

// Also works with single char
bool startsH = str.starts_with('H');        // true
```

## String Conversion

Convert between strings and numbers.

### Numbers to Strings

```cpp showLineNumbers 
// std::to_string (C++11)
int num = 42;
double pi = 3.14159;

std::string s1 = std::to_string(num);     // "42"
std::string s2 = std::to_string(pi);      // "3.141590"

// More control with stringstream
#include 
#include 

std::ostringstream oss;
oss << std::fixed << std::setprecision(2) << pi;
std::string s3 = oss.str();  // "3.14"
```

### Strings to Numbers

```cpp showLineNumbers 
std::string s = "12345";

// std::stoi, stol, stoll (string to integer)
int i = std::stoi(s);         // 12345
long l = std::stol(s);
long long ll = std::stoll(s);

// std::stof, stod, stold (string to float)
std::string s2 = "3.14159";
float f = std::stof(s2);
double d = std::stod(s2);
long double ld = std::stold(s2);

// Error handling
std::string invalid = "abc123";
try {
    int val = std::stoi(invalid);  // throws std::invalid_argument
} catch (const std::invalid_argument& e) {
    std::cerr << "Invalid input\n";
}

// Advanced: position and base
std::string hex = "0x1A";
size_t pos;
int value = std::stoi(hex, &pos, 16);  // 26 (parse as hex)
// pos now contains index of first non-parsed character
```

## std::string_view (C++17)

Non-owning string reference - no allocation, efficient passing.

```cpp showLineNumbers 
#include 

// Create from various sources
std::string_view sv1 = "Hello";           // From literal
std::string str = "World";
std::string_view sv2 = str;               // From string
std::string_view sv3(str.data(), 3);      // "Wor"

// Efficient function parameter
void process(std::string_view sv) {  // No copy!
    std::cout << sv;
}

process("literal");      // No string object created
process(str);            // No copy
process(sv1);            // Already a view

// Substring (no allocation)
std::string_view sub = sv1.substr(1, 3);  // "ell"

// Common operations
sv1.size();
sv1.empty();
sv1.front();
sv1.back();
sv1[0];
sv1.data();  // Raw pointer

// Comparison
sv1 == sv2;
sv1 < sv2;

// Search (same as string)
sv1.find("lo");
sv1.starts_with('H');
sv1.ends_with('o');

// Remove prefix/suffix
std::string_view sv4 = "Hello, World!";
sv4.remove_prefix(7);   // "World!"
sv4.remove_suffix(1);   // "World"
```

**Use case:** Function parameters when you don't need to own or modify the string.

**Warning:** string_view doesn't own data - ensure underlying data outlives the view!

```cpp showLineNumbers 
std::string_view dangling() {
    std::string temp = "danger";
    return temp;  // ❌ Returns view to destroyed string!
}
```

## String Literals

Different string literal types for different character encodings.

```cpp showLineNumbers 
// Narrow strings (char)
const char* s1 = "Hello";
std::string s2 = "Hello";

// Wide strings (wchar_t)
const wchar_t* ws = L"Hello";
std::wstring wstr = L"Hello";

// UTF-8 (char, C++11)
const char* u8s = u8"Hello 世界";
std::string u8str = u8"Hello 世界";

// UTF-16 (char16_t, C++11)
const char16_t* u16s = u"Hello";
std::u16string u16str = u"Hello";

// UTF-32 (char32_t, C++11)
const char32_t* u32s = U"Hello";
std::u32string u32str = U"Hello";

// Raw strings (no escape processing)
std::string raw = R"(Line 1
Line 2
C:\path\to\file)";

// Raw string with delimiter (when string contains )")
std::string raw2 = R"delim(String with )" inside)delim";
```

## Common String Operations

Practical examples for common tasks.

### Splitting Strings

```cpp showLineNumbers 
#include 
#include 

// Split by delimiter
std::vector split(const std::string& str, char delim) {
    std::vector tokens;
    std::stringstream ss(str);
    std::string token;
    
    while (std::getline(ss, token, delim)) {
        tokens.push_back(token);
    }
    
    return tokens;
}

std::string csv = "apple,banana,cherry";
auto fruits = split(csv, ',');  // {"apple", "banana", "cherry"}
```

### Trimming Whitespace

```cpp showLineNumbers 
std::string trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    
    size_t end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

std::string s = "   Hello   ";
std::string trimmed = trim(s);  // "Hello"
```

### Case Conversion

```cpp showLineNumbers 
#include 
#include 

std::string toUpper(std::string str) {
    std::transform(str.begin(), str.end(), str.begin(), ::toupper);
    return str;
}

std::string toLower(std::string str) {
    std::transform(str.begin(), str.end(), str.begin(), ::tolower);
    return str;
}

std::string s = "Hello World";
std::string upper = toUpper(s);  // "HELLO WORLD"
std::string lower = toLower(s);  // "hello world"
```

### Replace All Occurrences

```cpp showLineNumbers 
void replaceAll(std::string& str, const std::string& from, const std::string& to) {
    size_t pos = 0;
    while ((pos = str.find(from, pos)) != std::string::npos) {
        str.replace(pos, from.length(), to);
        pos += to.length();
    }
}

std::string text = "Hello World, Hello Everyone";
replaceAll(text, "Hello", "Hi");  // "Hi World, Hi Everyone"
```

### Joining Strings

```cpp showLineNumbers 
template
std::string join(const Container& strings, const std::string& delim) {
    std::string result;
    bool first = true;
    
    for (const auto& str : strings) {
        if (!first) result += delim;
        result += str;
        first = false;
    }
    
    return result;
}

std::vector words = {"Hello", "World", "!"};
std::string sentence = join(words, " ");  // "Hello World !"
```

## Performance Considerations

Understanding string performance characteristics.

```cpp showLineNumbers 
// ❌ Inefficient: repeated concatenation
std::string result;
for (int i = 0; i < 1000; ++i) {
    result += std::to_string(i) + " ";  // Multiple allocations
}

// ✅ Better: reserve capacity
std::string result;
result.reserve(5000);  // Pre-allocate
for (int i = 0; i < 1000; ++i) {
    result += std::to_string(i) + " ";
}

// ✅ Best: use stringstream for many concatenations
std::ostringstream oss;
for (int i = 0; i < 1000; ++i) {
    oss << i << " ";
}
std::string result = oss.str();

// String copying is expensive for large strings
void process(const std::string& str) {  // ✅ Pass by const reference
    // ...
}

void process2(std::string_view sv) {    // ✅ Even better (C++17)
    // ...
}
```

## Small String Optimization (SSO)

Most implementations optimize for short strings.

```cpp showLineNumbers 
// Short strings stored inside string object (no heap allocation)
std::string short_str = "Hi";  // Likely no allocation

// Long strings allocated on heap
std::string long_str(1000, 'x');  // Definitely allocated

// Typical SSO capacity: 15-23 bytes (implementation-defined)
// Check with: sizeof(std::string)
```

**Benefit:** Short strings are fast with no dynamic allocation overhead.

:::success String Essentials

**std::string** = owned, mutable, dynamic  
**std::string_view** = non-owning, efficient passing  
**operator+** = concatenation  
**find/rfind** = search forward/backward  
**substr** = extract substring  
**compare/operators** = lexicographical comparison  
**to_string/stoi** = conversions  
**reserve** = pre-allocate for performance  
**C++20** = starts_with/ends_with  
**SSO** = small strings optimized (no allocation)
:::

