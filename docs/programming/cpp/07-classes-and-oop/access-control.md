---
id: access-control
title: Access Control
sidebar_label: Access Control
sidebar_position: 2
tags: [c++, classes, access-control, encapsulation, public, private, protected]
---

# Access Control

Access control (public, private, protected) enables encapsulation by controlling which parts of code can access class members. This protects invariants, hides implementation details, and creates clear interfaces.

:::info Encapsulation Through Access
Access specifiers define the interface (public) and hide implementation (private). Protected enables inheritance while maintaining encapsulation.
:::

## The Three Access Levels

C++ provides three access levels that control member visibility from different contexts.

```cpp showLineNumbers 
class Widget {
public:
    int publicMember;       // Accessible everywhere
    void publicMethod() {}
    
protected:
    int protectedMember;    // Accessible in this class and derived classes
    void protectedMethod() {}
    
private:
    int privateMember;      // Only accessible in this class
    void privateMethod() {}
};

Widget w;
w.publicMember = 10;     // ✅ OK
// w.protectedMember = 10;  // ❌ Error
// w.privateMember = 10;    // ❌ Error
```

Public members form the class interface - they're accessible from any code. Private members are implementation details accessible only within the class. Protected members are accessible in the class and its derived classes, enabling inheritance while hiding from other code.

## Default Access

class and struct have different default access, but are otherwise identical.

```cpp showLineNumbers 
class MyClass {
    int x;  // ❌ Private by default
};

struct MyStruct {
    int x;  // ✅ Public by default
};

MyClass c;
// c.x = 10;  // ❌ Error: x is private

MyStruct s;
s.x = 10;     // ✅ OK: x is public
```

Use `class` when you want private-by-default (typical for objects with invariants). Use `struct` when you want public-by-default (typical for plain data). The choice is mostly stylistic but conveys intent: struct suggests data aggregation, class suggests encapsulated behavior.

## Access in Member Functions

All member functions can access all members of their own class regardless of access level.

```cpp showLineNumbers 
class Account {
private:
    double balance;
    
public:
    Account(double initial) : balance(initial) {}
    
    void deposit(double amount) {
        balance += amount;  // ✅ Can access private member
    }
    
    double getBalance() const {
        return balance;     // ✅ Can access private member
    }
};
```

Member functions are "inside" the class, so they have full access to implement functionality while maintaining the invariant (balance is never negative, for example). External code cannot modify balance directly, only through the controlled public interface.

## Friends

Friend declarations grant external functions or classes access to private and protected members.

```cpp showLineNumbers 
class Secret {
private:
    int data;
    
    // Friend function
    friend void revealSecret(const Secret& s);
    
    // Friend class
    friend class SecretKeeper;
    
public:
    Secret(int d) : data(d) {}
};

void revealSecret(const Secret& s) {
    std::cout << s.data;  // ✅ Can access private member
}

class SecretKeeper {
public:
    void peek(const Secret& s) {
        std::cout << s.data;  // ✅ Can access private member
    }
};
```

Friends are useful for helper functions that need access to internals (like operator overloads) or tightly-coupled classes. However, friends break encapsulation, so use them sparingly. They're one-way: declaring X as a friend doesn't make the current class a friend of X.

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

## Protected Access and Inheritance

Protected members are accessible in derived classes, enabling inheritance while hiding from external code.

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
    void access() {
        protectedValue = 100;  // ✅ Can access protected
        // privateValue = 100;    // ❌ Cannot access private
    }
};

Derived d;
// d.protectedValue = 100;  // ❌ Still protected from outside
```

Protected allows derived classes to access and modify base class internals while preventing external access. This is essential for inheritance where derived classes extend base class behavior.

## Access Control in Inheritance

The inheritance access specifier (public, protected, private) affects how base class members are accessible in derived class.

```cpp showLineNumbers 
class Base {
public:
    int pub;
protected:
    int prot;
private:
    int priv;
};

// Public inheritance
class PublicDerived : public Base {
    // pub is public
    // prot is protected
    // priv is inaccessible
};

// Protected inheritance
class ProtectedDerived : protected Base {
    // pub is protected
    // prot is protected
    // priv is inaccessible
};

// Private inheritance
class PrivateDerived : private Base {
    // pub is private
    // prot is private
    // priv is inaccessible
};
```

Public inheritance maintains access levels (most common, represents "is-a" relationship). Protected inheritance makes public members protected (rarely used). Private inheritance makes everything private (used for implementation inheritance, "implemented-in-terms-of").

### Why Different Inheritance Access

Different inheritance access controls what parts of the base interface remain public in derived class.

```cpp showLineNumbers 
class Engine {
public:
    void start() { /* ... */ }
};

// Public inheritance: Car IS-A vehicle with an engine
class Car : public Engine {
    // start() is public - cars can be started
};

// Private inheritance: Car HAS-AN engine (implementation detail)
class Car : private Engine {
    // start() is private - external code can't call it
public:
    void ignition() {
        start();  // ✅ Can call privately inherited member
    }
};

Car c;
// c.start();  // ❌ Error: start() is private
c.ignition();  // ✅ OK: public interface
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
    using Base::protectedFunc;  // Make it public in Derived
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

Static members don't require an object instance, but access control still applies based on where the access occurs.

## Practical Encapsulation

Access control enables hiding implementation and protecting invariants.

```cpp showLineNumbers 
class BankAccount {
private:
    double balance;  // Protected - cannot go negative
    
public:
    explicit BankAccount(double initial) : balance(initial) {
        if (initial < 0) throw std::invalid_argument("Negative balance");
    }
    
    bool withdraw(double amount) {
        if (amount > balance) {
            return false;  // Insufficient funds
        }
        balance -= amount;  // Maintain invariant
        return true;
    }
    
    void deposit(double amount) {
        if (amount < 0) throw std::invalid_argument("Negative deposit");
        balance += amount;
    }
    
    double getBalance() const { return balance; }
};

// Cannot set balance directly - must use deposit/withdraw
// This prevents negative balance (invariant)
```

By making balance private, we ensure all modifications go through methods that maintain the invariant. External code cannot corrupt the account by setting balance directly.

:::warning Access Control Limitations

**Not Security**: Access control is enforced at compile-time, not runtime.

**Cast Away**: Determined code can bypass with pointer casts (undefined behavior).

**Different Units**: Separate compilation units with same class definition can access privates.

**Template Instantiation**: Template code might access privates through instantiation.

**Not Encryption**: Private doesn't mean the data is hidden from debuggers or memory inspection.
:::

## Summary

Access control enables encapsulation through three levels: public (accessible everywhere), private (accessible only in class), protected (accessible in class and derived classes). class defaults to private, struct defaults to public. Member functions have full access to all members of their class regardless of access level. Friend declarations grant external functions or classes access to private members - use sparingly. Protected enables inheritance by allowing derived classes to access base class internals. Inheritance access (public/protected/private) controls how base members appear in derived class - public maintains levels, protected makes public members protected, private makes everything private. Public inheritance represents "is-a" relationships, private inheritance is implementation detail. using declarations can restore access to inherited members. Nested classes have access to outer class private members. Access control protects invariants by preventing external code from corrupting state. Static members follow the same access rules as instance members. Access control is compile-time enforcement, not runtime security. Good encapsulation hides implementation details and exposes only necessary interface, making code more maintainable and preventing misuse.

:::success Access Control Principles

**Public = Interface**: What the class promises to its users.

**Private = Implementation**: Hidden details that can change without breaking code.

**Protected = Inheritance**: For derived classes while hiding from external code.

**Encapsulation**: Protects invariants by controlling how state is modified.

**Friend = Exception**: Grants access when needed but use sparingly.

**Inheritance Access**: Controls what parts of base class become part of derived interface.

**Not Security**: Compile-time check, not runtime protection.

**class vs struct**: class private-default, struct public-default.
:::