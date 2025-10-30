# SMART POINTERS
We'll set the ball rolling with a discussion on "smart" pointers. We're assuming here that you know what constuctors (hereafter shortened to ctors) and destructors (shortened to dtors) are and have a general sense of when they get called.

## Before Smart Pointers: Life Was Manual

In old-school C/C++, we use pointers like this:

```
int* p = new int(42);
// ...
delete p;
```
If you forgot the delete, or called it twice, or returned early — 💥 memory leak or crash. Memory ownership was purely manual. Part of the reason why OS developers love this and also why it is easy to break things in C.


## What Makes a Pointer “Smart”

A smart pointer is a small C++ class that acts like a pointer but automatically handles cleanup.
When it goes out of scope, its destructor runs and releases the memory.
In essence:
```
Smart Pointer = Pointer + Ownership Semantics
```
They rely on RAII (Resource Acquisition Is Initialization) — allocate in the constructor, release in the destructor.

## The Big Three Smart Pointers
### Unique pointer
- std::unique_ptr<"T"> (where T is a stand-in for the type of object being passed to it)
  - Sole ownership
  - Fast, simple — one owner only
### Shared pointer
- std::shared_ptr<T> (where T is a stand-in for the type of object being passed to it)
  - Shared ownership
  - Multiple owners, ref-counted
### Weak pointer
- std::weak_ptr<T> (where T is a stand-in for the type of object being passed to it)
  - Non-owning observer
  - Break cyclic references


## std::unique_ptr — The Lightweight Owner

A unique_ptr owns exactly one object and deletes it automatically.
```
auto p = std::make_unique<int>(42);
```
It cannot be copied (only moved). Perfect for clear, single-owner semantics. Arrays work perfectly with it like so:

```
auto arr = std::make_unique<int[]>(5);
```
The reason something like this does NOT fail is because it just performs a simple runtime new int[5] under the hood. The standard defines an overload that understands that the number 5 in the expression above is the length of the array. No control blocks, no reference counting — so no complexity.


## std::shared_ptr — Shared Ownership

Sometimes multiple pieces of code must share one object. Example: a shared cache entry or configuration data. Or a project class that is shared across multiple employee objects all working on the same project (amongst other projects which may or may not overlap). 
`std::shared_ptr` adds a reference count to track how many owners exist. When the count hits zero → the resource is deleted.


### Inside a std::shared_ptr

A shared_ptr consists of:
```
+------------------------------------------+
| Control Block                            |
|------------------------------------------|
|  Strong ref count                        |
|  Weak ref count                          |
|  Deleter function pointer                |
|------------------------------------------|
|  (optional allocator, type info, etc.)   |
+------------------------------------------+
| Managed object (allocated separately or folded) |
+------------------------------------------+

```
That control block is where all that “smart”_ness_ lives.

#### Two Ways to Create a shared_ptr
---

(A) Direct construction
```c++
auto p = std::shared_ptr<int>(new int(42));
```
This creates wwo allocations:
```
[ control block ]  [ int(42) ]
```
Simple, explicit, works on all C++ versions. The control block and the object live in separate heap blocks.

(B) Using std::make_shared
```c++
auto p = std::make_shared<int>(42);
```
What this does is, it does a folded allocation (single heap block):
```
[ control block | int(42) ]
```
This saves one allocation and improves cache locality. That’s the main reason make_shared exists. But folding requires Compile-Time Size Knowledge. To “fold” both pieces together, the library must know:
- sizeof(control_block) (fixed)
- sizeof(T) (depends on your type)
- alignof(T)
- how to construct and destroy T

The compiler determines all of this at compile time. If the object’s size isn’t known until runtime — folding can’t work. But there's a gotcha here with how this works with arrays, which typically break this model (they don't after the C++ standard 20 but most folks are yet to adopt that compiler).

##### Arrays with `make_shared`
The following statement would fail to compile on a system without C++ 20 support (both the compiler as well as the standard library)
```c++
std::make_shared<int[]>(5);
```
The type int[] is an array of unknown bound. The 5 is a runtime value, not part of the type. At compile time, the compiler cannot compute:
```c++
sizeof(int[])
```
It has no idea how big the combined [control block | array] block should be. Hence, no viable `make_shared` overload existed before C++20. This doesn't mean we can use bounded array types with `make_shared`. Even though something like int[5] has a known size at compile time, pre-C++20 standard libraries did not provide any `make_shared` overloads for array types at all. So something like:
```C++
auto p = std::make_shared<int[5]>();  // illegal before C++20
```
will _still_ fail to compile before C++ 20, even though sizeof(int[5]) is known. 

_WHY_?
- The library simply didn’t define overloads that accepted array types (T[N] or T[]).
- make_shared templates were constrained to “object types,” and int[5] is not a valid object type parameter in those templates.
- So even with compile-time knowledge of 5, overload resolution never matched — there was no candidate function.

So if one is not with C++20, `make_shared` should _only_ be used with 'scalar' types and is typically used to create shared pointers to scalar custom classes. A safe way to create a shared pointer to an array is shown below

$ The “Legal Pre-C++20 Way”
```c++
auto p = std::shared_ptr<int[]>(new int[5]);  
```
This works fine because it performs two separate allocations:
```
[ control block ]        [ int[5] ]

```
- The array (new int[5]) happens at runtime.
- The control block (for refcounting) is created separately, also at runtime.
- The compiler never needed to know how many elements exist.
Since C++17, shared_ptr<T[]> automatically uses delete[] — so this is safe.
---

#### C++20 to the Rescue

Proposal P0674R1 (C++20) introduced proper overloads:
```c++
auto a = std::make_shared<int[]>(5);   // unbounded array
auto b = std::make_shared<int[5]>();   // bounded array

```
Now the standard library knows how to:
- Allocate one combined block for the control structure and array
- Default/value-initialize array elements
- Destroy all elements safely when refcount hits zero
These new overloads were standardized in C++20. The standards recommend checking the following feature macro to determine support for arrays with shared pointers
with the feature test macro:
```c++
#if defined(__has_include)
#  if __has_include(<version>)
#    include <version>
#  endif
#endif
#include <memory>

#if defined(__cpp_lib_shared_ptr_arrays) && __cpp_lib_shared_ptr_arrays >= 201707L
```

If this sounds like too much of a hassle, best to stick with 
```c++
auto p = std::shared_ptr<int[]>(new int[5]);

```
That constructor has existed since C++17. It just doesn’t fold allocations, but it does handle cleanup correctly (delete[]).

## Visual Cheat Sheet
```
make_shared<int>(42)        → [ctrl | int]
make_shared<int[5]>()       → [ctrl | int[5]]      (C++20+)
make_shared<int[]>(n)       → [ctrl | int[n]]      (C++20+)
shared_ptr(new int[5])      → [ctrl] [int[5]]      (always OK)
```

## Runtime vs Compile-Time Roles
As a recap, lets go over what happens at compile time vs run time. Deducing the type (of the object being shared), computing its size and layout happens at compile type whereas actual mem allocation, object construction and management of reference counts happen at run time.
So, all work happens at runtime, but the recipe (layout and folding plan) must be complete at compile time. Incomplete or runtime-sized types break that plan.


## One-Line Summary to Remember
- make_shared = “single folded allocation → needs known size.”
- shared_ptr(new …) = “two allocations → runtime size OK.”
- C++20 finally teaches make_shared to handle arrays, but older libraries (like GCC 11.3) don’t implement that lesson yet.