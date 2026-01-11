---
layout: post
title: "OOP Concepts in the Account Example (Section 09)"
date: 2026-01-11 16:42:48 +0530
tags:
  - C++
  - OOP
  - encapsulation
  - inheritance
  - polymorphism
  - RTTI
---
# OOP Concepts in the Account Example

This note summarizes the **object-oriented programming concepts** demonstrated using the simple banking example shown [here](https://github.com/redbilledpanda/Complete-Modern-C-Plus-Plus-11-14-17/tree/master/Section%2009/Account/Account). The focus is on the class design and runtime behavior, with only brief mention of utilities like persistence or user prompts.

## 1) Encapsulation (data + behavior)

The [`Account`](https://github.com/redbilledpanda/Complete-Modern-C-Plus-Plus-11-14-17/blob/master/Section%2009/Account/Account/Account.h#L3) class wraps state and behavior together:

- **Private data members** (`m_Name`, `m_AccNo`, `m_Closed`) are hidden from direct
  external access.
- **Public methods** (`GetName`, `Deposit`, `Withdraw`) expose controlled access.

The derived types ([`Checking`](https://github.com/redbilledpanda/Complete-Modern-C-Plus-Plus-11-14-17/blob/master/Section%2009/Account/Account/Checking.h#L3), [`Savings`](https://github.com/redbilledpanda/Complete-Modern-C-Plus-Plus-11-14-17/blob/master/Section%2009/Account/Account/Savings.h#L3)) also encapsulate
their own private state: `m_MinimumBalance` and `m_Rate`. This keeps each account’s
invariants inside its class.

## 2) Inheritance (is-a relationships)

`Checking` and `Savings` inherit from `Account`:

```cpp
class Checking : public Account { ... };
class Savings : public Account { ... };
```

This models an **is-a** relationship: a checking account *is an* account, and can be
used anywhere an `Account` is expected.

## 3) Polymorphism (runtime dispatch)

`Account` declares virtual functions such as:

- `virtual void AccumulateInterest();`
- `virtual void Withdraw(float amount);`
- `virtual float GetInterestRate() const;`

When `Account*` or `Account&` points to a `Checking` or `Savings` instance, the
overridden implementation is called at runtime. This is used in
`Transact(Account*)` and in the main loop where accounts are stored
as `std::unique_ptr<Account>` in [`main.cpp`](https://github.com/redbilledpanda/Complete-Modern-C-Plus-Plus-11-14-17/blob/master/Section%2009/Account/Account/main.cpp).

## 4) Function overriding and specialization

Derived classes **override** base behavior to enforce specific rules:

- `Checking::Withdraw` checks minimum balance before delegating to `Account::Withdraw`.
- `Savings::AccumulateInterest` applies its rate to the balance.

This shows **behavior specialization** without rewriting the entire base class.

## 5) Protected members for controlled reuse

`Account` keeps `m_Balance` in the **protected** section so derived classes can use
it directly (e.g., `Savings::AccumulateInterest`) while still hiding it from general
external access.

## 6) Static members (class-level state)

`Account::s_ANGenerator` is a **static member** that tracks the next account number.
It belongs to the class, not any specific instance, and is synchronized in the
constructor and via `Account::SyncAccountNumber`.

## 7) RTTI and safe downcasting

`dynamic_cast` is used in [`Transaction.cpp`](https://github.com/redbilledpanda/Complete-Modern-C-Plus-Plus-11-14-17/blob/master/Section%2009/Account/Account/Transaction.cpp) and in account reporting to safely check whether a base pointer actually refers to a `Checking` or `Savings`
instance. This is a practical example of **RTTI (Run-Time Type Information)**.

## 8) Constructors and object initialization

Constructors initialize base and derived parts cleanly:

- `Checking` and `Savings` call the `Account` constructor in their initializer list.
- `using Account::Account;` in `Checking` illustrates constructor inheritance.

This shows how **construction flows from base to derived**.

---

### Passing references to non-OOP features

The example also includes **persistence** (saving accounts to a file) and **user input**
prompts. These are helpful utilities but are not central to the OOP concepts described
above.