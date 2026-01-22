---
id: dynamic-vs-static-polymorphism
title: Dynamic vs Static Polymorphism
sidebar_label: Dynamic vs Static Polymorphism
sidebar_position: 9
tags: [c++, polymorphism, templates, virtual-functions]
---

# Dynamic vs Static Polymorphism

C++ supports two forms of polymorphism: dynamic (runtime, using virtual functions) and static (compile-time, using templates). Each has different trade-offs.

:::info Two Types of Polymorphism
**Dynamic** = runtime flexibility with virtual functions (slight overhead)  
**Static** = compile-time with templates (zero overhead but more code)
:::

## Dynamic Polymorphism

Uses inheritance and virtual functions. Type decided at runtime:

```cpp showLineNumbers 
class Shape {
public:
    virtual void draw() = 0;
    virtual ~Shape() = default;
};

class Circle : public Shape {
public:
    void draw() override {
        std::cout << "Drawing circle\n";
    }
};

class Rectangle : public Shape {
public:
    void draw() override {
        std::cout << "Drawing rectangle\n";
    }
};

void render(Shape* shape) {
    shape->draw();  // Decided at runtime
}

Shape* s = getShape();  // Could be Circle or Rectangle
render(s);              // Don't know which until runtime
```

**Characteristics:**
- Runtime type selection
- vtable lookup overhead (~2-3ns per call)
- Single compiled version of code
- Can store different types in same container
- Type determined while program runs

## Static Polymorphism

Uses templates. Type decided at compile-time:

```cpp showLineNumbers 
class Circle {
public:
    void draw() {
        std::cout << "Drawing circle\n";
    }
};

class Rectangle {
public:
    void draw() {
        std::cout << "Drawing rectangle\n";
    }
};

template<typename Shape>
void render(Shape& shape) {
    shape.draw();  // Decided at compile-time
}

Circle c;
render(c);      // Compiles to: c.draw() directly

Rectangle r;
render(r);      // Compiles to: r.draw() directly
```

**Characteristics:**
- Compile-time type selection
- No runtime overhead (direct calls, can inline)
- Separate compiled version for each type
- Can't store different types in same container easily
- Type must be known at compile-time

## Performance Comparison

```cpp showLineNumbers 
// Dynamic polymorphism
std::vector<std::unique_ptr<Shape>> shapes;
shapes.push_back(std::make_unique<Circle>());
shapes.push_back(std::make_unique<Rectangle>());

for (auto& shape : shapes) {
    shape->draw();  // Virtual call: ~3ns per call
}

// Static polymorphism
std::vector<Circle> circles;
std::vector<Rectangle> rectangles;

for (auto& circle : circles) {
    circle.draw();  // Direct call: ~1ns, can inline
}
for (auto& rect : rectangles) {
    rect.draw();   // Direct call: ~1ns, can inline
}
```

Static polymorphism is 2-3x faster per call and allows inlining.

## Code Size

```cpp showLineNumbers 
// Dynamic: One compiled function
void processShape(Shape* s) {
    s->draw();
}
// Compiled once, works with all Shape subclasses

// Static: Separate function per type
template<typename T>
void processShape(T& s) {
    s.draw();
}
// Compiled separately for Circle, Rectangle, etc.
// Larger total code size
```

Dynamic polymorphism generates less code. Static polymorphism duplicates code for each type used.

## Flexibility

```cpp showLineNumbers 
// Dynamic: Can choose type at runtime
Shape* getShape(int choice) {
    if (choice == 1)
        return new Circle();
    else
        return new Rectangle();
}

int userChoice = getUserInput();
Shape* s = getShape(userChoice);  // Runtime decision

// Static: Type must be known at compile-time
template<typename T>
void process() {
    T object;
    object.draw();
}

process<Circle>();     // Must specify type here
// Can't decide based on runtime input
```

Dynamic polymorphism can make runtime decisions. Static polymorphism requires compile-time knowledge.

## Mixing Both Approaches

You can combine dynamic and static polymorphism:

```cpp showLineNumbers 
template<typename Derived>
class ShapeBase {
public:
    void draw() {
        // CRTP: Compile-time polymorphism
        static_cast<Derived*>(this)->drawImpl();
    }
};

class Circle : public ShapeBase<Circle> {
public:
    void drawImpl() {
        std::cout << "Drawing circle\n";
    }
};

// Or use std::variant for runtime type with static dispatch
using Shape = std::variant<Circle, Rectangle>;

void draw(Shape& s) {
    std::visit([](auto& shape) {
        shape.draw();  // Static dispatch inside variant
    }, s);
}
```

## When to Use Each

**Use Dynamic (Virtual Functions) when:**
- Need runtime type selection
- Storing different types in same container
- Plugin architectures
- Working with dynamically loaded libraries
- Type not known until runtime
- Code size matters more than speed

**Use Static (Templates) when:**
- Type known at compile-time
- Performance critical (tight loops)
- Need inlining
- Working with algorithms
- Generic programming
- Don't need type erasure

## Real-World Example

```cpp showLineNumbers 
// Dynamic: GUI framework
class Widget {
public:
    virtual void render() = 0;
    virtual void handleClick() = 0;
};
// Different widgets loaded at runtime from plugins

// Static: Generic algorithms
template<typename Iterator>
void sort(Iterator begin, Iterator end) {
    // Works with any iterator type at compile-time
    // Fully optimized for each specific iterator
}
```

GUI frameworks typically use dynamic polymorphism (runtime type selection). Generic algorithms use static polymorphism (compile-time optimization).

:::success Choosing Polymorphism Type

**Dynamic Polymorphism:**
- Runtime flexibility ✓
- Single compiled version ✓
- vtable overhead ✗
- Can't inline ✗

**Static Polymorphism:**
- Compile-time only ✗
- Code duplication ✗
- Zero overhead ✓
- Can inline ✓

**Choose dynamic** for flexibility  
**Choose static** for performance  
**Can mix both** for best of both worlds
:::