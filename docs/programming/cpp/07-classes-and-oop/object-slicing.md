---
id: object-slicing
title: Object Slicing
sidebar_label: Object Slicing
sidebar_position: 12
tags: [c++, object-slicing, polymorphism, pitfalls]
---

# Object Slicing

Object slicing occurs when you copy a derived class object to a base class object. The derived parts are "sliced off" and lost.

:::info The Slicing Problem
Copying derived object to base object only copies the base part. Derived data and virtual function overrides are lost!
:::

## Basic Slicing Example

```cpp showLineNumbers 
class Animal {
public:
    int legs = 4;
    virtual void speak() { std::cout << "Animal sound\n"; }
};

class Dog : public Animal {
public:
    std::string breed = "Golden Retriever";
    void speak() override { std::cout << "Woof!\n"; }
};

Dog dog;
dog.breed = "Labrador";

Animal animal = dog;  // ⚠️ SLICING!
// Only Animal part is copied
// breed is lost!
// speak() calls Animal's version!

animal.speak();  // "Animal sound" - not "Woof!"
// animal.breed;  // ❌ Error: Animal has no breed member
```

When you assign a Dog to an Animal, only the Animal parts are copied. The Dog-specific parts (breed member, overridden speak()) are gone.

## Why Slicing Happens

```cpp showLineNumbers 
Animal animal = dog;
// This is NOT polymorphic assignment!
// It's copy construction: Animal(const Animal& other)
// The copy constructor only knows how to copy Animal parts

sizeof(Animal);  // 16 bytes
sizeof(Dog);     // 48 bytes (Animal + Dog parts)
// Can't fit a Dog into an Animal-sized space!
```

Base class copy constructor/assignment only handles base class members. It doesn't know about derived class parts.

## Slicing with Functions

Passing by value causes slicing:

```cpp showLineNumbers 
void processAnimal(Animal a) {  // ⚠️ Pass by value
    a.speak();  // Always calls Animal::speak!
}

Dog dog;
processAnimal(dog);  // "Animal sound" - sliced!
// Dog is copied to Animal parameter, losing derived parts
```

## Preventing Slicing: Use Pointers

```cpp showLineNumbers 
void processAnimal(Animal* a) {  // ✅ Pointer
    a->speak();  // Calls correct overridden version!
}

Dog dog;
processAnimal(&dog);  // "Woof!" - no slicing!
```

Pointers and references preserve polymorphism. No copying, no slicing.

## Preventing Slicing: Use References

```cpp showLineNumbers 
void processAnimal(const Animal& a) {  // ✅ Reference
    a.speak();  // Calls correct overridden version!
}

Dog dog;
processAnimal(dog);  // "Woof!" - no slicing!
```

References are usually the best choice for polymorphic parameters.

## Slicing in Containers

Storing objects (not pointers) in containers causes slicing:

```cpp showLineNumbers 
std::vector<Animal> animals;  // ⚠️ Stores Animal objects

Dog dog;
Cat cat;

animals.push_back(dog);  // Sliced to Animal!
animals.push_back(cat);  // Sliced to Animal!

for (auto& a : animals) {
    a.speak();  // All say "Animal sound"
}
```

**Solution**: Store pointers (preferably smart pointers):

```cpp showLineNumbers 
std::vector<std::unique_ptr<Animal>> animals;  // ✅ Pointers

animals.push_back(std::make_unique<Dog>());
animals.push_back(std::make_unique<Cat>());

for (auto& a : animals) {
    a->speak();  // Calls correct overridden versions!
}
```

## Assignment Slicing

```cpp showLineNumbers 
Dog dog;
Cat cat;
Animal& ref = dog;  // ✅ Reference, no slicing

ref = cat;  // ⚠️ Slicing!
// Calls Animal::operator=(const Animal&)
// Only copies Animal parts of cat into dog's Animal part
// dog is still a Dog, but with corrupted Animal data!

dog.speak();  // "Woof!" - still a Dog
// But animal data is messed up from cat
```

Assignment through references still slices because it calls the base class assignment operator.

## Copy Construction vs Assignment

```cpp showLineNumbers 
Dog dog;

Animal a1 = dog;    // Copy construction: slicing
Animal a2(dog);     // Copy construction: slicing
Animal a3{dog};     // Copy construction: slicing

Animal a4;
a4 = dog;           // Copy assignment: slicing
```

All of these slice! They all invoke Animal's copy operations which only copy Animal parts.

## Detecting Slicing

Some compilers warn about slicing:

```bash
# GCC/Clang warnings
g++ -Wextra -Wall file.cpp
# warning: slicing object of type 'Dog' to 'Animal'

# Enable more warnings
g++ -Weffc++ file.cpp
```

## Real-World Example

```cpp showLineNumbers 
// ❌ Bad: slicing
std::vector<Animal> zoo;
zoo.push_back(Dog());   // Sliced!
zoo.push_back(Cat());   // Sliced!
zoo.push_back(Bird());  // Sliced!

for (auto& animal : zoo) {
    animal.speak();  // All say "Animal sound"
}

// ✅ Good: polymorphic collection
std::vector<std::unique_ptr<Animal>> zoo;
zoo.push_back(std::make_unique<Dog>());
zoo.push_back(std::make_unique<Cat>());
zoo.push_back(std::make_unique<Bird>());

for (auto& animal : zoo) {
    animal->speak();  // Each speaks correctly!
}
```

:::success Avoiding Slicing

**Problem** = copying derived to base loses derived parts  
**Pass by value** = causes slicing  
**Pass by pointer/reference** = preserves polymorphism  
**Containers of objects** = slice  
**Containers of pointers** = preserve polymorphism  
**Smart pointers** = best for polymorphic collections  
**Always use pointers/references** for polymorphic behavior
:::