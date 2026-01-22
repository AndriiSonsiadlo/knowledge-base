---
id: access-control
title: Access Control
sidebar_label: Access Control
sidebar_position: 2
tags: [c++, classes, access-control, encapsulation, public, private, protected]
---

# Access Control

Access control (`public`, `private`, `protected`) enables encapsulation by controlling which code can access class members.

:::info Three Access Levels
**public** = accessible everywhere (interface)  
**private** = accessible only in class (implementation)  
**protected** = accessible in class and derived classes (inheritance)
:::

## The Three Access Levels

C++ provides three access levels that control member visibility from different contexts.

```cpp showLineNumbers 
class Widget {
public:
    int publicData;
    void publicMethod() {}
    
protected:
    int protectedData;
    void protectedMethod() {}
    
private:
    int privateData;
    void privateMethod() {}
};

Widget w;
w.publicData = 10;      // ✅ OK
// w.protectedData = 10; // ❌ Error
// w.privateData = 10;   // ❌ Error
```

**Access from outside class:**
- `public` - ✅ Accessible
- `protected` - ❌ Not accessible
- `private` - ❌ Not accessible

**Inside class (member functions):**
- All members accessible regardless of access level

## Default Access

`class` and `struct` have different default access, but are otherwise identical.

```cpp showLineNumbers 
class MyClass {
    int x;  // ❌ private by default
};

struct MyStruct {
    int x;  // ✅ public by default
};

MyClass c;
// c.x = 10;  // ❌ Error: private

MyStruct s;
s.x = 10;     // ✅ OK: public
```

:::success class vs struct
- `class` - private by default (use for objects with behavior)
- `struct` - public by default (use for plain data)
  
Same otherwise - purely stylistic choice!
:::

## Encapsulation Pattern

Use access control to protect invariants and hide implementation.

```cpp showLineNumbers
class BankAccount {
private:
    double balance;  // Protected - can't go negative
    
public:
    explicit BankAccount(double initial) : balance(initial) {
        if (initial < 0) {
            throw std::invalid_argument("Negative balance");
        }
    }
    
    bool withdraw(double amount) {
        if (amount > balance) {
            return false;  // Insufficient funds
        }
        balance -= amount;
        return true;
    }
    
    void deposit(double amount) {
        if (amount < 0) {
            throw std::invalid_argument("Negative deposit");
        }
        balance += amount;
    }
    
    double getBalance() const { return balance; }
};

// Cannot corrupt account - balance always valid
```

:::success Benefits
- Invariants protected (balance ≥ 0)
- Implementation can change without breaking code
- Clear interface (public methods)
:::

## Friend Declarations

Friend grants external functions or classes access to private members.
```cpp showLineNumbers
class Secret {
private:
    int data;
    
    friend void revealSecret(const Secret& s);
    friend class SecretKeeper;
    
public:
    Secret(int d) : data(d) {}
};

void revealSecret(const Secret& s) {
    std::cout << s.data;  // ✅ Can access private
}

class SecretKeeper {
public:
    void peek(const Secret& s) {
        std::cout << s.data;  // ✅ Can access private
    }
};
```

:::warning Use Friends Sparingly
- Breaks encapsulation
- One-way relationship (not symmetric)
- **Good uses:** Operator overloads, tightly-coupled classes
- **Bad uses:** Lazy access to internals
:::

### Friend Member Functions

You can make specific member functions of another class friends, rather than the entire class.

```cpp showLineNumbers 
class Storage;

class Accessor {
public:
    void read(const Storage& s);
    void write(Storage& s);
};

class Storage {
private:
    int data;
    
    friend void Accessor::read(const Storage&);  // Only read is friend
    // write is not a friend - cannot access data
    
public:
    Storage(int d) : data(d) {}
};

void Accessor::read(const Storage& s) {
    std::cout << s.data;  // ✅ OK
}

void Accessor::write(Storage& s) {
    // s.data = 100;  // ❌ Error: not a friend
}
```

This provides fine-grained control, granting access only where needed. It's more restrictive than making the entire class a friend.

## Protected and Inheritance

Protected members are accessible in derived classes, enabling extension while hiding from outside.

```cpp showLineNumbers
class Base {
protected:
    int protectedValue;
    
private:
    int privateValue;
    
public:
    Base(int v) : protectedValue(v), privateValue(v) {}
};

class Derived : public Base {
public:
    void modify() {
        protectedValue = 100;  // ✅ OK
        // privateValue = 100;  // ❌ Error: private
    }
};

Derived d;
// d.protectedValue = 100;  // ❌ Still protected from outside
```

**Access summary:**
| Member | Same Class | Derived Class | Outside |
|--------|-----------|---------------|---------|
| public | ✅ | ✅ | ✅ |
| protected | ✅ | ✅ | ❌ |
| private | ✅ | ❌ | ❌ |

## Access Control in Inheritance

The inheritance access specifier controls how base members appear in derived class.
```cpp showLineNumbers
class Base {
    public:    int pub;
    protected: int prot;
    private:   int priv;
};

// Public inheritance (most common)
class PublicDerived : public Base {
    // pub → public
    // prot → protected
    // priv → inaccessible
};

// Protected inheritance (rare)
class ProtectedDerived : protected Base {
    // pub → protected
    // prot → protected
    // priv → inaccessible
};

// Private inheritance (implementation detail)
class PrivateDerived : private Base {
    // pub → private
    // prot → private
    // priv → inaccessible
};
```

:::info Inheritance Types
**public** - "is-a" relationship (maintains interface)  
**protected** - rarely used  
**private** - "implemented-in-terms-of" (hides base interface)
:::

### Why Different Inheritance Access?

```cpp showLineNumbers
class Engine {
public:
    void start() {}
};

// Public: Car IS-A vehicle with engine
class Car1 : public Engine {
    // start() is public
};

// Private: Car HAS-AN engine (implementation detail)
class Car2 : private Engine {
    // start() is private (hidden from users)
public:
    void ignition() {
        start();  // ✅ Can call privately inherited member
    }
};

Car1 c1;
c1.start();  // ✅ Public inheritance

Car2 c2;
// c2.start();  // ❌ Private inheritance hides it
c2.ignition();  // ✅ Use public interface
```

Private inheritance hides the base class interface, making it an implementation detail. This is useful when you want to reuse base class implementation without exposing its interface.

## using Declarations for Access

You can use `using` to change the accessibility of inherited members.

```cpp showLineNumbers 
class Base {
protected:
    void protectedFunc() {}
};

class Derived : public Base {
public:
    using Base::protectedFunc;  // Make public in Derived
};

Derived d;
d.protectedFunc();  // ✅ Now accessible (was protected in Base)
```

This is useful when you want to expose specific base class members that would otherwise be hidden. It's commonly used to restore access to members hidden by private/protected inheritance.

## Nested Classes and Access

Nested classes have access to the enclosing class's private members.

```cpp showLineNumbers 
class Outer {
private:
    int secret;
    
    class Inner {
    public:
        void access(Outer& o) {
            o.secret = 100;  // ✅ Can access Outer's private members
        }
    };
    
public:
    Outer() : secret(0) {}
    
    void useInner() {
        Inner i;
        i.access(*this);
    }
};
```

Nested classes are useful for implementation helpers that need full access to the outer class's internals. However, the outer class cannot automatically access the nested class's private members unless specifically granted friendship.

## Static Members and Access

Static members follow the same access rules as non-static members.

```cpp showLineNumbers 
class Config {
private:
    static int privateCounter;
    
protected:
    static int protectedCounter;
    
public:
    static int publicCounter;
    
    static void increment() {
        privateCounter++;    // ✅ OK in member function
        protectedCounter++;
        publicCounter++;
    }
};

// Config::privateCounter++;     // ❌ Error: private
// Config::protectedCounter++;   // ❌ Error: protected
Config::publicCounter++;         // ✅ OK: public
```

## Summary

:::info Three access levels
- `public` - interface (accessible everywhere)
- `protected` - inheritance (accessible in derived classes)
- `private` - implementation (accessible only in class)
:::

:::info Defaults
- `class` defaults to private
- `struct` defaults to public
- Choice is stylistic (same otherwise)
:::

:::info Encapsulation
- Protects invariants through controlled access
- Hides implementation details
- Provides clear interface
:::

:::info Inheritance access
- `public` inheritance - "is-a" relationship
- `protected` inheritance - rarely used
- `private` inheritance - implementation detail
:::

:::info Friend
- Grants access to private members
- Breaks encapsulation (use sparingly)
- One-way relationship
:::

:::info Best practices
- Make data members private
- Provide public accessor methods
- Use protected for inheritance needs
- Friend for operator overloads and tight coupling only
:::
