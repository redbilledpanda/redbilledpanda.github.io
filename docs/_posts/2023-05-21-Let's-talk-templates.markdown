---
layout: post
title:  "Let's talk templates!"
date:   2023-05-21 08:42:48 +0530
tags: 
    - C++
    - Templates
    - overloading
---
Let's refresh our rather rusty C++ starting with one of the language's more commonly used feature; one which also differentiates it from good old C! Aptly named "templates", it is usually used for generating code on the fly. A rather typical scenario would include having a templatized version of a function which can then be used with different arguments. Since this (multiple functions with the same name having differing argument types) is valid C++, it saves us a bunch of typing.

Without further ado, let's see how it looks!

```C++
#include <iostream>

template<typename T>
void swap(T &a, T &b) {
  T temp;

  temp = a;
  a = b;
  b = temp;
}

int main() {
    using namespace std;

    int a,b;

    a = 7, b = 10;

    cout << "a is " << a << " while b is " << b << endl;
    swap(a,b);
    cout << "a is " << a << " while b is " << b << endl;
    
    return 0;
}
```

As can be seen, the keyword `template` defines a template function. There's no point to a template without a placeholder who's type will be determined at run-time. This is exactly what the statement  `typename T` does. Once this placeholder has been defined, we can use it just like any other type. Since we're just getting (re)started with C++, let's keep it simple with just one type.<br/>

Compiling this as is will give us a compile time error! gcc (v13) tell us that
```shell
<source>: In function 'int main()':
<source>:21:9: error: call of overloaded 'swap(int&, int&)' is ambiguous
   21 |     swap(a,b);
      |     ~~~~^~~~~
In file included from /opt/compiler-explorer/gcc-13.1.0/include/c++/13.1.0/bits/exception_ptr.h:41,
                 from /opt/compiler-explorer/gcc-13.1.0/include/c++/13.1.0/exception:164,
                 from /opt/compiler-explorer/gcc-13.1.0/include/c++/13.1.0/ios:41,
                 from /opt/compiler-explorer/gcc-13.1.0/include/c++/13.1.0/ostream:40,
                 from /opt/compiler-explorer/gcc-13.1.0/include/c++/13.1.0/iostream:41,
                 from <source>:2:
/opt/compiler-explorer/gcc-13.1.0/include/c++/13.1.0/bits/move.h:196:5: note: candidate: 'std::_Require<std::__not_<std::__is_tuple_like<_Tp> >, std::is_move_constructible<_Tp>, std::is_move_assignable<_Tp> > std::swap(_Tp&, _Tp&) [with _Tp = int; _Require<__not_<__is_tuple_like<_Tp> >, is_move_constructible<_Tp>, is_move_assignable<_Tp> > = void]'
  196 |     swap(_Tp& __a, _Tp& __b)
      |     ^~~~
<source>:5:6: note: candidate: 'void swap(T&, T&) [with T = int]'
    5 | void swap(T &a, T &b) {
      |      ^~~~
```

It appears the template library (a collection of powerful functions pre-defined for our use) already implements a swap function. Which is why our function here is not allowed (as conflict ensues, literally!). For it to work, we need to replace <s>swap</s> with _<b>S</b>wap_ (mind you C++, like C, is case sensitive). Once done, it compiles and then we can use it with any kind of arguments (provided both a and b are interoperable).

Let's see how the resulting binary would look like when used with a good 'ol integer. Running `objdump` on it with the `-C` switch (for unmangling the decorated function names, which the g++ compiler does) we see this (partial output for brevity):
```asm
000000000000136f <void Swap<int>(int&, int&)>:
    136f:       f3 0f 1e fa             endbr64
    1373:       55                      push   %rbp
    1374:       48 89 e5                mov    %rsp,%rbp
    1377:       48 89 7d e8             mov    %rdi,-0x18(%rbp)
    137b:       48 89 75 e0             mov    %rsi,-0x20(%rbp)
    137f:       48 8b 45 e8             mov    -0x18(%rbp),%rax
    1383:       8b 00                   mov    (%rax),%eax
    1385:       89 45 fc                mov    %eax,-0x4(%rbp)
    1388:       48 8b 45 e0             mov    -0x20(%rbp),%rax
    138c:       8b 10                   mov    (%rax),%edx
    138e:       48 8b 45 e8             mov    -0x18(%rbp),%rax
    1392:       89 10                   mov    %edx,(%rax)
    1394:       48 8b 45 e0             mov    -0x20(%rbp),%rax
    1398:       8b 55 fc                mov    -0x4(%rbp),%edx
    139b:       89 10                   mov    %edx,(%rax)
    139d:       90                      nop
    139e:       5d                      pop    %rbp
    139f:       c3                      ret
```

We thus see that the template was filled out and replaced with an actual `Swap` function that takes two integer references as input!